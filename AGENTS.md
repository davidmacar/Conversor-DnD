# PROJECT KNOWLEDGE BASE: Conversor-DnD

**Generated:** 2026-04-29  
**Commit:** 53a3f36  
**Branch:** main  

## OVERVIEW

D&D 5.5 (2024) character sheet converter/editor. Parses HTML from Nivel20.com, stores JSON characters, generates filled PDFs using PyMuPDF. Flask backend + Alpine.js frontend.

## STRUCTURE

```
.
├── app.py                    # Entry point (wrapper → editor.app)
├── editor/                   # Flask web application
│   ├── app.py               # Main Flask app (588 lines, ~15 routes)
│   ├── static/              # Frontend assets
│   │   ├── js/editor.js     # Alpine.js app (1400+ lines)
│   │   ├── css/style.css    # Styles
│   │   └── img/             # Character portraits
│   └── templates/           # Jinja2 templates
│       └── index.html       # Single-page editor
├── scripts/                  # Core business logic
│   ├── parse_character.py   # HTML→JSON parser (1757 lines)
│   ├── generate_pdf.py      # JSON→PDF generator (1893 lines)
│   ├── aplanar.py           # PDF flattener (421 lines)
│   └── project_paths.py     # Path resolution & validation
├── data/                     # Character JSON storage
├── output/                   # Generated PDFs
├── templates/                # PDF templates & fonts
└── fonts/                    # CaslonAntique TTF files
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `editor/app.py` | No Blueprints — add @app.route directly |
| Fix PDF generation | `scripts/generate_pdf.py` | Uses PyMuPDF (fitz), field mapping system |
| Parse Nivel20 HTML | `scripts/parse_character.py` | BeautifulSoup4, ability/skill mapping tables |
| Update frontend | `editor/static/js/editor.js` | Alpine.js, single monolithic component |
| Add font support | `templates/` + `fonts/` | TTF files referenced by path resolution |
| Storage limits | `editor/app.py` lines 40-43 | DND_STORAGE_LIMIT_BYTES env var |
| Path configuration | `scripts/project_paths.py` | All paths centralized via dataclass |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `app` | Flask | `editor/app.py:28` | Main application instance |
| `run_dev_server()` | function | `editor/app.py:573` | Entry point for development |
| `get_project_paths()` | function | `scripts/project_paths.py:36` | Resolves all project paths |
| `ProjectPaths` | dataclass | `scripts/project_paths.py:9` | Immutable path container |
| `characterEditor()` | function | `editor/static/js/editor.js` | Alpine.js data/methods |
| `generate_pdf()` | function | `scripts/generate_pdf.py` | Main PDF generation entry |
| `parse_character()` | function | `scripts/parse_character.py` | HTML parser entry |

## CONVENTIONS

- **Imports**: stdlib → third-party → local; all scripts bootstrap `sys.path` at top
- **Paths**: Use `project_paths.get_project_paths()` — never hardcode paths
- **Environment**: All config via `DND_*` env vars (see docker-compose.yml)
- **Error handling**: Custom exceptions (e.g., `StorageQuotaExceeded`) → Flask error handlers
- **Typing**: Modern Python type hints throughout (dataclasses preferred)
- **Comments**: Spanish for intent, English for code symbols

## ANTI-PATTERNS (THIS PROJECT)

- **No modular frontend**: `editor.js` is 1400+ lines with no code splitting
- **No Flask Blueprints**: All routes in single `editor/app.py`
- **Module-level side effects**: `editor/app.py` lines 24-26 run at import time
- **Broad exception catching**: Several routes catch bare `Exception`
- **Duplicate app.py names**: Root `app.py` and `editor/app.py` confuse entry points

## UNIQUE STYLES

- **Spanish UI strings**: All user-facing messages in Spanish
- **Field naming**: PDF fields use Spanish names ("Dotes", "Rasgo", "Puntuacion-Fuerza")
- **Continuous text blocks**: Custom field-filling system for multi-line text (see `ContinuousBlockSpec`)
- **PDF widget manipulation**: Direct xref manipulation for AcroForm fields

## COMMANDS

```bash
# Development
docker-compose up -d                    # Start container
docker-compose logs -f                  # Follow logs

# PDF Generation (inside container)
python scripts/generate_pdf.py          # Default: data/personaje.json → output/
python scripts/generate_pdf.py data/custom.json output/custom.pdf

# HTML Parsing (inside container)
python scripts/parse_character.py https://nivel20.com/.../ID-nombre data/out.json

# PDF Flattening
python scripts/aplanar.py input.pdf output.pdf

# Build & deploy
docker-compose build
docker-compose up -d
```

## NOTES

- No test suite exists (add pytest before refactoring)
- No CI/CD configured
- No linting/formatting config (no Black/Flake8/pyproject.toml)
- Storage quota enforced: default 1GB limit on data/output
- Font embedding: Uses standard PDF Helvetica, not embedded TTF
- Docker healthcheck hits `/api/status` endpoint

## EXTERNAL REFERENCES

- **PyMuPDF (fitz)**: PDF manipulation library
- **BeautifulSoup4**: HTML parsing for Nivel20.com
- **Alpine.js**: Frontend reactivity (loaded via CDN)
- **Nivel20.com**: Source of character HTML (D&D 2024 Spanish)
