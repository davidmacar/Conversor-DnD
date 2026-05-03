# Conversor-DnD — Editor de Personajes D&D 2024

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Alpine.js](https://img.shields.io/badge/Alpine.js-3.x-orange.svg)](https://alpinejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Editor web y generador de hojas de personaje para D&D 5.5 (2024)**  
> Extrae personajes desde [Nivel20.com](https://nivel20.com), edítalos en un interfaz medieval interactivo, y exporta a PDF relleno automáticamente.

---

## Tabla de Contenidos

- [Características Principales](#características-principales)
- [Capturas de Pantalla](#capturas-de-pantalla)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Instalación y Uso](#instalación-y-uso)
- [Funcionalidades Detalladas](#funcionalidades-detalladas)
- [API del Backend](#api-del-backend)
- [Mapeo de Campos PDF](#mapeo-de-campos-pdf)
- [Desarrollo](#desarrollo)
- [Tecnologías](#tecnologías)
- [Licencia](#licencia)

---

## Características Principales

### 🎭 Extracción Automática
- **Parseo de HTML**: Extrae personajes completos desde Nivel20.com (D&D 2024 en español)
- **Conversión inteligente**: Transforma datos HTML a JSON estructurado con todos los campos del personaje
- **Mapeo completo**: Atributos, habilidades, salvaciones, conjuros, equipamiento, rasgos, dotes...

### 📝 Editor Web Interactivo
- **Interfaz medieval oscura**: Tema de pergamino con acentos dorados y carmesí
- **Edición en tiempo real**: Todos los campos editables con reactividad instantánea
- **Contadores de caracteres**: Indicadores en vivo con límites del PDF (rojo al exceder)
- **Cálculos automáticos**: Velocidad de natación/vuelo/trepar, saltos, velocidad de viaje
- **Atajos de teclado**: `Ctrl+S` para guardar

### 📄 Generación de PDF
- **Campos rellenados automáticamente**: Mapeo completo a campos PDF en español
- **Tamaños de fuente dinámicos**: 10pt/8pt/7pt según importancia del campo
- **Texto enriquecido**: Títulos y descripciones de rasgos en misma línea cuando caben
- **PDFs planos**: Texto renderizado estáticamente (no editable), checkboxes interactivos
- **Campos centrados**: Velocidad, saltos y atributos centrados en sus cajas

### 🔄 Gestión de Personajes
- **Crear nuevo personaje**: Plantilla vacía con estructura completa
- **Cargar desde JSON**: Drag & drop o pegar JSON directamente
- **Exportar a JSON**: Generación client-side con formato legible
- **Exportar a PDF**: Botón con icono SVG estilizado
- **Almacenamiento persistente**: JSONs guardados en servidor con cuota configurable

---

## Capturas de Pantalla

> *[Próximamente]*

---

## Arquitectura del Proyecto

```
Conversor-DnD/
├── 📁 editor/                  # Aplicación Flask
│   ├── app.py                  # Backend: rutas, API, almacenamiento
│   ├── static/
│   │   ├── js/editor.js        # Frontend: Alpine.js (~2200 líneas)
│   │   ├── css/style.css       # Estilos: tema medieval (~2400 líneas)
│   │   └── img/                # Retratos de personajes
│   └── templates/
│       └── index.html          # SPA: editor de una sola página
│
├── 📁 scripts/                 # Lógica de negocio
│   ├── parse_character.py      # HTML → JSON (BeautifulSoup4)
│   ├── generate_pdf.py         # JSON → PDF (PyMuPDF/fitz)
│   ├── aplanar.py             # Aplanador de PDFs (pikepdf)
│   └── project_paths.py       # Resolución centralizada de rutas
│
├── 📁 data/                    # Almacenamiento de personajes JSON
├── 📁 output/                  # PDFs generados
├── 📁 templates/               # Plantillas PDF + fuentes
├── 📁 fonts/                   # Fuentes CaslonAntique TTF
├── docker-compose.yml          # Orquestación de contenedores
├── Dockerfile                  # Build del contenedor
└── app.py                      # Punto de entrada (wrapper)
```

### Flujo de Datos

```
Nivel20.com ──[HTML]──► parse_character.py ──[JSON]──► editor/web
                                             │
                                             └──[JSON]──► generate_pdf.py ──[PDF]──► output/
```

---

## Instalación y Uso

### Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose
- Navegador web moderno (Chrome, Firefox, Edge)

### Inicio Rápido

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd Conversor-DnD

# Iniciar el servicio
docker-compose up -d

# Ver logs
docker-compose logs -f
```

El editor estará disponible en: `http://localhost:5000`

### Uso del Editor Web

1. **Cargar personaje existente**: Selecciona desde el dropdown superior
2. **Crear nuevo personaje**: Botón "✦ Nuevo" → introduce nombre → confirmar
3. **Editar campos**: Haz clic en cualquier campo y edita directamente
4. **Guardar**: `Ctrl+S` o el botón "Guardar"
5. **Exportar PDF**: Botón con icono de documento → genera y descarga
6. **Exportar JSON**: Botón "JSON" → copia o descarga el JSON

### Parseo desde Nivel20.com

```bash
# Dentro del contenedor
docker exec -it conversor-dnd-web bash

# Parsear personaje
python scripts/parse_character.py \
  "https://nivel20.com/.../ID-nombre" \
  data/mi-personaje.json
```

### Generación de PDF

```bash
# Generar PDF desde JSON existente
python scripts/generate_pdf.py \
  data/mi-personaje.json \
  output/mi-personaje.pdf

# Con verbose y verificación visual
python scripts/generate_pdf.py \
  data/mi-personaje.json \
  output/mi-personaje.pdf \
  --verbose --verify
```

### Aplanar PDF

```bash
# Convertir PDF editable a plano (texto estático)
python scripts/aplanar.py input.pdf output.pdf
```

---

## Funcionalidades Detalladas

### Editor Web — Secciones

| Sección | Campos | Características |
|---------|--------|-----------------|
| **Identidad** | Nombre, raza, clase, trasfondo, alineamiento, nivel, PX | Campos básicos del personaje |
| **Atributos** | Fuerza, Destreza, Constitución, Inteligencia, Sabiduría, Carisma | Scores, modificadores, salvaciones |
| **Combate** | CA, iniciativa, velocidad, PG, dados de golpe | Cálculos automáticos de velocidad y saltos |
| **Habilidades** | 18 habilidades con modificadores | Auto-calculado desde atributos |
| **Conjuros** | Espacios, CD, ataque, lista de conjuros | Gestión completa de spellcasting |
| **Inventario** | Armas, armaduras, equipo, dinero (CP/SP/EP/GP/PP) | Sección extensible |
| **Rasgos** | Rasgos de clase, rasgos de especie, dotes | Límite combinado de 1450 caracteres |
| **Trasfondo** | Rasgos de personalidad, ideales, vínculos, defectos, historia | Contadores individuales por campo |
| **Notas** | Notas generales del personaje | Límite de 1500 caracteres |
| **Apariencia** | Edad, altura, peso, género, tamaño, ojos, piel, pelo, descripción | Límite en descripción/resumen |
| **Aliados/Enemigos** | Lista de contactos del personaje | Límite individual |

### Cálculos Automáticos (Velocidad)

Al modificar **"Base (m)"** se recalculan automáticamente:

| Campo | Fórmula |
|-------|---------|
| Natación | = Base |
| Vuelo | = Base |
| Trepar | = Base |
| Salto largo | = Fuerza × 0.3048 m |
| Salto alto | = (3 + mod Fuerza) × 0.3048 m |
| Velocidad/hora | = Base × 0.6 km/h |
| Velocidad/jornada | = Velocidad/hora × 8 km |

### Límites de Caracteres (PDF)

| Campo | Límite | Nivel de borde |
|-------|--------|----------------|
| Descripción de apariencia | 550 | Textarea individual |
| Rasgos de personalidad | 550 | Textarea individual |
| Ideales | 550 | Textarea individual |
| Vínculos | 550 | Textarea individual |
| Defectos | 550 | Textarea individual |
| Amigos/Aliados | 550 | Textarea individual |
| Enemigos | 550 | Textarea individual |
| Historia de personaje | 1250 | Sub-sección |
| Rasgos de Clase + Especie | 1450 | Tarjeta combinada |
| Dotes | 1400 | Tarjeta completa |
| Notas | 1500 | Tarjeta completa |

Cuando se excede el límite:
- **Campos individuales**: Borde rojo en el textarea
- **Secciones completas**: Borde rojo en toda la tarjeta
- **Contadores**: Muestran `actual/límite` en rojo

---

## API del Backend

### Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Página principal del editor |
| `GET` | `/api/characters` | Lista de personajes disponibles |
| `GET` | `/api/characters/<name>` | Obtener JSON de personaje |
| `POST` | `/api/characters/<name>` | Guardar personaje (JSON body) |
| `POST` | `/api/characters/<name>/pdf` | Generar y descargar PDF |
| `POST` | `/api/characters/<name>/delete` | Eliminar personaje |
| `GET` | `/api/field-limits` | Obtener límites de caracteres |
| `GET` | `/api/status` | Healthcheck (Docker) |
| `POST` | `/api/upload-image` | Subir retrato de personaje |

### Ejemplo de Uso API

```bash
# Listar personajes
curl http://localhost:5000/api/characters

# Obtener personaje
curl http://localhost:5000/api/characters/mi-personaje

# Guardar personaje
curl -X POST http://localhost:5000/api/characters/mi-personaje \
  -H "Content-Type: application/json" \
  -d @data/mi-personaje.json

# Generar PDF
curl -X POST http://localhost:5000/api/characters/mi-personaje/pdf \
  --output mi-personaje.pdf
```

---

## Mapeo de Campos PDF

### Campos Centrados

Los siguientes campos aparecen **centrados** en el PDF:

- `Clase-Armadura`, `Iniciativa`, `Velocidad`, `Percepcion-Pasiva`
- `Puntos-Golpe-Actuales`, `Puntos-Golpe-Maximo`, `Puntos-Golpe-Temporales`
- `Dados-Golpe-Maximos`, `Dados-Golpe-Gastados`
- `Bonificador-Competencia`, `PX-Personaje`
- Todas las `Puntuacion-*` y `Modificador-*` de atributos
- Todas las `Modificador-Salvacion-*`
- Todas las `Modificador-*` de habilidades
- Monedas: `Cobre`, `Plata`, `Electro`, `Oro`, `Platino`
- **Velocidad**: `Velocidad-Hora`, `Velocidad-Jornada`, `Velocidad-Especial`
- **Velocidad adicional**: `Velocidad-Volando`, `Velocidad-Trepando`, `Velocidad-Nadando`
- **Saltos**: `Salto-Horizontal`, `Salto-Altura`

### Tamaños de Fuente

| Tamaño | Campos |
|--------|--------|
| **10pt** | Estadísticas clave: CA, iniciativa, velocidad, PG, PX |
| **8pt** | Campos importantes: nombre, clase, raza, atributos |
| **7pt** | Campos medianos: habilidades, salvaciones |
| **6pt** | Campos de trasfondo y apariencia (inmutable) |

---

## Desarrollo

### Estructura del Código Frontend

```javascript
// editor.js — Estructura Alpine.js
document.addEventListener('alpine:init', () => {
  Alpine.data('characterEditor', () => ({
    // Datos
    character: { /* ... */ },
    characters: [],
    fieldLimits: {},
    
    // Ciclo de vida
    async init() { /* ... */ },
    
    // Cálculos
    modifier(score) { /* ... */ },
    updateAll() { /* ... */ },
    
    // Límites
    sectionCharCount(section) { /* ... */ },
    isOverLimit(section) { /* ... */ },
    
    // Acciones
    async save() { /* ... */ },
    async generatePdf() { /* ... */ },
    exportJson() { /* ... */ },
    loadFromJson(json) { /* ... */ },
    createNewCharacter(name) { /* ... */ },
    
    // Utilidades
    _ensureArrays() { /* ... */ },
    normalizeCharacterPayload() { /* ... */ },
  }))
})
```

### Convenciones de Código

- **Python**: Type hints modernos, dataclasses, excepciones personalizadas
- **JavaScript**: ES6+, Alpine.js 3.x, todo en español (UI strings)
- **CSS**: Variables CSS para consistencia de colores, mobile-first
- **Comentarios**: Español para intención, inglés para símbolos de código

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DND_STORAGE_LIMIT_BYTES` | Cuota máxima de almacenamiento | `1073741824` (1GB) |
| `FLASK_ENV` | Entorno de Flask | `production` |
| `FLASK_PORT` | Puerto del servidor | `5000` |

---

## Tecnologías

### Backend
- **[Flask](https://flask.palletsprojects.com/)** — Framework web Python
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** — Manipulación de PDFs
- **[pikepdf](https://pikepdf.readthedocs.io/)** — Estructura PDF de bajo nivel
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** — Parseo HTML

### Frontend
- **[Alpine.js](https://alpinejs.dev/)** — Framework reactivo ligero
- **[Cinzel](https://fonts.google.com/specimen/Cinzel)** — Fuente para títulos medievales
- **[Crimson Text](https://fonts.google.com/specimen/Crimson+Text)** — Fuente para cuerpo de texto

### Infraestructura
- **[Docker](https://www.docker.com/)** — Contenerización
- **[Gunicorn](https://gunicorn.org/)** — Servidor WSGI
- **[Nginx Proxy Manager](https://nginxproxymanager.com/)** — Proxy inverso (opcional)

---

## Licencia

Este proyecto es de código abierto bajo la licencia MIT.

---

## Créditos

- **Fuente de datos**: [Nivel20.com](https://nivel20.com) — Comunidad D&D en español
- **Reglas**: D&D 5.5 (2024) — Wizards of the Coast
- **Desarrollo**: Creado con ❤️ para la comunidad rolera

---

<p align="center">
  <em>"Que los dados te sean propicios"</em> 🎲
</p>
