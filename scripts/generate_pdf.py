#!/usr/bin/env python3
"""
scripts/generate_pdf.py — Generador híbrido D&D 2024 (PyMuPDF + CaslonAntique).

Preserva los AP originales del template (círculos teal ZaDb, fondos azules de
conjuros, estrella ☆ de inspiración) e inyecta CaslonAntique para los campos
de texto — fidelidad visual + tipografía medieval coherente.

Los campos quedan editables con CaslonAntique en cualquier visor que soporte
la fuente embebida (Acrobat Reader, Chrome, Foxit, etc.).

Uso:
    venv/Scripts/python scripts/generate_pdf.py
    venv/Scripts/python scripts/generate_pdf.py data/personaje.json output/salida.pdf
    venv/Scripts/python scripts/generate_pdf.py -v --verify

Requiere: PyMuPDF >= 1.27.2 + fonttools (ambos en venv)
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
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT  = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "Hoja-Personaje-Editable-Completa-ES.pdf"
FONT_PATH     = PROJECT_ROOT / "fonts" / "CaslonAntique-Regular.ttf"
DEFAULT_JSON  = PROJECT_ROOT / "data" / "personaje.json"
DEFAULT_OUT   = PROJECT_ROOT / "output" / "personaje_output.pdf"

# ---------------------------------------------------------------------------
# Reutilizar de scripts/fill_pdf.py (sin duplicar código)
# ---------------------------------------------------------------------------

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from fill_pdf import (  # type: ignore
    build_field_map,
    FontInfo, _pdf_escape, _align,
    KEY_STATS, HIGH, MEDIUM,
    SIZE_XLARGE, SIZE_HIGH, SIZE_MEDIUM, SIZE_LOW,
)

# ---------------------------------------------------------------------------
# Tipografía
# ---------------------------------------------------------------------------

def _field_size(name: str) -> int:
    """Tamaño de fuente CaslonAntique según jerarquía del campo."""
    if name in KEY_STATS: return SIZE_XLARGE  # 10
    if name in HIGH:      return SIZE_HIGH    # 8
    if name in MEDIUM:    return SIZE_MEDIUM  # 7
    return SIZE_LOW                           # 6


def _pdf_str_value(text: str) -> str:
    """
    Codifica texto como hex string PDF para xref_set_key.
    Evita problemas de encoding entre Python (UTF-8) y PDF (CP1252/latin-1).
    Ejemplo: "Héros" → "<48E9726F73>"
    """
    return "<" + text.encode("cp1252", errors="replace").hex().upper() + ">"


# ---------------------------------------------------------------------------
# Checkbox helpers
# ---------------------------------------------------------------------------

def _checkbox_on_state(pdf: fitz.Document, xref: int, raw: str | None = None) -> str:
    """Lee el nombre del estado activo ('On', 'Yes', etc.) del AP /N del checkbox."""
    try:
        if raw is None:
            raw = pdf.xref_object(xref, compressed=False)
        m = re.search(r'/N\s*<<(.*?)>>', raw, re.DOTALL)
        if m:
            for k in re.findall(r'/([^\s/(<\[]+)', m.group(1)):
                if k != "Off":
                    return k
        for cand in ("Yes", "On"):
            if f"/{cand}" in raw:
                return cand
    except Exception:
        pass
    return "Yes"


# ---------------------------------------------------------------------------
# Inyección de CaslonAntique en AcroForm /DR con la API xref de PyMuPDF
# ---------------------------------------------------------------------------

def _embed_caslon_fitz(pdf: fitz.Document, font_info: FontInfo) -> str:
    """
    Inyecta CaslonAntique TrueType en AcroForm /DR/Font usando la API xref de PyMuPDF.
    Devuelve la referencia indirecta ("N 0 R") para los /Resources de los AP streams.

    Estructura PDF creada:
        FontFile2 stream  ← bytes TTF en crudo (compress=False, Length1 obligatorio)
        FontDescriptor    ← métricas escaladas a espacio 1000-unit
        Font dict         ← TrueType, WinAnsiEncoding, FirstChar 32, LastChar 255
    """
    upm = font_info.upm

    # ── 1. Stream FontFile2 (bytes TTF sin comprimir) ────────────────────────
    with open(FONT_PATH, "rb") as f:
        ttf_bytes = f.read()
    ff2_xref = pdf.get_new_xref()
    pdf.update_object(ff2_xref, "<<>>")   # inicializar como dict antes de añadir stream
    pdf.update_stream(ff2_xref, ttf_bytes, new=True, compress=False)
    pdf.xref_set_key(ff2_xref, "Length1", str(len(ttf_bytes)))

    # ── 2. FontDescriptor ────────────────────────────────────────────────────
    b    = font_info.bbox   # ya en espacio 1000-unit (calculado en FontInfo.load)
    asc  = round(font_info.ascent     * 1000 / upm)
    desc = round(font_info.descent    * 1000 / upm)
    caph = round(font_info.cap_height * 1000 / upm)
    fd_xref = pdf.get_new_xref()
    pdf.update_object(fd_xref, (
        f"<</Type/FontDescriptor/FontName/CaslonAntique/Flags 32"
        f"/FontBBox[{b[0]} {b[1]} {b[2]} {b[3]}]"
        f"/ItalicAngle {font_info.italic_angle}"
        f"/Ascent {asc}/Descent {desc}/CapHeight {caph}/StemV {font_info.stemv}"
        f"/FontFile2 {ff2_xref} 0 R>>"
    ))

    # ── 3. Font dict TrueType ────────────────────────────────────────────────
    widths_str = " ".join(str(w) for w in font_info.widths)
    fo_xref = pdf.get_new_xref()
    pdf.update_object(fo_xref, (
        f"<</Type/Font/Subtype/TrueType/BaseFont/CaslonAntique"
        f"/Encoding/WinAnsiEncoding/FirstChar 32/LastChar 255"
        f"/Widths[{widths_str}]/FontDescriptor {fd_xref} 0 R>>"
    ))

    # ── 4. Registrar en AcroForm /DR/Font ────────────────────────────────────
    if "CaslonAntique" not in pdf.FormFonts:
        pdf._addFormFont("CaslonAntique", f"{fo_xref} 0 R")

    return f"{fo_xref} 0 R"


# ---------------------------------------------------------------------------
# Constructores de AP streams con CaslonAntique
# ---------------------------------------------------------------------------

def _make_xobject(pdf: fitz.Document, content: bytes,
                  font_ref: str, w: float, h: float) -> int:
    """
    Empaqueta bytes de contenido PDF en un Form XObject (AP stream).
    Devuelve el xref del objeto creado.
    El /Resources referencia solo CaslonAntique — auto-contenido.
    """
    ap_xref = pdf.get_new_xref()
    pdf.update_object(ap_xref, "<<>>")   # inicializar como dict antes de añadir stream
    pdf.update_stream(ap_xref, content, new=True)  # compress=True por defecto
    pdf.xref_set_key(ap_xref, "Type",      "/XObject")
    pdf.xref_set_key(ap_xref, "Subtype",   "/Form")
    pdf.xref_set_key(ap_xref, "FormType",  "1")
    pdf.xref_set_key(ap_xref, "BBox",      f"[0 0 {w:.3f} {h:.3f}]")
    pdf.xref_set_key(ap_xref, "Matrix",    "[1 0 0 1 0 0]")
    pdf.xref_set_key(ap_xref, "Resources",
        f"<</Font<</CaslonAntique {font_ref}>>/ProcSet[/PDF/Text]>>")
    return ap_xref


def _make_text_ap_xobj(pdf: fitz.Document, font_ref: str, font_info: FontInfo,
                       text: str, fsize: int, align: int,
                       w: float, h: float) -> int:
    """
    Form XObject de una línea con CaslonAntique.
    Shrink-to-fit si el texto es más ancho que el campo (mínimo 4pt).
    align: 0=izquierda, 1=centrado.
    """
    MARGIN  = 2.0
    avail_w = max(1.0, w - 2 * MARGIN)
    fs      = float(fsize)

    text_w = font_info.string_width(text, fs)
    if text_w > avail_w and fs > 4:
        fs     = max(4.0, fs * avail_w / text_w)
        text_w = font_info.string_width(text, fs)

    asc_pts = font_info.ascent_pts(fs)
    des_pts = font_info.descent_pts(fs)         # negativo
    y_base  = max(1.0, (h - (asc_pts - des_pts)) / 2 - des_pts)
    x_start = max(0.0, (w - text_w) / 2) if align == 1 else MARGIN

    content = (
        b"q\nBT\n"
        + f"/CaslonAntique {fs:.2f} Tf\n0 0 0 rg\n".encode("ascii")
        + f"{x_start:.3f} {y_base:.3f} Td\n(".encode("ascii")
        + _pdf_escape(text)
        + b") Tj\nET\nQ\n"
    )
    return _make_xobject(pdf, content, font_ref, w, h)


def _make_multiline_ap_xobj(pdf: fitz.Document, font_ref: str, font_info: FontInfo,
                             text: str, fsize: int,
                             w: float, h: float) -> int:
    """
    Form XObject multilínea con word-wrap y CaslonAntique.
    Alineación izquierda, anclado arriba. Leading = fsize × 1.2.
    """
    MARGIN_X = 2.0
    MARGIN_Y = 2.0
    avail_w  = max(1.0, w - 2 * MARGIN_X)
    leading  = fsize * 1.2
    asc_pts  = font_info.ascent_pts(fsize)

    render_lines: list[str] = []
    for paragraph in text.split("\n"):
        words, current = paragraph.split(" "), ""
        for word in words:
            candidate = (current + " " + word).strip() if current else word
            if font_info.string_width(candidate, fsize) <= avail_w:
                current = candidate
            else:
                if current:
                    render_lines.append(current)
                current = word
        render_lines.append(current)

    y_start = h - MARGIN_Y - asc_pts
    buf  = b"q\nBT\n"
    buf += f"/CaslonAntique {fsize:.2f} Tf\n0 0 0 rg\n".encode("ascii")
    buf += f"{leading:.2f} TL\n{MARGIN_X:.2f} {y_start:.3f} Td\n".encode("ascii")
    for i, line in enumerate(render_lines):
        if y_start - i * leading < MARGIN_Y:
            break
        if i > 0:
            buf += b"T*\n"
        buf += b"(" + _pdf_escape(line) + b") Tj\n"
    buf += b"ET\nQ\n"
    return _make_xobject(pdf, buf, font_ref, w, h)


# ---------------------------------------------------------------------------
# Parche de color teal en checkboxes ZaDb
# ---------------------------------------------------------------------------

_TEAL_RG = b'0.065994 0.313004 0.431 rg\n'


def _patch_checkbox_ap_color(pdf: fitz.Document) -> None:
    """
    Parcha los 7 checkboxes ZaDb del template que les falta el operador teal rg.
    Sin esto aparecen en negro en visores que renderizan desde el AP stream.
    También asegura que /DA tenga el color teal como fallback.
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
                m = re.search(
                    r'/' + re.escape(on_state) + r'\s+(\d+)\s+0\s+R',
                    n_m.group(1))
                if not m:
                    continue

                ap_xref = int(m.group(1))
                if ap_xref in seen:
                    continue
                seen.add(ap_xref)
                stream = pdf.xref_stream(ap_xref)

                if b'ZaDb' not in stream or b' rg' in stream:
                    continue

                patched = stream.replace(b'\nBT\n', b'\n' + _TEAL_RG + b'BT\n')
                if patched != stream:
                    pdf.update_stream(ap_xref, patched)

                stream_str = stream.decode('latin-1', errors='replace')
                sz_m       = re.search(r'/ZaDb\s+([\d.]+)\s+Tf', stream_str)
                font_sz    = sz_m.group(1) if sz_m else '9'

                # /DA con teal (3 decimales, igual que los widgets funcionales del PDF)
                pdf.xref_set_key(widget.xref, "DA",
                    f"(/ZaDb {font_sz} Tf 0.066 0.313 0.431 rg)")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Espacio de conjuro: preservar fondo azul circular
