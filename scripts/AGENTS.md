# SCRIPTS MODULE: PDF Generation & HTML Parsing

Core business logic for D&D character conversion. Heavy processing modules — largest files in project.

## STRUCTURE

```
scripts/
├── parse_character.py   # HTML→JSON parser (1757 lines)
├── generate_pdf.py      # JSON→PDF generator (~1940 lines)
├── aplanar.py          # PDF flattener (421 lines)
├── project_paths.py    # Path resolution dataclass
└── __init__.py         # Package marker
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Fix PDF field mapping | `generate_pdf.py` | `KEY_STATS`, `HIGH`, `MEDIUM`, `SIZE_6PT` field sets |
| Change font handling | `generate_pdf.py:_field_size()` | Lines ~166-172 |
| Change text alignment | `generate_pdf.py:_align()` | `CENTERED` set — 0=left, 1=centered |
| Update ability mapping | `parse_character.py:50-57` | `ABILITY_MAP` dict |
| Update skill mapping | `parse_character.py:59-99` | `SKILL_ABILITY_MAP`, `SKILL_NAME_MAP` |
| Modify field filling | `generate_pdf.py:build_field_map()` | Line ~900 |
| Flatten PDF | `aplanar.py` | Entry point for PDF flattening |
| Add path resolution | `project_paths.py` | `get_project_paths()` factory |
| Field limits | `generate_pdf.py:FIELD_LIMITS` | Hardcoded char limits per section |

## KEY CONCEPTS

- **Continuous blocks**: Multi-line text fields using `ContinuousBlockSpec`
- **Field classification**: Fields categorized by importance → font sizing (10pt/8pt/7pt/6pt)
- **SIZE_6PT**: Immutable 6pt for all background/appearance fields (personality traits, ideals, bonds, flaws, appearance, allies, enemies, backstory, notes)
- **CENTERED**: Set of fields with centered text alignment (stats, abilities, skills, speed fields)
- **Widget manipulation**: Direct xref access for AcroForm fields
- **Flattened PDFs**: Text rendered statically via pikepdf, only checkboxes remain interactive
- **BeautifulSoup4**: HTML parsing for Nivel20 extraction

## ANTI-PATTERNS

- 1800+ line files with single-responsibility violations
- Complex `_continuous_text_sections()` branching logic
- Hardcoded field name strings scattered throughout
- No unit tests for parser logic

## EXTERNAL DEPS

- `beautifulsoup4`: HTML parsing (parse_character.py)
- `pymupdf` (fitz): PDF manipulation (generate_pdf.py)
- `pikepdf`: PDF structure manipulation (aplanar.py)
- `fonttools`: Font metrics handling
