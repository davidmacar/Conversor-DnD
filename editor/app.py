import io
import json
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_file

_EDITOR_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _EDITOR_FILE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from project_paths import (  # noqa: E402
    collect_missing_required_paths,
    ensure_runtime_directories,
    get_paths_status,
    get_project_paths,
)

PATHS = get_project_paths()
ensure_runtime_directories(PATHS)
STARTUP_PATH_ERRORS = collect_missing_required_paths(PATHS)

app = Flask(
    __name__,
    template_folder=str(PATHS.editor_templates_dir),
    static_folder=str(PATHS.editor_static_dir),
    static_url_path='/static',
)

# ── Import scripts (parse_character + generate_pdf) ──────────────────────────
try:
    from scripts.parse_character import parse_html as _parse_html

    PARSE_OK = True
except Exception as _e:
    PARSE_OK = False
    _PARSE_ERR = str(_e)

try:
    from scripts.generate_pdf import generate as _generate_pdf

    PDF_EXPORT_OK = True
except Exception as _e:
    PDF_EXPORT_OK = False
    _PDF_EXPORT_ERR = str(_e)


def _iter_character_json_files():
    data_dir = PATHS.data_dir
    ignored = {'parsed_check.json'}
    if not data_dir.is_dir():
        return
    for file_path in sorted(data_dir.glob('*.json')):
        filename = file_path.name
        if not filename.lower().endswith('.json'):
            continue
        if filename in ignored:
            continue
        if file_path.is_file():
            yield filename, file_path


def _load_json(path: Path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', v='1')


@app.route('/api/character', methods=['GET'])
def get_character():
    char_id = str(request.args.get('id', '')).strip()

    # Keep backward-compatible behavior when no id is requested.
    if not char_id:
        if not PATHS.character_json.exists():
            return jsonify({
                'status': 'error',
                'message': f'No se encuentra el archivo de personaje: {PATHS.character_json}',
            }), 404
        return jsonify(json.loads(PATHS.character_json.read_text(encoding='utf-8')))

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
    PATHS.character_json.parent.mkdir(parents=True, exist_ok=True)
    PATHS.character_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
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
        PATHS.character_json.parent.mkdir(parents=True, exist_ok=True)
        PATHS.character_json.write_text(
            json.dumps(character, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        return jsonify(character)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Genera el PDF para descargar usando un payload temporal enviado por la web."""
    if not PDF_EXPORT_OK:
        return jsonify({'status': 'error', 'message': f'generate_pdf no disponible: {_PDF_EXPORT_ERR}'}), 500
    if not PATHS.template_pdf.exists():
        return jsonify({'status': 'error', 'message': f'Plantilla no encontrada: {PATHS.template_pdf}'}), 500
    if not PATHS.font_ttf.exists():
        return jsonify({'status': 'error', 'message': f'Fuente no encontrada: {PATHS.font_ttf}'}), 500

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'message': 'Payload de exportación inválido'}), 400

    PATHS.output_dir.mkdir(parents=True, exist_ok=True)

    fd_json, tmp_json_path = tempfile.mkstemp(
        prefix='personaje_export_payload_',
        suffix='.json',
        dir=str(PATHS.output_dir),
    )
    os.close(fd_json)
    Path(tmp_json_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    fd, tmp_pdf_path = tempfile.mkstemp(
        prefix='personaje_export_',
        suffix='.pdf',
        dir=str(PATHS.output_dir),
    )
    os.close(fd)

    try:
        _generate_pdf(Path(tmp_json_path), PATHS.template_pdf, Path(tmp_pdf_path))
    except Exception as e:
        try:
            Path(tmp_json_path).unlink(missing_ok=True)
        except Exception:
            pass
        try:
            Path(tmp_pdf_path).unlink(missing_ok=True)
        except Exception:
            pass
        return jsonify({'status': 'error', 'message': str(e)}), 500

    try:
        pdf_bytes = Path(tmp_pdf_path).read_bytes()
    finally:
        try:
            Path(tmp_json_path).unlink(missing_ok=True)
        except Exception:
            pass
        try:
            Path(tmp_pdf_path).unlink(missing_ok=True)
        except Exception:
            pass

    char_name = (data or {}).get('basic_info', {}).get('name', 'personaje')
    download_name = f"{char_name}_hoja.pdf"
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, mimetype='application/pdf',
                     download_name=download_name)


@app.route('/api/status', methods=['GET'])
def status():
    """Devuelve qué módulos están disponibles."""
    startup_errors = list(STARTUP_PATH_ERRORS)
    startup_errors.extend(_module_startup_errors())
    return jsonify({
        'parse_ok': PARSE_OK,
        'generate_ok': PDF_EXPORT_OK,
        'resources_ok': len(STARTUP_PATH_ERRORS) == 0,
        'path_errors': startup_errors,
        'paths': get_paths_status(PATHS),
    })


def _module_startup_errors() -> list[str]:
    errors = []
    if not PARSE_OK:
        errors.append(f'parse_character no disponible: {_PARSE_ERR}')
    if not PDF_EXPORT_OK:
        errors.append(f'generate_pdf no disponible: {_PDF_EXPORT_ERR}')
    return errors


def run_dev_server() -> None:
    startup_errors = list(STARTUP_PATH_ERRORS)
    startup_errors.extend(_module_startup_errors())

    print("=" * 52)
    print("  Editor de Hoja D&D 2024")
    print(f"  parse_character: {'OK' if PARSE_OK else 'NO DISPONIBLE'}")
    print(f"  generate_pdf:    {'OK' if PDF_EXPORT_OK else 'NO DISPONIBLE'}")
    print(f"  project_root:    {PATHS.project_root}")
    print(f"  data_dir:        {PATHS.data_dir}")
    print(f"  output_dir:      {PATHS.output_dir}")
    if startup_errors:
        print("  Advertencias:")
        for err in startup_errors:
            print(f"    - {err}")
    print("  http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    run_dev_server()
