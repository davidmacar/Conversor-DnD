#!/usr/bin/env python3
"""
parse_character.py — Conversor de hoja de personaje Nivel20 (D&D 2024) a JSON.

Uso:
    # Desde URL (descarga directa):
    python parse_character.py https://nivel20.com/games/dnd-2024/characters/ID-nombre
    python parse_character.py https://nivel20.com/.../ID-nombre salida.json --verbose

    # Desde fichero HTML local:
    python parse_character.py [input.html] [output.json] [--verbose]

Si no se pasan argumentos, busca personaje.html en el mismo directorio y
genera personaje.json junto a él.

Dependencias:
    pip install beautifulsoup4
"""

from __future__ import annotations

import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT_BOOTSTRAP = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT_BOOTSTRAP))

from project_paths import ensure_runtime_directories, get_project_paths

PATHS = get_project_paths()
ensure_runtime_directories(PATHS)

try:
    from bs4 import BeautifulSoup, Tag
except ImportError as exc:
    raise ImportError("Error: instala beautifulsoup4 con:  pip install beautifulsoup4") from exc


# ---------------------------------------------------------------------------
# Constantes de mapeo
# ---------------------------------------------------------------------------

ABILITY_MAP: dict[str, str] = {
    "fue": "strength",
    "des": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "sab": "wisdom",
    "car": "charisma",
}

SKILL_ABILITY_MAP: dict[str, str] = {
    "acrobacias":        "dexterity",
    "atletismo":         "strength",
    "arcanos":           "intelligence",
    "enganar":           "charisma",
    "historia":          "intelligence",
    "interpretacion":    "charisma",
    "intimidar":         "charisma",
    "investigacion":     "intelligence",
    "juego_de_manos":    "dexterity",
    "medicina":          "wisdom",
    "naturaleza":        "intelligence",
    "percepcion":        "wisdom",
    "perspicacia":       "wisdom",
    "persuasion":        "charisma",
    "religion":          "intelligence",
    "sigilo":            "dexterity",
    "supervivencia":     "wisdom",
    "trato_con_animales":"wisdom",
}

SKILL_NAME_MAP: dict[str, str] = {
    "acrobacias":        "Acrobacias",
    "atletismo":         "Atletismo",
    "arcanos":           "Conocimiento arcano",
    "enganar":           "Engaño",
    "historia":          "Historia",
    "interpretacion":    "Interpretación",
    "intimidar":         "Intimidación",
    "investigacion":     "Investigación",
    "juego_de_manos":    "Juego de Manos",
    "medicina":          "Medicina",
    "naturaleza":        "Naturaleza",
    "percepcion":        "Percepción",
    "perspicacia":       "Perspicacia",
    "persuasion":        "Persuasión",
    "religion":          "Religión",
    "sigilo":            "Sigilo",
    "supervivencia":     "Supervivencia",
    "trato_con_animales":"Trato con Animales",
}

# Dado de golpe por clase (D&D 2024)
CLASS_HIT_DIE: dict[str, int] = {
    "bárbaro": 12, "barbaro": 12,
    "bardo":    8,
    "clérigo":  8, "clerigo": 8,
    "druida":   8,
    "guerrero": 10,
    "hechicero":6,
    "mago":     6,
    "monje":    8,
    "paladín": 10, "paladin": 10,
    "pícaro":   8, "picaro":  8,
    "explorador":10,
    "brujo":    8,
}

# Habilidad de conjuración principal por clase
SPELL_ABILITY_BY_CLASS: dict[str, str] = {
    "mago":       "Inteligencia",
    "artífice":   "Inteligencia",
    "artifice":   "Inteligencia",
    "clérigo":    "Sabiduría",
    "clerigo":    "Sabiduría",
    "druida":     "Sabiduría",
    "monje":      "Sabiduría",
    "explorador": "Sabiduría",
    "hechicero":  "Carisma",
    "bardo":      "Carisma",
    "brujo":      "Carisma",
    "paladín":    "Carisma",
    "paladin":    "Carisma",
}

# Clases por tipo de lanzador
FULL_CASTER_CLASSES:  set[str] = {"mago", "clérigo", "clerigo", "druida", "bardo", "hechicero"}
HALF_CASTER_CLASSES:  set[str] = {"paladín", "paladin", "explorador", "artífice", "artifice"}
THIRD_CASTER_CLASSES: set[str] = {"pícaro", "picaro"}