# ---------------------------------------------------------------------------

def _set_spell_slot_value(pdf: fitz.Document, widget: fitz.Widget, value: str) -> None:
    """
    Fija el valor de un círculo de espacio de conjuro preservando el fondo azul.
    Añade texto Helv 12 centrado al AP stream del template sin reemplazarlo.
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
    block  = (
        f"q\nBT\n/Helv 12 Tf\n0 g\n"
        f"{text_x:.1f} {text_y:.1f} Td\n({value}) Tj\nET\nQ\n"
    ).encode("latin-1")
    pdf.update_stream(ap_xref, stream + b"\n" + block)


# ---------------------------------------------------------------------------
# Capturas de verificación
# ---------------------------------------------------------------------------

def _render_verify(doc: fitz.Document, output_path: Path) -> list[str]:
    """
    Genera 4 capturas PNG a 2.5× zoom de áreas clave del PDF generado.
    Permite verificar visualmente:
      verify2_name.png        — Nombre/Clase/Especie en CaslonAntique
      verify2_proficiency.png — Habilidades + círculos teal preservados
      verify2_features.png    — Rasgos de clase (texto multilínea CaslonAntique)
      verify2_spells.png      — Espacios de conjuro (círculo azul + "1")
    """
    out_dir = output_path.parent
    mat     = fitz.Matrix(2.5, 2.5)
    saved   = []

    clips = [
        (0, fitz.Rect(  0,   0, 595,  90), "verify2_name.png"),
        (0, fitz.Rect(  0,  80, 260, 580), "verify2_proficiency.png"),
        (1, fitz.Rect(  0,   0, 595, 400), "verify2_features.png"),
        (3, fitz.Rect(  0,   0, 595, 130), "verify2_spells.png"),
    ]
    for page_idx, rect, fname in clips:
        if page_idx < doc.page_count:
            pix = doc[page_idx].get_pixmap(matrix=mat, clip=rect)
            pix.save(str(out_dir / fname))
            saved.append(fname)

    return saved


# ---------------------------------------------------------------------------
# Generador principal
# ---------------------------------------------------------------------------

def generate(
    json_path:     Path,
    template_path: Path,
    output_path:   Path,
    verbose:       bool = False,
    verify:        bool = False,
) -> None:
    """
    Genera el PDF rellenando campos con CaslonAntique, preservando AP originales.

    Campos de texto    → AP manual CaslonAntique + /DA CaslonAntique (editable)
    CheckBox           → /V y /AS directos, SIN tocar el AP original (teal, ZaDb)
    Espacios conjuro   → _set_spell_slot_value (Helv, preserva fondo azul)
    Stamps ☆ y sin mapeo → conservados intactos desde la plantilla
    """
    if not FONT_PATH.exists():
        sys.exit(f"Error: fuente no encontrada en {FONT_PATH}\n"
                 f"Ejecuta primero: venv/Scripts/python scripts/fill_pdf.py (descarga la fuente)")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("proficiency_bonus"):
        data["proficiency_bonus"] = 2

    field_map = build_field_map(data)
    font_info = FontInfo.load(FONT_PATH)

    src = fitz.open(str(template_path))
    out = fitz.open()

    # CRÍTICO: insertar todas las páginas en un solo llamado.
    # Hacerlo por página rompe la fusión del AcroForm → widgets huérfanos.
    out.insert_pdf(src)

    # Eliminar última página si está vacía (bug de la plantilla)
    last = out[-1]
    if not last.get_text().strip() and not list(last.widgets()):
        out.delete_page(-1)

    # Inyectar CaslonAntique en AcroForm /DR/Font
    font_ref = _embed_caslon_fitz(out, font_info)

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

            # ── CheckBox: preservar AP original ─────────────────────────────
            if field_type == "CheckBox":
                if value:
                    on_state = _checkbox_on_state(out, widget.xref)
                    v_val, as_val = f"/{on_state}", f"/{on_state}"
                else:
                    v_val, as_val = "/Off", "/Off"
                out.xref_set_key(widget.xref, "V",  v_val)
                out.xref_set_key(widget.xref, "AS", as_val)
                # Propagar al nodo padre en el árbol AcroForm.
                # Algunos checkboxes son widgets-hijo que heredan /FT del padre:
                # si solo actualizamos el hijo, los visores leen el estado /V del
                # padre (que sigue en /Off) y necesitan dos clics para sincronizar.
                try:
                    _, parent_ref = out.xref_get_key(widget.xref, "Parent")
                    if parent_ref not in ("null", ""):
                        parent_xref = int(parent_ref.split()[0])
                        out.xref_set_key(parent_xref, "V",  v_val)
                        out.xref_set_key(parent_xref, "AS", as_val)
                except Exception:
                    pass
                counters["filled"] += 1
                continue

            text = str(value).strip()

            # ── Espacios de conjuro: preservar fondo azul circular ──────────
            if field_name.startswith("Total-Espacios-Conjuro."):
                if text:
                    _set_spell_slot_value(out, widget, text)
                counters["filled"] += 1
                continue

            if not text:
                counters["filled"] += 1
                continue

            # ── Campo de texto: AP manual con CaslonAntique ─────────────────
            fsize = _field_size(field_name)
            align = _align(field_name)
            r     = widget.rect
            rw, rh = r.width, r.height

            # Detectar campo multilínea (bit 12 del flag /Ff = 4096)
            try:
                _, ff_raw = out.xref_get_key(widget.xref, "Ff")
                ff_val = int(ff_raw)
            except (ValueError, TypeError):
                ff_val = 0
            is_multiline = bool(ff_val & 4096) or "\n" in text

            if is_multiline:
                ap_xref = _make_multiline_ap_xobj(
                    out, font_ref, font_info, text, fsize, rw, rh)
            else:
                ap_xref = _make_text_ap_xobj(
                    out, font_ref, font_info, text, fsize, align, rw, rh)

            # Adjuntar AP + /DA (para editabilidad) + /V (valor del campo)
            out.xref_set_key(widget.xref, "AP", f"<</N {ap_xref} 0 R>>")
            out.xref_set_key(widget.xref, "DA", f"(/CaslonAntique {fsize} Tf 0 g)")
            out.xref_set_key(widget.xref, "V",  _pdf_str_value(text))

            counters["filled"] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(output_path), garbage=4, deflate=True)

    saved: list[str] = []
    if verify:
        doc_v = fitz.open(str(output_path))
        saved = _render_verify(doc_v, output_path)
        doc_v.close()

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
        if verify:
            print(f"     Capturas guardadas : {', '.join(saved)}")
    else:
        print(f"PDF generado: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera PDF D&D 2024 — CaslonAntique + AP originales preservados."
    )
    parser.add_argument("json",   nargs="?", type=Path, default=DEFAULT_JSON,
                        help=f"JSON del personaje (default: {DEFAULT_JSON.name})")
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUT,
                        help=f"PDF de salida (default: {DEFAULT_OUT.name})")
    parser.add_argument("--template", type=Path, default=TEMPLATE_PATH,
                        help="Template PDF fuente")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Muestra estadísticas de campos")
    parser.add_argument("--verify", action="store_true",
                        help="Genera 4 capturas PNG de verificación en output/")
    args = parser.parse_args()
    generate(args.json, args.template, args.output,
             verbose=args.verbose, verify=args.verify)


if __name__ == "__main__":
    main()
