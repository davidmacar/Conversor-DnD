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
    classes_str = " / ".join(f"{c['name']} {c['level']}" for c in classes)

    # ── Info básica ──────────────────────────────────────────────────────────
    m["Nombre-Personaje"] = bi.get("name") or ""
    m["Clase-Y-Nivel"]    = classes_str
    m["Trasfondo"]        = bi.get("background") or ""
    m["Especie"]          = bi.get("species") or ""
    m["PX-Personaje"]     = str(bi.get("experience_points") or "")
    m["Alineamiento"]     = bi.get("alignment") or ""
    m["Tamano"]           = SPECIES_SIZE.get(
        (bi.get("species") or "").lower().strip(), "Mediana")
    m["Nombre-Jugador"]   = bi.get("player_name") or ""
    m["Vision"]           = bi.get("vision") or ""
    m["Deidad-Dominio"]   = bg.get("deity") or ""
    m["Descripcion-Deidad"] = bg.get("deity_description") or ""

    # ── Combate ──────────────────────────────────────────────────────────────
    speed        = cb.get("speed", {})
    walking_m    = speed.get("walking_meters", 0)
    perc_total   = sk.get("percepcion", {}).get("total", 0)
    passive_perc = 10 + perc_total

    m["Clase-Armadura"]    = str(cb.get("armor_class") or "")
    m["Iniciativa"]        = fmt_mod(cb.get("initiative") or 0)
    m["Velocidad"]         = f"{walking_m} m"
    m["Percepcion-Pasiva"] = str(passive_perc)
    m["Check-Escudo"]      = bool(cb.get("shield_equipped", False))
    m["Check-Inspiracion-Heroica"] = bool(bi.get("inspiration", False))
    m["Inspiracion-Heroica"] = ""  # el checkbox gestiona el estado

    hp = cb.get("hit_points", {})
    hp_current = hp.get("current")
    hp_max     = hp.get("maximum")
    m["Puntos-Golpe-Actuales"]   = str(hp_current if hp_current is not None else (hp_max or ""))
    m["Puntos-Golpe-Maximo"]     = str(hp_max or "")
    m["Puntos-Golpe-Temporales"] = "0"
    m["Dados-Golpe-Maximos"]     = cb.get("hit_dice", {}).get("total") or ""
    m["Dados-Golpe-Gastados"]    = "0"
    m["Bonificador-Competencia"] = fmt_mod(pb)

    # Death saves — leer del JSON
    ds        = cb.get("death_saves", {})
    successes = int(ds.get("successes") or 0)
    failures  = int(ds.get("failures")  or 0)
    for n in range(1, 4):
        m[f"Check-Salvacion-Muerte.Exito.{n}"] = (n <= successes)
        m[f"Check-Salvacion-Muerte.Fallo.{n}"] = (n <= failures)

    # Hit dice checkboxes — marcados = disponibles
    hd_remaining = int((cb.get("hit_dice") or {}).get("remaining") or 0)
    for i in range(1, 21):
        m[f"Check-Dado-Golpe.{i}"] = (i <= hd_remaining)

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
    for i, a in enumerate(atk[:5], 1):
        bonus    = a.get("attack_bonus") or 0
        damage   = a.get("damage") or ""
        dmg_type = a.get("damage_type") or ""
        dmg_str  = f"{damage} {dmg_type}".strip() if dmg_type else damage
        props    = a.get("properties") or []
        m[f"Arma-{i}-Nombre"]             = a.get("name") or ""
        m[f"Arma-{i}-Bonificador-Ataque"] = fmt_mod(bonus)
        m[f"Arma-{i}-Dano-Tipo"]          = dmg_str
        m[f"Arma-{i}-Notas"]              = ", ".join(props) if props else ""

    # ── Competencias ─────────────────────────────────────────────────────────
    armor_list  = pr.get("armor") or []
    armor_flags = pr.get("armor_flags") or {}
    if isinstance(armor_list, str):
        armor_list = [x.strip() for x in armor_list.split(",")]
    m["Check-Competencia-Armadura-Ligera"] = armor_flags.get("light", False) or any("ligera"  in a.lower() for a in armor_list)
    m["Check-Competencia-Armadura-Media"]  = armor_flags.get("medium", False) or any("media"   in a.lower() for a in armor_list)
    m["Check-Competencia-Armadura-Pesada"] = armor_flags.get("heavy",  False) or any("pesada"  in a.lower() for a in armor_list)
    m["Check-Competencia-Escudo"]          = armor_flags.get("shield", False) or any("escudo"  in a.lower() for a in armor_list)
    m["Competencia-Armas"]        = ", ".join(pr.get("weapons") or [])
    m["Competencia-Herramientas"] = ", ".join(pr.get("tools") or [])

    # ── Rasgos y características ─────────────────────────────────────────────
    species_traits = ft.get("species", [])
    feat_traits    = ft.get("feats", [])
    class_features = ft.get("class_features", [])
    m["Atributos-Especie"] = fmt_traits(species_traits)
    m["Dotes"]             = fmt_traits(feat_traits)
    half = (len(class_features) + 1) // 2
    m["Rasgos-Clase-1"] = fmt_traits(class_features[:half])
    m["Rasgos-Clase-2"] = fmt_traits(class_features[half:])

    # ── Monedas (jerárquico Piezas.Oro etc.) ────────────────────────────────
    currency = inv.get("currency", {})
    m["Piezas.Cobre"]   = str(currency.get("CP") or 0)
    m["Piezas.Plata"]   = str(currency.get("SP") or 0)
    m["Piezas.Electro"] = str(currency.get("EP") or 0)
    m["Piezas.Oro"]     = str(currency.get("GP") or 0)
    m["Piezas.Platino"] = str(currency.get("PP") or 0)

    # ── Inventario — por filas ───────────────────────────────────────────────
    for i, item in enumerate(inv.get("items", [])[:47], 1):
        name_val = item.get("name", "")
        qty_val  = str(item.get("quantity", 1))
        loc      = item.get("location", "") or ""
        m[f"Objeto-Nombre.{i}"]   = name_val
        m[f"Objeto-Cantidad.{i}"] = qty_val
        m[f"Objeto-Puesto.{i}"]   = (loc == "Equipado")
        m[f"Objeto-Mochila.{i}"]  = ("Transportado" in loc)
        m[f"Objeto-Bolsa.{i}"]    = (loc == "Otros")

    # ── Idiomas — campo único + campos individuales por fila ─────────────────
    m["Idiomas"] = ", ".join(langs)
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
    m["Dato-Personaje.Tamano"] = SPECIES_SIZE.get(
        (bi.get("species") or "").lower().strip(), "Mediana")

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
    phys_lines    = _split_lines(notes_d.get("physical_description"))
    for i in range(1, 4):
        m[f"Dato-Personaje.Amigo-Aliado-{i}"] = allies_lines[i-1]  if i-1 < len(allies_lines)  else ""
        m[f"Dato-Personaje.Enemigo-{i}"]      = enemies_lines[i-1] if i-1 < len(enemies_lines) else ""
        m[f"Dato-Personaje.Apariencia-{i}"]   = phys_lines[i-1]    if i-1 < len(phys_lines)    else ""

    m["Dato-Personaje.Deidad-Dominio"]    = bg.get("deity") or ""
    m["Dato-Personaje.Descripcion-Deidad"] = bg.get("deity_description") or ""

    other_lines = _split_lines(notes_d.get("other_notes"))
    m["Dato-Personaje.Trasfondo-Otros-1"] = bg.get("description", "")
    for i in range(2, 8):
        m[f"Dato-Personaje.Trasfondo-Otros-{i}"] = other_lines[i-2] if i-2 < len(other_lines) else ""

    # ── Conjuros ─────────────────────────────────────────────────────────────
    spell_ab_raw = sp.get("spellcasting_ability") or ""
    spell_ab_key = SPELL_ABILITY_KEY.get(spell_ab_raw, "intelligence")
    spell_ab_mod = (ab.get(spell_ab_key) or {}).get("modifier", 0)

    spell_atk = sp.get("spell_attack_bonus")
    # "Aptitud-Magica" es el campo bajo la etiqueta "BONO ATAQUE CONJ." en el template
    m["Aptitud-Magica"]              = fmt_mod(spell_atk) if spell_atk is not None else ""
    m["Modificador-Aptitud-Magica"]  = fmt_mod(spell_ab_mod)  # campo fantasma (no existe en template)
    m["CD-Salvacion-Conjuros"]       = str(sp.get("spell_save_dc") or "")
    m["Bonificador-Ataque-Conjuros"] = m["Aptitud-Magica"]  # alias (campo no existe en template)

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
    magic_max     = int(magic_res.get("max")     or 0)
    magic_current = int(magic_res.get("current") or 0)
    m["Puntos-Hechiceria-Max"]      = str(magic_max)               if magic_max > 0 else ""
    m["Puntos-Hechiceria-Gastados"] = str(magic_max - magic_current) if magic_max > 0 else ""

    # Espacios de conjuro (punto como separador: Total-Espacios-Conjuro.N)
    slots = sp.get("spell_slots") or {}
    for lvl in range(1, 10):
        slot_val = (slots.get(f"level_{lvl}") or {}).get("total", 0)
        m[f"Total-Espacios-Conjuro.{lvl}"] = str(slot_val) if slot_val else ""

    # Conjuros por nivel
    spells_data = sp.get("spells") or {}
    total_spells  = 0
    prepared_count = 0

    cantrips = spells_data.get("cantrips", [])
    total_spells += len(cantrips)
    for i, s in enumerate(cantrips[:MAX_SPELLS_PER_LEVEL[0]], 1):
        m[f"Nombre-Conjuro-Nivel-0.{i}"] = s.get("name") or ""

    for lvl in range(1, 10):
        spell_list = spells_data.get(f"level_{lvl}", [])
        total_spells  += len(spell_list)
        prepared_count += sum(1 for s in spell_list if s.get("prepared"))
        max_s = MAX_SPELLS_PER_LEVEL[lvl]
        for i, s in enumerate(spell_list[:max_s], 1):
            m[f"Nombre-Conjuro-Nivel-{lvl}.{i}"]          = s.get("name") or ""
            m[f"Check-Preparado-Conjuro-Nivel-{lvl}.{i}"] = bool(s.get("prepared"))

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

            if field_name not in field_map:
                skipped.append(field_name)
                continue

            val = field_map[field_name]

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
