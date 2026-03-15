import copy
import json
import os
import re
import sys
import time
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in dev

_STATIC_VERSION = str(int(time.time()))

@app.context_processor
def inject_version():
    return {'v': _STATIC_VERSION}

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.normpath(os.path.join(BASE_DIR, '..'))
DATA_DIR     = Path(ROOT_DIR) / 'data'
TEMPLATE_PDF = os.path.join(ROOT_DIR, 'templates', 'Hoja-Personaje-Editable-Completa-ES.pdf')
OUTPUT_PDF   = os.path.join(ROOT_DIR, 'output', 'personaje_export.pdf')

# Legacy: single active JSON (used as fallback when no character_id)
JSON_PATH    = str(DATA_DIR / 'personaje.json')

# ── Import scripts (parse_character + generate_pdf) ──────────────────────────
_SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

try:
    from parse_character import parse_html as _parse_html
    PARSE_OK = True
except Exception as _e:
    PARSE_OK = False
    _PARSE_ERR = str(_e)

try:
    from generate_pdf import generate as _fill_pdf
    FILL_OK = True
except Exception as _e:
    FILL_OK = False
    _FILL_ERR = str(_e)


# ── Smart-merge helpers ────────────────────────────────────────────────────────

def _get_nested(d: dict, dotted_key: str):
    """Obtiene un valor anidado por path con puntos. Ej: 'basic_info.name'"""
    parts = dotted_key.split('.')
    current = d
    for p in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(p)
    return current


def _set_nested(d: dict, dotted_key: str, value) -> None:
    """Establece un valor anidado por path con puntos. Crea nodos intermedios."""
    parts = dotted_key.split('.')
    current = d
    for p in parts[:-1]:
        if p not in current or not isinstance(current[p], dict):
            current[p] = {}
        current = current[p]
    current[parts[-1]] = value


def _smart_merge(existing: dict, new_data: dict) -> dict:
    """
    Actualiza en `existing` solo las claves listadas en new_data._meta.nivel20_keys,
    preservando todos los demás campos (ediciones manuales).
    """
    nivel20_keys = new_data.get('meta', {}).get('nivel20_keys', [])
    merged = copy.deepcopy(existing)
    for dotted_key in nivel20_keys:
        val = _get_nested(new_data, dotted_key)
        if val is not None:
            _set_nested(merged, dotted_key, val)
    # Siempre actualizar meta (sync info)
    merged['meta'] = new_data.get('meta', merged.get('meta', {}))
    return merged


def _find_character_json(character_id) -> Path | None:
    """Busca el fichero JSON de un personaje por su ID en data/."""
    if character_id is None:
        return None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for f in DATA_DIR.glob('*.json'):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if str(data.get('meta', {}).get('character_id')) == str(character_id):
                return f
        except Exception:
            continue
    return None


