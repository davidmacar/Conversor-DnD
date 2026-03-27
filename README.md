# Conversor DnD

Aplicacion web para editar personajes y exportar PDF.

## Requisitos

- Python 3.11+
- Dependencias instaladas desde `editor/requirements.txt`

## Arranque de la web

Ambos comandos estan soportados y funcionan desde cualquier carpeta (CWD):

```powershell
# Opcion 1: entrypoint en raiz
python C:/ruta/al/proyecto/app.py

# Opcion 2: entrypoint legacy
python C:/ruta/al/proyecto/editor/app.py
```

Tambien puedes usar `editor/start.bat` en Windows.

## Scripts CLI

Estos scripts tambien funcionan desde cualquier CWD:

- `scripts/generate_pdf.py`
- `scripts/parse_character.py`
- `scripts/aplanar.py`

Ejemplos:

```powershell
python C:/ruta/al/proyecto/scripts/generate_pdf.py --help
python C:/ruta/al/proyecto/scripts/parse_character.py C:/ruta/al/proyecto/data/personaje.html C:/ruta/al/proyecto/output/personaje.json
python C:/ruta/al/proyecto/scripts/aplanar.py C:/ruta/al/proyecto/templates/Hoja-Personaje-Editable-Completa-ES.pdf C:/ruta/al/proyecto/output/plantilla-aplanada.pdf
```

## Variables de entorno opcionales

Puedes sobreescribir rutas sin editar codigo:

- `DND_EDITOR_DIR`
- `DND_DATA_DIR`
- `DND_OUTPUT_DIR`
- `DND_TEMPLATES_DIR`
- `DND_FONTS_DIR`
- `DND_CHARACTER_JSON`
- `DND_TEMPLATE_PDF`
- `DND_OUTPUT_PDF`
- `DND_FONT_TTF`

Si una ruta por variable de entorno es relativa, se interpreta relativa a la raiz del proyecto.
