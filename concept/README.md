# concept/generate_pdf.py

Generador de hoja de personaje D&D 2024 en PDF **completamente estático**:
sin campos de formulario AcroForm, datos embebidos como texto.

## Concepto: Clone + Flatten

En lugar de rellenar un formulario PDF existente (enfoque de `scripts/fill_pdf.py`),
este script **genera un PDF nuevo desde cero** que es visualmente idéntico al template:

1. **Copia vectores** — cada página del template original se copia como fondo
   con `show_pdf_page()`. Esto preserva todos los bordes decorativos, líneas,
   etiquetas en español y el aspecto vacío de los campos.
2. **Extrae posiciones** — se iteran los 909 widgets AcroForm del template fuente
   para obtener las coordenadas exactas de cada campo.
3. **Embebe datos** — los valores del JSON del personaje se dibujan como texto
   estático (`insert_text` / `insert_textbox`) con la fuente CaslonAntique.
4. **Checkboxes** — los checkboxes marcados (`True`) se renderizan como una X
   dibujada con `draw_line()`.

El resultado es un PDF limpio, comprimido, sin dependencias de formulario.

## Uso

```bash
# Generar con datos por defecto (data/personaje.json → output/concept_output.pdf)
venv/Scripts/python concept/generate_pdf.py

# Archivos personalizados
venv/Scripts/python concept/generate_pdf.py data/mi_personaje.json output/mi_personaje.pdf

# Ver estadísticas de campos
venv/Scripts/python concept/generate_pdf.py --verbose

# Verificar que los valores clave aparecen en el PDF generado
venv/Scripts/python concept/generate_pdf.py --verify

# Combinado
venv/Scripts/python concept/generate_pdf.py --verbose --verify
```

## Jerarquía tipográfica

| Conjunto    | Tamaño | Ejemplos                                       |
|-------------|--------|------------------------------------------------|
| `KEY_STATS` |  10 pt | Puntuaciones, modificadores, CA, HP, iniciativa |
| `HIGH`      |   8 pt | Nombre, Clase+Nivel, Especie, armas, monedas   |
| `MEDIUM`    |   7 pt | Skills, salvaciones, espacios conjuro, idiomas |
| Default     |   6 pt | Todo lo demás                                  |

Campos centrados (CENTERED): puntuaciones, modificadores, CA, iniciativa,
HP, monedas, CD conjuros, bonificadores de ataque, etc.

## Dependencias

- **PyMuPDF** (`fitz`) >= 1.27.2 — ya instalado en el venv
- `templates/Hoja-Personaje-Editable-Completa-ES.pdf` — template fuente (5 páginas, 909 widgets)
- `templates/fonts/caslon-antique.regular.ttf` — fuente CaslonAntique
- `scripts/fill_pdf.py` — importado para reutilizar `build_field_map()` y constantes de tipografía
- `data/personaje.json` — datos del personaje (mismo formato que el resto del proyecto)

## Diferencia respecto a fill_pdf.py

| Aspecto            | `scripts/fill_pdf.py`          | `concept/generate_pdf.py`          |
|--------------------|--------------------------------|-------------------------------------|
| Librería principal | `pikepdf` + `fonttools`        | `PyMuPDF` (fitz)                   |
| Método             | Rellena campos AcroForm        | Genera PDF nuevo sin campos        |
| Resultado          | PDF con campos interactivos    | PDF estático, texto embebido       |
| Campos AcroForm    | 937 campos, rellenados en AP   | Ninguno — solo texto/vectores      |
| Compresión         | pikepdf save                   | `garbage=4, deflate=True`          |
| Fuente             | Inyectada en /DR de AcroForm   | Registrada por página via insert_font |

## Estructura del output

El PDF generado tiene las mismas 5 páginas A4 (595×842 pt) que el template,
con el mismo diseño visual y los datos del personaje en las posiciones exactas
donde estarían los campos del formulario original.
