# PROJECT KNOWLEDGE BASE: Conversor-DnD

**Generated:** 2026-05-03
**Branch:** main

## OVERVIEW

D&D 5.5 (2024) character sheet converter/editor. Parses HTML from Nivel20.com, stores JSON characters, generates filled PDFs using PyMuPDF. Flask backend + Alpine.js frontend.

## STRUCTURE

```
.
├── app.py                    # Entry point (wrapper → editor.app)
├── docker-compose.yml        # Container orchestration
├── Dockerfile                # Container build
├── editor/                   # Flask web application
│   ├── app.py               # Main Flask app (~600 lines, ~20 routes)
│   ├── static/              # Frontend assets
│   │   ├── js/editor.js     # Alpine.js app (~2200 lines)
│   │   ├── css/style.css    # Styles (~2400 lines)
│   │   └── img/             # Character portraits
│   └── templates/           # Jinja2 templates
│       └── index.html       # Single-page editor (~1500 lines)
├── scripts/                  # Core business logic
│   ├── parse_character.py   # HTML→JSON parser (1757 lines)
│   ├── generate_pdf.py      # JSON→PDF generator (~1940 lines)
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
| Field limits | `scripts/generate_pdf.py:FIELD_LIMITS` | Hardcoded char limits for PDF fields |
| Speed calculations | `editor/static/js/editor.js:updateAll()` | Auto-calculates swim/fly/climb/jump from walking speed |

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
| `FIELD_LIMITS` | dict | `scripts/generate_pdf.py` | Hardcoded field char limits |
| `updateAll()` | method | `editor/static/js/editor.js:950` | Auto-calculates derived fields |
| `sectionCharCount()` | method | `editor/static/js/editor.js` | Calculates chars per section |
| `isOverLimit()` | method | `editor/static/js/editor.js` | Checks if section exceeds limit |

## CONVENTIONS

- **Imports**: stdlib → third-party → local; all scripts bootstrap `sys.path` at top
- **Paths**: Use `project_paths.get_project_paths()` — never hardcode paths
- **Environment**: All config via `DND_*` env vars (see docker-compose.yml)
- **Error handling**: Custom exceptions (e.g., `StorageQuotaExceeded`) → Flask error handlers
- **Typing**: Modern Python type hints throughout (dataclasses preferred)
- **Comments**: Spanish for intent, English for code symbols

## ANTI-PATTERNS (THIS PROJECT)

- **No modular frontend**: `editor.js` is 2200+ lines with no code splitting
- **No Flask Blueprints**: All routes in single `editor/app.py`
- **Module-level side effects**: `editor/app.py` lines 24-26 run at import time
- **Broad exception catching**: Several routes catch bare `Exception`
- **Duplicate app.py names**: Root `app.py` and `editor/app.py` confuse entry points

## UNIQUE STYLES

- **Spanish UI strings**: All user-facing messages in Spanish
- **Field naming**: PDF fields use Spanish names ("Dotes", "Rasgo", "Puntuacion-Fuerza")
- **Continuous text blocks**: Custom field-filling system for multi-line text (see `ContinuousBlockSpec`)
- **PDF widget manipulation**: Direct xref manipulation for AcroForm fields
- **Theme**: Dark parchment medieval theme with gold accents

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

## FEATURES IMPLEMENTED

### PDF Generation
- **Text flow fix**: Race/class feature titles render on same line as description when space allows
- **Flattened PDFs**: Text rendered statically (not editable), checkboxes remain interactive
- **Font sizes**: Dynamic sizing (10pt/8pt/7pt/6pt) based on field importance; background fields fixed at 6pt
- **Centered fields**: Speed/movement fields (Velocidad, Salto, etc.) centered in PDF text boxes
- **Field limits**: Hardcoded `FIELD_LIMITS` dict with char limits per section

### Web Editor
- **Character counters**: Real-time char counters with red borders when exceeding PDF limits
- **Field limits enforced**: 
  - 550 chars: appearance summary, personality traits, ideals, bonds, flaws, allies, enemies
  - 1250 chars: backstory
  - 1450 chars: combined class + species features
  - 1400 chars: feats
  - 1500 chars: notes
- **Auto-calculation**: Speed/movement fields auto-calculated from base walking speed
- **Create character**: "✦ Nuevo" button with empty character template
- **Load JSON**: Drag & drop or paste JSON to load character
- **Export JSON**: Client-side JSON generation with pretty-print
- **Export PDF**: Inline SVG document icon with gold hover effect
- **Attacks & Weapons**: Reformatted with title, properties, stats, and notes rows
- **Keyboard shortcuts**: Ctrl+S to save

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
