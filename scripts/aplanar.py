#!/usr/bin/env python3
"""
aplanar.py — Aplana un PDF manteniendo los campos del formulario interactivos.

Las anotaciones visuales (Stamp, Square, Ink, Line, FreeText decorativo) se
RENDERIZAN al content stream de la página antes de eliminarse, haciéndolas
parte permanente e inamovible del contenido.

Elimina (renderizando primero si tienen apariencia):
  - Anotaciones visuales: Stamp, Square, Ink, Line, FreeText, Circle, etc.
  - Anotaciones Popup (ventanas de comentario, sin contenido visual)
  - Capas opcionales (/OCProperties) y sus referencias OC del content stream

Mantiene intactos:
  - Todos los campos AcroForm (/Widget): texto, checkboxes, dropdowns, etc.

Uso:
    venv/Scripts/python scripts/aplanar.py [input.pdf] [output.pdf] [--verbose]

Defaults:
    Entrada  → templates/Hoja-Personaje-Editable-Completa-ES.pdf
    Salida   → templates/Hoja-Personaje-Editable-Completa-ES-aplanado.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT_BOOTSTRAP = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT_BOOTSTRAP))

from project_paths import get_project_paths

try:
    import pikepdf
except ImportError as exc:
    raise ImportError("Error: instala pikepdf con:  pip install pikepdf") from exc


# ---------------------------------------------------------------------------
# Paths del proyecto
# ---------------------------------------------------------------------------

PATHS = get_project_paths()

PROJECT_ROOT  = PATHS.project_root
TEMPLATE_PATH = PATHS.template_pdf

# Tipos de anotación que se renderizan al content y se eliminan
VISUAL_SUBTYPES = {
    pikepdf.Name('/Stamp'),
    pikepdf.Name('/Square'),
    pikepdf.Name('/Circle'),
    pikepdf.Name('/Ink'),
    pikepdf.Name('/Line'),
    pikepdf.Name('/PolyLine'),
    pikepdf.Name('/Polygon'),
    pikepdf.Name('/FreeText'),
    pikepdf.Name('/StrikeOut'),
    pikepdf.Name('/Highlight'),
    pikepdf.Name('/Underline'),
    pikepdf.Name('/Caret'),
    pikepdf.Name('/FileAttachment'),
}


# ---------------------------------------------------------------------------
# Renderizado de anotación al content stream
# ---------------------------------------------------------------------------

def _compute_cm_matrix(
    bbox: list[float],
    matrix: list[float],
    rect: list[float],
) -> list[float]:
    """
    Calcula la matriz de transformación [a,b,c,d,e,f] para colocar el
    Form XObject (con /BBox y /Matrix dados) en el Rect de la anotación.

    Soporta ambos patrones:
      - BBox global + Matrix identidad (Stamps): escala BBox al Rect
      - BBox = coords de página + Matrix traslada al origen (Square/Ink/Line)
    """
    bx0, by0, bx1, by1 = bbox
    ma, mb, mc, md, me, mf = matrix
    rx0, ry0, rx1, ry1 = rect

    # Transformar esquinas del BBox por la Matrix del Form
    mx0 = bx0 * ma + by0 * mc + me
    my0 = bx0 * mb + by0 * md + mf
    mx1 = bx1 * ma + by1 * mc + me
    my1 = bx1 * mb + by1 * md + mf

    mw = mx1 - mx0
    mh = my1 - my0
    if abs(mw) < 1e-6 or abs(mh) < 1e-6:
        return []

    scx = (rx1 - rx0) / mw
    scy = (ry1 - ry0) / mh
    tx  = rx0 - scx * mx0
    ty  = ry0 - scy * my0

    return [scx, 0.0, 0.0, scy, tx, ty]


def _flatten_annot_to_cmd(
    pdf:       pikepdf.Pdf,
    page:      pikepdf.Page,
    annot,
    xobj_name: str,
    verbose:   bool,
) -> bytes | None:
    """
    Prepara el Form XObject de la anotación como recurso de la página y
    devuelve el comando PDF para renderizarlo en el content stream.

    Retorna None si la anotación no tiene apariencia válida.
    """
    # Obtener AP /N (Normal appearance)
    ap = annot.get('/AP')
    if ap is None:
        return None

    if isinstance(ap, pikepdf.Dictionary):
        ap_n = ap.get('/N')
    else:
        ap_n = ap

    if ap_n is None or not hasattr(ap_n, 'read_bytes'):
        return None

    # Obtener Rect de la anotación
    rect_raw = annot.get('/Rect')
    if rect_raw is None:
        return None

    rx0 = float(rect_raw[0]); ry0 = float(rect_raw[1])
    rx1 = float(rect_raw[2]); ry1 = float(rect_raw[3])
    if rx0 > rx1: rx0, rx1 = rx1, rx0
    if ry0 > ry1: ry0, ry1 = ry1, ry0

    rw = rx1 - rx0
    rh = ry1 - ry0
    if rw < 0.5 or rh < 0.5:
        return None

    # BBox y Matrix del Form XObject
    bbox_raw = ap_n.get('/BBox', pikepdf.Array([0, 0, 1, 1]))
    bx0 = float(bbox_raw[0]); by0 = float(bbox_raw[1])
    bx1 = float(bbox_raw[2]); by1 = float(bbox_raw[3])

    mat_raw = ap_n.get('/Matrix', pikepdf.Array([1, 0, 0, 1, 0, 0]))
    mat = [float(v) for v in mat_raw]

    cm = _compute_cm_matrix([bx0, by0, bx1, by1], mat, [rx0, ry0, rx1, ry1])
    if not cm:
        if verbose:
            print(f"    Advertencia: matriz degenerada para {xobj_name}, omitiendo")
        return None

    # Agregar Form XObject a los recursos de la página
    if '/Resources' not in page:
        page['/Resources'] = pikepdf.Dictionary()
    res = page['/Resources']
    if '/XObject' not in res:
        res['/XObject'] = pikepdf.Dictionary()
    res['/XObject'][xobj_name] = ap_n

    # Construir comando de renderizado
    a, b, c, d, e, f = cm
    cmd = (
        f"q {a:.6f} {b:.6f} {c:.6f} {d:.6f} {e:.6f} {f:.6f} cm "
        f"{xobj_name} Do Q\n"
    ).encode('ascii')

    return cmd


# ---------------------------------------------------------------------------
# Manejo de content streams
# ---------------------------------------------------------------------------

def _remove_oc_references(content_bytes: bytes) -> bytes:
    """Elimina marcadores /OC /LayerName BDC del content stream."""
    text = content_bytes.decode('latin-1', errors='replace')
    text = re.sub(r'/OC\s+/\S+\s+BDC\s*', '', text)
    return text.encode('latin-1', errors='replace')


def _append_to_contents(pdf: pikepdf.Pdf, page, extra: bytes) -> None:
    """Agrega bytes extra al final del content stream de la página."""
    if not extra:
        return

    if '/Contents' not in page:
        page['/Contents'] = pikepdf.Stream(pdf, extra)
        return

    contents = page['/Contents']

    if isinstance(contents, list):
        # Array de streams: agregar nuevo stream al final
        new_stream = pdf.make_indirect(pikepdf.Stream(pdf, extra))
        contents_list = list(contents)
        contents_list.append(new_stream)
        page['/Contents'] = pikepdf.Array(contents_list)
    else:
        # Stream único: concatenar
        try:
            original = contents.read_bytes()
        except Exception:
            original = b''
        page['/Contents'] = pikepdf.Stream(pdf, original + b'\n' + extra)


# ---------------------------------------------------------------------------
# Aplanado principal
# ---------------------------------------------------------------------------

def _flatten_pdf(input_path: Path, output_path: Path, verbose: bool = False) -> None:
    """
    Aplana el PDF:
      1. Renderiza anotaciones visuales (Stamp, Square, Ink…) al content stream
      2. Elimina esas anotaciones (ahora son contenido permanente)
      3. Elimina Popup (sin contenido visual)
      4. Elimina /OCProperties y refs OC del content stream
      5. Mantiene intactos todos los /Widget
    """
    if not input_path.exists():
        sys.exit(f"Error: no se encuentra '{input_path}'")

    print(f"Abriendo PDF: {input_path}")
    pdf = pikepdf.open(str(input_path))
    print(f"PDF cargado: {len(pdf.pages)} paginas")

    stats = {
        'pages':      0,
        'widgets':    0,
        'rendered':   0,
        'dropped':    0,
        'oc_cleaned': 0,
    }

    # ── 1. Remover /OCProperties ──────────────────────────────────────────
    if '/OCProperties' in pdf.Root:
        del pdf.Root['/OCProperties']
        if verbose:
            print("Removido /OCProperties del root")

    # ── 2. Procesar cada página ───────────────────────────────────────────
    for page_idx, page in enumerate(pdf.pages):
        stats['pages'] += 1

        if verbose:
            print(f"\n  Pagina {page_idx + 1}:")

        # ── 2a. Limpiar OC refs del content stream ────────────────────────
        if '/Contents' in page:
            contents = page['/Contents']
            streams_to_clean = list(contents) if isinstance(contents, list) else [contents]
            cleaned_any = False

            for i, s in enumerate(streams_to_clean):
                try:
                    original = s.read_bytes()
                    cleaned  = _remove_oc_references(original)
                    if len(cleaned) < len(original):
                        if isinstance(contents, list):
                            streams_to_clean[i] = pikepdf.Stream(pdf, cleaned)
                        else:
                            page['/Contents'] = pikepdf.Stream(pdf, cleaned)
                        cleaned_any = True
                        stats['oc_cleaned'] += 1
                except Exception as e:
                    if verbose:
                        print(f"    Advertencia OC limpieza: {e}")

            if isinstance(contents, list) and cleaned_any:
                page['/Contents'] = pikepdf.Array(streams_to_clean)

        # ── 2b. Clasificar anotaciones ────────────────────────────────────
        if '/Annots' not in page:
            continue

        annots     = page['/Annots']
        widgets    = []        # mantener intactos
        to_render  = []        # renderizar al content y eliminar

        for annot in annots:
            subtype = annot.get('/Subtype')

            if subtype == pikepdf.Name('/Widget'):
                widgets.append(annot)
                stats['widgets'] += 1

            elif subtype == pikepdf.Name('/Popup'):
                # Sin contenido visual — eliminar directamente
                stats['dropped'] += 1

            elif subtype in VISUAL_SUBTYPES:
                to_render.append(annot)

            else:
                # Tipo desconocido: mantener por seguridad
                if verbose:
                    print(f"    Anotacion desconocida mantenida: {subtype}")
                widgets.append(annot)

        # ── 2c. Renderizar anotaciones visuales ───────────────────────────
        render_cmds = bytearray()
        for i, annot in enumerate(to_render):
            xobj_name = f"/FlatAnnot{page_idx}_{i}"
            cmd = _flatten_annot_to_cmd(pdf, page, annot, xobj_name, verbose)

            if cmd:
                render_cmds += cmd
                stats['rendered'] += 1
                if verbose:
                    sub = str(annot.get('/Subtype', '?'))
                    print(f"    Renderizado {sub} -> {xobj_name}")
            else:
                stats['dropped'] += 1
                if verbose:
                    sub = str(annot.get('/Subtype', '?'))
                    print(f"    Sin AP, descartado {sub}")

        if render_cmds:
            _append_to_contents(pdf, page, bytes(render_cmds))

        # ── 2d. Actualizar /Annots (solo widgets) ─────────────────────────
        page['/Annots'] = pikepdf.Array(widgets)

        if verbose:
            rendered_types = set(str(a.get('/Subtype', '?')) for a in to_render)
            print(f"    Widgets: {len(widgets)}, Renderizados: {len(to_render)}, "
                  f"Eliminados: {stats['dropped'] if page_idx == 0 else '...'}")
            if rendered_types:
                print(f"    Tipos renderizados: {rendered_types}")

    # ── 3. Guardar ────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nGuardando: {output_path}")
    pdf.save(str(output_path))
    pdf.close()

    # ── 4. Resumen ────────────────────────────────────────────────────────
    print(f"\n=== RESUMEN DE APLANADO ===")
    print(f"Paginas procesadas      : {stats['pages']}")
    print(f"Widgets conservados     : {stats['widgets']}")
    print(f"Anotaciones renderizadas: {stats['rendered']}")
    print(f"Anotaciones eliminadas  : {stats['dropped']}")
    print(f"Streams OC limpiados    : {stats['oc_cleaned']}")
    print(f"\nPDF aplanado guardado en: {output_path}")

    if verbose:
        _verify_flattened(output_path, stats['widgets'])


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------

def _verify_flattened(pdf_path: Path, expected_widgets: int) -> None:
    """Verifica que el PDF aplanado mantiene sus widgets."""
    print(f"\n--- Verificacion del PDF aplanado ---")
    try:
        pdf = pikepdf.open(str(pdf_path))

        widget_count = sum(
            1
            for page in pdf.pages
            if '/Annots' in page
            for annot in page['/Annots']
            if annot.get('/Subtype') == pikepdf.Name('/Widget')
        )

        has_acroform = '/AcroForm' in pdf.Root
        no_oc        = '/OCProperties' not in pdf.Root

        print(f"  [{'OK  ' if has_acroform else 'FAIL'}] AcroForm presente: {has_acroform}")
        print(f"  [{'OK  ' if widget_count == expected_widgets else 'WARN'}] "
              f"Widgets: {widget_count} (esperado: {expected_widgets})")
        print(f"  [{'OK  ' if no_oc else 'FAIL'}] Sin OCProperties: {no_oc}")

        pdf.close()
    except Exception as e:
        print(f"  [FAIL] Error: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith('-')]
    verbose    = '--verbose' in sys.argv or '-v' in sys.argv

    input_path = Path(positional[0]) if len(positional) >= 1 else TEMPLATE_PATH

    if not input_path.exists():
        sys.exit(f"Error: no se encuentra '{input_path}'")

    if len(positional) >= 2:
        output_path = Path(positional[1])
    else:
        output_path = input_path.parent / f"{input_path.stem}-aplanado{input_path.suffix}"

    print(f"Entrada: {input_path}")
    print(f"Salida : {output_path}")
    print()

    _flatten_pdf(input_path, output_path, verbose=verbose)


if __name__ == '__main__':
    main()
