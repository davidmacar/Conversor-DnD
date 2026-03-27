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
import urllib.request
from dataclasses import dataclass
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT_BOOTSTRAP = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT_BOOTSTRAP))

from project_paths import ensure_runtime_directories, get_project_paths

try:
    import fitz  # PyMuPDF
except ImportError as exc:
    raise ImportError("Error: instala PyMuPDF con:  pip install pymupdf") from exc

try:
    from fontTools.ttLib import TTFont as _TTFont
except ImportError as exc:
    raise ImportError("Error: instala fonttools con:  pip install fonttools") from exc

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PATHS = get_project_paths()
ensure_runtime_directories(PATHS)

PROJECT_ROOT  = PATHS.project_root
TEMPLATE_PATH = PATHS.template_pdf
FONT_PATH     = PATHS.font_ttf
DEFAULT_JSON  = PATHS.character_json
DEFAULT_OUT   = PATHS.output_dir / "personaje_output.pdf"

# ---------------------------------------------------------------------------
# Lógica de mapeo y tipografía unificada (antes en fill_pdf.py)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Clasificación de campos por tamaño de fuente
# ---------------------------------------------------------------------------

# Estadísticas de consulta frecuente — tamaño 10
KEY_STATS: set[str] = {
    "Puntuacion-Fuerza",       "Modificador-Fuerza",
    "Puntuacion-Destreza",     "Modificador-Destreza",
    "Puntuacion-Constitucion", "Modificador-Constitucion",
    "Puntuacion-Inteligencia", "Modificador-Inteligencia",
    "Puntuacion-Sabiduria",    "Modificador-Sabiduria",
    "Puntuacion-Carisma",      "Modificador-Carisma",
    "Clase-Armadura", "Iniciativa", "Velocidad", "Percepcion-Pasiva",
    "Puntos-Golpe-Actuales", "Puntos-Golpe-Maximo",
    "Bonificador-Competencia",
}

# Importancia alta — tamaño 8
HIGH: set[str] = {
    "Nombre-Personaje",
    "Clase-Y-Nivel", "Especie", "Trasfondo",
    "Dados-Golpe-Maximos",
    "Arma-1-Nombre", "Arma-1-Ataque", "Arma-1-Dano", "Arma-1-Tipo",
    "Arma-2-Nombre", "Arma-2-Ataque", "Arma-2-Dano", "Arma-2-Tipo",
    "Arma-3-Nombre", "Arma-3-Ataque", "Arma-3-Dano", "Arma-3-Tipo",
    "Oro", "Plata", "Cobre", "Platino", "Electro",
    "Piezas.Oro", "Piezas.Plata", "Piezas.Cobre", "Piezas.Platino", "Piezas.Electro",
    "CD-Salvacion-Conjuros", "Aptitud-Magica",
}

# Importancia media — tamaño 7
MEDIUM: set[str] = {
    "PX-Personaje", "Alineamiento",
    "Dados-Golpe-Gastados", "Puntos-Golpe-Temporales",
    "Modificador-Salvacion-Fuerza",      "Modificador-Salvacion-Destreza",
    "Modificador-Salvacion-Constitucion","Modificador-Salvacion-Inteligencia",
    "Modificador-Salvacion-Sabiduria",   "Modificador-Salvacion-Carisma",
    "Modificador-Acrobacias",    "Modificador-Atletismo",
    "Modificador-Conocimiento-Arcano",   "Modificador-Engano",
    "Modificador-Historia",      "Modificador-Perspicacia",
    "Modificador-Intimidacion",  "Modificador-Investigacion",
    "Modificador-Medicina",      "Modificador-Naturaleza",
    "Modificador-Percepcion",    "Modificador-Interpretacion",
    "Modificador-Persuasion",    "Modificador-Religion",
    "Modificador-Juegos-De-Manos","Modificador-Sigilo",
    "Modificador-Supervivencia", "Modificador-Trato-Con-Animales",
    "Modificador-Aptitud-Magica",
    "Arma-1-Notas", "Arma-2-Notas", "Arma-3-Notas",
    "Arma-4-Nombre", "Arma-4-Ataque", "Arma-4-Dano", "Arma-4-Tipo", "Arma-4-Notas",
    "Arma-5-Nombre", "Arma-5-Ataque", "Arma-5-Dano", "Arma-5-Tipo", "Arma-5-Notas",
    "Competencia-Armas", "Competencia-Herramientas",
    "Idiomas",
} | {f"Total-Espacios-Conjuro.{i}" for i in range(1, 10)}

SIZE_XLARGE = 10
SIZE_HIGH   = 8
SIZE_MEDIUM = 7
SIZE_LOW    = 6

# Campos con alineación centrada
CENTERED: set[str] = {
    "Clase-Armadura", "Iniciativa", "Velocidad", "Percepcion-Pasiva",
    "Puntos-Golpe-Actuales", "Puntos-Golpe-Maximo", "Puntos-Golpe-Temporales",
    "Dados-Golpe-Maximos", "Dados-Golpe-Gastados",
    "Bonificador-Competencia", "PX-Personaje",
    "Puntuacion-Fuerza",       "Modificador-Fuerza",
    "Puntuacion-Destreza",     "Modificador-Destreza",
    "Puntuacion-Constitucion", "Modificador-Constitucion",
    "Puntuacion-Inteligencia", "Modificador-Inteligencia",
    "Puntuacion-Sabiduria",    "Modificador-Sabiduria",
    "Puntuacion-Carisma",      "Modificador-Carisma",
    "Modificador-Salvacion-Fuerza",      "Modificador-Salvacion-Destreza",
    "Modificador-Salvacion-Constitucion","Modificador-Salvacion-Inteligencia",
    "Modificador-Salvacion-Sabiduria",   "Modificador-Salvacion-Carisma",
    "Modificador-Acrobacias",    "Modificador-Atletismo",
    "Modificador-Conocimiento-Arcano",   "Modificador-Engano",
    "Modificador-Historia",      "Modificador-Perspicacia",
    "Modificador-Intimidacion",  "Modificador-Investigacion",
    "Modificador-Medicina",      "Modificador-Naturaleza",
    "Modificador-Percepcion",    "Modificador-Interpretacion",
    "Modificador-Persuasion",    "Modificador-Religion",
        "Modificador-Juegos-De-Manos","Modificador-Sigilo",
    "Modificador-Supervivencia", "Modificador-Trato-Con-Animales",
    "Cobre", "Plata", "Electro", "Oro", "Platino",
    "Piezas.Cobre", "Piezas.Plata", "Piezas.Electro", "Piezas.Oro", "Piezas.Platino",
    "CD-Salvacion-Conjuros", "Modificador-Aptitud-Magica",  # campos fantasma (no existen en template)
} | {f"Total-Espacios-Conjuro.{i}" for i in range(1, 10)} \
    | {f"Arma-{i}-Ataque" for i in range(1, 6)}


