import fitz, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
tmpl = fitz.open(str(ROOT / 'templates/Hoja-Personaje-Editable-Completa-ES.pdf'))
gen  = fitz.open(str(ROOT / 'output/concept_fresh.pdf'))

IDENTITY = ['Nombre-Personaje','Clase-Y-Nivel','Especie','Trasfondo','Alineamiento','PX-Personaje']

print('=== TEMPLATE ===')
for page in tmpl:
    for w in page.widgets():
        if w.field_name in IDENTITY:
            raw = tmpl.xref_object(w.xref, compressed=False)
            da  = re.search(r'/DA\s*\(([^)]+)\)', raw)
            q   = re.search(r'/Q\s+(\d)', raw)
            print('%s | rect=(%0.0f,%0.0f,%0.0f,%0.0f) | DA=%-25s | Q=%s' % (
                w.field_name, w.rect.x0, w.rect.y0, w.rect.x1, w.rect.y1,
                da.group(1) if da else '?', q.group(1) if q else '?'))

print()
print('=== GENERATED ===')
for page in gen:
    for w in page.widgets():
        if w.field_name in IDENTITY:
            raw = gen.xref_object(w.xref, compressed=False)
            da  = re.search(r'/DA\s*\(([^)]+)\)', raw)
            m   = re.search(r'/AP.*?/N\s+(\d+)\s+0\s+R', raw, re.DOTALL)
            if m:
                ap = gen.xref_stream(int(m.group(1))).decode('latin-1', errors='replace').replace('\n',' ')[:120]
            else:
                ap = 'no AP'
            print('%s | val=%-15r | DA=%-25s | AP=%s' % (
                w.field_name, w.field_value,
                da.group(1) if da else '?', ap))
