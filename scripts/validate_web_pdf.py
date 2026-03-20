#!/usr/bin/env python3
"""Valida consistencia entre JSON web y PDF generado en iteraciones."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from extract_pdf_fields import extract_pdf_fields
from fill_pdf import ABILITY_NAMES, SKILL_MAP, build_field_map
from generate_pdf import generate

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "Hoja-Personaje-Editable-Completa-ES.pdf"
DEFAULT_JSON = PROJECT_ROOT / "data" / "personaje.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "output" / "validacion_web_pdf"

CORE_FIELDS = {
    "Nombre-Personaje",
    "Clase-Y-Nivel",
    "Especie",
    "Trasfondo",
    "Clase-Armadura",
    "Iniciativa",
    "Velocidad",
    "Bonificador-Competencia",
    "Puntos-Golpe-Actuales",
    "Puntos-Golpe-Maximo",
    "Puntuacion-Fuerza",
    "Puntuacion-Destreza",
    "Puntuacion-Constitucion",
    "Puntuacion-Inteligencia",
    "Puntuacion-Sabiduria",
    "Puntuacion-Carisma",
    "Modificador-Fuerza",
    "Modificador-Destreza",
    "Modificador-Constitucion",
    "Modificador-Inteligencia",
    "Modificador-Sabiduria",
    "Modificador-Carisma",
}


def flatten_json(value: object, prefix: str = "") -> dict[str, object]:
    out: dict[str, object] = {}

    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else k
            out.update(flatten_json(v, child))
        return out

    if isinstance(value, list):
        for i, item in enumerate(value):
            child = f"{prefix}[{i}]"
            out.update(flatten_json(item, child))
        return out

    out[prefix] = value
    return out


def _lines_to_targets(prefix: str, text: object, max_lines: int = 3) -> list[str]:
    if not isinstance(text, str):
        return [f"{prefix}-{i}" for i in range(1, max_lines + 1)]
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    count = max(1, min(max_lines, len(lines)))
    return [f"{prefix}-{i}" for i in range(1, count + 1)]


def _canonical_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\[\d+\]$", "", s)
    s = re.sub(r"(\.\d+)?[a-zA-Z]$", "", s)
    return s


def map_web_path_to_pdf(web_path: str) -> list[str]:
    if web_path == "basic_info.name":
        return ["Nombre-Personaje"]
    if web_path.startswith("basic_info.classes["):
        return ["Clase-Y-Nivel", "Clase-Lanzador-Conjuros"]
    if web_path == "basic_info.total_level":
        return ["Clase-Y-Nivel"]
    if web_path == "basic_info.background":
        return ["Trasfondo"]
    if web_path == "basic_info.species":
        return ["Especie", "Tamano", "Dato-Personaje.Tamano"]
    if web_path == "basic_info.experience_points":
        return ["PX-Personaje"]
    if web_path == "basic_info.next_level_xp":
        return ["PX-Proximo-Nivel"]
    if web_path == "basic_info.creation_date":
        return ["Dato-Personaje-Fecha-Creacion"]
    if web_path == "basic_info.alignment":
        return ["Alineamiento"]
    if web_path == "basic_info.player_name":
        return ["Nombre-Jugador"]
    if web_path == "basic_info.vision":
        return ["Vision"]
    if web_path == "basic_info.inspiration":
        return ["Check-Inspiracion-Heroica"]

    m_ability = re.match(r"ability_scores\.(\w+)\.(score|modifier)$", web_path)
    if m_ability:
        ability_eng, kind = m_ability.groups()
        ability_es = ABILITY_NAMES.get(ability_eng)
        if not ability_es:
            return []
        if kind == "score":
            return [f"Puntuacion-{ability_es}"]
        return [f"Modificador-{ability_es}"]

    m_save = re.match(r"saving_throws\.(\w+)\.(total|proficient)$", web_path)
    if m_save:
        ability_eng, kind = m_save.groups()
        ability_es = ABILITY_NAMES.get(ability_eng)
        if not ability_es:
            return []
        if kind == "total":
            return [f"Modificador-Salvacion-{ability_es}"]
        return [f"Check-Competencia-Salvacion-{ability_es}"]

    m_skill = re.match(r"skills\.(\w+)\.(total|proficient|expertise)$", web_path)
    if m_skill:
        skill_key, kind = m_skill.groups()
        suffix = SKILL_MAP.get(skill_key)
        if not suffix:
            return []
        if kind == "total":
            fields = [f"Modificador-{suffix}"]
            if skill_key == "percepcion":
                fields.append("Percepcion-Pasiva")
            return fields
        if kind == "proficient":
            return [f"Check-Competencia-{suffix}"]
        return [f"Check-Pericia-{suffix}"]

    if web_path == "combat.armor_class":
        return ["Clase-Armadura"]
    if web_path == "combat.initiative":
        return ["Iniciativa"]
    if web_path == "combat.speed.walking_meters":
        return ["Velocidad", "Velocidad-Hora", "Velocidad-Jornada"]
    if web_path == "combat.speed.hour_text":
        return ["Velocidad-Hora"]
    if web_path == "combat.speed.day_text":
        return ["Velocidad-Jornada"]
    if web_path == "combat.speed.jump_long":
        return ["Salto-Horizontal"]
    if web_path == "combat.speed.jump_high":
        return ["Salto-Altura"]
    if web_path == "combat.speed.special_senses":
        return ["Velocidad-Especial"]
    if web_path in {"combat.speed.swim_meters", "combat.speed.fly_meters", "combat.speed.climb_meters"}:
        return ["Velocidad-Especial"]
    if web_path == "combat.shield_equipped":
        return ["Check-Escudo"]
    if web_path == "combat.hit_points.current":
        return ["Puntos-Golpe-Actuales"]
    if web_path == "combat.hit_points.maximum":
        return ["Puntos-Golpe-Maximo"]
    if web_path == "combat.hit_points.temporary":
        return ["Puntos-Golpe-Temporales"]
    if web_path == "combat.hit_dice.total":
        return ["Dados-Golpe-Maximos"]
    if web_path == "combat.hit_dice.used":
        return [f"Check-Dado-Golpe.{i}" for i in range(1, 21)]
    if web_path == "combat.hit_dice.remaining":
        return [f"Check-Dado-Golpe.{i}" for i in range(1, 21)]
    if web_path in {"combat.hit_dice.count", "combat.hit_dice.type", "combat.hit_dice.die_type"}:
        return ["Dados-Golpe-Maximos"]
    if web_path == "combat.death_saves.successes":
        return [f"Check-Salvacion-Muerte.Exito.{i}" for i in range(1, 4)]
    if web_path == "combat.death_saves.failures":
        return [f"Check-Salvacion-Muerte.Fallo.{i}" for i in range(1, 4)]

    if web_path == "proficiency_bonus":
        return ["Bonificador-Competencia"]

    m_attack = re.match(r"attacks\[(\d+)\]\.(name|attack_bonus|attack_roll|damage|damage_type|range|weight|properties\[\d+\])$", web_path)
    if m_attack:
        idx = int(m_attack.group(1)) + 1
        key = m_attack.group(2)
        if idx > 5:
            return []
        if key == "name":
            return [f"Arma-{idx}-Nombre"]
        if key == "damage":
            return [f"Arma-{idx}-Dano"]
        if key == "damage_type":
            return [f"Arma-{idx}-Tipo"]
        if key == "range":
            return [f"Arma-{idx}-Alcance"]
        if key == "weight":
            return [f"Arma-{idx}-Peso"]
        if key in {"attack_bonus", "attack_roll"} or key.startswith("properties["):
            return [f"Arma-{idx}-Notas"]

    m_prot = re.match(r"combat\.protections\[(\d+)\]\.", web_path)
    if m_prot:
        idx = int(m_prot.group(1))
        slot_map = {0: 1, 1: 2, 2: 4, 3: 5}
        if idx in slot_map:
            return [f"Armadura-Escudo-Protecciones.{slot_map[idx]}"]
        return []

    m_adv = re.match(r"combat\.advantages_resistances\[(\d+)\]", web_path)
    if m_adv:
        idx = int(m_adv.group(1)) + 1
        if 1 <= idx <= 8:
            return [f"Ventaja-Resistencia-Inmunidad.{idx}"]
        return []

    m_ammo = re.match(r"combat\.ammunition\[(\d+)\]\.(name|max|note|pip_states\[(\d+)\])$", web_path)
    if m_ammo:
        idx = int(m_ammo.group(1))
        key = m_ammo.group(2)
        pip_idx = m_ammo.group(3)
        if not (0 <= idx <= 2):
            return []
        slot = idx + 1
        if key in {"name", "max", "note"}:
            return [f"Municion-{idx}-Nombre"]
        if pip_idx is not None:
            p = int(pip_idx) + 1
            if 1 <= p <= 20:
                return [f"Check-Contador-Municion.{slot}.{p}"]
        return []

    if web_path.startswith("proficiencies.armor_flags."):
        flag = web_path.rsplit(".", 1)[-1]
        return {
            "light": ["Check-Competencia-Armadura-Ligera"],
            "medium": ["Check-Competencia-Armadura-Media"],
            "heavy": ["Check-Competencia-Armadura-Pesada"],
            "shield": ["Check-Competencia-Escudo"],
        }.get(flag, [])

    if web_path.startswith("proficiencies.armor["):
        return [
            "Check-Competencia-Armadura-Ligera",
            "Check-Competencia-Armadura-Media",
            "Check-Competencia-Armadura-Pesada",
            "Check-Competencia-Escudo",
        ]
    if web_path.startswith("proficiencies.weapons["):
        return [f"Competencia.{i}" for i in range(1, 8)]
    if web_path.startswith("proficiencies.tools["):
        return [f"Competencia.{i}" for i in range(1, 8)]
    if web_path.startswith("proficiencies.raw["):
        return [f"Competencia.{i}" for i in range(1, 8)]
    if web_path == "proficiencies.simple_weapons":
        return ["Check-Competencia-Armas-Simples", "Competencia.1"]
    if web_path == "proficiencies.martial_weapons":
        return ["Check-Competencia-Armas-Marciales", "Competencia.1"]

    if web_path.startswith("features_and_traits.species["):
        return [f"Rasgo.{i}" for i in range(1, 21)]
    if web_path.startswith("features_and_traits.feats["):
        return [f"Dotes.{i}" for i in range(1, 17)]
    if web_path.startswith("features_and_traits.class_features["):
        return [f"Rasgo.{i}" for i in range(1, 21)]

    m_currency = re.match(r"inventory\.currency\.(CP|SP|EP|GP|PP)$", web_path)
    if m_currency:
        cur = m_currency.group(1)
        return {
            "CP": ["Piezas.Cobre"],
            "SP": ["Piezas.Plata"],
            "EP": ["Piezas.Electro"],
            "GP": ["Piezas.Oro"],
            "PP": ["Piezas.Platino"],
        }.get(cur, [])
    if web_path == "inventory.currency.other_notes":
        return ["Piezas.Otros.1", "Piezas.Otros.2"]

    m_item = re.match(r"inventory\.items\[(\d+)\]\.(name|quantity|location|weight_kg)$", web_path)
    if m_item:
        idx = int(m_item.group(1)) + 1
        key = m_item.group(2)
        if idx > 47:
            return []
        if key == "name":
            return [f"Objeto-Nombre.{idx}"]
        if key == "quantity":
            return [f"Objeto-Cantidad.{idx}", f"Objeto-Puesto.{idx}", f"Objeto-Mochila.{idx}", f"Objeto-Bolsa.{idx}", "Total-Cantidad"]
        if key == "weight_kg":
            return [f"Objeto-Nombre.{idx}", "Total-Pesos-Puesto", "Total-Pesos-Equipados", "Total-Pesos-Mochila", "Total-Pesos-Bolsa"]
        return [f"Objeto-Puesto.{idx}", f"Objeto-Mochila.{idx}", f"Objeto-Bolsa.{idx}"]

    if web_path == "inventory.other_possessions":
        return ["Otro-1"]

    m_mount = re.match(r"inventory\.mounts\[(\d+)\]", web_path)
    if m_mount:
        idx = int(m_mount.group(1)) + 1
        if 1 <= idx <= 19:
            return [f"Montura.{idx}"]
        return []

    m_gem = re.match(r"inventory\.gems\[(\d+)\]", web_path)
    if m_gem:
        idx = int(m_gem.group(1)) + 1
        if 1 <= idx <= 7:
            return [f"Gema.{idx}"]
        return []

    m_loan = re.match(r"inventory\.loaned\[(\d+)\]\.(to|name|quantity|due|notes)$", web_path)
    if m_loan:
        idx = int(m_loan.group(1)) + 1
        key = m_loan.group(2)
        if not (1 <= idx <= 6):
            return []
        if key in {"to", "name"}:
            return [f"Prestad-Depositado-Recibido-Lugar.{idx}"]
        if key == "quantity":
            return [f"Prestad-Depositado-Recibido-Cantidad.{idx}"]
        return [f"Prestad-Depositado-Recibido-Momento.{idx}"]

    if web_path == "languages":
        return ["Idioma.1", "Idioma.2", "Idioma.3", "Idioma.4"]
    m_lang = re.match(r"languages\[(\d+)\]$", web_path)
    if m_lang:
        idx = int(m_lang.group(1)) + 1
        targets: list[str] = []
        if idx <= 4:
            targets.append(f"Idioma.{idx}")
        return targets

    if web_path == "appearance.age":
        return ["Dato-Personaje.Edad"]
    if web_path == "appearance.size":
        return ["Tamano", "Dato-Personaje.Tamano"]
    if web_path == "appearance.height":
        return ["Dato-Personaje.Altura"]
    if web_path == "appearance.weight":
        return ["Dato-Personaje.Peso"]
    if web_path == "appearance.eyes":
        return ["Dato-Personaje.Ojos"]
    if web_path == "appearance.skin":
        return ["Dato-Personaje.Piel"]
    if web_path == "appearance.hair":
        return ["Dato-Personaje.Pelo"]
    if web_path == "appearance.gender":
        return ["Dato-Personaje.Genero"]

    if web_path == "background_details.deity":
        return ["Dato-Personaje.Deidad-Dominio"]
    if web_path == "background_details.name":
        return ["Trasfondo"]
    if web_path == "background_details.deity_description":
        return ["Dato-Personaje.Descripcion-Deidad"]
    if web_path == "background_details.birth_place":
        return ["Dato-Personaje-Lugar-Fecha-Nacimiento"]
    if web_path == "background_details.birth_date":
        return ["Dato-Personaje-Lugar-Fecha-Nacimiento"]
    if web_path == "background_details.description":
        return ["Dato-Personaje.Trasfondo-Otros-1"]

    m_bg_multi = re.match(r"background_details\.(personality_traits|ideals|bonds|flaws)\[(\d+)\]", web_path)
    if m_bg_multi:
        kind = m_bg_multi.group(1)
        idx = int(m_bg_multi.group(2)) + 1
        if idx > 3:
            return []
        prefix = {
            "personality_traits": "Dato-Personaje.Rasgo-Personalidad",
            "ideals": "Dato-Personaje.Ideal",
            "bonds": "Dato-Personaje.Vinculo",
            "flaws": "Dato-Personaje.Defecto",
        }[kind]
        return [f"{prefix}-{idx}"]

    if web_path == "notes.allies":
        return ["Dato-Personaje.Amigo-Aliado-1", "Dato-Personaje.Amigo-Aliado-2", "Dato-Personaje.Amigo-Aliado-3"]
    if web_path == "notes.enemies":
        return ["Dato-Personaje.Enemigo-1", "Dato-Personaje.Enemigo-2", "Dato-Personaje.Enemigo-3"]
    if web_path == "notes.physical_description":
        return ["Dato-Personaje.Apariencia-1", "Dato-Personaje.Apariencia-2", "Dato-Personaje.Apariencia-3"]
    if web_path == "appearance.summary":
        return ["Dato-Personaje.Apariencia-1", "Dato-Personaje.Apariencia-2", "Dato-Personaje.Apariencia-3"]
    if web_path == "notes.general":
        return [f"Nota.{i}" for i in range(1, 17)]
    if web_path == "notes.additional_notes":
        return [f"Nota.{i}" for i in range(1, 17)]
    if web_path == "notes.organizations":
        return [f"Nota.{i}" for i in range(1, 17)]
    if web_path == "notes.backstory":
        return [f"Nota.{i}" for i in range(1, 17)]
    if web_path == "notes.other_notes":
        return [f"Dato-Personaje.Trasfondo-Otros-{i}" for i in range(2, 8)]
    if web_path == "notes.other_possessions":
        return ["Otro-1"]

    if web_path == "spellcasting.spellcasting_ability":
        return ["Caracteristica-Clase-Lanzador-Conjuro"]
    if web_path == "spellcasting.spell_attack_bonus":
        return ["Aptitud-Magica"]
    if web_path == "spellcasting.spell_save_dc":
        return ["CD-Salvacion-Conjuros"]

    if web_path == "spellcasting.sorcery_points_max":
        return ["Puntos-Hechiceria-Max"]
    if web_path == "spellcasting.sorcery_points_used":
        return ["Puntos-Hechiceria-Gastados"]

    m_slot_total = re.match(r"spellcasting\.spell_slots\.level_(\d+)\.total$", web_path)
    if m_slot_total:
        lvl = int(m_slot_total.group(1))
        if 1 <= lvl <= 9:
            return [f"Total-Espacios-Conjuro.{lvl}"]

    m_slot_used = re.match(r"spellcasting\.spell_slots\.level_(\d+)\.used$", web_path)
    if m_slot_used:
        lvl = int(m_slot_used.group(1))
        checks = {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        if 1 <= lvl <= 9:
            return [f"Check-Espacio-Conjuro-Gastado-{lvl}.{i}" for i in range(1, checks[lvl] + 1)]

    m_slot_pip = re.match(r"spellcasting\.spell_slots\.level_(\d+)\.pip_states\[(\d+)\]$", web_path)
    if m_slot_pip:
        lvl = int(m_slot_pip.group(1))
        idx = int(m_slot_pip.group(2)) + 1
        checks = {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        if 1 <= lvl <= 9 and 1 <= idx <= checks[lvl]:
            return [f"Check-Espacio-Conjuro-Gastado-{lvl}.{idx}"]
        return []

    m_cantrip = re.match(r"spellcasting\.spells\.cantrips\[(\d+)\]\.name$", web_path)
    if m_cantrip:
        idx = int(m_cantrip.group(1)) + 1
        if idx <= 7:
            return [f"Nombre-Conjuro-Nivel-0.{idx}", "Conjuros-Concidos"]
        return ["Conjuros-Concidos"]

    m_spell_name = re.match(r"spellcasting\.spells\.level_(\d+)\[(\d+)\]\.name$", web_path)
    if m_spell_name:
        lvl = int(m_spell_name.group(1))
        idx = int(m_spell_name.group(2)) + 1
        targets = ["Conjuros-Concidos"]
        if 1 <= lvl <= 9:
            targets.append(f"Nombre-Conjuro-Nivel-{lvl}.{idx}")
        return targets

    m_spell_prepared = re.match(r"spellcasting\.spells\.level_(\d+)\[(\d+)\]\.prepared$", web_path)
    if m_spell_prepared:
        lvl = int(m_spell_prepared.group(1))
        idx = int(m_spell_prepared.group(2)) + 1
        targets = ["Conjuros-Preparados"]
        if 1 <= lvl <= 9:
            targets.append(f"Check-Preparado-Conjuro-Nivel-{lvl}.{idx}")
        return targets

    if web_path.startswith("resources."):
        m_res = re.match(r"resources\.([^\.]+)\.(name|note|recharge|trigger|max|current|pip_states\[(\d+)\])$", web_path)
        if not m_res:
            return []
        field = m_res.group(2)
        pip_idx = m_res.group(3)
        # Sin indice estable en flatten, permitimos trazabilidad a todo el bloque.
        targets = [f"Habilidades-Combate.{i}" for i in range(1, 10)]
        if field == "recharge":
            return [f"Check-Refresco-Habilidades-Combate.{i}" for i in range(1, 10)]
        if field == "trigger":
            return [f"Check-Refresco-Habilidades-Combate.{i}" for i in range(1, 10)]
        if field in {"max", "current"}:
            return [f"Check-Contador-Habilidades-Combate.{i}.{j}" for i in range(1, 10) for j in range(1, 6)]
        if pip_idx is not None:
            p = int(pip_idx) + 1
            if 1 <= p <= 5:
                return [f"Check-Contador-Habilidades-Combate.{i}.{p}" for i in range(1, 10)]
            return []
        return targets

    return []


def normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower().lstrip("/")
    return text not in {"", "off", "false", "0", "none", "null"}


def normalize_soft(text: object) -> str:
    val = str(text or "").strip().lower()
    val = re.sub(r"\s*([+\-])\s*", r"\1", val)
    val = re.sub(r"\s+", " ", val)
    return val


def compare_field(field: str, expected: object, actual: object) -> tuple[str, str]:
    if isinstance(expected, bool):
        exp_bool = bool(expected)
        act_bool = normalize_bool(actual)
        return ("exact", "") if exp_bool == act_bool else ("mismatch", "checkbox")

    exp = str(expected or "").strip()
    act = str(actual or "").strip()

    if exp == act:
        return ("exact", "")

    if exp.startswith("+") and exp[1:] == act:
        return ("heuristic", "sign")
    if act.startswith("+") and act[1:] == exp:
        return ("heuristic", "sign")
    if normalize_soft(exp) == normalize_soft(act):
        return ("heuristic", "spacing")

    return ("mismatch", "value")


def build_traceability(data: dict) -> tuple[list[dict[str, object]], dict[str, list[str]]]:
    flat = flatten_json(data)
    records: list[dict[str, object]] = []
    pdf_to_web: dict[str, list[str]] = {}

    for web_path, value in sorted(flat.items()):
        targets = map_web_path_to_pdf(web_path)
        status = "mapped" if targets else "sin_destino_pdf"

        records.append(
            {
                "web_path": web_path,
                "status": status,
                "pdf_fields": targets,
                "value_preview": str(value)[:120],
            }
        )

        for target in targets:
            pdf_to_web.setdefault(target, []).append(web_path)

    return records, pdf_to_web


def run_iteration(iteration: int, data: dict, json_path: Path, template_path: Path, out_dir: Path) -> dict[str, object]:
    iter_tag = f"iter_{iteration:02d}"
    pdf_path = out_dir / f"{iter_tag}_personaje.pdf"
    fields_path = out_dir / f"{iter_tag}_pdf_fields.json"
    map_path = out_dir / f"{iter_tag}_web_to_pdf_map.json"
    report_path = out_dir / f"{iter_tag}_reporte.json"
    csv_path = out_dir / f"{iter_tag}_discrepancias.csv"

    generate(json_path, template_path, pdf_path, verbose=False, verify=False)

    extracted = extract_pdf_fields(pdf_path)
    fields_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")

    trace, pdf_to_web = build_traceability(data)
    map_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")

    expected = build_field_map(data)
    available_pdf_fields = set(extracted.keys())
    available_pdf_fields_canon = {_canonical_name(name) for name in available_pdf_fields}
    canon_to_real: dict[str, str] = {}
    for real_name in sorted(available_pdf_fields):
        canon_to_real.setdefault(_canonical_name(real_name), real_name)

    exact = 0
    heuristic = 0
    mismatch = 0
    no_template = 0

    results: list[dict[str, object]] = []

    for field_name in sorted(expected.keys()):
        exp_val = expected[field_name]
        src_paths = sorted(set(pdf_to_web.get(field_name, [])))

        real_name = field_name if field_name in available_pdf_fields else canon_to_real.get(_canonical_name(field_name))

        if real_name is None and _canonical_name(field_name) not in available_pdf_fields_canon:
            no_template += 1
            results.append(
                {
                    "field": field_name,
                    "status": "sin_campo_template",
                    "severity": "low",
                    "expected": exp_val,
                    "actual": None,
                    "note": "No existe widget con ese nombre en la plantilla PDF",
                    "source_paths": src_paths,
                }
            )
            continue

        act_val = extracted.get(real_name or field_name, {}).get("value", "")
        status, note = compare_field(field_name, exp_val, act_val)

        if status == "exact":
            exact += 1
        elif status == "heuristic":
            heuristic += 1
        else:
            mismatch += 1

        severity = "high" if (status == "mismatch" and field_name in CORE_FIELDS) else "medium"

        results.append(
            {
                "field": field_name,
                "status": status,
                "severity": severity if status == "mismatch" else "info",
                "expected": exp_val,
                "actual": act_val,
                "note": note,
                "source_paths": src_paths,
            }
        )

    unmapped_paths = [r["web_path"] for r in trace if r["status"] == "sin_destino_pdf"]

    summary = {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "expected_fields": len(expected),
        "template_fields": len(available_pdf_fields),
        "exact": exact,
        "heuristic": heuristic,
        "mismatch": mismatch,
        "sin_campo_template": no_template,
        "web_paths_total": len(trace),
        "web_paths_sin_destino_pdf": len(unmapped_paths),
    }

    report = {
        "summary": summary,
        "mismatches": [r for r in results if r["status"] == "mismatch"],
        "heuristic_matches": [r for r in results if r["status"] == "heuristic"],
        "sin_campo_template": [r for r in results if r["status"] == "sin_campo_template"],
        "results": results,
        "web_paths_sin_destino_pdf": unmapped_paths,
        "artifacts": {
            "pdf": str(pdf_path),
            "pdf_fields_json": str(fields_path),
            "web_to_pdf_map_json": str(map_path),
            "csv": str(csv_path),
        },
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "iteration",
                "field",
                "status",
                "severity",
                "expected",
                "actual",
                "source_paths",
                "note",
            ],
        )
        writer.writeheader()
        for row in results:
            if row["status"] in {"mismatch", "sin_campo_template", "heuristic"}:
                writer.writerow(
                    {
                        "iteration": iteration,
                        "field": row["field"],
                        "status": row["status"],
                        "severity": row["severity"],
                        "expected": row["expected"],
                        "actual": row["actual"],
                        "source_paths": " | ".join(row["source_paths"]),
                        "note": row["note"],
                    }
                )

    print(f"[{iter_tag}] PDF: {pdf_path.name}")
    print(
        f"[{iter_tag}] exact={exact} heuristic={heuristic} mismatch={mismatch} "
        f"sin_campo_template={no_template} sin_destino_pdf={len(unmapped_paths)}"
    )

    return {
        "report_path": str(report_path),
        "csv_path": str(csv_path),
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida JSON web vs PDF generado")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="JSON fuente")
    parser.add_argument("--template", type=Path, default=TEMPLATE_PATH, help="Plantilla PDF")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Carpeta de artefactos")
    parser.add_argument("--iterations", type=int, default=2, help="Numero de iteraciones")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(args.json.read_text(encoding="utf-8"))

    all_runs: list[dict[str, object]] = []
    for i in range(1, max(1, args.iterations) + 1):
        all_runs.append(run_iteration(i, data, args.json, args.template, args.out_dir))

    final_path = args.out_dir / "resumen_iteraciones.json"
    final_path.write_text(json.dumps(all_runs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumen global: {final_path}")


if __name__ == "__main__":
    main()
