#!/usr/bin/env python3
"""
generate_pdf.py — Genera PDF de personaje D&D 2024 rellenando campos de formulario.

Enfoque "Clone + Fill":
  1. Copia todas las páginas del template con insert_pdf(), preservando
     TODAS las anotaciones: Stamps (☆), Widgets, AP streams, etc.
  2. Para campos de texto: establece field_value y regenera el AP stream
     via widget.update() manteniendo el estilo del formulario.
  3. Para checkboxes: establece /V y /AS mediante la API de bajo nivel
     preservando los AP streams originales (círculos, puntos, ZaDb…).
  4. Stamps y campos sin mapeo se conservan intactos.

Uso:
    venv/Scripts/python concept/generate_pdf.py
    venv/Scripts/python concept/generate_pdf.py data/personaje.json output/mi_char.pdf
    venv/Scripts/python concept/generate_pdf.py --verbose

Requiere: PyMuPDF >= 1.27.2 (ya instalado en venv)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Error: instala PyMuPDF con:  pip install pymupdf")

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

PROJECT_ROOT  = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "Hoja-Personaje-Editable-Completa-ES.pdf"
DEFAULT_JSON  = PROJECT_ROOT / "data" / "personaje.json"
DEFAULT_OUT   = PROJECT_ROOT / "output" / "concept_output.pdf"

# ---------------------------------------------------------------------------
# Re-use constants and build_field_map from fill_pdf.py (no duplication)
# ---------------------------------------------------------------------------

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from fill_pdf import (  # type: ignore
    build_field_map,
    KEY_STATS, HIGH, MEDIUM,
    SIZE_XLARGE, SIZE_HIGH, SIZE_MEDIUM, SIZE_LOW,
)

# Tamaño de fuente para los círculos de espacios de conjuro.
# El /DA original de la plantilla declara /Helv 12 Tf — no entra en ninguna
# categoría de la jerarquía estándar (KEY_STATS=10, HIGH=8, MEDIUM=7, LOW=6).
SIZE_SPELL_SLOT = 12

# ---------------------------------------------------------------------------
# Typography helper
# ---------------------------------------------------------------------------

def _field_size(name: str) -> int:
    """Devuelve el tamaño de fuente apropiado para el campo."""
    if name.startswith("Total-Espacios-Conjuro."):
        return SIZE_SPELL_SLOT
    if name in KEY_STATS: return SIZE_XLARGE
    if name in HIGH:      return SIZE_HIGH
    if name in MEDIUM:    return SIZE_MEDIUM
    return SIZE_LOW


# ---------------------------------------------------------------------------
# Checkbox helpers
# ---------------------------------------------------------------------------

def _checkbox_on_state(pdf: fitz.Document, xref: int, raw: str | None = None) -> str:
    """
    Lee el estado 'marcado' del checkbox desde su AP /N stream.
    Los checkboxes de este PDF usan 'On', 'Yes' o nombres custom (ej: 'S#EC').
    Acepta `raw` pre-leído para evitar una segunda llamada a xref_object.
    """
    try:
        if raw is None:
            raw = pdf.xref_object(xref, compressed=False)
        m = re.search(r'/N\s*<<(.*?)>>', raw, re.DOTALL)
        if m:
            keys = re.findall(r'/([^\s/(<\[]+)', m.group(1))
            for k in keys:
                if k != "Off":
                    return k
        for cand in ("Yes", "On"):
            if f"/{cand}" in raw:
                return cand
    except Exception:
        pass
    return "Yes"


def _detect_autosize_fields(src: fitz.Document) -> set[str]:
    """
    Devuelve los nombres de campo que usan auto-size en la plantilla.
    Incluye campos sin /DA explícito (heredan 0 Tf del AcroForm raíz) y
    campos con /DA que declaran explícitamente tamaño 0.
    widget.update() con text_fontsize=0 deja que el visor calcule el tamaño óptimo.
    """
    result: set[str] = set()
    for page in src:
        for widget in page.widgets():
            try:
                raw = src.xref_object(widget.xref, compressed=False)
                da  = re.search(r'/DA\s*\(([^)]+)\)', raw)
                if not da:
                    result.add(widget.field_name)
                else:
                    sz = re.search(r'/\w+\s+([\d.]+)\s+Tf', da.group(1))
                    if sz and float(sz.group(1)) == 0.0:
                        result.add(widget.field_name)
            except Exception:
                pass
    return result


# ---------------------------------------------------------------------------
# AP color patch (bug de plantilla: 7 checkboxes ZaDb sin color teal)
# ---------------------------------------------------------------------------

_TEAL_RG = b'0.065994 0.313004 0.431 rg\n'


def _patch_checkbox_ap_color(pdf: fitz.Document) -> None:
    """
    Parcha AP /N/On streams y /DA de checkboxes ZaDb que no tienen color teal.

    La plantilla tiene 7 checkboxes (Fuerza/Destreza + Historia) cuyos AP /N/On
    usan ZaDb pero les falta el comando de color teal. Aplica dos correcciones:
      1. AP /N/On stream: inserta teal rg antes de BT.
      2. /DA: añade el operador rg como fallback para visores que regeneran
         la apariencia desde /DA en lugar de usar el AP precompilado.

    Nota: busca el xref dentro del bloque /N << ... >> para evitar confundir
    el estado "pulsado" (/D/On) con el estado "mostrado" (/N/On).
    """
    seen: set[int] = set()
    for page in pdf:
        for widget in page.widgets():
            if widget.field_type_string != "CheckBox":
                continue
            try:
                raw      = pdf.xref_object(widget.xref, compressed=False)
                on_state = _checkbox_on_state(pdf, widget.xref, raw=raw)

                n_m = re.search(r'/N\s*<<(.*?)>>', raw, re.DOTALL)
                if not n_m:
                    continue
                m = re.search(r'/' + re.escape(on_state) + r'\s+(\d+)\s+0\s+R', n_m.group(1))
                if not m:
                    continue

                ap_xref = int(m.group(1))
                if ap_xref in seen:
                    continue
                seen.add(ap_xref)
                stream = pdf.xref_stream(ap_xref)

                if b'ZaDb' not in stream or b' rg' in stream:
                    continue

                # Parchar AP stream
                patched = stream.replace(b'\nBT\n', b'\n' + _TEAL_RG + b'BT\n')
                if patched != stream:
                    pdf.update_stream(ap_xref, patched)

                # Añadir/actualizar /DA con teal como fallback
                stream_str = stream.decode('latin-1', errors='replace')
                sz_m       = re.search(r'/ZaDb\s+([\d.]+)\s+Tf', stream_str)
                font_sz    = sz_m.group(1) if sz_m else '9'

                da_m = re.search(r'/DA\s*\(([^)]*)\)', raw)
                if da_m:
                    if 'rg' not in da_m.group(1):
                        pdf.xref_set_key(widget.xref, "DA",
                                         f"({da_m.group(1)} 0.065994 0.313004 0.431 rg)")
                else:
                    pdf.xref_set_key(widget.xref, "DA",
                                     f"(/ZaDb {font_sz} Tf 0.065994 0.313004 0.431 rg)")

            except Exception:
                pass


# ---------------------------------------------------------------------------
# Spell slot circle helper
# ---------------------------------------------------------------------------

def _set_spell_slot_value(pdf: fitz.Document, widget: fitz.Widget, value: str) -> None:
    """
    Fija el valor de un círculo de espacio de conjuro (Total-Espacios-Conjuro.*)
    preservando el fondo visual azul de la plantilla.

    widget.update() destruiría el AP circular original. En su lugar establece /V
    directamente y añade un bloque de texto centrado al AP stream existente.
    """
    if not value:
        return

    pdf.xref_set_key(widget.xref, "V", f"({value})")

    raw = pdf.xref_object(widget.xref, compressed=False)
    m   = re.search(r'/AP\b.*?/N\s+(\d+)\s+0\s+R', raw, re.DOTALL)
    if not m:
        return

    ap_xref = int(m.group(1))
    stream  = pdf.xref_stream(ap_xref)

    if b'BT' in stream:
        return  # ya tiene texto — evitar duplicados

    r      = widget.rect
    text_x = max(2.0, (r.width  - len(value) * 6.5) / 2)
    text_y = max(2.0, (r.height - 8.5) / 2)

    text_block = (
        f"q\nBT\n/Helv 12 Tf\n0 g\n"
        f"{text_x:.1f} {text_y:.1f} Td\n({value}) Tj\nET\nQ\n"
    ).encode("latin-1")

    pdf.update_stream(ap_xref, stream + b"\n" + text_block)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate(
    json_path: Path,
    template_path: Path,
    output_path: Path,
    verbose: bool = False,
) -> None:
    """
    Genera el PDF rellenando los campos de formulario del template.

    - Texto:      field_value + text_fontsize → widget.update()
    - CheckBox:   /V y /AS directos (sin update) para preservar AP originales
    - Conjuros:   _set_spell_slot_value() para no destruir el fondo circular
    - Stamps y campos sin mapeo: conservados intactos
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("proficiency_bonus"):
        data["proficiency_bonus"] = 2

    field_map      = build_field_map(data)
    src            = fitz.open(str(template_path))
    autosize_fields = _detect_autosize_fields(src)
    out            = fitz.open()

    # CRÍTICO: insert_pdf() en un solo llamado — llamarlo por página rompe
    # la fusión del AcroForm y deja las páginas 2-4 sin widgets.
    out.insert_pdf(src)

    # Eliminar última página si está vacía (bug de la plantilla)
    last = out[-1]
    if not last.get_text().strip() and not list(last.widgets()):
        out.delete_page(-1)

    # Corregir 7 checkboxes ZaDb sin color teal en la plantilla
    _patch_checkbox_ap_color(out)

    counters = {"total": 0, "filled": 0, "no_map": 0, "skipped": 0}

    for new_page in out:
        for widget in new_page.widgets():
            field_name = widget.field_name
            field_type = widget.field_type_string
            counters["total"] += 1

            if field_type == "Button":
                counters["skipped"] += 1
                continue
            if widget.rect.width < 1 or widget.rect.height < 1:
                counters["skipped"] += 1
                continue
            if field_name not in field_map:
                counters["no_map"] += 1
                continue

            value = field_map[field_name]

            if field_type == "CheckBox":
                # Sin widget.update() para preservar AP originales (círculos ZaDb, etc.)
                if value:
                    on_state = _checkbox_on_state(out, widget.xref)
                    out.xref_set_key(widget.xref, "V",  f"/{on_state}")
                    out.xref_set_key(widget.xref, "AS", f"/{on_state}")
                else:
                    out.xref_set_key(widget.xref, "V",  "/Off")
                    out.xref_set_key(widget.xref, "AS", "/Off")
                counters["filled"] += 1
                continue

            text = str(value).strip()
            if not text:
                counters["filled"] += 1
                continue

            if field_name.startswith("Total-Espacios-Conjuro."):
                # Sin widget.update() para preservar el fondo circular azul
                _set_spell_slot_value(out, widget, text)
                counters["filled"] += 1
                continue

            widget.field_value   = text
            widget.text_fontsize = 0.0 if field_name in autosize_fields else float(_field_size(field_name))
            widget.text_color    = (0, 0, 0)
            widget.update()
            counters["filled"] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(output_path), garbage=4, deflate=True)
    out.close()
    src.close()

    if verbose:
        t = counters["total"]
        f = counters["filled"]
        print(f"[OK] Guardado: {output_path}")
        print(f"     Widgets totales    : {t}")
        print(f"     Campos rellenos    : {f}  ({f * 100 // max(t, 1)}%)")
        print(f"     Sin mapeo de datos : {counters['no_map']}")
        print(f"     Otros skips        : {counters['skipped']}")
    else:
        print(f"PDF generado: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera PDF de personaje D&D 2024 rellenando campos de formulario."
    )
    parser.add_argument(
        "json", nargs="?", type=Path, default=DEFAULT_JSON,
        help=f"JSON del personaje (default: {DEFAULT_JSON.name})",
    )
    parser.add_argument(
        "output", nargs="?", type=Path, default=DEFAULT_OUT,
        help=f"PDF de salida (default: {DEFAULT_OUT.name})",
    )
    parser.add_argument(
        "--template", type=Path, default=TEMPLATE_PATH,
        help="Template PDF fuente",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Muestra estadísticas de campos",
    )
    args = parser.parse_args()
    generate(args.json, args.template, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()
