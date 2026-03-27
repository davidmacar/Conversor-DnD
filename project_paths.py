from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    editor_dir: Path
    editor_templates_dir: Path
    editor_static_dir: Path
    data_dir: Path
    output_dir: Path
    templates_dir: Path
    fonts_dir: Path
    character_json: Path
    template_pdf: Path
    default_output_pdf: Path
    font_ttf: Path


def _resolve_env_path(env_name: str, default_path: Path, project_root: Path) -> Path:
    raw_value = os.environ.get(env_name, "").strip()
    if not raw_value:
        return default_path.resolve()

    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve()


def get_project_paths() -> ProjectPaths:
    project_root = Path(__file__).resolve().parent
    editor_dir = _resolve_env_path("DND_EDITOR_DIR", project_root / "editor", project_root)

    data_dir = _resolve_env_path("DND_DATA_DIR", project_root / "data", project_root)
    output_dir = _resolve_env_path("DND_OUTPUT_DIR", project_root / "output", project_root)
    templates_dir = _resolve_env_path("DND_TEMPLATES_DIR", project_root / "templates", project_root)
    fonts_dir = _resolve_env_path("DND_FONTS_DIR", project_root / "fonts", project_root)

    character_json = _resolve_env_path("DND_CHARACTER_JSON", data_dir / "personaje.json", project_root)
    template_pdf = _resolve_env_path(
        "DND_TEMPLATE_PDF",
        templates_dir / "Hoja-Personaje-Editable-Completa-ES.pdf",
        project_root,
    )
    default_output_pdf = _resolve_env_path(
        "DND_OUTPUT_PDF",
        output_dir / "personaje_export.pdf",
        project_root,
    )
    font_ttf = _resolve_env_path("DND_FONT_TTF", fonts_dir / "CaslonAntique-Regular.ttf", project_root)

    return ProjectPaths(
        project_root=project_root,
        editor_dir=editor_dir,
        editor_templates_dir=editor_dir / "templates",
        editor_static_dir=editor_dir / "static",
        data_dir=data_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        fonts_dir=fonts_dir,
        character_json=character_json,
        template_pdf=template_pdf,
        default_output_pdf=default_output_pdf,
        font_ttf=font_ttf,
    )


def ensure_runtime_directories(paths: ProjectPaths) -> None:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)


def collect_missing_required_paths(paths: ProjectPaths) -> list[str]:
    missing: list[str] = []
    if not paths.editor_templates_dir.exists():
        missing.append(f"No existe la carpeta de templates web: {paths.editor_templates_dir}")
    if not paths.editor_static_dir.exists():
        missing.append(f"No existe la carpeta de static web: {paths.editor_static_dir}")
    if not paths.template_pdf.exists():
        missing.append(f"No existe la plantilla PDF: {paths.template_pdf}")
    if not paths.font_ttf.exists():
        missing.append(f"No existe la fuente TTF: {paths.font_ttf}")
    return missing


def get_paths_status(paths: ProjectPaths) -> dict:
    return {
        "project_root": str(paths.project_root),
        "editor_dir": str(paths.editor_dir),
        "data_dir": str(paths.data_dir),
        "output_dir": str(paths.output_dir),
        "templates_dir": str(paths.templates_dir),
        "fonts_dir": str(paths.fonts_dir),
        "character_json": str(paths.character_json),
        "template_pdf": str(paths.template_pdf),
        "font_ttf": str(paths.font_ttf),
        "editor_templates_exists": paths.editor_templates_dir.exists(),
        "editor_static_exists": paths.editor_static_dir.exists(),
        "template_pdf_exists": paths.template_pdf.exists(),
        "font_ttf_exists": paths.font_ttf.exists(),
        "character_json_exists": paths.character_json.exists(),
    }
