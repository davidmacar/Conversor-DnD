# EDITOR MODULE: Flask Web Application

D&D Character Editor web interface. Single-page Alpine.js frontend served by Flask backend.

## STRUCTURE

```
editor/
├── app.py              # Flask app (588 lines) — routes, storage quota, API
├── __init__.py         # Package marker
├── requirements.txt    # Python deps (Flask, PyMuPDF, etc.)
├── start.bat          # Windows dev runner
├── static/
│   ├── js/editor.js   # Alpine.js app (1400+ lines) — all UI logic
│   ├── css/style.css  # Custom styles
│   └── img/           # Character portrait uploads
└── templates/
    └── index.html     # Single-page app template
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `app.py` | Add @app.route directly (no Blueprints) |
| Fix character loading | `app.py:_load_json()` | Line ~149 |
| Fix storage quota | `app.py:40-43` | DND_STORAGE_LIMIT_BYTES env var |
| Update frontend | `static/js/editor.js` | `characterEditor()` returns all data/methods |
| Change UI strings | `static/js/editor.js` | All Spanish user-facing text |

## CONVENTIONS

- Routes use `/api/*` prefix for JSON endpoints
- Storage quota enforced via `_assert_storage_capacity()`
- Custom exceptions → `register_error_handlers()` for Flask
- `PATHS` global from `project_paths` module (import-time side effect)

## ANTI-PATTERNS

- No Flask Blueprints — all routes in single file
- Module-level side effects on import (lines 24-26)
- 1400+ line monolithic JS file with no modules
