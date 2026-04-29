import io
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_file

_EDITOR_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _EDITOR_FILE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.project_paths import (  # noqa: E402  # type: ignore[reportMissingImports]
    collect_missing_required_paths,
    ensure_runtime_directories,
    get_paths_status,
    get_project_paths,
)

PATHS = get_project_paths()
ensure_runtime_directories(PATHS)
STARTUP_PATH_ERRORS = collect_missing_required_paths(PATHS)


def _read_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name, '').strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value >= 0 else default


DEFAULT_STORAGE_LIMIT_BYTES = 1024 * 1024 * 1024
DEFAULT_EXPORT_TMP_BUDGET_BYTES = 64 * 1024 * 1024
STORAGE_LIMIT_BYTES = _read_env_int('DND_STORAGE_LIMIT_BYTES', DEFAULT_STORAGE_LIMIT_BYTES)
EXPORT_TMP_BUDGET_BYTES = _read_env_int('DND_EXPORT_TMP_BUDGET_BYTES', DEFAULT_EXPORT_TMP_BUDGET_BYTES)


class StorageQuotaExceeded(RuntimeError):
    pass


def _format_bytes(size_bytes: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    value = float(max(size_bytes, 0))
    unit = units[0]
    for candidate in units:
        unit = candidate
        if value < 1024.0 or candidate == units[-1]:
            break
        value /= 1024.0
    if unit == 'B':
        return f'{int(value)} {unit}'
    return f'{value:.2f} {unit}'


def _directory_usage_bytes(directory: Path) -> int:
    if not directory.exists():
        return 0
    total = 0
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue
        try:
            total += file_path.stat().st_size
        except OSError:
            continue
    return total


def _current_storage_usage_bytes() -> int:
    unique_dirs = []
    for directory in (PATHS.data_dir.resolve(), PATHS.output_dir.resolve()):
        if directory not in unique_dirs:
            unique_dirs.append(directory)
    return sum(_directory_usage_bytes(directory) for directory in unique_dirs)


def _assert_storage_capacity(required_extra_bytes: int = 0) -> None:
    if STORAGE_LIMIT_BYTES <= 0:
        return
    usage_bytes = _current_storage_usage_bytes()
    projected_bytes = usage_bytes + max(0, required_extra_bytes)
    if projected_bytes <= STORAGE_LIMIT_BYTES:
        return
    raise StorageQuotaExceeded(
        'Limite de almacenamiento alcanzado. '
        f'Uso actual: {_format_bytes(usage_bytes)}; '
        f'limite: {_format_bytes(STORAGE_LIMIT_BYTES)}.'
    )


def _ensure_writable_directory(directory: Path, label: str) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory, prefix='.dnd_write_probe_', delete=True):
            pass
    except OSError as exc:
        raise PermissionError(f'No hay permisos de escritura en {label}: {directory}') from exc

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
    from scripts.generate_pdf import PdfCapacityError, generate as _generate_pdf

    PDF_EXPORT_OK = True
except Exception as _e:
    PDF_EXPORT_OK = False
    _PDF_EXPORT_ERR = str(_e)
    PdfCapacityError = RuntimeError


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


def _extract_character_id(character: dict | None) -> str:
    if not isinstance(character, dict):
        return ''
    meta = character.get('meta') or {}
    return str(meta.get('character_id') or '').strip()


def _sanitize_filename(raw_filename: str | None) -> str | None:
    if raw_filename is None:
        return None

    candidate = Path(str(raw_filename)).name.strip()
    if not candidate:
        return None

    stem = Path(candidate).stem
    suffix = Path(candidate).suffix.lower()
    if suffix not in ('', '.json'):
        return None

    safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '-', stem).strip(' .-_')
    if not safe_stem:
        return None
    return f'{safe_stem}.json'


def _slugify_text(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(value or ''))
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^A-Za-z0-9]+', '-', ascii_text).strip('-').lower()


def _default_filename_for_character(character: dict) -> str:
    char_id = _extract_character_id(character)
    basic_info = character.get('basic_info') or {}
    name_slug = _slugify_text(str(basic_info.get('name') or 'personaje')) or 'personaje'
    if char_id:
        return f'{char_id}-{name_slug}.json'
    return f'{name_slug}.json'


def _find_character_matches_by_id(char_id: str):
    matches = []
    for filename, file_path in _iter_character_json_files() or []:
        character = _load_json(file_path)
        if not character:
            continue
        if _extract_character_id(character) == char_id:
            matches.append((filename, file_path, character))
    return matches


def _pick_preferred_match(matches, char_id: str):
    preferred_prefix = f'{char_id}-'
    preferred_exact = f'{char_id}.json'
    default_filename = PATHS.character_json.name.lower()

    def _rank(item):
        filename = item[0].lower()
        if filename.startswith(preferred_prefix) or filename == preferred_exact:
            return (0, filename)
        if filename == default_filename:
            return (2, filename)
        return (1, filename)

    return sorted(matches, key=_rank)[0]


