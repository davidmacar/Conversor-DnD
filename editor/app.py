import io
import json
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.normpath(os.path.join(BASE_DIR, '..'))
JSON_PATH    = os.path.join(ROOT_DIR, 'data', 'personaje.json')
TEMPLATE_PDF = os.path.join(ROOT_DIR, 'templates', 'Hoja-Personaje-Editable-Completa-ES.pdf')
OUTPUT_PDF   = os.path.join(ROOT_DIR, 'output', 'personaje_export.pdf')

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
    from generate_pdf import generate as _generate_pdf
    PDF_EXPORT_OK = True
except Exception as _e:
    PDF_EXPORT_OK = False
    _PDF_EXPORT_ERR = str(_e)


def _iter_character_json_files():
    data_dir = os.path.join(ROOT_DIR, 'data')
    ignored = {'parsed_check.json'}
    if not os.path.isdir(data_dir):
        return
    for filename in sorted(os.listdir(data_dir)):
        if not filename.lower().endswith('.json'):
            continue
        if filename in ignored:
            continue
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path):
            yield filename, file_path


def _load_json(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/character', methods=['GET'])
def get_character():
    char_id = str(request.args.get('id', '')).strip()

    # Keep backward-compatible behavior when no id is requested.
    if not char_id:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))

    for _, file_path in _iter_character_json_files() or []:
        character = _load_json(file_path)
        if not character:
            continue
        current_id = character.get('meta', {}).get('character_id')
        if str(current_id).strip() == char_id:
            return jsonify(character)

    return jsonify({'status': 'error', 'message': f'Personaje no encontrado: {char_id}'}), 404


@app.route('/api/characters', methods=['GET'])
def list_characters():
    by_id = {}

    for filename, file_path in _iter_character_json_files() or []:
        character = _load_json(file_path)
        if not character:
            continue

        meta = character.get('meta') or {}
        basic_info = character.get('basic_info') or {}
        character_id = meta.get('character_id')
        if character_id in (None, ''):
            continue

        key = str(character_id).strip()
        if not key or key in by_id:
            continue

        classes = basic_info.get('classes')
        if not isinstance(classes, list):
            classes = []

        name = str(basic_info.get('name') or Path(filename).stem).strip()
        by_id[key] = {
            'character_id': character_id,
            'name': name,
            'classes': classes,
            'filename': filename,
        }

    characters = sorted(by_id.values(), key=lambda c: c['name'].lower())
    return jsonify(characters)


@app.route('/api/character', methods=['POST'])
def save_character():
    data = request.get_json()
    if data is None:
        return jsonify({'status': 'error', 'message': 'JSON inválido'}), 400
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'ok'})


@app.route('/api/import', methods=['POST'])
def import_character():
    """Descarga y parsea un personaje desde una URL de Nivel20."""
    if not PARSE_OK:
        return jsonify({'status': 'error', 'message': f'parse_character no disponible: {_PARSE_ERR}'}), 500

    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'status': 'error', 'message': 'URL requerida'}), 400
    if not url.startswith('http'):
        return jsonify({'status': 'error', 'message': 'URL inválida (debe empezar por http)'}), 400

    try:
        character = _parse_html(url)
        # Persist to disk
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(character, f, ensure_ascii=False, indent=2)
        return jsonify(character)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Guarda el JSON actual y genera el PDF relleno para descargar."""
    if not PDF_EXPORT_OK:
        return jsonify({'status': 'error', 'message': f'generate_pdf no disponible: {_PDF_EXPORT_ERR}'}), 500
    if not os.path.exists(TEMPLATE_PDF):
        return jsonify({'status': 'error', 'message': f'Plantilla no encontrada: {TEMPLATE_PDF}'}), 500

    # Persist latest state from frontend before generating
    data = request.get_json()
    if data:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    output_dir = os.path.dirname(OUTPUT_PDF)
    os.makedirs(output_dir, exist_ok=True)

    fd, tmp_pdf_path = tempfile.mkstemp(prefix='personaje_export_', suffix='.pdf', dir=output_dir)
    os.close(fd)

    try:
        _generate_pdf(Path(JSON_PATH), Path(TEMPLATE_PDF), Path(tmp_pdf_path))
    except Exception as e:
        try:
            os.remove(tmp_pdf_path)
        except OSError:
            pass
        return jsonify({'status': 'error', 'message': str(e)}), 500

    try:
        with open(tmp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
    finally:
        try:
            os.remove(tmp_pdf_path)
        except OSError:
            pass

    char_name = (data or {}).get('basic_info', {}).get('name', 'personaje')
    download_name = f"{char_name}_hoja.pdf"
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, mimetype='application/pdf',
                     download_name=download_name)


@app.route('/api/status', methods=['GET'])
def status():
    """Devuelve qué módulos están disponibles."""
    return jsonify({
        'parse_ok': PARSE_OK,
        'fill_ok': PDF_EXPORT_OK,
        'generate_ok': PDF_EXPORT_OK,
    })


if __name__ == '__main__':
    print("=" * 52)
    print("  Editor de Hoja D&D 2024")
    print(f"  parse_character: {'OK' if PARSE_OK else 'NO DISPONIBLE'}")
    print(f"  generate_pdf:    {'OK' if PDF_EXPORT_OK else 'NO DISPONIBLE'}")
    print("  http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000)