def _field_size(name: str) -> int:
    """Devuelve el tamaño de fuente para el campo dado."""
    if name in KEY_STATS: return SIZE_XLARGE
    if name in HIGH:      return SIZE_HIGH
    if name in MEDIUM:    return SIZE_MEDIUM
    return SIZE_LOW


def _align(name: str) -> int:
    """0=izquierda, 1=centrado."""
    return 1 if name in CENTERED else 0


# ---------------------------------------------------------------------------
# Constantes de mapeo
# ---------------------------------------------------------------------------

SPECIES_SIZE: dict[str, str] = {
    "humano":    "Mediana",  "elfo":      "Mediana",
    "enano":     "Mediana",  "semiorco":  "Mediana",
    "tiefling":  "Mediana",  "dragonido": "Mediana",
    "draconido": "Mediana",  "mediano":   "Pequeña",
    "gnomo":     "Pequeña",
}

ABILITY_NAMES: dict[str, str] = {
    "strength":     "Fuerza",      "dexterity":    "Destreza",
    "constitution": "Constitucion", "intelligence": "Inteligencia",
    "wisdom":       "Sabiduria",   "charisma":     "Carisma",
}

SKILL_MAP: dict[str, str] = {
    "acrobacias":         "Acrobacias",
    "atletismo":          "Atletismo",
    "arcanos":            "Conocimiento-Arcano",
    "enganar":            "Engano",
    "historia":           "Historia",
    "perspicacia":        "Perspicacia",
    "intimidar":          "Intimidacion",
    "investigacion":      "Investigacion",
    "medicina":           "Medicina",
    "naturaleza":         "Naturaleza",
    "percepcion":         "Percepcion",
    "interpretacion":     "Interpretacion",
    "persuasion":         "Persuasion",
    "religion":           "Religion",
    "juego_de_manos":     "Juego-De-Manos",
    "sigilo":             "Sigilo",
    "supervivencia":      "Supervivencia",
    "trato_con_animales": "Trato-Con-Animales",
}

SPELL_ABILITY_KEY: dict[str, str] = {
    "Inteligencia": "intelligence", "Sabiduría":  "wisdom",
    "Sabiduria":    "wisdom",       "Carisma":    "charisma",
    "Fuerza":       "strength",     "Destreza":   "dexterity",
    "Constitución": "constitution", "Constitucion": "constitution",
}