# Espacios de conjuro por nivel de personaje (D&D 2024 PHB)
# Índice: nivel_personaje - 1,  columna: nivel_conjuro - 1  (9 slots)
FULL_CASTER_SLOTS: list[list[int]] = [
    [2, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 1
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 2
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 3
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 4
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 5
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 6
    [4, 3, 3, 1, 0, 0, 0, 0, 0],  # nv 7
    [4, 3, 3, 2, 0, 0, 0, 0, 0],  # nv 8
    [4, 3, 3, 3, 1, 0, 0, 0, 0],  # nv 9
    [4, 3, 3, 3, 2, 0, 0, 0, 0],  # nv 10
    [4, 3, 3, 3, 2, 1, 0, 0, 0],  # nv 11
    [4, 3, 3, 3, 2, 1, 0, 0, 0],  # nv 12
    [4, 3, 3, 3, 2, 1, 1, 0, 0],  # nv 13
    [4, 3, 3, 3, 2, 1, 1, 0, 0],  # nv 14
    [4, 3, 3, 3, 2, 1, 1, 1, 0],  # nv 15
    [4, 3, 3, 3, 2, 1, 1, 1, 0],  # nv 16
    [4, 3, 3, 3, 2, 1, 1, 1, 1],  # nv 17
    [4, 3, 3, 3, 3, 1, 1, 1, 1],  # nv 18
    [4, 3, 3, 3, 3, 2, 1, 1, 1],  # nv 19
    [4, 3, 3, 3, 3, 2, 2, 1, 1],  # nv 20
]

HALF_CASTER_SLOTS: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 1
    [2, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 2
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 3
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 4
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 5
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 6
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 7
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 8
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 9
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 10
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 11
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 12
    [4, 3, 3, 1, 0, 0, 0, 0, 0],  # nv 13
    [4, 3, 3, 1, 0, 0, 0, 0, 0],  # nv 14
    [4, 3, 3, 2, 0, 0, 0, 0, 0],  # nv 15
    [4, 3, 3, 2, 0, 0, 0, 0, 0],  # nv 16
    [4, 3, 3, 3, 1, 0, 0, 0, 0],  # nv 17
    [4, 3, 3, 3, 1, 0, 0, 0, 0],  # nv 18
    [4, 3, 3, 3, 2, 0, 0, 0, 0],  # nv 19
    [4, 3, 3, 3, 2, 0, 0, 0, 0],  # nv 20
]

THIRD_CASTER_SLOTS: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 1
    [0, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 2
    [2, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 3
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 4
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 5
    [3, 0, 0, 0, 0, 0, 0, 0, 0],  # nv 6
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 7
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 8
    [4, 2, 0, 0, 0, 0, 0, 0, 0],  # nv 9
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 10
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 11
    [4, 3, 0, 0, 0, 0, 0, 0, 0],  # nv 12
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 13
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 14
    [4, 3, 2, 0, 0, 0, 0, 0, 0],  # nv 15
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 16
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 17
    [4, 3, 3, 0, 0, 0, 0, 0, 0],  # nv 18
    [4, 3, 3, 1, 0, 0, 0, 0, 0],  # nv 19
    [4, 3, 3, 1, 0, 0, 0, 0, 0],  # nv 20
]

CURRENCY_NAMES: dict[str, str] = {
    "oro":     "GP",
    "plata":   "SP",
    "cobre":   "CP",
    "platino": "PP",
    "electro": "EP",
}

# Nombres de trackers custom (se excluyen del inventario normal)
CUSTOM_TRACKER_NAMES: set[str] = {"wuju", "afortunado"}

# Regex para detectar items de moneda, p.ej. "Oro: 27"
CURRENCY_RE = re.compile(r"^(Oro|Plata|Cobre|Platino|Electro):\s*(-?\d+)$", re.IGNORECASE)

VERBOSE = False


def _warn(msg: str) -> None:
    if VERBOSE:
        print(f"[WARN] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Helpers de extracción
# ---------------------------------------------------------------------------

def _url_param(url_str: str, param: str) -> str | None:
    """Extrae un parámetro de la query string de una URL."""
    try:
        params = parse_qs(urlparse(url_str).query)
        vals = params.get(param)
        return vals[0] if vals else None
    except Exception:
        return None


def _modifier_from_formula(formula: str) -> int | None:
    """
    Parsea '1d20+3' → 3, '1d20-1' → -1, '1d20+0' → 0, '1d20' → 0.
    """
    if not formula:
        return None
    clean = formula.replace(" ", "")
    m = re.search(r"1d20([+-]\d+)?", clean)
    if not m:
        return None
    suffix = m.group(1)
    return int(suffix) if suffix else 0


def _is_proficient(icon_el: Tag | None) -> bool:
    """True si el icono FontAwesome es fa-circle (con competencia)."""
    if icon_el is None:
        return False
    classes = icon_el.get("class", [])
    return "fa-circle" in classes and "fa-circle-o" not in classes


def _normalize_weight(text: str) -> float | None:
    """
    Convierte '0,5 kg', "0'5 kg", '2.5 kg', '2 kg' → float.
    """
    if not text:
        return None
    clean = text.lower().replace("kg", "").strip()
    clean = re.sub(r"[,']", ".", clean)
    try:
        return float(clean)
    except ValueError:
        return None


def _strong_value(container: Tag, label: str) -> str | None:
    """
    Busca <p><strong>LABEL</strong>. VALUE</p> (o ': VALUE') en el container.
    Devuelve VALUE como string limpio.
    Usa siblings para evitar errores de índice por whitespace en el texto completo.
    """
    for p in container.find_all("p"):
        strong = p.find("strong")
        if not strong:
            continue
        strong_text = strong.get_text(strip=True).rstrip(".").strip()
        if strong_text == label:
            # Recolectar todos los nodos de texto DESPUÉS del strong dentro del <p>
            parts: list[str] = []
            for sibling in strong.next_siblings:
                if hasattr(sibling, "get_text"):
                    parts.append(sibling.get_text(strip=True))
                else:
                    parts.append(str(sibling))
            value = "".join(parts).lstrip(". :").strip()
            return value or None
    return None


def _item_id_from_href(href: str) -> str | None:
    """'...items/5665785-daga/edit' → '5665785'"""
    m = re.search(r"/items/(\d+)-", href or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# parse_meta
# ---------------------------------------------------------------------------

def parse_meta(soup: BeautifulSoup) -> dict:
    try:
        url_tag = soup.find("meta", property="og:url")
        url = url_tag["content"] if url_tag else None

        char_id = None
        if url:
            m = re.search(r"/characters/(\d+)-", url)
            char_id = int(m.group(1)) if m else None

        body = soup.find("body")
        owner = body.get("data-user-name") if body else None

        return {
            "system": "D&D 5.5 (2024)",
            "platform": "Nivel20.com",
            "character_url": url,
            "character_id": char_id,
            "owner": owner,
        }
    except Exception as e:
        _warn(f"parse_meta: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_basic_info
# ---------------------------------------------------------------------------

def parse_basic_info(soup: BeautifulSoup) -> dict:
    try:
        # Nombre
        h1 = soup.find("h1", class_="content-header-title")
        name = h1.get_text(strip=True) if h1 else None

        # Retrato: meta og:image
        og_img = soup.find("meta", property="og:image")
        portrait_url = og_img["content"] if og_img else None

        # Raza
        race = None
        race_link = soup.find("a", class_="custom-value-link",
                              href=re.compile(r"field=race"))
        if race_link:
            span = race_link.find("span")
            race = span.get_text(strip=True) if span else race_link.get_text(strip=True)

        # Clases y nivel total
        classes: list[dict] = []
        total_level = 0

        # Busca el texto del contenedor de descripción del personaje
        char_desc = soup.find(class_="character-desc")
        desc_text = char_desc.get_text(separator=" ", strip=True) if char_desc else ""

        # Patrón: NombreClase Nivel, p. ej. "Monje 2" o "Guerrero 3 / Pícaro 2"
        for class_name, level_str in re.findall(
            r"([A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+)\s+(\d+)", desc_text
        ):
            # Ignorar si es la raza
            if class_name.lower() == (race or "").lower():
                continue
            # Ignorar palabras como "Nivel"
            if class_name.lower() == "nivel":
                continue
            level = int(level_str)
            classes.append({"name": class_name.capitalize(), "level": level, "subclass": None})
            total_level += level

        # Fallback: busca <strong>Nivel N</strong>
        if not classes:
            nivel_tag = soup.find("strong", string=re.compile(r"Nivel\s+\d+"))
            if nivel_tag:
                m = re.search(r"Nivel\s+(\d+)", nivel_tag.get_text())
                if m:
                    total_level = int(m.group(1))

        # Campaña
        # Trasfondo: h4 "Trasfondo: X" en #panel-background
        background = None
        panel_bg = soup.find(id="panel-background")
        if panel_bg:
            for h4 in panel_bg.find_all("h4"):
                t = h4.get_text(strip=True)
                if t.startswith("Trasfondo:"):
                    background = t.replace("Trasfondo:", "").strip()
                    break

        # Alineamiento
        alignment = None
        if panel_bg:
            alignment = _strong_value(panel_bg, "Alineamiento")

        return {
            "name": name,
            "species": race,
            "classes": classes,
            "total_level": total_level or (classes[0]["level"] if classes else None),
            "background": background,
            "alignment": alignment,
            "experience_points": None,
            "inspiration": False,
            "portrait_url": portrait_url,
        }
    except Exception as e:
        _warn(f"parse_basic_info: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_appearance
# ---------------------------------------------------------------------------

def parse_appearance(soup: BeautifulSoup) -> dict:
    try:
        panel_bg = soup.find(id="panel-background")
        fields: dict[str, object] = {
            "age": None, "height": None, "weight": None,
            "eyes": None, "skin": None, "hair": None, "gender": None,
        }
        if panel_bg:
            for label, key in [
                ("Edad",    "age"),
                ("Género",  "gender"),
                ("Genero",  "gender"),
                ("Altura",  "height"),
                ("Peso",    "weight"),
                ("Ojos",    "eyes"),
                ("Piel",    "skin"),
                ("Pelo",    "hair"),
                ("Cabello", "hair"),
            ]:
                if fields[key] is not None:
                    continue
                val = _strong_value(panel_bg, label)
                if not val:
                    continue
                if key == "age":
                    try:
                        fields[key] = int(val)
                    except ValueError:
                        fields[key] = val
                else:
                    fields[key] = val
        return {**fields, "size": "Mediana"}
    except Exception as e:
        _warn(f"parse_appearance: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_languages
# ---------------------------------------------------------------------------

def parse_languages(soup: BeautifulSoup) -> list[str]:
    try:
        panel_bg = soup.find(id="panel-background")
        if not panel_bg:
            return []
        val = _strong_value(panel_bg, "Idiomas")
        if not val:
            return []
        return [lang.strip() for lang in re.split(r",\s*", val) if lang.strip()]
    except Exception as e:
        _warn(f"parse_languages: {e}")
        return []


# ---------------------------------------------------------------------------
# parse_ability_scores
# ---------------------------------------------------------------------------

def parse_ability_scores(soup: BeautifulSoup) -> dict:
    result: dict = {}
    try:
        panel_info = soup.find(id="panel-info")
        if not panel_info:
            _warn("parse_ability_scores: no #panel-info")
            return result

        for cell in panel_info.find_all("div", class_="ability-cell"):
            box = cell.find(class_="custom-value-box")
            if not box:
                continue
            url = box.get("data-remote", "")
            field = _url_param(url, "field")
            if not field or field not in ABILITY_MAP:
                continue

            # Score
            score = None
            val_div = cell.find("div", class_="value")
            if val_div:
                try:
                    score = int(val_div.get_text(strip=True))
                except ValueError:
                    pass
            if score is None:
                raw = _url_param(url, "current_value")
                if raw:
                    try:
                        score = int(raw)
                    except ValueError:
                        pass

            # Modifier desde data-dice-roll
            modifier = None
            mod_span = cell.find("span", attrs={"data-dice-roll": True})
            if mod_span:
                modifier = _modifier_from_formula(mod_span.get("data-dice-roll", ""))
                if modifier is None:
                    try:
                        modifier = int(mod_span.get_text(strip=True).replace("+", ""))
                    except ValueError:
                        pass

            result[ABILITY_MAP[field]] = {"score": score, "modifier": modifier}

    except Exception as e:
        _warn(f"parse_ability_scores: {e}")
    return result


# ---------------------------------------------------------------------------
# parse_proficiency_bonus
# ---------------------------------------------------------------------------

def parse_proficiency_bonus(soup: BeautifulSoup) -> int | None:
    try:
        box = soup.find(attrs={"data-remote": re.compile(r"field=proficiency_bonus")})
        if box:
            raw = _url_param(box.get("data-remote", ""), "current_value")
            if raw:
                return int(raw.lstrip("+"))
    except Exception as e:
        _warn(f"parse_proficiency_bonus: {e}")
    return None


# ---------------------------------------------------------------------------
# parse_saving_throws
# ---------------------------------------------------------------------------

def parse_saving_throws(soup: BeautifulSoup) -> dict:
    result: dict = {}
    try:
        panel_info = soup.find(id="panel-info")
        if not panel_info:
            return result

        for link in panel_info.find_all("a", href=re.compile(r"category=saving_throws")):
            href = link.get("href", "")
            field = _url_param(href, "field")
            if not field:
                continue

            # Total desde current_value
            total = None
            raw = _url_param(href, "current_value")
            if raw:
                try:
                    total = int(raw.lstrip("+"))
                except ValueError:
                    pass

            # Proficiencia
            icon = link.find("i", class_="proficiency-icon")
            proficient = _is_proficient(icon)

            # Roll desde el span en la misma fila
            roll = None
            row = link.find_parent(class_="table-row")
            if row:
                span = row.find("span", attrs={"data-dice-roll": True})
                if span:
                    roll = span.get("data-dice-roll")
                    if total is None:
                        total = _modifier_from_formula(roll)

            en_key = ABILITY_MAP.get(field, field)
            result[en_key] = {
                "total": total,
                "proficient": proficient,
                "roll": roll,
            }
    except Exception as e:
        _warn(f"parse_saving_throws: {e}")
    return result


# ---------------------------------------------------------------------------
# parse_skills
# ---------------------------------------------------------------------------

def parse_skills(soup: BeautifulSoup) -> dict:
    result: dict = {}
    try:
        accordion = soup.find(id="skillsAccordion")
        if not accordion:
            _warn("parse_skills: no #skillsAccordion")
            return result

        for link in accordion.find_all("a", href=re.compile(r"category=skills")):
            href = link.get("href", "")
            field = _url_param(href, "field")
            if not field:
                continue

            total = None
            raw = _url_param(href, "current_value")
            if raw:
                try:
                    total = int(raw)
                except ValueError:
                    pass

            icon = link.find("i", class_="proficiency-icon")
            proficient = _is_proficient(icon)

            roll = None
            row = link.find(class_="table-row") or link
            span = row.find("span", attrs={"data-dice-roll": True})
            if span:
                roll = span.get("data-dice-roll")
                if total is None:
                    total = _modifier_from_formula(roll)

            result[field] = {
                "name":      SKILL_NAME_MAP.get(field, field.replace("_", " ").title()),
                "ability":   SKILL_ABILITY_MAP.get(field, "unknown"),
                "total":     total,
                "proficient":proficient,
                "expertise": False,
                "roll":      roll,
            }
    except Exception as e:
        _warn(f"parse_skills: {e}")
    return result


# ---------------------------------------------------------------------------
# parse_combat
# ---------------------------------------------------------------------------

def parse_combat(soup: BeautifulSoup, basic_info: dict | None = None) -> dict:
    try:
        def _static(field_name: str) -> str | None:
            box = soup.find(attrs={"data-remote": re.compile(rf"field={field_name}")})
            if box:
                return _url_param(box.get("data-remote", ""), "current_value")
            return None

        # HP
        hp_raw = _static("hit_points")
        hp_max = None
        if hp_raw:
            try:
                hp_max = int(hp_raw.lstrip("+"))
            except ValueError:
                pass

        # Iniciativa
        init_raw = _static("initiative")
        initiative = None
        if init_raw:
            try:
                initiative = int(init_raw.lstrip("+"))
            except ValueError:
                pass

        # Velocidad: span.distance-label con data-unit="feet"
        speed_feet = None
        span_dist = soup.find("span", class_="distance-label",
                              attrs={"data-unit": "feet"})
        if span_dist:
            try:
                speed_feet = float(span_dist.get("data-value", 0))
            except ValueError:
                pass
        speed_meters = round(speed_feet * 0.3) if speed_feet else None

        # CA
        ac_raw = _static("armor_normal")
        ac = None
        if ac_raw:
            try:
                ac = int(ac_raw)
            except ValueError:
                pass

        # Dado de golpe desde la clase
        hit_die = "d8"
        total_level = 1
        if basic_info:
            total_level = basic_info.get("total_level") or 1
            for cls in basic_info.get("classes", []):
                cls_name = cls.get("name", "").lower()
                die = CLASS_HIT_DIE.get(cls_name)
                if die:
                    hit_die = f"d{die}"
                    break

        return {
            "armor_class": ac,
            "initiative": initiative,
            "speed": {
                "walking_feet":   int(speed_feet) if speed_feet else None,
                "walking_meters": speed_meters,
                "swim_meters":    None,
                "fly_meters":     None,
                "climb_meters":   None,
            },
            "hit_points": {
                "maximum":   hp_max,
                "current":   None,
                "temporary": None,
            },
            "hit_dice": {
                "total":    f"{total_level}{hit_die}",
                "remaining": total_level,
                "used":     0,
                "die_type": hit_die,
            },
            "death_saves": {"successes": 0, "failures": 0},
        }
    except Exception as e:
        _warn(f"parse_combat: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_attacks
# ---------------------------------------------------------------------------

def parse_attacks(soup: BeautifulSoup) -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    try:
        for atk_span in soup.find_all("span", attrs={"data-roll-type": "attack"}):
            row = atk_span.find_parent("tr")
            if row is None:
                continue
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            name = cells[0].get_text(strip=True)
            if name in seen:
                continue
            seen.add(name)

            atk_formula = atk_span.get("data-dice-roll", "")
            try:
                atk_bonus = int(atk_span.get_text(strip=True).lstrip("+"))
            except ValueError:
                atk_bonus = _modifier_from_formula(atk_formula)

            dmg_span = cells[2].find("span", attrs={"data-roll-type": "damage"})
            dmg_formula = dmg_span.get("data-dice-roll", "").strip() if dmg_span else ""
            dmg_text = dmg_span.get_text(strip=True) if dmg_span else ""

            # Extraer tipo de daño: última palabra no numérica del texto de daño
            damage_type = None
            if dmg_text:
                parts = dmg_text.rsplit(" ", 1)
                if len(parts) == 2 and re.match(r"^[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+$", parts[-1]):
                    damage_type = parts[-1]

            result.append({
                "name":          name,
                "attack_bonus":  atk_bonus,
                "attack_roll":   atk_formula,
                "damage":        dmg_formula,
                "damage_type":   damage_type,
                "damage_display":dmg_text,
            })
    except Exception as e:
        _warn(f"parse_attacks: {e}")
    return result


# ---------------------------------------------------------------------------
# parse_proficiencies
# ---------------------------------------------------------------------------

def parse_proficiencies(soup: BeautifulSoup) -> dict:
    armor: list[str] = []
    weapons: list[str] = []
    tools: list[str] = []
    raw_lines: list[str] = []

    try:
        for card in soup.find_all("div", class_="card"):
            header = card.find(class_="card-header")
            if header and "otras competencias" in header.get_text(strip=True).lower():
                for li in card.find_all("li"):
                    raw_lines.append(li.get_text(strip=True))
                break

        armor_kw  = {"armadura", "escudo", "ligera", "media", "pesada"}
        tool_kw   = {"herramienta", "instrumento", "vehículo", "kit", "naipes", "dados"}

        for line in raw_lines:
            items_in_line = [x.strip() for x in re.split(r",\s*|\s+y\s+", line) if x.strip()]
            for item in items_in_line:
                item_lower = item.lower()
                if any(kw in item_lower for kw in armor_kw):
                    armor.append(item)
                elif any(kw in item_lower for kw in tool_kw):
                    tools.append(item)
                else:
                    weapons.append(item)
    except Exception as e:
        _warn(f"parse_proficiencies: {e}")

    return {"armor": armor, "weapons": weapons, "tools": tools, "raw": raw_lines}


# ---------------------------------------------------------------------------
# parse_features_and_traits
# ---------------------------------------------------------------------------

def parse_features_and_traits(soup: BeautifulSoup) -> dict:
    species_traits: list[dict] = []
    class_features: list[dict] = []
    feats: list[dict] = []

    try:
        panel = soup.find(id="panel-feats")
        if not panel:
            _warn("parse_features_and_traits: no #panel-feats")
            return {}

        current_source = "unknown"
        current_source_type = "unknown"  # species | class | feat

        for child in panel.descendants:
            if not isinstance(child, Tag):
                continue

            # --- Detectar encabezado h3 ---
            if child.name == "h3":
                race_a  = child.find("a", href=re.compile(r"/races/"))
                prof_a  = child.find("a", href=re.compile(r"/professions/"))
                dotes_i = child.find("i", class_=re.compile(r"ra-feather"))
                h3_text = child.get_text(strip=True).lower()

                if race_a:
                    current_source      = race_a.get_text(strip=True)
                    current_source_type = "species"
                elif prof_a:
                    current_source      = prof_a.get_text(strip=True)
                    current_source_type = "class"
                elif "dotes" in h3_text:
                    current_source      = "Dotes"
                    current_source_type = "feat"
                continue

            # --- Rasgo de especie: div[data-static-floating] ---
            if child.name == "div" and child.get("data-static-floating") == "true":
                t_name = child.get("data-floating-title", "").strip()
                t_desc = child.get("data-floating-content", "").strip()
                if t_name:
                    species_traits.append({
                        "name":        t_name,
                        "source":      current_source,
                        "description": t_desc or None,
                    })
                continue

            # --- Rasgo de clase o dote: a[data-floating] ---
            if child.name == "a" and child.get("data-floating") == "true":
                href   = child.get("href", "")
                t_name = child.get("data-floating-title", "").strip()
                if not t_name:
                    continue

                # Descripción: data-floating-content o primer div interno
                t_desc = child.get("data-floating-content", "").strip()
                if not t_desc:
                    style_div = child.find("div", style=re.compile(r"margin-top"))
                    if style_div:
                        first_div = style_div.find("div")
                        if first_div:
                            t_desc = first_div.get_text(strip=True)

                # Sub-detalles desde ul.character-feat-levels
                details: dict = {}
                feat_ul = child.find("ul", class_="character-feat-levels")
                if feat_ul:
                    for li in feat_ul.find_all("li"):
                        li_text = li.get_text(strip=True)
                        if ":" in li_text:
                            k, _, v = li_text.partition(":")
                            details[k.strip()] = v.strip()
                        else:
                            details[f"item_{len(details)}"] = li_text

                # ID numérico del rasgo
                feat_id = None
                for pattern in (r"/feats/(\d+)-", r"/profession_traits/(\d+)-"):
                    m = re.search(pattern, href)
                    if m:
                        feat_id = m.group(1)
                        break

                entry: dict = {
                    "name":        t_name,
                    "source":      current_source,
                    "description": t_desc or None,
                }
                if details:
                    entry["details"] = details
                if feat_id:
                    entry["id"] = feat_id

                if current_source_type == "feat" or "/feats/" in href:
                    feats.append(entry)
                else:
                    class_features.append(entry)

    except Exception as e:
        _warn(f"parse_features_and_traits: {e}")

    return {
        "species":        species_traits,
        "class_features": class_features,
        "feats":          feats,
    }


# ---------------------------------------------------------------------------
# parse_spellcasting
# ---------------------------------------------------------------------------

def _derive_spell_slots(basic_info: dict, feats: list[dict]) -> dict:
    """Deriva los spell slots de reglas de clase y dotes (D&D 2024)."""
    slots: dict = {}
    feat_names = {f.get("name", "").lower() for f in feats}
    classes = basic_info.get("classes", [])

    # Acumular niveles por tipo de lanzador
    full_level  = 0
    half_level  = 0
    third_level = 0
    for cls in classes:
        name  = (cls.get("name") or "").lower()
        level = cls.get("level") or 0
        if name in FULL_CASTER_CLASSES:
            full_level  += level
        elif name in HALF_CASTER_CLASSES:
            half_level  += level
        elif name in THIRD_CASTER_CLASSES:
            third_level += level

    is_any_caster = full_level or half_level or third_level

    # Iniciado en la magia → 1 slot de nv.1 solo si no es lanzador de ningún tipo
    if "iniciado en la magia" in feat_names and not is_any_caster:
        return {
            "level_1": {
                "total":  1,
                "used":   0,
                "source": "Iniciado en la magia",
                "note":   "1 lanzamiento gratuito por descanso largo",
            }
        }

    if not is_any_caster:
        return slots

    # Nivel efectivo de lanzador (regla de multiclase)
    effective = full_level + (half_level // 2) + (third_level // 3)
    if effective == 0:
        return slots

    # Seleccionar tabla según la clase dominante
    row_idx = min(max(effective, 1), 20) - 1
    if full_level:
        table_row = FULL_CASTER_SLOTS[row_idx]
    elif half_level:
        # Para clase pura half-caster usar su nivel real (no el efectivo mezclado)
        table_row = HALF_CASTER_SLOTS[min(half_level, 20) - 1]
    else:
        table_row = THIRD_CASTER_SLOTS[min(third_level, 20) - 1]

    for spell_lvl, count in enumerate(table_row, start=1):
        if count > 0:
            slots[f"level_{spell_lvl}"] = {"total": count, "used": 0}

    return slots


def _get_spellcasting_ability(basic_info: dict) -> str | None:
    """Devuelve la característica de conjuración de la clase principal."""
    for cls in basic_info.get("classes", []):
        name = (cls.get("name") or "").lower()
        ability = SPELL_ABILITY_BY_CLASS.get(name)
        if ability:
            return ability
    return None


def parse_spellcasting(
    soup: BeautifulSoup,
    basic_info: dict | None = None,
    feats: list[dict] | None = None,
) -> dict:
    try:
        panel = soup.find(id="panel-magic")
        if not panel:
            _warn("parse_spellcasting: no #panel-magic")
            return {}

        # CD de salvación
        spell_dc = None
        dc_box = panel.find(attrs={"data-remote": re.compile(r"field=spell_save")})
        if dc_box:
            raw = _url_param(dc_box.get("data-remote", ""), "current_value")
            if raw:
                try:
                    spell_dc = int(raw)
                except ValueError:
                    pass
            if spell_dc is None:
                mod_div = dc_box.find(class_="modifier")
                if mod_div:
                    try:
                        spell_dc = int(mod_div.get_text(strip=True))
                    except ValueError:
                        pass

        # Bono ataque con conjuros
        spell_attack = None
        spell_attack_roll = None
        atk_box = panel.find(attrs={"data-remote": re.compile(r"field=spell_attack")})
        if atk_box:
            span = atk_box.find("span", attrs={"data-dice-roll": True})
            if span:
                spell_attack_roll = span.get("data-dice-roll")
                try:
                    spell_attack = int(span.get_text(strip=True).lstrip("+"))
                except ValueError:
                    spell_attack = _modifier_from_formula(spell_attack_roll)

        # Conjuros: a.spell-row
        spells_by_level: dict[int, list] = {}

        for spell_a in panel.find_all("a", class_="spell-row"):
            s_name = spell_a.get("data-floating-title", "").strip()
            if not s_name:
                continue

            s_id   = spell_a.get("data-spell-id")
            s_href = spell_a.get("href", "")

            # Nivel: div.xcol-md-1 con texto "Truco" o "Nv. X"
            level = 0
            for div in spell_a.find_all("div"):
                classes_list = div.get("class", [])
                if "xcol-md-1" in classes_list:
                    lvl_text = div.get_text(strip=True).lower()
                    if "truco" in lvl_text:
                        level = 0
                    else:
                        m = re.search(r"(\d+)", lvl_text)
                        if m:
                            level = int(m.group(1))
                    break

            # Metadatos: escuela, tiempo, duración, rango, componentes
            school = cast_time = duration = spell_range = components = None
            meta_container = spell_a.find("div", class_=re.compile(r"xcol-md-8"))
            if meta_container:
                inner_row = meta_container.find("div", class_="row")
                if inner_row:
                    cols = inner_row.find_all("div", recursive=False)
                    if len(cols) > 0:
                        school     = cols[0].get_text(strip=True) or None
                    if len(cols) > 1:
                        cast_time  = cols[1].get_text(strip=True) or None
                    if len(cols) > 2:
                        duration   = cols[2].get_text(strip=True) or None
                    if len(cols) > 3:
                        spell_range = cols[3].get_text(strip=True) or None
                    if len(cols) > 4:
                        components = cols[4].get_text(strip=True) or None

            # Descripción: segundo div.row dentro del spell-row-content
            description = None
            content_div = spell_a.find(class_="spell-row-content")
            if content_div:
                rows = content_div.find_all("div", class_="row", recursive=False)
                if len(rows) >= 2:
                    desc_inner = rows[1].find("div")
                    if desc_inner:
                        description = desc_inner.get_text(strip=True) or None

            spell_entry = {
                "name":         s_name,
                "spell_id":     s_id,
                "school":       school,
                "casting_time": cast_time,
                "duration":     duration,
                "range":        spell_range or None,
                "components":   components,
                "description":  description,
            }
            spells_by_level.setdefault(level, []).append(spell_entry)

        spell_slots = _derive_spell_slots(basic_info or {}, feats or [])
        spell_ability = _get_spellcasting_ability(basic_info or {})

        return {
            "spellcasting_ability": spell_ability,
            "spell_save_dc":        spell_dc,
            "spell_attack_bonus":   spell_attack,
            "spell_attack_roll":    spell_attack_roll,
            "spell_slots":          spell_slots,
            "spells": {
                "cantrips": spells_by_level.get(0, []),
                **{
                    f"level_{lvl}": spells
                    for lvl, spells in sorted(spells_by_level.items())
                    if lvl > 0
                },
            },
        }
    except Exception as e:
        _warn(f"parse_spellcasting: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_inventory — helper de extracción de un item
# ---------------------------------------------------------------------------

def _extract_item_data(body: Tag, item_name: str) -> dict:
    """Extrae todos los campos de un ítem del cuerpo del acordeón."""
    data: dict = {"name": item_name}

    # Descripción
    card_text = body.find(class_="card-text")
    if card_text:
        p = card_text.find("p")
        data["description"] = p.get_text(strip=True) if p else None

    pt_div = body.find("div", class_="pt-1") or body
    if pt_div:
        data["type"]     = _strong_value(pt_div, "Tipo de objeto")
        data["category"] = _strong_value(pt_div, "Categoría")

        roll_div = pt_div.find("div", attrs={"data-roll-name": True})
        if roll_div:
            prof_raw = _strong_value(roll_div, "Competencia")
            data["proficient"] = (prof_raw == "Competencia") if prof_raw else False

            price_raw  = _strong_value(roll_div, "Precio")
            data["price"] = price_raw

            weight_raw = _strong_value(roll_div, "Peso")
            data["weight_kg"] = _normalize_weight(weight_raw) if weight_raw else None

            # ¿Es un arma? Detecta el span de ataque
            atk_span = roll_div.find("span", attrs={"data-roll-type": "attack"})
            if atk_span:
                data["is_weapon"] = True
                data["attack_roll"] = atk_span.get("data-dice-roll")
                try:
                    data["attack_bonus"] = int(atk_span.get_text(strip=True).lstrip("+"))
                except ValueError:
                    data["attack_bonus"] = _modifier_from_formula(data["attack_roll"])

                # Tabla de daño
                dmg_table = roll_div.find("table", class_="item-damage-table")
                if dmg_table:
                    dmg_spans = dmg_table.find_all("span", attrs={"data-dice-roll": True})
                    if dmg_spans:
                        data["damage"]          = dmg_spans[0].get("data-dice-roll", "").strip()
                    if len(dmg_spans) >= 2:
                        data["critical_damage"] = dmg_spans[1].get("data-dice-roll", "").strip()

                data["damage_type"] = _strong_value(roll_div, "Tipo de daño")

                # Rango (armas arrojadizas o a distancia)
                range_spans = roll_div.find_all("span", class_="distance-value")
                if range_spans:
                    ranges: list[dict] = []
                    for rs in range_spans:
                        dv = rs.get("data-value")
                        du = rs.get("data-unit", "feet")
                        if dv:
                            val = float(dv)
                            if du == "feet":
                                ranges.append({"feet": round(val), "meters": round(val * 0.3)})
                            else:
                                ranges.append({"feet": round(val / 0.3), "meters": round(val)})
                    if len(ranges) >= 2:
                        data["range_normal"] = ranges[0]
                        data["range_long"]   = ranges[1]
                    elif ranges:
                        data["range_normal"] = ranges[0]
            else:
                data["is_weapon"] = False

            # Propiedades (badges)
            badge_list = roll_div.find(class_="badge-list")
            if badge_list:
                badges = [b.get_text(strip=True)
                          for b in badge_list.find_all("span", class_="badge")
                          if b.get_text(strip=True)]
                if badges:
                    data["properties"] = badges

        # ID de item desde el enlace "Editar"
        edit_a = pt_div.find("a", href=re.compile(r"/items/\d+-"))
        if edit_a:
            data["item_id"] = _item_id_from_href(edit_a.get("href", ""))

    return data


# ---------------------------------------------------------------------------
# parse_inventory
# ---------------------------------------------------------------------------

def parse_inventory(soup: BeautifulSoup) -> dict:
    currency      = {"PP": 0, "GP": 0, "EP": 0, "SP": 0, "CP": 0}
    items_data:     dict[str, dict] = {}   # nombre → datos del ítem con cantidades por ubicación
    custom_trackers: list[dict]     = []
    other_possessions = None
    current_location  = ""

    try:
        panel = soup.find(id="panel-items")
        if not panel:
            _warn("parse_inventory: no #panel-items")
            return {}

        # "Otras posesiones"
        eq_ta = panel.find("textarea", id="equipment-editor")
        if eq_ta:
            other_possessions = (eq_ta.get("data-value") or "").strip() or None
        else:
            alert = panel.find("div", class_="alert-bordered")
            if alert:
                p = alert.find("p")
                other_possessions = p.get_text(strip=True) if p else None

        for wrapper in panel.find_all("div", class_="accordion-wrapper"):
            title_span = wrapper.find("span", class_="accordion-title")
            if not title_span:
                continue

            item_name = title_span.get_text(strip=True)

            # Filtrar headers de GRUPO ("Equipado", "Transportado", "Otros"):
            # Los grupos tienen span.accordion-value (el contador) y NO tienen
            # el span.accordion-title envuelto en un <a> de collapse.
            # Los ítems individuales SÍ tienen su span dentro de un <a data-toggle>.
            header_div = wrapper.find("div", class_="accordion-header")
            if header_div:
                # Si hay un span.accordion-value es un header de sección, no un ítem
                if header_div.find("span", class_="accordion-value"):
                    current_location = item_name
                    continue
                # Si el title_span NO está dentro de un <a>, también es un grupo
                if not title_span.find_parent("a"):
                    current_location = item_name
                    continue

            # --- Moneda ---
            m_curr = CURRENCY_RE.match(item_name)
            if m_curr:
                key    = CURRENCY_NAMES.get(m_curr.group(1).lower(), "XX")
                amount = int(m_curr.group(2))
                currency[key] = amount
                continue

            # --- Tracker custom por nombre ---
            if item_name.lower() in CUSTOM_TRACKER_NAMES:
                body = wrapper.find(class_="card-body")
                if body:
                    custom_trackers.append(_extract_item_data(body, item_name))
                continue

            # --- Tracker custom por descripción ---
            body = wrapper.find(class_="card-body")
            if body:
                card_text_el = body.find(class_="card-text")
                desc_text = card_text_el.get_text(strip=True).lower() if card_text_el else ""
                if "contador" in desc_text and "puntos" in desc_text:
                    custom_trackers.append(_extract_item_data(body, item_name))
                    continue

            # --- Ítem normal ---
            if item_name not in items_data:
                items_data[item_name] = _extract_item_data(body, item_name) if body else {"name": item_name}
                items_data[item_name]["qty_equipped"] = 0
                items_data[item_name]["qty_backpack"] = 0
                items_data[item_name]["qty_bag"] = 0

            if current_location == "Equipado":
                items_data[item_name]["qty_equipped"] += 1
            elif current_location == "Transportado":
                items_data[item_name]["qty_backpack"] += 1
            else:
                items_data[item_name]["qty_bag"] += 1

    except Exception as e:
        _warn(f"parse_inventory: {e}")
        return {}

    # Construir lista final con cantidad y localización
    items: list[dict] = []
    for entry in items_data.values():
        qty_total = (
            int(entry.get("qty_equipped") or 0)
            + int(entry.get("qty_backpack") or 0)
            + int(entry.get("qty_bag") or 0)
        )
        entry["quantity"] = qty_total
        items.append(entry)

    return {
        "currency":          currency,
        "other_possessions": other_possessions,
        "items":             items,
        "_custom_trackers":  custom_trackers,   # usado internamente, se elimina antes de exportar
    }


# ---------------------------------------------------------------------------
# parse_background_details
# ---------------------------------------------------------------------------

def parse_background_details(soup: BeautifulSoup) -> dict:
    try:
        panel = soup.find(id="panel-background")
        if not panel:
            return {}

        background_name = None
        background_desc = None

        for h4 in panel.find_all("h4"):
            t = h4.get_text(strip=True)
            if t.startswith("Trasfondo:"):
                background_name = t.replace("Trasfondo:", "").strip()
                next_p = h4.find_next_sibling("p")
                if next_p:
                    background_desc = next_p.get_text(strip=True)
                break

        skill_profs_text = _strong_value(panel, "Competencia con habilidades del trasfondo")
        skill_profs: list[str] = []
        if skill_profs_text:
            skill_profs = [
                s.strip()
                for s in re.split(r"\s+y\s+|,\s*", skill_profs_text)
                if s.strip()
            ]

        return {
            "name":               background_name,
            "description":        background_desc,
            "skill_proficiencies":skill_profs,
            "personality_traits": [],
            "ideals":             [],
            "bonds":              [],
            "flaws":              [],
        }
    except Exception as e:
        _warn(f"parse_background_details: {e}")
        return {}


# ---------------------------------------------------------------------------
# parse_resources
# ---------------------------------------------------------------------------

def parse_resources(
    soup: BeautifulSoup,
    basic_info: dict | None  = None,
    features: dict | None    = None,
    inventory: dict | None   = None,
    proficiency_bonus: int | None = None,
) -> dict:
    resources: dict = {}
    try:
        bi  = basic_info or {}
        ft  = features  or {}
        inv = inventory or {}

        classes     = bi.get("classes", [])
        total_level = bi.get("total_level", 1) or 1
        feat_names  = {f.get("name", "").lower() for f in ft.get("feats", [])}
        all_class_f = ft.get("class_features", [])
        trackers    = inv.get("_custom_trackers", [])

        # Puntos de Concentración (Ki) — Monje
        is_monk = any(c.get("name", "").lower() == "monje" for c in classes)
        if is_monk:
            monk_level = next(
                (c.get("level", 0) for c in classes if c.get("name", "").lower() == "monje"),
                total_level,
            )
            ki_current = monk_level
            for tracker in trackers:
                if tracker.get("name", "").lower() == "wuju":
                    desc = tracker.get("description", "") or ""
                    m = re.search(r"Munición[:\s]+(\d+)", desc)
                    if m:
                        ki_current = int(m.group(1))
                    break

            resources["concentration_points"] = {
                "name":     "Puntos de Concentración (Ki)",
                "max":      monk_level,
                "current":  ki_current,
                "recharge": "descanso corto o largo",
            }

        # Puntos de Suerte — Afortunado
        if "afortunado" in feat_names:
            pb = proficiency_bonus or 2
            luck_current = pb
            for tracker in trackers:
                if tracker.get("name", "").lower() == "afortunado":
                    desc = tracker.get("description", "") or ""
                    m = re.search(r"Munición[:\s]+(\d+)", desc)
                    if m:
                        luck_current = int(m.group(1))
                    break

            resources["luck_points"] = {
                "name":     "Puntos de Suerte (Afortunado)",
                "max":      pb,
                "current":  luck_current,
                "recharge": "descanso largo",
            }

        # Metabolismo asombroso
        if any("metabolismo" in f.get("name", "").lower() for f in all_class_f):
            resources["metabolismo_asombroso"] = {
                "name":     "Metabolismo asombroso",
                "max":      1,
                "current":  1,
                "recharge": "descanso largo",
                "trigger":  "al tirar iniciativa",
            }

        # Inspiración heroica (Humano - Ingenioso)
        if any("ingenioso" in t.get("name", "").lower() for t in ft.get("species", [])):
            resources["inspiracion_heroica"] = {
                "name":     "Inspiración heroica (Ingenioso)",
                "max":      1,
                "current":  None,
                "recharge": "descanso largo",
            }

        # Conjuro gratuito — Iniciado en la magia
        if "iniciado en la magia" in feat_names:
            resources["escudo_gratis"] = {
                "name":     "Escudo (conjuro gratuito - Iniciado en la magia)",
                "max":      1,
                "current":  1,
                "recharge": "descanso largo",
            }

    except Exception as e:
        _warn(f"parse_resources: {e}")

    return resources


# ---------------------------------------------------------------------------
# parse_notes
# ---------------------------------------------------------------------------

def parse_notes(
    soup: BeautifulSoup,
    inventory: dict   | None = None,
    background: dict  | None = None,
) -> dict:
    try:
        return {
            "other_possessions": (inventory  or {}).get("other_possessions"),
            "backstory":         (background or {}).get("description") or "",
            "organizations":     "",
            "allies":            "",
            "enemies":           "",
            "additional_notes":  "",
        }
    except Exception as e:
        _warn(f"parse_notes: {e}")
        return {}


# ---------------------------------------------------------------------------
# HTTP fetching
# ---------------------------------------------------------------------------

def _fetch_url(url: str) -> str:
    """
    Descarga el HTML de una URL de Nivel20.
    La página es pública — no requiere autenticación ni cookies.
    Usa urllib.request (stdlib), sin dependencias adicionales.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Orquestación principal
# ---------------------------------------------------------------------------

def _derive_unarmed_attack(
    basic_info: dict,
    features: dict,
    ability_scores: dict,
    proficiency_bonus: int,
) -> dict | None:
    """Deriva el ataque desarmado para un Monje con Artes Marciales."""
    is_monk = any(
        c.get("name", "").lower() == "monje"
        for c in basic_info.get("classes", [])
    )
    if not is_monk:
        return None

    # Dado de daño desarmado desde detalles de Artes Marciales
    unarmed_die = "d6"
    for f in features.get("class_features", []):
        if "artes marciales" in f.get("name", "").lower():
            die = (f.get("details") or {}).get("Daño desarmado", "")
            if re.match(r"1d\d+", die):
                unarmed_die = die[1:]  # "1d6" → "d6"
            break

    dex = (ability_scores.get("dexterity") or {}).get("modifier", 0)
    pb  = proficiency_bonus or 2
    bonus = dex + pb
    sign = "+" if bonus >= 0 else ""
    dex_sign = "+" if dex >= 0 else ""
    return {
        "name":           "Ataque desarmado",
        "attack_bonus":   bonus,
        "attack_roll":    f"1d20{sign}{bonus}",
        "damage":         f"1{unarmed_die}{dex_sign}{dex}" if dex != 0 else f"1{unarmed_die}",
        "damage_type":    "contundente",
        "damage_display": f"1{unarmed_die}{dex_sign}{dex} contundente" if dex != 0 else f"1{unarmed_die} contundente",
        "properties":     ["finura", "sin carga"],
    }


def parse_html(source: Path | str) -> dict:
    """
    Parsea un personaje de Nivel20 y devuelve un dict con todos sus datos.

    source puede ser:
    - Path  → ruta a un fichero HTML local
    - str   → HTML ya descargado como texto (p.ej. desde _fetch_url)
    """
    if isinstance(source, Path):
        html_text = source.read_text(encoding="utf-8", errors="replace")
    else:
        html_text = source

    soup = BeautifulSoup(html_text, "html.parser")

    meta              = parse_meta(soup)
    basic_info        = parse_basic_info(soup)
    appearance        = parse_appearance(soup)
    languages         = parse_languages(soup)
    ability_scores    = parse_ability_scores(soup)
    proficiency_bonus = parse_proficiency_bonus(soup)
    saving_throws     = parse_saving_throws(soup)
    skills            = parse_skills(soup)
    combat            = parse_combat(soup, basic_info)
    attacks           = parse_attacks(soup)
    proficiencies     = parse_proficiencies(soup)
    features          = parse_features_and_traits(soup)

    # Inferir expertise: si proficient y total > ability_mod + pb → expertise=True
    pb = proficiency_bonus or 2
    for sk_key, sk in skills.items():
        if sk.get("expertise"):
            continue
        if not sk.get("proficient"):
            continue
        ability_key = sk.get("ability", "")
        ab_mod = (ability_scores.get(ability_key) or {}).get("modifier", 0) or 0
        total  = sk.get("total")
        if total is not None and total > ab_mod + pb:
            sk["expertise"] = True

    # Derivar ataque desarmado para Monje (no está en la tabla de ataques del HTML)
    unarmed = _derive_unarmed_attack(basic_info, features, ability_scores, proficiency_bonus)
    if unarmed:
        existing_names = [a.get("name", "").lower() for a in attacks]
        if unarmed["name"].lower() not in existing_names:
            # Insertar en segunda posición (después de Daga, antes de Antorcha)
            attacks.insert(1, unarmed)
    inventory         = parse_inventory(soup)
    background        = parse_background_details(soup)
    spellcasting      = parse_spellcasting(soup, basic_info, features.get("feats", []))
    resources         = parse_resources(soup, basic_info, features, inventory, proficiency_bonus)
    notes             = parse_notes(soup, inventory, background)

    # inventory limpio (sin clave interna)
    clean_inventory = {k: v for k, v in inventory.items() if not k.startswith("_")}

    # Claves que provienen de Nivel20 (para smart-merge: estas se actualizan en re-import)
    nivel20_keys = [
        "basic_info.name", "basic_info.species", "basic_info.classes",
        "basic_info.total_level", "basic_info.background", "basic_info.alignment",
        "basic_info.portrait_url",
        "appearance.age", "appearance.size",
        "languages",
        "ability_scores",
        "proficiency_bonus",
        "saving_throws",
        "skills",
        "combat.armor_class", "combat.initiative",
        "combat.speed.walking_feet", "combat.speed.walking_meters",
        "combat.hit_dice",
        "attacks",
        "proficiencies",
        "features_and_traits",
        "spellcasting.spell_save_dc", "spellcasting.spell_attack_bonus",
        "spellcasting.spell_attack_roll", "spellcasting.spell_slots",
        "spellcasting.spells", "spellcasting.spellcasting_ability",
        "inventory.items", "inventory.currency",
        "background_details.name", "background_details.description",
        "background_details.skill_proficiencies",
        "resources",
    ]
    meta["nivel20_keys"] = nivel20_keys
    meta["last_sync"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "meta":              meta,
        "basic_info":        basic_info,
        "appearance":        appearance,
        "languages":         languages,
        "ability_scores":    ability_scores,
        "proficiency_bonus": proficiency_bonus,
        "saving_throws":     saving_throws,
        "skills":            skills,
        "combat":            combat,
        "attacks":           attacks,
        "proficiencies":     proficiencies,
        "features_and_traits": features,
        "spellcasting":      spellcasting,
        "inventory":         clean_inventory,
        "background_details":background,
        "resources":         resources,
        "notes":             notes,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    global VERBOSE

    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

    source_arg = positional[0] if positional else None
    is_url = bool(source_arg and source_arg.startswith(("http://", "https://")))

    if is_url:
        url = source_arg
        # Nombre de salida por defecto: slug de la URL, p. ej. "1966429-webons.json"
        slug = url.rstrip("/").split("/")[-1]
        default_out = PATHS.data_dir / f"{slug}.json"
        output_path = Path(positional[1]) if len(positional) >= 2 else default_out

        print(f"Descargando: {url}")
        try:
            source: Path | str = _fetch_url(url)
        except Exception as e:
            sys.exit(f"Error al descargar '{url}': {e}")
        print(f"Descarga completada ({len(source):,} bytes)")
    else:
        input_path  = Path(source_arg) if source_arg else PATHS.data_dir / "personaje.html"
        output_path = Path(positional[1]) if len(positional) >= 2 else input_path.with_suffix(".json")

        if not input_path.exists():
            sys.exit(f"Error: no se encuentra '{input_path}'")

        print(f"Procesando: {input_path}")
        source = input_path

    data = parse_html(source)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Resumen
    bi   = data.get("basic_info", {})
    name = bi.get("name", "?")
    race = bi.get("species", "?")
    cls  = ", ".join(f"{c['name']} {c['level']}" for c in bi.get("classes", [])) or "?"
    spells_all = data.get("spellcasting", {}).get("spells", {})
    n_spells   = sum(len(v) for v in spells_all.values())
    ft         = data.get("features_and_traits", {})

    print(f"\nPersonaje : {name} ({race}, {cls})")
    print(f"  Puntuaciones :  {len(data.get('ability_scores', {}))} características")
    print(f"  Habilidades  :  {len(data.get('skills', {}))} habilidades")
    print(f"  Ataques      :  {len(data.get('attacks', []))} ataques únicos")
    print(f"  Rasgos       :  {len(ft.get('class_features', []))} de clase  |  "
          f"{len(ft.get('species', []))} de especie  |  "
          f"{len(ft.get('feats', []))} dotes")
    print(f"  Conjuros     :  {n_spells} conjuros")
    print(f"  Inventario   :  {len(data.get('inventory', {}).get('items', []))} ítems únicos")
    print(f"  Recursos     :  {list(data.get('resources', {}).keys())}")
    print(f"\nJSON guardado en: {output_path}")


if __name__ == "__main__":
    main()