def _safe_filename(name: str) -> str:
    """Convierte un nombre a slug seguro para nombre de fichero."""
    name = name.lower()
    name = re.sub(r'[áàâä]', 'a', name)
    name = re.sub(r'[éèêë]', 'e', name)
    name = re.sub(r'[íìîï]', 'i', name)
    name = re.sub(r'[óòôö]', 'o', name)
    name = re.sub(r'[úùûü]', 'u', name)
    name = re.sub(r'[ñ]', 'n', name)
    name = re.sub(r'[^a-z0-9_-]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name or 'personaje'


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/characters', methods=['GET'])
def list_characters():
    """Lista todos los personajes guardados en data/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    chars = []
    for f in sorted(DATA_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            meta = data.get('meta', {})
            bi   = data.get('basic_info', {})
            chars.append({
                'filename':     f.name,
                'character_id': meta.get('character_id'),
                'name':         bi.get('name', f.stem),
                'classes':      bi.get('classes', []),
                'total_level':  bi.get('total_level'),
                'species':      bi.get('species'),
                'last_sync':    meta.get('last_sync'),
            })
        except Exception:
            continue
    return jsonify(chars)


@app.route('/api/character', methods=['GET'])
def get_character():
    """Carga un personaje. Acepta ?id=XXXX o devuelve el activo por defecto."""
    char_id = request.args.get('id')
    if char_id:
        path = _find_character_json(char_id)
        if path is None:
            return jsonify({'status': 'error', 'message': f'Personaje {char_id} no encontrado'}), 404
        return jsonify(json.loads(path.read_text(encoding='utf-8')))
    # Fallback: personaje.json
    if not os.path.exists(JSON_PATH):
        return jsonify({}), 404
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/character', methods=['POST'])
def save_character():
    data = request.get_json()
    if data is None:
        return jsonify({'status': 'error', 'message': 'JSON inválido'}), 400

    char_id = data.get('meta', {}).get('character_id')
    if char_id:
        existing_path = _find_character_json(char_id)
        if existing_path:
            existing_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            return jsonify({'status': 'ok', 'file': existing_path.name})

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'ok', 'file': 'personaje.json'})


@app.route('/api/import', methods=['POST'])
def import_character():
    """Descarga y parsea un personaje desde una URL de Nivel20.
    Si ya existe un JSON guardado para ese character_id, hace smart-merge.
    """
    if not PARSE_OK:
        return jsonify({'status': 'error', 'message': f'parse_character no disponible: {_PARSE_ERR}'}), 500

    req_data = request.get_json() or {}
    url = req_data.get('url', '').strip()
    if not url:
        return jsonify({'status': 'error', 'message': 'URL requerida'}), 400
    if not url.startswith('http'):
        return jsonify({'status': 'error', 'message': 'URL inválida (debe empezar por http)'}), 400

    try:
        new_data = _parse_html(url)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    char_id = new_data.get('meta', {}).get('character_id')

    # Buscar JSON existente para este personaje
    existing_path = _find_character_json(char_id) if char_id else None

    if existing_path and existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding='utf-8'))
            merged = _smart_merge(existing, new_data)
        except Exception:
            merged = new_data
        existing_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
        return jsonify(merged)
    else:
        # Nuevo personaje: guardar con nombre descriptivo
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        char_name  = _safe_filename(new_data.get('basic_info', {}).get('name', 'personaje'))
        out_name   = f"{char_name}-{char_id}.json" if char_id else 'personaje.json'
        out_path   = DATA_DIR / out_name
        out_path.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding='utf-8')
        return jsonify(new_data)


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Guarda el JSON actual y genera el PDF relleno para descargar."""
    if not FILL_OK:
        return jsonify({'status': 'error', 'message': f'generate_pdf no disponible: {_FILL_ERR}'}), 500
    if not os.path.exists(TEMPLATE_PDF):
        return jsonify({'status': 'error', 'message': f'Plantilla no encontrada: {TEMPLATE_PDF}'}), 500

    data = request.get_json()

    # Guardar el JSON antes de generar el PDF
    if data:
        char_id = data.get('meta', {}).get('character_id')
        save_path = None
        if char_id:
            save_path = _find_character_json(char_id)
        if save_path is None:
            save_path = Path(JSON_PATH)
        save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    active_json = save_path if (data and save_path) else Path(JSON_PATH)
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

    try:
        _fill_pdf(active_json, Path(TEMPLATE_PDF), Path(OUTPUT_PDF))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    char_name = (data or {}).get('basic_info', {}).get('name', 'personaje')
    download_name = f"{char_name}_hoja.pdf"
    return send_file(OUTPUT_PDF, as_attachment=True, mimetype='application/pdf',
                     download_name=download_name)


@app.route('/api/status', methods=['GET'])
def api_status():
    """Devuelve qué módulos están disponibles."""
    return jsonify({
        'parse_ok': PARSE_OK,
        'fill_ok':  FILL_OK,
    })


if __name__ == '__main__':
    print("=" * 52)
    print("  Editor de Hoja D&D 2024")
    print(f"  parse_character: {'OK' if PARSE_OK else 'NO DISPONIBLE'}")
    print(f"  generate_pdf:    {'OK' if FILL_OK else 'NO DISPONIBLE'}")
    print("  http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000)