# Máximo de conjuros por nivel en el ES PDF
MAX_SPELLS_PER_LEVEL: dict[int, int] = {
    0: 7,
    1: 11, 2: 10, 3: 9, 4: 9,
    5: 8,  6: 8,  7: 7, 8: 7, 9: 7,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_mod(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def fmt_traits(traits: list[dict]) -> str:
    parts = []
    for t in traits:
        name = t.get("name", "").upper()
        desc = t.get("description", "")
        parts.append(f"{name}\n{desc}" if desc else name)
    return "\n\n".join(parts)


def _split_lines(text: str | None) -> list[str]:
    """Divide texto por saltos de línea, descartan líneas vacías."""
    return [l.strip() for l in (text or "").split("\n") if l.strip()]


def _to_int(value: object, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _fmt_1(value: float) -> str:
    return f"{value:.1f}"


def _norm_name(name: str) -> str:
    return (name or "").strip().lower()


def _join_non_empty(parts: list[str], sep: str = " | ") -> str:
    return sep.join([p for p in parts if p])


def _fill_line_fields(m: dict[str, str | bool], prefix: str, lines: list[str], max_lines: int) -> None:
    for i in range(1, max_lines + 1):
        m[f"{prefix}.{i}"] = lines[i - 1] if i - 1 < len(lines) else ""


def _feature_lines(traits: list[dict]) -> list[str]:
    def _clean(text: str) -> str:
        cleaned = str(text or "").strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        # Quita coletillas de uso por descanso que ensucian la ficha.
        cleaned = re.sub(r"\s*[\(\[]?\d+\s*(?:/|por)\s*descanso(?:\s+(?:corto|largo))?[\)\]]?\.?$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip(" -|,;")

    lines: list[str] = []
    for t in traits:
        name = _clean(str((t or {}).get("name") or ""))
        desc = _clean(str((t or {}).get("description") or ""))
        line = _join_non_empty([name, desc], " - ")
        if line:
            lines.append(line)
    return lines


def _item_for_attack(atk_obj: dict, attack_index: int, inventory_items: list[dict]) -> dict:
    atk_name = _norm_name(str(atk_obj.get("name") or ""))
    for item in inventory_items:
        if _norm_name(str(item.get("name") or "")) == atk_name:
            return item
    weapon_items = [it for it in inventory_items if bool(it.get("is_weapon"))]
    if attack_index < len(weapon_items):
        return weapon_items[attack_index]
    return {}


def _format_attack_range(atk_obj: dict, item_obj: dict) -> str:
    range_min = str(atk_obj.get("range_min") or "").strip()
    range_max = str(atk_obj.get("range_max") or "").strip()
    if range_min and range_max:
        return range_min if range_min == range_max else f"{range_min} / {range_max}"
    if range_min:
        return range_min
    if range_max:
        return range_max

    attack_range = str(atk_obj.get("range") or "").strip()
    if attack_range:
        return attack_range

    normal_m = _to_int(((item_obj.get("range_normal") or {}).get("meters")), 0)
    long_m = _to_int(((item_obj.get("range_long") or {}).get("meters")), 0)
    if normal_m and long_m and long_m != normal_m:
        return f"{normal_m} m / {long_m} m"
    if normal_m:
        return f"{normal_m} m"

    props = item_obj.get("properties") or atk_obj.get("properties") or []
    for p in props:
        ptxt = str(p).strip()
        if ptxt.lower().startswith("alcance"):
            return ptxt
    return ""


def _canonical_bool_pips(raw_pips: object, max_count: int, filled_count: int) -> list[bool]:
    if isinstance(raw_pips, list):
        vals = [bool(x) for x in raw_pips[:max_count]]
        if len(vals) < max_count:
            vals += [False] * (max_count - len(vals))
        return vals
    safe_count = max(0, min(max_count, filled_count))
    return [i < safe_count for i in range(max_count)]


# ---------------------------------------------------------------------------
# Construcción del mapa de campos
# ---------------------------------------------------------------------------

def build_field_map(d: dict) -> dict[str, str | bool]:
    bi    = d.get("basic_info", {})
    ab    = d.get("ability_scores", {})
    st    = d.get("saving_throws", {})
    sk    = d.get("skills", {})
    cb    = d.get("combat", {})
    atk   = d.get("attacks", [])
    pr    = d.get("proficiencies", {})
    ft    = d.get("features_and_traits", {})
    sp    = d.get("spellcasting", {})
    inv   = d.get("inventory", {})
    bg    = d.get("background_details", {})
    pb    = d.get("proficiency_bonus", 2)
    langs = d.get("languages", [])
    app   = d.get("appearance", {})
    notes_d     = d.get("notes", {})
    resources_d = d.get("resources", {})

    m: dict[str, str | bool] = {}

    classes     = bi.get("classes", [])
    classes_str = " / ".join(
        f"{str(c.get('name') or '').strip()} {_to_int(c.get('level'), 1)}".strip()
        for c in classes if isinstance(c, dict)
    )

    # ── Info básica ──────────────────────────────────────────────────────────
    m["Nombre-Personaje"] = bi.get("name") or ""
    m["Clase-Y-Nivel"]    = classes_str
    m["Trasfondo"]        = bi.get("background") or bg.get("name") or ""
    m["Especie"]          = bi.get("species") or ""
    m["PX-Personaje"]     = str(bi.get("experience_points") or "")
    m["PX-Proximo-Nivel"] = str(bi.get("next_level_xp") or "")
    m["Alineamiento"]     = bi.get("alignment") or ""
    size_value = str(app.get("size") or "").strip() or SPECIES_SIZE.get(
        (bi.get("species") or "").lower().strip(), "Mediana")
    m["Nombre-Jugador"]   = bi.get("player_name") or ""
    m["Vision"]           = bi.get("vision") or ""
    m["Dato-Personaje-Fecha-Creacion"] = str(bi.get("creation_date") or "")
    birth_place = str(bg.get("birth_place") or "").strip()
    birth_date = str(bg.get("birth_date") or "").strip()
    m["Dato-Personaje-Lugar-Fecha-Nacimiento"] = _join_non_empty([birth_place, birth_date])

    # ── Combate ──────────────────────────────────────────────────────────────
    speed        = cb.get("speed", {})
    walking_m    = _to_float(speed.get("walking_meters"), 0.0)
    swim_m       = _to_float(speed.get("swim_meters"), 0.0)
    fly_m        = _to_float(speed.get("fly_meters"), 0.0)
    climb_m      = _to_float(speed.get("climb_meters"), 0.0)
    perc_total   = sk.get("percepcion", {}).get("total", 0)
    passive_perc = 10 + perc_total

    m["Clase-Armadura"]    = str(cb.get("armor_class") or "")
    m["Iniciativa"]        = fmt_mod(cb.get("initiative") or 0)
    m["Velocidad"]         = f"{_fmt_1(walking_m)} m"
    m["Velocidad-Hora"]    = str(speed.get("hour_text") or "").strip()
    m["Velocidad-Jornada"] = str(speed.get("day_text") or "").strip()
    m["Velocidad-Especial"] = ""
    jump_long = speed.get("jump_long")
    jump_high = speed.get("jump_high")
    m["Salto-Horizontal"]  = f"{jump_long} m" if jump_long not in (None, "") else ""
    m["Salto-Altura"]      = f"{jump_high} m" if jump_high not in (None, "") else ""
    m["Percepcion-Pasiva"] = str(passive_perc)
    m["Check-Inspiracion"] = bool(bi.get("inspiration", False))

    hp = cb.get("hit_points", {})
    hp_current = hp.get("current")
    hp_max     = hp.get("maximum")
    m["Puntos-Golpe-Actuales"]   = str(hp_current if hp_current is not None else (hp_max or ""))
    m["Puntos-Golpe-Maximo"]     = str(hp_max or "")
    m["Puntos-Golpe-Temporales"] = str(hp.get("temporary") or "")
    hit_dice = cb.get("hit_dice", {})
    hd_total = str(hit_dice.get("total") or "").strip()
    if not hd_total:
        hd_count = _to_int(hit_dice.get("count"), 0)
        hd_type = str(hit_dice.get("type") or hit_dice.get("die_type") or "").strip()
        hd_total = f"{hd_count}{hd_type}" if hd_count and hd_type else ""
    m["Dados-Golpe-Maximos"]     = hd_total
    m["Bonificador-Competencia"] = fmt_mod(pb)

    str_score = _to_int((ab.get("strength") or {}).get("score"), 10)
    carry_normal = str_score * 7.5
    carry_over = str_score * 15.0
    carry_max = str_score * 22.5
    carry_push = str_score * 30.0
    m["Capacidad-Carga-Cargado"] = _fmt_1(carry_normal)
    m["Capacidad-Carga-Muy-Cargado"] = _fmt_1(carry_over)
    m["Capacidad-Carga-Maxima"] = _fmt_1(carry_max)
    m["Capacidad-Carga-Empujar"] = _fmt_1(carry_push)

    # Death saves — leer del JSON
    ds        = cb.get("death_saves", {})
    successes = int(ds.get("successes") or 0)
    failures  = int(ds.get("failures")  or 0)
    for n in range(1, 4):
        m[f"Check-Salvacion-Muerte.Exito.{n}"] = (n <= successes)
        m[f"Check-Salvacion-Muerte.Fallo.{n}"] = (n <= failures)

    # Hit dice checkboxes — marcados = gastados
    hd_used = _to_int((cb.get("hit_dice") or {}).get("used"), -1)
    if hd_used < 0:
        hd_remaining = _to_int((cb.get("hit_dice") or {}).get("remaining"), 0)
        hd_count = _to_int((cb.get("hit_dice") or {}).get("count"), 0)
        hd_used = max(0, hd_count - hd_remaining) if hd_count else 0
    for i in range(1, 21):
        m[f"Check-Dado-Golpe.{i}"] = (i <= hd_used)

    # ── Puntuaciones de habilidad ────────────────────────────────────────────
    for eng, esp in ABILITY_NAMES.items():
        ability = ab.get(eng, {})
        m[f"Puntuacion-{esp}"]  = str(ability.get("score") or "")
        m[f"Modificador-{esp}"] = fmt_mod(ability.get("modifier") or 0)

    # ── Tiradas de salvación ─────────────────────────────────────────────────
    for eng, esp in ABILITY_NAMES.items():
        ts = st.get(eng, {})
        m[f"Modificador-Salvacion-{esp}"]       = fmt_mod(ts.get("total") or 0)
        m[f"Check-Competencia-Salvacion-{esp}"] = bool(ts.get("proficient"))

    # ── Habilidades ──────────────────────────────────────────────────────────
    for key, suffix in SKILL_MAP.items():
        skill = sk.get(key, {})
        if skill:
            mod_suffix = "Juegos-De-Manos" if key == "juego_de_manos" else suffix
            m[f"Modificador-{mod_suffix}"]   = fmt_mod(skill.get("total") or 0)
            m[f"Check-Competencia-{suffix}"] = bool(skill.get("proficient"))
            m[f"Check-Pericia-{suffix}"]     = bool(skill.get("expertise"))

    # ── Ataques (máximo 5) ───────────────────────────────────────────────────
    inv_items = inv.get("items", [])
    for i, a in enumerate(atk[:5], 1):
        item = _item_for_attack(a, i - 1, inv_items)
        bonus = _to_int(a.get("attack_bonus"), 0)
        damage = str(a.get("damage") or item.get("damage") or "").strip()
        dmg_type = str(a.get("damage_type") or item.get("damage_type") or "").strip()
        weight = _to_float(a.get("weight", item.get("weight_kg")), 0.0)
        props_raw = a.get("properties") or item.get("properties") or []
        if isinstance(props_raw, str):
            props_raw = [x.strip() for x in props_raw.split(",") if x.strip()]
        notes_parts = []
        for p in props_raw:
            prop_txt = str(p).strip()
            if not prop_txt:
                continue
            # Evita duplicar datos que ya tienen campo dedicado.
            if re.search(r"\balcance\b", prop_txt, flags=re.IGNORECASE):
                continue
            notes_parts.append(prop_txt)

        extra_notes = str(a.get("notes") or item.get("notes") or "").strip()
        if extra_notes:
            notes_parts.append(extra_notes)

        m[f"Arma-{i}-Nombre"] = str(a.get("name") or item.get("name") or "")
        m[f"Arma-{i}-Ataque"] = fmt_mod(bonus)
        m[f"Arma-{i}-Dano"] = damage
        m[f"Arma-{i}-Tipo"] = dmg_type
        m[f"Arma-{i}-Alcance"] = _format_attack_range(a, item)
        m[f"Arma-{i}-Peso"] = _fmt_1(weight) if weight else ""
        m[f"Arma-{i}-Notas"] = ", ".join(notes_parts)

    # Protecciones
    prot_slots = [1, 2, 3, 4]
    protections = cb.get("protections", [])
    for idx, slot in enumerate(prot_slots):
        if idx < len(protections):
            p = protections[idx] or {}
            p_name = str(p.get("name") or "").strip()
            p_type = str(p.get("type") or "").strip()
            p_ac = _to_int(p.get("ac_bonus"), 0)
            p_equipped = bool(p.get("equipped"))
            m[f"Armadura-Escudo-Protecciones.{slot}"] = _join_non_empty([
                p_name,
                p_type,
                f"+{p_ac} CA" if p_ac else "",
            ])
            m[f"Check-Armadura-Escudo-Protecciones.{slot}"] = p_equipped
        else:
            m[f"Armadura-Escudo-Protecciones.{slot}"] = ""
            m[f"Check-Armadura-Escudo-Protecciones.{slot}"] = False

    adv_lines: list[str] = []
    for adv in cb.get("advantages_resistances", [])[:8]:
        if isinstance(adv, dict):
            adv_lines.append(_join_non_empty([str(adv.get("category") or ""), str(adv.get("description") or "")], " | "))
        else:
            adv_lines.append(str(adv or ""))
    for i in range(1, 9):
        m[f"Ventaja-Resistencia-Inmunidad.{i}"] = adv_lines[i - 1] if i - 1 < len(adv_lines) else ""

    # Municion
    ammunition = cb.get("ammunition", [])
    for ammo_idx in range(1, 4):
        if ammo_idx - 1 < len(ammunition):
            ammo = ammunition[ammo_idx - 1] or {}
            name = str(ammo.get("name") or "").strip()
            max_v = _to_int(ammo.get("max"), 0)
            m[f"Municion-{ammo_idx - 1}-Nombre"] = name
            pips = _canonical_bool_pips(None, 20, max_v)
            for pip_idx in range(1, 21):
                m[f"Check-Contador-Municion.{ammo_idx}.{pip_idx}"] = bool(pips[pip_idx - 1])
        else:
            m[f"Municion-{ammo_idx - 1}-Nombre"] = ""
            for pip_idx in range(1, 21):
                m[f"Check-Contador-Municion.{ammo_idx}.{pip_idx}"] = False

    # Habilidades/beneficios de combate (resources)
    resources_list = [v for v in resources_d.values() if isinstance(v, dict)]
    for ridx in range(1, 10):
        if ridx - 1 < len(resources_list):
            res = resources_list[ridx - 1]
            name = str(res.get("name") or "").strip()
            note = str(res.get("note") or "").strip()
            recharge = str(res.get("recharge") or "").strip()
            m[f"Habilidades-Combate.{ridx}"] = _join_non_empty([name, note], " - ")
            m[f"Check-Refresco-Habilidades-Combate.{ridx}"] = bool(recharge)

            max_pips = min(5, max(_to_int(res.get("max"), 0), 0))
            current_pips = _to_int(res.get("current"), 0)
            pips = _canonical_bool_pips(res.get("pip_states"), 5, current_pips if max_pips else 0)
            for j in range(1, 6):
                m[f"Check-Contador-Habilidades-Combate.{ridx}.{j}"] = bool(pips[j - 1])
        else:
            m[f"Habilidades-Combate.{ridx}"] = ""
            m[f"Check-Refresco-Habilidades-Combate.{ridx}"] = False
            for j in range(1, 6):
                m[f"Check-Contador-Habilidades-Combate.{ridx}.{j}"] = False

    # ── Competencias ─────────────────────────────────────────────────────────
    armor_list  = pr.get("armor") or []
    armor_flags = pr.get("armor_flags") or {}
    if isinstance(armor_list, str):
        armor_list = [x.strip() for x in armor_list.split(",")]
    m["Check-Competencia-Armadura-Ligera"] = armor_flags.get("light", False) or any("ligera"  in str(a).lower() for a in armor_list)
    m["Check-Competencia-Armadura-Media"]  = armor_flags.get("medium", False) or any("media"   in str(a).lower() for a in armor_list)
    m["Check-Competencia-Armadura-Pesada"] = armor_flags.get("heavy",  False) or any("pesada"  in str(a).lower() for a in armor_list)
    m["Check-Competencia-Escudo"]          = armor_flags.get("shield", False) or any("escudo"  in str(a).lower() for a in armor_list)
    m["Check-Competencia-Armas-Simples"]   = bool(pr.get("simple_weapons", False))
    m["Check-Competencia-Armas-Marciales"] = bool(pr.get("martial_weapons", False))

    comp_lines: list[str] = []
    for item in (pr.get("other_competencies") or []):
        if isinstance(item, dict):
            txt = _join_non_empty([
                str(item.get("title") or item.get("name") or "").strip(),
                str(item.get("description") or item.get("note") or "").strip(),
            ], " - ")
        else:
            txt = str(item or "").strip()
        if txt:
            comp_lines.append(txt)

    for seq in (pr.get("weapons") or [], pr.get("tools") or [], pr.get("raw") or []):
        for raw in seq:
            txt = str(raw or "").strip()
            if txt:
                comp_lines.append(txt)

    seen_comp: set[str] = set()
    ordered_comp: list[str] = []
    for c in comp_lines:
        key = c.lower().strip()
        # Evita repetir en texto los labels genéricos ya cubiertos por checkboxes.
        if key in {"armadura ligera", "armadura media", "armadura pesada", "escudo"}:
            continue
        if bool(pr.get("simple_weapons", False)) and key in {"armas simples", "simple weapons"}:
            continue
        if bool(pr.get("martial_weapons", False)) and key in {"armas marciales", "martial weapons"}:
            continue
        if key in seen_comp:
            continue
        seen_comp.add(key)
        ordered_comp.append(c)
    for i in range(1, 15):
        m[f"Competencia.{i}"] = ordered_comp[i - 1] if i - 1 < len(ordered_comp) else ""

    # ── Rasgos y características ─────────────────────────────────────────────
    species_traits = ft.get("species", [])
    feat_traits    = ft.get("feats", [])
    class_features = ft.get("class_features", [])
    feat_lines = _feature_lines(feat_traits)
    trait_lines = _feature_lines(species_traits) + _feature_lines(class_features)
    _fill_line_fields(m, "Dotes", feat_lines, 16)
    _fill_line_fields(m, "Rasgo", trait_lines, 20)

    # ── Monedas (jerárquico Piezas.Oro etc.) ────────────────────────────────
    currency = inv.get("currency", {})
    m["Piezas.Cobre"]   = str(currency.get("CP") or 0)
    m["Piezas.Plata"]   = str(currency.get("SP") or 0)
    m["Piezas.Electro"] = str(currency.get("EP") or 0)
    m["Piezas.Oro"]     = str(currency.get("GP") or 0)
    m["Piezas.Platino"] = str(currency.get("PP") or 0)
    other_currency_text = str(currency.get("other_notes") or inv.get("other_possessions") or "")
    other_currency_lines = _split_lines(other_currency_text)
    m["Piezas.Otros.1"] = other_currency_lines[0] if len(other_currency_lines) > 0 else ""
    m["Piezas.Otros.2"] = other_currency_lines[1] if len(other_currency_lines) > 1 else ""

    # ── Inventario — por filas ───────────────────────────────────────────────
    qty_total = 0
    qty_by_loc = {"Equipado": 0, "Transportado": 0, "Otros": 0}
    weight_by_loc = {"Equipado": 0.0, "Transportado": 0.0, "Otros": 0.0}
    for i, item in enumerate(inv_items[:47], 1):
        name_val = str(item.get("name") or "")
        qty_eq = max(0, _to_int(item.get("qty_equipped"), 0))
        qty_bp = max(0, _to_int(item.get("qty_backpack"), 0))
        qty_bg = max(0, _to_int(item.get("qty_bag"), 0))
        qty_i = qty_eq + qty_bp + qty_bg

        # Compatibilidad con JSON antiguo: quantity + location.
        if qty_i == 0 and ("quantity" in item or "location" in item):
            legacy_qty = max(0, _to_int(item.get("quantity"), 0))
            legacy_loc = str(item.get("location") or "").strip()
            if legacy_loc == "Equipado":
                qty_eq = legacy_qty
            elif legacy_loc == "Transportado":
                qty_bp = legacy_qty
            else:
                qty_bg = legacy_qty
            qty_i = qty_eq + qty_bp + qty_bg

        w_i = _to_float(item.get("weight_kg"), 0.0)
        total_weight_eq = w_i * qty_eq
        total_weight_bp = w_i * qty_bp
        total_weight_bg = w_i * qty_bg

        qty_total += qty_i
        qty_by_loc["Equipado"] += qty_eq
        qty_by_loc["Transportado"] += qty_bp
        qty_by_loc["Otros"] += qty_bg
        weight_by_loc["Equipado"] += total_weight_eq
        weight_by_loc["Transportado"] += total_weight_bp
        weight_by_loc["Otros"] += total_weight_bg

        name_with_weight = f"{name_val} ({_fmt_1(w_i)} kg)" if w_i else name_val
        m[f"Objeto-Nombre.{i}"]   = name_with_weight
        m[f"Objeto-Cantidad.{i}"] = str(qty_i)
        m[f"Objeto-Puesto.{i}"]   = str(qty_eq) if qty_eq else ""
        m[f"Objeto-Mochila.{i}"]  = str(qty_bp) if qty_bp else ""
        m[f"Objeto-Bolsa.{i}"]    = str(qty_bg) if qty_bg else ""

    m["Total-Cantidad"] = str(qty_total)
    m["Total-Puesto"] = str(qty_by_loc["Equipado"])
    m["Total-Mochila"] = str(qty_by_loc["Transportado"])
    m["Total-Bolsa"] = str(qty_by_loc["Otros"])
    m["Total-Pesos-Puesto"] = _fmt_1(weight_by_loc["Equipado"])
    m["Total-Pesos-Equipados"] = _fmt_1(weight_by_loc["Equipado"])
    m["Total-Pesos-Mochila"] = _fmt_1(weight_by_loc["Transportado"])
    m["Total-Pesos-Bolsa"] = _fmt_1(weight_by_loc["Otros"])

    # ── Idiomas — campos individuales por fila (1..12) ──────────────────────
    for i in range(1, 13):
        m[f"Idioma.{i}"] = langs[i - 1] if i - 1 < len(langs) else ""

    # ── Tamaño — campo plano + bajo Dato-Personaje ───────────────────────────
    m["Dato-Personaje.Tamano"] = size_value

    # ── Apariencia — campos individuales bajo Dato-Personaje ─────────────────
    m["Dato-Personaje.Edad"]   = str(app.get("age")    or "")
    m["Dato-Personaje.Altura"] = str(app.get("height") or "")
    m["Dato-Personaje.Peso"]   = str(app.get("weight") or "")
    m["Dato-Personaje.Ojos"]   = str(app.get("eyes")   or "")
    m["Dato-Personaje.Piel"]   = str(app.get("skin")   or "")
    m["Dato-Personaje.Pelo"]   = str(app.get("hair")   or "")
    m["Dato-Personaje.Genero"] = str(app.get("gender") or "")
    m["Dato-Personaje.Tamano"] = size_value

    # ── Personalidad (vacíos si no están en el JSON) ─────────────────────────
    pers_keys = [
        ("Rasgo-Personalidad", "personality_traits"),
        ("Ideal",              "ideals"),
        ("Vinculo",            "bonds"),
        ("Defecto",            "flaws"),
    ]
    for field_prefix, bg_key in pers_keys:
        items_list = bg.get(bg_key) or []
        if isinstance(items_list, str):
            items_list = [items_list]
        for i in range(1, 4):
            raw = items_list[i - 1] if i - 1 < len(items_list) else ""
            if isinstance(raw, dict):
                raw = raw.get("description", "")
            m[f"Dato-Personaje.{field_prefix}-{i}"] = raw or ""

    allies_lines  = _split_lines(notes_d.get("allies"))
    enemies_lines = _split_lines(notes_d.get("enemies"))
    appearance_text = str(app.get("summary") or notes_d.get("physical_description") or "")
    phys_lines = _split_lines(appearance_text)
    for i in range(1, 4):
        m[f"Dato-Personaje.Amigo-Aliado-{i}"] = allies_lines[i-1]  if i-1 < len(allies_lines)  else ""
        m[f"Dato-Personaje.Enemigo-{i}"]      = enemies_lines[i-1] if i-1 < len(enemies_lines) else ""
        m[f"Dato-Personaje.Apariencia-{i}"]   = phys_lines[i-1]    if i-1 < len(phys_lines)    else ""

    m["Dato-Personaje.Deidad-Dominio"]     = bg.get("deity") or ""
    m["Dato-Personaje.Descripcion-Deidad"] = bg.get("deity_description") or ""

    story_text = str(notes_d.get("backstory") or "").strip()
    story_lines = _split_lines(story_text)
    if not story_lines:
        story_lines = _split_lines(str(bg.get("description") or ""))
        story_lines += _split_lines(notes_d.get("other_notes"))
    for i in range(1, 8):
        m[f"Dato-Personaje.Trasfondo-Otros-{i}"] = story_lines[i-1] if i-1 < len(story_lines) else ""

    # Notas de texto libres
    note_text = str(notes_d.get("general") or notes_d.get("additional_notes") or "")
    note_lines = _split_lines(note_text)
    _fill_line_fields(m, "Nota", note_lines, 16)

    # Otros
    m["Titulo-Otro"] = "Otras posesiones"
    m["Otro-1"] = str(inv.get("other_possessions") or notes_d.get("other_possessions") or "")

    # Monturas
    mount_lines: list[str] = []
    for mt in inv.get("mounts", [])[:19]:
        mount_lines.append(_join_non_empty([
            str(mt.get("name") or "").strip(),
            str(mt.get("notes") or "").strip(),
        ], " - "))
    _fill_line_fields(m, "Montura", mount_lines, 19)

    # Gemas
    gem_lines: list[str] = []
    for gm in inv.get("gems", [])[:7]:
        gem_lines.append(_join_non_empty([
            str(gm.get("name") or "").strip(),
            f"x{_to_int(gm.get('quantity'), 0)}" if _to_int(gm.get("quantity"), 0) else "",
            f"{_to_int(gm.get('value_gp'), 0)} po" if _to_int(gm.get("value_gp"), 0) else "",
            str(gm.get("note") or "").strip(),
        ], " - "))
    _fill_line_fields(m, "Gema", gem_lines, 7)

    # Prestados / depositados / recibidos
    loaned = inv.get("loaned", [])
    for i in range(1, 7):
        if i - 1 < len(loaned):
            ln = loaned[i - 1] or {}
            m[f"Prestad-Depositado-Recibido-Lugar.{i}"] = _join_non_empty([
                str(ln.get("to") or ln.get("where") or "").strip(),
                str(ln.get("name") or "").strip(),
            ])
            qty_raw = str(ln.get("quantity") if ln.get("quantity") not in (None, "") else (ln.get("amount") or "")).strip()
            m[f"Prestad-Depositado-Recibido-Cantidad.{i}"] = qty_raw
            m[f"Prestad-Depositado-Recibido-Momento.{i}"] = _join_non_empty([
                str(ln.get("due") or ln.get("when") or "").strip(),
                str(ln.get("notes") or "").strip(),
            ])
        else:
            m[f"Prestad-Depositado-Recibido-Lugar.{i}"] = ""
            m[f"Prestad-Depositado-Recibido-Cantidad.{i}"] = ""
            m[f"Prestad-Depositado-Recibido-Momento.{i}"] = ""

    # ── Conjuros ─────────────────────────────────────────────────────────────
    spell_ab_raw = sp.get("spellcasting_ability") or ""
    spell_ab_key = SPELL_ABILITY_KEY.get(spell_ab_raw, "intelligence")
    spell_ab_mod = (ab.get(spell_ab_key) or {}).get("modifier", 0)

    spell_atk = sp.get("spell_attack_bonus")
    # "Aptitud-Magica" es el campo bajo la etiqueta "BONO ATAQUE CONJ." en el template
    m["Aptitud-Magica"]              = fmt_mod(spell_atk) if spell_atk is not None else ""
    m["CD-Salvacion-Conjuros"]       = str(sp.get("spell_save_dc") or "")

    m["Clase-Lanzador-Conjuros"] = (
        classes[0].get("name", "") if spell_ab_raw and classes else ""
    )
    m["Caracteristica-Clase-Lanzador-Conjuro"] = spell_ab_raw
    magic_res = next(
        (v for v in resources_d.values()
         if any(kw in (v.get("name") or "").lower()
                for kw in ("ki", "concentraci", "hechiceria", "sorcery"))),
        {}
    )
    magic_max     = _to_int(magic_res.get("max"), 0)
    magic_current = _to_int(magic_res.get("current"), 0)
    if magic_max <= 0:
        magic_max = _to_int(sp.get("sorcery_points_max"), 0)
        magic_used = _to_int(sp.get("sorcery_points_used"), 0)
        magic_current = max(0, magic_max - magic_used)
    m["Puntos-Hechiceria-Max"]      = str(magic_max)               if magic_max > 0 else ""
    m["Puntos-Hechiceria-Gastados"] = str(magic_max - magic_current) if magic_max > 0 else ""

    # Espacios de conjuro (punto como separador: Total-Espacios-Conjuro.N)
    slots = sp.get("spell_slots") or {}
    for lvl in range(1, 10):
        slot_val = _to_int((slots.get(f"level_{lvl}") or {}).get("total"), 0)
        m[f"Total-Espacios-Conjuro.{lvl}"] = str(slot_val) if slot_val else ""

    slot_checks = {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
    for lvl in range(1, 10):
        max_checks = slot_checks[lvl]
        slot_data = slots.get(f"level_{lvl}") or {}
        used_count = _to_int(slot_data.get("used"), 0)
        pips = _canonical_bool_pips(slot_data.get("pip_states"), max_checks, used_count)
        for i in range(1, max_checks + 1):
            m[f"Check-Espacio-Conjuro-Gastado-{lvl}.{i}"] = bool(pips[i - 1])

    # Conjuros por nivel
    spells_data = sp.get("spells") or {}
    total_spells  = 0
    prepared_count = 0

    cantrips = spells_data.get("cantrips", [])
    total_spells += len(cantrips)
    for i in range(1, MAX_SPELLS_PER_LEVEL[0] + 1):
        s = cantrips[i - 1] if i - 1 < len(cantrips) else {}
        m[f"Nombre-Conjuro-Nivel-0.{i}"] = str(s.get("name") or "") if isinstance(s, dict) else ""

    for lvl in range(1, 10):
        spell_list = spells_data.get(f"level_{lvl}", [])
        total_spells  += len(spell_list)
        prepared_count += sum(1 for s in spell_list if s.get("prepared"))
        max_s = MAX_SPELLS_PER_LEVEL[lvl]
        for i in range(1, max_s + 1):
            s = spell_list[i - 1] if i - 1 < len(spell_list) else {}
            if isinstance(s, dict):
                m[f"Nombre-Conjuro-Nivel-{lvl}.{i}"]          = str(s.get("name") or "")
                m[f"Check-Preparado-Conjuro-Nivel-{lvl}.{i}"] = bool(s.get("prepared"))
            else:
                m[f"Nombre-Conjuro-Nivel-{lvl}.{i}"]          = ""
                m[f"Check-Preparado-Conjuro-Nivel-{lvl}.{i}"] = False

    known_count = _to_int(sp.get("spells_known"), -1)
    prepared_total = _to_int(sp.get("spells_prepared"), -1)
    if known_count < 0:
        known_count = total_spells
    if prepared_total < 0:
        prepared_total = prepared_count

    m["Conjuros-Concidos"]   = str(known_count) if known_count > 0 else ""  # sic: typo in PDF
    m["Conjuros-Preparados"] = str(prepared_total) if prepared_total > 0 else ""

    return m


# ---------------------------------------------------------------------------
# FontInfo — métricas tipográficas del TTF (para layout de AP streams)
# ---------------------------------------------------------------------------

@dataclass
class FontInfo:
    path:         str
    upm:          int
    ascent:       int
    descent:      int
    cap_height:   int
    italic_angle: float
    bbox:         list
    stemv:        int
    widths:       list

    @classmethod
    def load(cls, path: Path) -> "FontInfo":
        font = _TTFont(str(path))
        upm  = font["head"].unitsPerEm
        try:
            os2     = font["OS/2"]
            ascent  = os2.sTypoAscender
            descent = os2.sTypoDescender
            cap_h   = getattr(os2, "sCapHeight", 0) or round(ascent * 0.72)
            weight  = getattr(os2, "usWeightClass", 400)
        except KeyError:
            hhea    = font["hhea"]
            ascent  = hhea.ascent
            descent = hhea.descent
            cap_h   = round(ascent * 0.72)
            weight  = 400

        italic = float(font["post"].italicAngle)
        head   = font["head"]
        bbox   = [
            round(head.xMin * 1000 / upm),
            round(head.yMin * 1000 / upm),
            round(head.xMax * 1000 / upm),
            round(head.yMax * 1000 / upm),
        ]
        stemv  = max(50, round(10 + 220 * max(0, weight - 400) / 600))
        cmap   = font.getBestCmap() or {}
        hmtx   = font["hmtx"].metrics
        widths = []
        for cp in range(32, 256):
            gname = cmap.get(cp)
            aw    = hmtx.get(gname, (500, 0))[0] if gname else 500
            widths.append(round(aw * 1000 / upm))

        return cls(
            path=str(path), upm=upm, ascent=ascent, descent=descent,
            cap_height=cap_h, italic_angle=italic, bbox=bbox,
            stemv=stemv, widths=widths,
        )

    def ascent_pts(self, fsize: float) -> float:
        return self.ascent * fsize / self.upm

    def descent_pts(self, fsize: float) -> float:
        return self.descent * fsize / self.upm   # negativo

    def string_width(self, text: str, fsize: float) -> float:
        total = 0.0
        for ch in text:
            cp  = ord(ch)
            idx = cp - 32
            w1k = self.widths[idx] if 0 <= idx < 224 else 500
            total += w1k * fsize / 1000.0
        return total

# ---------------------------------------------------------------------------
# Helpers compartidos del generador
# ---------------------------------------------------------------------------

def _pdf_escape(text: str) -> bytes:
    """Codifica texto a cp1252 y escapa los caracteres especiales de PDF strings."""
    encoded = text.encode("cp1252", errors="replace")
    result  = bytearray()
    for b in encoded:
        if   b == 0x5C: result += b"\\\\"
        elif b == 0x28: result += b"\\("
        elif b == 0x29: result += b"\\)"
        else:           result.append(b)
    return bytes(result)

def _canonical_name(name: str) -> str:
    """Normaliza nombres PDF removiendo sufijos de repeticion como [123], 10b o 11.1."""
    s = (name or "").strip()
    s = re.sub(r"\s*\[\d+\]", "", s)
    if s.startswith("Nombre-Conjuro-Nivel-"):
        s = re.sub(r"(\.\d+)\.\d+$", r"\1", s)
    s = re.sub(r"(\.\d+)?[a-zA-Z]$", "", s)
    return s

def _download_remote_image(url: str, timeout: float = 10.0) -> bytes | None:
    if not url:
        return None
    req = urllib.request.Request(url, headers={"User-Agent": "DnD-Conversor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except Exception:
        return None
    return data or None


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
    if not json_path.exists():
        raise FileNotFoundError(f"JSON no encontrado: {json_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"Plantilla PDF no encontrada: {template_path}")
    if not FONT_PATH.exists():
        raise FileNotFoundError(
            f"Fuente no encontrada: {FONT_PATH}. "
            "Coloca CaslonAntique-Regular.ttf en la carpeta fonts/ o configura DND_FONT_TTF."
        )

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("proficiency_bonus"):
        data["proficiency_bonus"] = 2

    field_map = build_field_map(data)
    canonical_field_map = {_canonical_name(k): v for k, v in field_map.items()}
    portrait_url = str(((data.get("basic_info") or {}).get("portrait_url") or "")).strip()
    portrait_bytes = _download_remote_image(portrait_url) if portrait_url else None
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
                if field_name == "Imagen-Personaje_af_image" and portrait_url:
                    inserted = False
                    if portrait_bytes and widget.rect.width >= 1 and widget.rect.height >= 1:
                        try:
                            new_page.insert_image(widget.rect, stream=portrait_bytes, keep_proportion=True, overlay=True)
                            inserted = True
                        except Exception:
                            inserted = False
                    if not inserted:
                        out.xref_set_key(
                            widget.xref,
                            "A",
                            f"<</S/URI/URI{_pdf_str_value(portrait_url)}>>",
                        )
                    counters["filled"] += 1
                    continue
                counters["skipped"] += 1
                continue
            if widget.rect.width < 1 or widget.rect.height < 1:
                counters["skipped"] += 1
                continue
            if field_name in field_map:
                value = field_map[field_name]
            else:
                value = canonical_field_map.get(_canonical_name(field_name))
            if value is None:
                counters["no_map"] += 1
                continue

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
    try:
        generate(args.json, args.template, args.output,
                 verbose=args.verbose, verify=args.verify)
    except Exception as exc:
        sys.exit(f"Error: {exc}")


if __name__ == "__main__":
    main()
