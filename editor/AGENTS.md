# EDITOR MODULE: Flask Web Application

D&D Character Editor web interface. Single-page Alpine.js frontend served by Flask backend.

## STRUCTURE

```
editor/
├── app.py              # Flask app (~600 lines, ~20 routes)
├── __init__.py         # Package marker
├── requirements.txt    # Python deps (Flask, PyMuPDF, etc.)
├── start.bat          # Windows dev runner
├── static/
│   ├── js/editor.js   # Alpine.js app (~2200 lines) — all UI logic
│   ├── css/style.css  # Custom styles (~2400 lines)
│   └── img/           # Character portrait uploads
└── templates/
    └── index.html     # Single-page app template (~1500 lines)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `app.py` | Add @app.route directly (no Blueprints) |
| Fix character loading | `app.py:_load_json()` | Line ~149 |
| Fix storage quota | `app.py:40-43` | DND_STORAGE_LIMIT_BYTES env var |
| Update frontend | `static/js/editor.js` | `characterEditor()` returns all data/methods |
| Change UI strings | `static/js/editor.js` | All Spanish user-facing text |
| Field limits display | `static/js/editor.js:sectionCharCount()` | Char counting per section |
| Red border logic | `static/js/editor.js:isOverLimit()` | Over-limit detection |
| Speed calculations | `static/js/editor.js:updateAll()` | Auto-calculates derived speed fields |
| Create character | `static/js/editor.js:createNewCharacter()` | Empty template generation |
| Load JSON | `static/js/editor.js:loadFromJson()` | Drag & drop + paste |
| Export JSON | `static/js/editor.js:exportJson()` | Client-side generation |
| Keyboard shortcuts | `static/js/editor.js:init()` | Ctrl+S handler |

## CONVENTIONS

- Routes use `/api/*` prefix for JSON endpoints
- Storage quota enforced via `_assert_storage_capacity()`
- Custom exceptions → `register_error_handlers()` for Flask
- `PATHS` global from `project_paths` module (import-time side effect)
- Field limits fetched from `/api/field-limits` on init

## ANTI-PATTERNS

- No Flask Blueprints — all routes in single file
- Module-level side effects on import (lines 24-26)
- 2200+ line monolithic JS file with no modules
- No frontend build step (pure CDN Alpine.js + vanilla CSS)

## FEATURES

### Character Management
- **Create new**: "✦ Nuevo" button with empty template and custom filename
- **Load JSON**: Modal with drag & drop or textarea paste
- **Export JSON**: Client-side pretty-printed generation
- **Export PDF**: Inline SVG document icon with gold hover effect
- **Save**: Ctrl+S keyboard shortcut + button

### Field Limits & Validation
- **Real-time counters**: Top-right positioned char counters on cards/fields
- **Red borders**: `.card-over-limit` for sections, `.textarea-over-limit` for individual fields
- **Limits**: appearance (550), personality/ideals/bonds/flaws/allies/enemies (550 each), backstory (1250), class+species features combined (1450), feats (1400), notes (1500)
- **API endpoint**: `/api/field-limits` returns hardcoded limits dict

### Auto-Calculations
- **Speed**: swim/fly/climb = walking speed; hour/day = derived from base
- **Jumps**: long = strength × 0.3048m; high = (3 + str_mod) × 0.3048m
- **Stats**: All modifiers auto-calculated from ability scores

### UI/UX
- **Theme**: Dark parchment medieval with gold accents
- **Fonts**: Cinzel (titles), Crimson Text (body)
- **Responsive**: Cards layout, mobile-friendly forms
- **Attacks section**: Reformatted with title, properties, stats, notes rows