def _resolve_target_path(character: dict, requested_filename: str | None, allow_create: bool = True):
    warnings = []

    if requested_filename:
        safe_filename = _sanitize_filename(requested_filename)
        if not safe_filename:
            raise ValueError('Nombre de archivo inválido para guardado')
        return PATHS.data_dir / safe_filename, warnings

    char_id = _extract_character_id(character)
    if char_id:
        matches = _find_character_matches_by_id(char_id)
        if len(matches) == 1:
            return matches[0][1], warnings
        if len(matches) > 1:
            selected = _pick_preferred_match(matches, char_id)
            warnings.append(
                f'ID duplicado {char_id}: se guardará en {selected[0]} '
                f'entre {len(matches)} archivos coincidentes.'
            )
            return selected[1], warnings
        if allow_create:
            return PATHS.data_dir / _default_filename_for_character(character), warnings

    return PATHS.character_json, warnings


def _build_character_response(character: dict, filename: str, warnings: list[str] | None = None) -> dict:
    return {
        'character': character,
        'filename': filename,
        'warnings': warnings or [],
    }


def _duplicate_character_ids() -> dict:
    by_id = {}
    for filename, file_path in _iter_character_json_files() or []:
        character = _load_json(file_path)
        if not character:
            continue
        char_id = _extract_character_id(character)
        if not char_id:
            continue
        by_id.setdefault(char_id, []).append(filename)
    return {
        char_id: sorted(files)
        for char_id, files in by_id.items()
        if len(files) > 1
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', v='1')


@app.route('/api/character', methods=['GET'])
def get_character():
    filename = str(request.args.get('filename', '')).strip()
    char_id = str(request.args.get('id', '')).strip()

    if filename:
        safe_filename = _sanitize_filename(filename)
        if not safe_filename:
            return jsonify({'status': 'error', 'message': 'Parámetro filename inválido'}), 400

        file_path = PATHS.data_dir / safe_filename
        if not file_path.exists():
            return jsonify({'status': 'error', 'message': f'Archivo no encontrado: {safe_filename}'}), 404

        character = _load_json(file_path)
        if not character:
            return jsonify({'status': 'error', 'message': f'JSON inválido en {safe_filename}'}), 500

        return jsonify(_build_character_response(character, safe_filename))

    # Keep backward-compatible behavior when no id is requested.
    if not char_id:
        if PATHS.character_json.exists():
            character = _load_json(PATHS.character_json)
            if character:
                return jsonify(_build_character_response(character, PATHS.character_json.name))

        for found_filename, file_path in _iter_character_json_files() or []:
            character = _load_json(file_path)
            if character:
                warnings = ['No se encontró personaje por defecto; se cargó el primer personaje disponible.']
                return jsonify(_build_character_response(character, found_filename, warnings))

        return jsonify({
            'status': 'error',
            'message': f'No se encontró ningún personaje en {PATHS.data_dir}',
        }), 404

    matches = _find_character_matches_by_id(char_id)
    if matches:
        warnings = []
        if len(matches) > 1:
            warnings.append(
                f'ID duplicado {char_id}: se cargó { _pick_preferred_match(matches, char_id)[0] } '
                f'entre {len(matches)} archivos coincidentes.'
            )
        selected = _pick_preferred_match(matches, char_id)
        return jsonify(_build_character_response(selected[2], selected[0], warnings))

    return jsonify({'status': 'error', 'message': f'Personaje no encontrado: {char_id}'}), 404


@app.route('/api/characters', methods=['GET'])
def list_characters():
    characters = []
    duplicate_ids = _duplicate_character_ids()

    for filename, file_path in _iter_character_json_files() or []:
        character = _load_json(file_path)
        if not character:
            continue

        meta = character.get('meta') or {}
        basic_info = character.get('basic_info') or {}
        character_id = str(meta.get('character_id') or '').strip()

        classes = basic_info.get('classes')
        if not isinstance(classes, list):
            classes = []

        name = str(basic_info.get('name') or Path(filename).stem).strip()
        characters.append({
            'character_id': character_id or None,
            'name': name,
            'classes': classes,
            'filename': filename,
            'is_duplicate_id': bool(character_id and character_id in duplicate_ids),
        })

    characters = sorted(characters, key=lambda c: (c['name'].lower(), c['filename'].lower()))
    return jsonify(characters)


@app.route('/api/character', methods=['POST'])
def save_character():
    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify({'status': 'error', 'message': 'JSON inválido'}), 400

    if 'character' in payload:
        character = payload.get('character')
        requested_filename = payload.get('filename')
        if not isinstance(character, dict):
            return jsonify({'status': 'error', 'message': 'Payload inválido: falta objeto character'}), 400
    else:
        character = payload
        requested_filename = payload.get('filename') if isinstance(payload.get('filename'), str) else None

    try:
        target_path, warnings = _resolve_target_path(character, requested_filename, allow_create=True)
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400

    try:
        _ensure_writable_directory(target_path.parent, 'data_dir')
        serialized = json.dumps(character, ensure_ascii=False, indent=2)
        new_size = len(serialized.encode('utf-8'))
        current_size = target_path.stat().st_size if target_path.exists() else 0
        _assert_storage_capacity(max(0, new_size - current_size))
        target_path.write_text(serialized, encoding='utf-8')
    except StorageQuotaExceeded as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 507
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500

    return jsonify({
        'status': 'ok',
        'filename': target_path.name,
        'warnings': warnings,
    })


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
        requested_filename = data.get('filename') if isinstance(data.get('filename'), str) else None

        try:
            target_path, warnings = _resolve_target_path(character, requested_filename, allow_create=True)
        except ValueError as exc:
            return jsonify({'status': 'error', 'message': str(exc)}), 400

        # Persist to disk
        _ensure_writable_directory(target_path.parent, 'data_dir')
        serialized = json.dumps(character, ensure_ascii=False, indent=2)
        new_size = len(serialized.encode('utf-8'))
        current_size = target_path.stat().st_size if target_path.exists() else 0
        _assert_storage_capacity(max(0, new_size - current_size))
        target_path.write_text(serialized, encoding='utf-8')
        return jsonify({
            'status': 'ok',
            'character': character,
            'filename': target_path.name,
            'warnings': warnings,
        })
    except PdfCapacityError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 422
    except StorageQuotaExceeded as e:
        return jsonify({'status': 'error', 'message': str(e)}), 507
    except PermissionError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
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

    payload_json = json.dumps(data, ensure_ascii=False, indent=2)
    payload_size = len(payload_json.encode('utf-8'))

    try:
        _ensure_writable_directory(PATHS.output_dir, 'output_dir')
        _assert_storage_capacity(payload_size + EXPORT_TMP_BUDGET_BYTES)
    except StorageQuotaExceeded as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 507
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500

    tmp_json_path: str | None = None
    tmp_pdf_path: str | None = None

    try:
        fd_json, tmp_json_path = tempfile.mkstemp(
            prefix='personaje_export_payload_',
            suffix='.json',
            dir=str(PATHS.output_dir),
        )
        os.close(fd_json)
        Path(tmp_json_path).write_text(payload_json, encoding='utf-8')

        fd, tmp_pdf_path = tempfile.mkstemp(
            prefix='personaje_export_',
            suffix='.pdf',
            dir=str(PATHS.output_dir),
        )
        os.close(fd)

        _generate_pdf(Path(tmp_json_path), PATHS.template_pdf, Path(tmp_pdf_path))
        _assert_storage_capacity(0)
        pdf_bytes = Path(tmp_pdf_path).read_bytes()
    except StorageQuotaExceeded as e:
        return jsonify({'status': 'error', 'message': str(e)}), 507
    except PermissionError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if tmp_json_path:
            try:
                Path(tmp_json_path).unlink(missing_ok=True)
            except Exception:
                pass
        if tmp_pdf_path:
            try:
                Path(tmp_pdf_path).unlink(missing_ok=True)
            except Exception:
                pass

    char_name = (data or {}).get('basic_info', {}).get('name', 'personaje')
    download_name = f"{char_name}_hoja.pdf"
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, mimetype='application/pdf',
                     download_name=download_name)


