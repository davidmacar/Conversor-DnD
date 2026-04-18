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

## Despliegue con Docker

Configuracion incluida en el proyecto:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`

### 1) Preparar variables opcionales

Desde la raiz del proyecto:

```bash
cp .env.example .env
```

Si quieres usar otro puerto, cambia `DND_PORT` en `.env`.

### 2) Construir y levantar contenedor

```bash
docker compose up -d --build
```

La web quedara disponible en:

`http://localhost:${DND_PORT:-5000}`

### 3) Ver logs y estado

```bash
docker compose logs -f conversor-dnd
docker compose ps
```

### 4) Detener servicio

```bash
docker compose down
```

### Persistencia de datos

El compose monta volumenes bind para mantener datos entre reinicios:

- `./data -> /app/data`
- `./output -> /app/output`

Esto conserva personajes JSON y PDFs exportados fuera del contenedor.

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
