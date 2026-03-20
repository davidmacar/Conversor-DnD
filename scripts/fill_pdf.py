#!/usr/bin/env python3
"""
fill_pdf.py — Rellena Hoja-Personaje-Editable-Completa-ES.pdf con datos de personaje JSON.

Fuente: Caslon Antique, embebida dinámicamente en el template ES durante el relleno.
El script carga caslon-antique.regular.ttf para métricas y la inyecta en /DR del AcroForm.

Jerarquía tipográfica:
  - Estadísticas clave (puntuaciones, CA, HP...): tamaño 10
  - Importancia alta (nombre, clase, armas...):   tamaño 8
  - Importancia media (habilidades, tiradas...):  tamaño 7
  - Resto:                                        tamaño 6

Checkboxes marcados: X negra en negrita (trazo 2 pt).

Uso:
    venv/Scripts/python scripts/fill_pdf.py [data/personaje.json] [output/salida.pdf]

Defaults:
    JSON   → data/personaje.json
    Salida → output/{Nombre-Personaje}_filled.pdf

Requiere:
    pip install pikepdf fonttools
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

try:
    import pikepdf
except ImportError:
    sys.exit("Error: instala pikepdf con:  pip install pikepdf")

try:
    from fontTools.ttLib import TTFont as _TTFont
except ImportError:
    sys.exit("Error: instala fonttools con:  pip install fonttools")


# ---------------------------------------------------------------------------
# Paths del proyecto
# ---------------------------------------------------------------------------

PROJECT_ROOT  = Path(__file__).parent.parent
FONTS_DIR     = PROJECT_ROOT / "fonts"
FONT_REGULAR  = FONTS_DIR / "CaslonAntique-Regular.ttf"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "Hoja-Personaje-Editable-Completa-ES.pdf"


def _ensure_fonts() -> None:
    """Descarga Caslon Antique Regular si no está en templates/fonts/."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    if not FONT_REGULAR.exists():
        print(f"Descargando fuente: {FONT_REGULAR.name} ...")
        try:
            urllib.request.urlretrieve(
                "https://st.1001fonts.net/download/font/caslon-antique.regular.ttf",
                FONT_REGULAR,
            )
            print(f"  Guardado en: {FONT_REGULAR}")
        except Exception as e:
            sys.exit(f"Error descargando {FONT_REGULAR.name}: {e}")


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
    "Arma-1-Nombre", "Arma-1-Bonificador-Ataque", "Arma-1-Dano-Tipo",
    "Arma-2-Nombre", "Arma-2-Bonificador-Ataque", "Arma-2-Dano-Tipo",
    "Arma-3-Nombre", "Arma-3-Bonificador-Ataque", "Arma-3-Dano-Tipo",
    "Oro", "Plata", "Cobre", "Platino", "Electro",
    "Piezas.Oro", "Piezas.Plata", "Piezas.Cobre", "Piezas.Platino", "Piezas.Electro",
    "CD-Salvacion-Conjuros", "Aptitud-Magica",
}