@app.route('/api/field-limits', methods=['GET'])
def field_limits():
    """Devuelve los límites aproximados de caracteres por sección del PDF."""
    if not PDF_EXPORT_OK:
        return jsonify({'status': 'error', 'message': 'PDF export no disponible'}), 503
    try:
        from scripts.generate_pdf import compute_field_limits, FONT_PATH
        limits = compute_field_limits(PATHS.template_pdf, FONT_PATH)
        return jsonify({'status': 'ok', 'limits': limits})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Devuelve qué módulos están disponibles."""
    startup_errors = collect_missing_required_paths(PATHS)
    startup_errors.extend(_module_startup_errors())
    duplicate_ids = _duplicate_character_ids()
    return jsonify({
        'parse_ok': PARSE_OK,
        'generate_ok': PDF_EXPORT_OK,
        'resources_ok': len(startup_errors) == 0,
        'storage_limit_enabled': STORAGE_LIMIT_BYTES > 0,
        'storage_limit_bytes': STORAGE_LIMIT_BYTES,
        'storage_usage_bytes': _current_storage_usage_bytes(),
        'export_tmp_budget_bytes': EXPORT_TMP_BUDGET_BYTES,
        'path_errors': startup_errors,
        'paths': get_paths_status(PATHS),
        'duplicate_character_ids': duplicate_ids,
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
    if STORAGE_LIMIT_BYTES > 0:
        print(f"  storage_limit:   {_format_bytes(STORAGE_LIMIT_BYTES)}")
        print(f"  storage_usage:   {_format_bytes(_current_storage_usage_bytes())}")
    if startup_errors:
        print("  Advertencias:")
        for err in startup_errors:
            print(f"    - {err}")
    print("  http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    run_dev_server()