# Importancia media — tamaño 7
MEDIUM: set[str] = {
    "PX-Personaje", "Alineamiento", "Tamano",
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
    "Modificador-Juego-De-Manos","Modificador-Sigilo",
    "Modificador-Supervivencia", "Modificador-Trato-Con-Animales",
    "Modificador-Aptitud-Magica",
    "Arma-1-Notas", "Arma-2-Notas", "Arma-3-Notas",
    "Arma-4-Nombre", "Arma-4-Bonificador-Ataque", "Arma-4-Dano-Tipo", "Arma-4-Notas",
    "Arma-5-Nombre", "Arma-5-Bonificador-Ataque", "Arma-5-Dano-Tipo", "Arma-5-Notas",
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
    "Modificador-Juego-De-Manos","Modificador-Sigilo",
    "Modificador-Supervivencia", "Modificador-Trato-Con-Animales",
    "Cobre", "Plata", "Electro", "Oro", "Platino",
    "Piezas.Cobre", "Piezas.Plata", "Piezas.Electro", "Piezas.Oro", "Piezas.Platino",
    "CD-Salvacion-Conjuros", "Modificador-Aptitud-Magica",  # campos fantasma (no existen en template)
} | {f"Total-Espacios-Conjuro.{i}" for i in range(1, 10)} \
  | {f"Arma-{i}-Bonificador-Ataque" for i in range(1, 6)}


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
    lines: list[str] = []
    for t in traits:
        name = str((t or {}).get("name") or "").strip()
        desc = str((t or {}).get("description") or "").strip()
        details = (t or {}).get("details") or {}
        details_text = ""
        if isinstance(details, dict):
            details_vals = [str(v).strip() for v in details.values() if str(v).strip()]
            details_text = ", ".join(details_vals)
        line = _join_non_empty([name, desc, details_text], " - ")
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
    m["Tamano"]           = str(app.get("size") or "").strip() or SPECIES_SIZE.get(
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
    speed_h = walking_m * 600.0 / 1000.0
    speed_d = speed_h * 8.0

    m["Clase-Armadura"]    = str(cb.get("armor_class") or "")
    m["Iniciativa"]        = fmt_mod(cb.get("initiative") or 0)
    m["Velocidad"]         = f"{_fmt_1(walking_m)} m"
    m["Velocidad-Hora"]    = str(speed.get("hour_text") or "").strip() or f"{_fmt_1(speed_h)} km/h"
    m["Velocidad-Jornada"] = str(speed.get("day_text") or "").strip() or f"{_fmt_1(speed_d)} km/dia"
    special_parts = []
    special_text = str(speed.get("special_senses") or "").strip()
    if special_text:
        special_parts.append(special_text)
    if swim_m:
        special_parts.append(f"Nado {_fmt_1(swim_m)} m")
    if fly_m:
        special_parts.append(f"Vuelo {_fmt_1(fly_m)} m")
    if climb_m:
        special_parts.append(f"Trepar {_fmt_1(climb_m)} m")
    m["Velocidad-Especial"] = " | ".join(special_parts)
    jump_long = speed.get("jump_long")
    jump_high = speed.get("jump_high")
    m["Salto-Horizontal"]  = f"{jump_long} m" if jump_long not in (None, "") else ""
    m["Salto-Altura"]      = f"{jump_high} m" if jump_high not in (None, "") else ""
    m["Percepcion-Pasiva"] = str(passive_perc)
    m["Check-Escudo"]      = bool(cb.get("shield_equipped", False))
    m["Check-Inspiracion-Heroica"] = bool(bi.get("inspiration", False))
    m["Inspiracion-Heroica"] = ""  # el checkbox gestiona el estado

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
            m[f"Modificador-{suffix}"]       = fmt_mod(skill.get("total") or 0)
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
        notes_parts = [str(p).strip() for p in (a.get("properties") or item.get("properties") or []) if str(p).strip()]
        attack_roll = str(a.get("attack_roll") or "").strip()
        if bonus:
            notes_parts.append(f"Ataque {fmt_mod(bonus)}")
        if attack_roll:
            notes_parts.append(attack_roll)

        m[f"Arma-{i}-Nombre"] = str(a.get("name") or item.get("name") or "")
        m[f"Arma-{i}-Dano"] = damage
        m[f"Arma-{i}-Tipo"] = dmg_type
        m[f"Arma-{i}-Alcance"] = _format_attack_range(a, item)
        m[f"Arma-{i}-Peso"] = _fmt_1(weight) if weight else ""
        m[f"Arma-{i}-Notas"] = ", ".join(notes_parts)

    # Protecciones
    prot_slots = [1, 2, 4, 5]
    protections = cb.get("protections", [])
    for idx, slot in enumerate(prot_slots):
        if idx < len(protections):
            p = protections[idx] or {}
            p_name = str(p.get("name") or "").strip()
            p_type = str(p.get("type") or "").strip()
            p_ac = _to_int(p.get("ac_bonus"), 0)
            p_eq = "equipada" if bool(p.get("equipped")) else "no equipada"
            p_w = _to_float(p.get("weight_kg"), 0.0)
            m[f"Armadura-Escudo-Protecciones.{slot}"] = _join_non_empty([
                p_name,
                p_type,
                f"+{p_ac} CA" if p_ac else "",
                f"{_fmt_1(p_w)} kg" if p_w else "",
                p_eq,
            ])
        else:
            m[f"Armadura-Escudo-Protecciones.{slot}"] = ""

    adv_lines: list[str] = []
    for adv in cb.get("advantages_resistances", [])[:8]:
        if isinstance(adv, dict):
            adv_lines.append(_join_non_empty([str(adv.get("category") or ""), str(adv.get("description") or "")], ": "))
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
            note = str(ammo.get("note") or "").strip()
            m[f"Municion-{ammo_idx - 1}-Nombre"] = _join_non_empty([
                name,
                f"max {max_v}" if max_v else "",
                note,
            ], " - ")
            pips = _canonical_bool_pips(ammo.get("pip_states"), 20, max_v)
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
    if bool(pr.get("simple_weapons", False)):
        comp_lines.append("Armas simples")
    if bool(pr.get("martial_weapons", False)):
        comp_lines.append("Armas marciales")
    for seq in (pr.get("armor") or [], pr.get("weapons") or [], pr.get("tools") or [], pr.get("raw") or []):
        for raw in seq:
            txt = str(raw or "").strip()
            if txt:
                comp_lines.append(txt)

    seen_comp: set[str] = set()
    ordered_comp: list[str] = []
    for c in comp_lines:
        key = c.lower()
        if key in seen_comp:
            continue
        seen_comp.add(key)
        ordered_comp.append(c)
    for i in range(1, 8):
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
    other_currency_lines = _split_lines(str(currency.get("other_notes") or ""))
    m["Piezas.Otros.1"] = other_currency_lines[0] if len(other_currency_lines) > 0 else ""
    m["Piezas.Otros.2"] = other_currency_lines[1] if len(other_currency_lines) > 1 else ""

    # ── Inventario — por filas ───────────────────────────────────────────────
    qty_total = 0
    qty_by_loc = {"Equipado": 0, "Transportado": 0, "Otros": 0}
    weight_by_loc = {"Equipado": 0.0, "Transportado": 0.0, "Otros": 0.0}
    for i, item in enumerate(inv_items[:47], 1):
        name_val = str(item.get("name") or "")
        qty_i = max(0, _to_int(item.get("quantity"), 0))
        loc = str(item.get("location") or "").strip()
        w_i = _to_float(item.get("weight_kg"), 0.0)
        total_weight_i = w_i * qty_i

        qty_total += qty_i
        if loc in qty_by_loc:
            qty_by_loc[loc] += qty_i
            weight_by_loc[loc] += total_weight_i

        name_with_weight = f"{name_val} ({_fmt_1(w_i)} kg)" if w_i else name_val
        m[f"Objeto-Nombre.{i}"]   = name_with_weight
        m[f"Objeto-Cantidad.{i}"] = str(qty_i)
        m[f"Objeto-Puesto.{i}"]   = str(qty_i) if loc == "Equipado" else ""
        m[f"Objeto-Mochila.{i}"]  = str(qty_i) if loc == "Transportado" else ""
        m[f"Objeto-Bolsa.{i}"]    = str(qty_i) if loc == "Otros" else ""

    m["Total-Cantidad"] = str(qty_total)
    m["Total-Puesto"] = str(qty_by_loc["Equipado"])
    m["Total-Mochila"] = str(qty_by_loc["Transportado"])
    m["Total-Bolsa"] = str(qty_by_loc["Otros"])
    m["Total-Pesos-Puesto"] = _fmt_1(weight_by_loc["Equipado"])
    m["Total-Pesos-Equipados"] = _fmt_1(weight_by_loc["Equipado"])
    m["Total-Pesos-Mochila"] = _fmt_1(weight_by_loc["Transportado"])
    m["Total-Pesos-Bolsa"] = _fmt_1(weight_by_loc["Otros"])

    # ── Idiomas — campo único + campos individuales por fila ─────────────────
    for i, lang in enumerate(langs[:4], 1):
        m[f"Idioma.{i}"] = lang

    # ── Tamaño — campo plano + bajo Dato-Personaje ───────────────────────────
    m["Dato-Personaje.Tamano"] = m["Tamano"]

    # ── Apariencia — campos individuales bajo Dato-Personaje ─────────────────
    m["Dato-Personaje.Edad"]   = str(app.get("age")    or "")
    m["Dato-Personaje.Altura"] = str(app.get("height") or "")
    m["Dato-Personaje.Peso"]   = str(app.get("weight") or "")
    m["Dato-Personaje.Ojos"]   = str(app.get("eyes")   or "")
    m["Dato-Personaje.Piel"]   = str(app.get("skin")   or "")
    m["Dato-Personaje.Pelo"]   = str(app.get("hair")   or "")
    m["Dato-Personaje.Genero"] = str(app.get("gender") or "")
    m["Dato-Personaje.Tamano"] = m["Tamano"]

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
    phys_lines = _split_lines(notes_d.get("physical_description"))
    phys_lines += _split_lines(str(app.get("summary") or ""))
    for i in range(1, 4):
        m[f"Dato-Personaje.Amigo-Aliado-{i}"] = allies_lines[i-1]  if i-1 < len(allies_lines)  else ""
        m[f"Dato-Personaje.Enemigo-{i}"]      = enemies_lines[i-1] if i-1 < len(enemies_lines) else ""
        m[f"Dato-Personaje.Apariencia-{i}"]   = phys_lines[i-1]    if i-1 < len(phys_lines)    else ""

    m["Dato-Personaje.Deidad-Dominio"]     = bg.get("deity") or ""
    m["Dato-Personaje.Descripcion-Deidad"] = bg.get("deity_description") or ""

    other_lines = _split_lines(notes_d.get("other_notes"))
    m["Dato-Personaje.Trasfondo-Otros-1"] = bg.get("description", "")
    for i in range(2, 8):
        m[f"Dato-Personaje.Trasfondo-Otros-{i}"] = other_lines[i-2] if i-2 < len(other_lines) else ""

    # Notas de texto libres
    note_lines: list[str] = []
    note_lines += _split_lines(str(notes_d.get("general") or ""))
    note_lines += _split_lines(str(notes_d.get("additional_notes") or ""))
    note_lines += _split_lines(str(notes_d.get("organizations") or ""))
    note_lines += _split_lines(str(notes_d.get("backstory") or ""))
    _fill_line_fields(m, "Nota", note_lines, 16)

    # Otros
    m["Titulo-Otro"] = "Otras posesiones"
    m["Otro-1"] = str(inv.get("other_possessions") or notes_d.get("other_possessions") or "")

    # Monturas
    mount_lines: list[str] = []
    for mt in inv.get("mounts", [])[:19]:
        mount_lines.append(_join_non_empty([
            str(mt.get("name") or "").strip(),
            str(mt.get("species") or "").strip(),
            f"x{_to_int(mt.get('quantity'), 0)}" if _to_int(mt.get("quantity"), 0) else "",
            f"{_to_int(mt.get('speed_m'), 0)} m" if _to_int(mt.get("speed_m"), 0) else "",
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
                str(ln.get("to") or "").strip(),
                str(ln.get("name") or "").strip(),
            ])
            m[f"Prestad-Depositado-Recibido-Cantidad.{i}"] = str(_to_int(ln.get("quantity"), 0))
            m[f"Prestad-Depositado-Recibido-Momento.{i}"] = _join_non_empty([
                str(ln.get("due") or "").strip(),
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

    m["Conjuros-Concidos"]   = str(total_spells)   if total_spells   else ""  # sic: typo in PDF
    m["Conjuros-Preparados"] = str(prepared_count) if prepared_count > 0 else ""

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
# Embebido de CaslonAntique en /DR del AcroForm (ES PDF no la incluye)
# ---------------------------------------------------------------------------

def _embed_caslon(pdf: pikepdf.Pdf, font_info: FontInfo) -> object:
    """Embebe CaslonAntique desde el TTF en el /DR del AcroForm y devuelve la referencia."""
    with open(FONT_REGULAR, "rb") as f:
        font_bytes = f.read()

    font_stream = pikepdf.Stream(pdf, font_bytes)
    font_stream["/Length1"] = len(font_bytes)

    fd = pikepdf.Dictionary(
        Type=pikepdf.Name("/FontDescriptor"),
        FontName=pikepdf.Name("/CaslonAntique"),
        Flags=32,
        FontBBox=pikepdf.Array([pikepdf.Integer(v) for v in font_info.bbox]),
        ItalicAngle=font_info.italic_angle,
        Ascent=round(font_info.ascent * 1000 / font_info.upm),
        Descent=round(font_info.descent * 1000 / font_info.upm),
        CapHeight=round(font_info.cap_height * 1000 / font_info.upm),
        StemV=font_info.stemv,
        FontFile2=pdf.make_indirect(font_stream),
    )

    widths_arr = pikepdf.Array([pikepdf.Integer(w) for w in font_info.widths])
    font_dict = pikepdf.Dictionary(
        Type=pikepdf.Name("/Font"),
        Subtype=pikepdf.Name("/TrueType"),
        BaseFont=pikepdf.Name("/CaslonAntique"),
        Encoding=pikepdf.Name("/WinAnsiEncoding"),
        FirstChar=pikepdf.Integer(32),
        LastChar=pikepdf.Integer(255),
        Widths=widths_arr,
        FontDescriptor=pdf.make_indirect(fd),
    )

    acroform = pdf.Root.AcroForm
    if "/DR" not in acroform:
        acroform["/DR"] = pikepdf.Dictionary()
    dr = acroform["/DR"]
    if "/Font" not in dr:
        dr["/Font"] = pikepdf.Dictionary()

    font_ref = pdf.make_indirect(font_dict)
    dr["/Font"]["/CaslonAntique"] = font_ref
    return font_ref


# ---------------------------------------------------------------------------
# Helpers de content streams PDF
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


def _make_form_xobject(
    pdf:        pikepdf.Pdf,
    content:    bytes,
    font_alias: str,
    font_ref:   object,
    w:          float,
    h:          float,
) -> object:
    """Envuelve content bytes en un Form XObject (/AP stream)."""
    stream = pikepdf.Stream(pdf, content)
    stream["/Subtype"]   = pikepdf.Name("/Form")
    stream["/Type"]      = pikepdf.Name("/XObject")
    stream["/FormType"]  = 1
    stream["/BBox"]      = pikepdf.Array([0, 0, float(w), float(h)])
    stream["/Matrix"]    = pikepdf.Array([1, 0, 0, 1, 0, 0])
    stream["/Resources"] = pikepdf.Dictionary(
        Font    = pikepdf.Dictionary(**{font_alias: font_ref}),
        ProcSet = pikepdf.Array([pikepdf.Name("/PDF"), pikepdf.Name("/Text")]),
    )
    return pdf.make_indirect(stream)


def _make_text_ap(
    pdf:        pikepdf.Pdf,
    font_ref:   object,
    font_info:  FontInfo,
    text:       str,
    fsize:      float,
    align:      int,
    w:          float,
    h:          float,
) -> object:
    """AP stream para un campo de texto de una sola línea."""
    MARGIN   = 2.0
    avail_w  = max(1.0, w - 2 * MARGIN)
    fs       = float(fsize)

    text_w = font_info.string_width(text, fs)
    if text_w > avail_w and fs > 4:
        fs     = max(4.0, fs * avail_w / text_w)
        text_w = font_info.string_width(text, fs)

    asc_pts = font_info.ascent_pts(fs)
    des_pts = font_info.descent_pts(fs)   # negativo
    text_h  = asc_pts - des_pts
    y_base  = max(1.0, (h - text_h) / 2 - des_pts)
    x_start = max(0.0, (w - text_w) / 2) if align == 1 else MARGIN

    buf  = bytearray()
    buf += b"q\nBT\n"
    buf += f"/CaslonAntique {fs:.2f} Tf\n".encode("ascii")
    buf += b"0 0 0 rg\n"
    buf += f"{x_start:.3f} {y_base:.3f} Td\n".encode("ascii")
    buf += b"("
    buf += _pdf_escape(text)
    buf += b") Tj\nET\nQ\n"

    return _make_form_xobject(pdf, bytes(buf), "CaslonAntique", font_ref, w, h)


def _make_multiline_ap(
    pdf:       pikepdf.Pdf,
    font_ref:  object,
    font_info: FontInfo,
    text:      str,
    fsize:     float,
    w:         float,
    h:         float,
) -> object:
    """AP stream para un campo de texto multilínea con word-wrap."""
    MARGIN_X = 2.0
    MARGIN_Y = 2.0
    avail_w  = max(1.0, w - 2 * MARGIN_X)
    leading  = fsize * 1.2
    asc_pts  = font_info.ascent_pts(fsize)

    render_lines: list[str] = []
    for paragraph in text.split("\n"):
        words   = paragraph.split(" ")
        current = ""
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

    buf  = bytearray()
    buf += b"q\nBT\n"
    buf += f"/CaslonAntique {fsize:.2f} Tf\n".encode("ascii")
    buf += b"0 0 0 rg\n"
    buf += f"{leading:.2f} TL\n".encode("ascii")
    buf += f"{MARGIN_X:.2f} {y_start:.3f} Td\n".encode("ascii")

    for i, line in enumerate(render_lines):
        if y_start - i * leading < MARGIN_Y:
            break
        if i > 0:
            buf += b"T*\n"
        buf += b"("
        buf += _pdf_escape(line)
        buf += b") Tj\n"

    buf += b"ET\nQ\n"
    return _make_form_xobject(pdf, bytes(buf), "CaslonAntique", font_ref, w, h)


def _make_checkbox_ap(
    pdf:     pikepdf.Pdf,
    checked: bool,
    w:       float,
    h:       float,
) -> object:
    """AP stream para checkbox: X negra en negrita (marcado) o vacío (no marcado)."""
    if checked:
        MARGIN = 1.5
        x0, y0 = MARGIN, MARGIN
        x1, y1 = w - MARGIN, h - MARGIN
        content = (
            f"q\n"
            f"2 w\n"
            f"0 G\n"
            f"{x0:.2f} {y0:.2f} m {x1:.2f} {y1:.2f} l S\n"
            f"{x1:.2f} {y0:.2f} m {x0:.2f} {y1:.2f} l S\n"
            f"Q\n"
        ).encode("ascii")
    else:
        content = b""

    stream = pikepdf.Stream(pdf, content)
    stream["/Subtype"]   = pikepdf.Name("/Form")
    stream["/Type"]      = pikepdf.Name("/XObject")
    stream["/FormType"]  = 1
    stream["/BBox"]      = pikepdf.Array([0, 0, float(w), float(h)])
    stream["/Matrix"]    = pikepdf.Array([1, 0, 0, 1, 0, 0])
    stream["/Resources"] = pikepdf.Dictionary(
        ProcSet = pikepdf.Array([pikepdf.Name("/PDF")])
    )
    return pdf.make_indirect(stream)


def _get_field_name(annot: object) -> str:
    """Devuelve el path completo con puntos recorriendo toda la cadena de /Parent."""
    parts: list[str] = []
    obj = annot
    while obj is not None:
        t = obj.get("/T")
        if t is not None:
            parts.append(str(t))
        obj = obj.get("/Parent")
    parts.reverse()
    return ".".join(parts) if parts else ""


def _canonical_name(name: str) -> str:
    """Normaliza nombres PDF removiendo sufijos de repeticion como [123], 10b o 11.1."""
    s = (name or "").strip()
    s = re.sub(r"\[\d+\]$", "", s)
    s = re.sub(r"(\.\d+)?[a-zA-Z]$", "", s)
    return s


# ---------------------------------------------------------------------------
# Relleno del PDF
# ---------------------------------------------------------------------------

def fill_pdf(
    json_path:     Path,
    template_path: Path,
    output_path:   Path,
    verbose:       bool = False,
) -> None:
    """
    Rellena los campos AcroForm del PDF usando pikepdf.
    Cada widget recibe /V (valor), /DA (CaslonAntique) y /AP /N (appearance stream).
    """
    if not FONT_REGULAR.exists():
        _ensure_fonts()

    print("Cargando métricas de fuente...")
    font_info = FontInfo.load(FONT_REGULAR)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    field_map = build_field_map(data)

    pdf = pikepdf.open(str(template_path))

    # Embeber CaslonAntique en /DR del ES PDF (no viene incluida)
    print("Embebiendo fuente CaslonAntique en el template...")
    caslon_ref = _embed_caslon(pdf, font_info)

    # NeedAppearances=False: los /AP que generamos son definitivos
    pdf.Root.AcroForm["/NeedAppearances"] = False

    filled:  int       = 0
    skipped: list[str] = []

    canonical_map: dict[str, str | bool] = {}
    for k, v in field_map.items():
        canonical_map[_canonical_name(k)] = v

    for page in pdf.pages:
        annots = page.get("/Annots")
        if annots is None:
            continue

        for annot in annots:
            if annot.get("/Subtype") != pikepdf.Name("/Widget"):
                continue

            field_name = _get_field_name(annot)
            if not field_name:
                continue

            if field_name in field_map:
                val = field_map[field_name]
            else:
                val = canonical_map.get(_canonical_name(field_name))

            if val is None:
                skipped.append(field_name)
                continue

            # Geometría del widget
            rect = annot["/Rect"]
            x0 = float(rect[0]); y0 = float(rect[1])
            x1 = float(rect[2]); y1 = float(rect[3])
            if x0 > x1: x0, x1 = x1, x0
            if y0 > y1: y0, y1 = y1, y0
            fw = x1 - x0
            fh = y1 - y0

            if fw < 1 or fh < 1:
                filled += 1
                continue

            # Tipo de campo (/FT puede estar heredado del /Parent)
            ft = annot.get("/FT")
            if ft is None:
                parent = annot.get("/Parent")
                if parent is not None:
                    ft = parent.get("/FT")

            if ft == pikepdf.Name("/Btn"):
                checked = bool(val)
                v_name  = pikepdf.Name("/Yes") if checked else pikepdf.Name("/Off")
                annot["/V"]  = v_name
                annot["/AS"] = v_name
                annot["/AP"] = pikepdf.Dictionary(N=pikepdf.Dictionary(
                    Yes=_make_checkbox_ap(pdf, True,  fw, fh),
                    Off=_make_checkbox_ap(pdf, False, fw, fh),
                ))

            else:
                text = str(val).strip()
                annot["/V"] = pikepdf.String(text)

                if not text:
                    filled += 1
                    continue

                fsize = _field_size(field_name)
                align = _align(field_name)

                annot["/DA"] = pikepdf.String(f"/CaslonAntique {fsize} Tf 0 g")

                ff_val       = int(annot.get("/Ff") or 0)
                is_multiline = bool(ff_val & 4096) or "\n" in text

                if is_multiline:
                    ap = _make_multiline_ap(
                        pdf, caslon_ref, font_info,
                        text, float(fsize), fw, fh,
                    )
                else:
                    ap = _make_text_ap(
                        pdf, caslon_ref, font_info,
                        text, float(fsize), align, fw, fh,
                    )

                annot["/AP"] = pikepdf.Dictionary(N=ap)

            filled += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(str(output_path))
    pdf.close()

    print(f"\nCampos procesados : {filled}")
    print(f"Campos sin mapeo  : {len(skipped)}")
    if skipped and verbose:
        print("  Sin mapeo:", sorted(set(skipped)))
    print(f"PDF guardado en   : {output_path}")


# ---------------------------------------------------------------------------
# Verificaciones
# ---------------------------------------------------------------------------

def verify_fields(output_path: Path) -> None:
    """Verifica campos AcroForm leyendo /V directamente con pikepdf."""
    pdf    = pikepdf.open(str(output_path))
    values: dict[str, str] = {}

    for page in pdf.pages:
        annots = page.get("/Annots")
        if annots is None:
            continue
        for annot in annots:
            if annot.get("/Subtype") != pikepdf.Name("/Widget"):
                continue
            name = _get_field_name(annot)
            v    = annot.get("/V")
            if v is not None and name and name not in values:
                try:
                    values[name] = str(v)
                except Exception:
                    pass
    pdf.close()

    checks = {
        "WebOns":    ("Nombre-Personaje",        "nombre del personaje"),
        "Monje":     ("Clase-Y-Nivel",           "clase y nivel"),
        "Vagabundo": ("Trasfondo",               "trasfondo"),
        "16":        ("Clase-Armadura",           "CA = 10+DEX+SAB"),
        "+3":        ("Iniciativa",              "iniciativa = DEX modifier"),
        "12 m":      ("Velocidad",               "velocidad Monje 2"),
        "13":        ("Percepcion-Pasiva",        "percepción pasiva"),
        "+2":        ("Bonificador-Competencia",  "bono competencia nivel 2"),
        "27":        ("Piezas.Oro",            "monedas GP"),
    }

    print("\n--- Verificación de campos AcroForm ---")
    errors = 0
    for expected, (field_name, note) in checks.items():
        actual = values.get(field_name, "")
        ok     = expected in actual
        print(f"  [{'OK  ' if ok else 'FAIL'}] '{expected}' en '{field_name}' = {actual!r}  ({note})")
        if not ok:
            errors += 1
    print(f"\n{len(checks) - errors}/{len(checks)} verificaciones pasadas")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose    = "--verbose" in sys.argv or "-v" in sys.argv
    verify     = "--verify"  in sys.argv

    default_json = PROJECT_ROOT / "data" / "personaje.json"

    json_path = Path(positional[0]) if len(positional) >= 1 else default_json

    if not json_path.exists():
        sys.exit(f"Error: no se encuentra '{json_path}'")
    if not TEMPLATE_PATH.exists():
        sys.exit(f"Error: no se encuentra la plantilla '{TEMPLATE_PATH}'")

    with open(json_path, encoding="utf-8") as f:
        char_name = json.load(f).get("basic_info", {}).get("name", "personaje")
    safe_name   = char_name.replace(" ", "-")
    default_out = PROJECT_ROOT / "output" / f"{safe_name}_filled.pdf"
    output_path = Path(positional[1]) if len(positional) >= 2 else default_out

    print(f"JSON      : {json_path}")
    print(f"Plantilla : {TEMPLATE_PATH}")
    print(f"Fuente    : Caslon Antique  ({FONT_REGULAR.name})")
    print(f"Salida    : {output_path}")

    fill_pdf(json_path, TEMPLATE_PATH, output_path, verbose=verbose)

    if verify:
        verify_fields(output_path)


if __name__ == "__main__":
    main()
