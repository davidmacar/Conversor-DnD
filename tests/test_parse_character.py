"""
Tests para el parser de Nivel20 (parse_character.py).

Estos tests validan que el parser genere JSON compatible con el editor web.
Para ejecutar:
    pytest tests/test_parse_character.py -v

Requiere: pytest, beautifulsoup4
"""

import sys
from pathlib import Path

# Bootstrap path para importar scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup

from scripts.parse_character import (
    parse_inventory,
    parse_background_details,
    parse_proficiencies,
    parse_notes,
    parse_combat,
    parse_basic_info,
    parse_appearance,
)


# ── HTML de muestra para tests ────────────────────────────────────────────

MINIMAL_HTML = """
<html><body>
<div id="panel-items">
    <div class="accordion-wrapper">
        <div class="accordion-header">
            <span class="accordion-title">Transportado 8</span>
            <span class="accordion-value">8</span>
        </div>
    </div>
    <div class="accordion-wrapper">
        <div class="accordion-header">
            <a data-toggle="collapse">
                <span class="accordion-title">Daga</span>
            </a>
            <span class="accordion-value">5</span>
        </div>
        <div class="card-body">
            <div class="card-text"><p>Arma sencilla</p></div>
        </div>
    </div>
    <div class="accordion-wrapper">
        <div class="accordion-header">
            <a data-toggle="collapse">
                <span class="accordion-title">Antorcha</span>
            </a>
        </div>
        <div class="card-body">
            <div class="card-text"><p>Iluminación</p></div>
        </div>
    </div>
    <div class="accordion-wrapper">
        <div class="accordion-header">
            <span class="accordion-title">Otros 3</span>
            <span class="accordion-value">3</span>
        </div>
    </div>
    <div class="accordion-wrapper">
        <div class="accordion-header">
            <a data-toggle="collapse">
                <span class="accordion-title">Herramientas de Calígrafo</span>
            </a>
        </div>
        <div class="card-body">
            <div class="card-text"><p>Equipo de aventuras</p></div>
        </div>
    </div>
</div>
</body></html>
"""

BACKGROUND_HTML = """
<html><body>
<div id="panel-background">
    <h4>Trasfondo: Vagabundo</h4>
    <p>Un vagabundo que ha recorrido el mundo.</p>
    <p><strong>Edad.</strong> 25</p>
    <p><strong>Género.</strong> Masculino</p>
    <p><strong>Alineamiento.</strong> Caótico bueno</p>
    <p><strong>Competencia con habilidades del trasfondo.</strong> Supervivencia y Naturaleza</p>
    <h5>Rasgos de personalidad</h5>
    <p>Siempre tengo un plan para cuando las cosas salgan mal.</p>
    <h5>Ideales</h5>
    <p>La libertad es el bien más preciado.</p>
    <h5>Vínculos</h5>
    <p>Debo proteger a mi hermano menor.</p>
    <h5>Defectos</h5>
    <p>Tengo un problema con la autoridad.</p>
</div>
</body></html>
"""

PROFICIENCIES_HTML = """
<html><body>
<div class="card">
    <div class="card-header">Otras competencias</div>
    <ul>
        <li>Armadura ligera, Armadura media, Escudo</li>
        <li>Armas sencillas, Armas marciales</li>
        <li>Herramienta de ladrón</li>
    </ul>
</div>
</body></html>
"""

COMBAT_HTML = """
<html><body>
<span class="distance-label" data-unit="feet" data-value="30">30 pies</span>
</body></html>
"""

CAMPAIGN_HTML = """
<html><body>
<h1 class="content-header-title">WebOns</h1>
<div class="character-desc">Humano Monje 2</div>
<a href="/campaigns/123-mi-campana">Mi Campaña</a>
<div id="panel-background">
    <h4>Trasfondo: Vagabundo</h4>
</div>
</body></html>
"""


# ── Tests ─────────────────────────────────────────────────────────────────


class TestParseInventory:
    def test_detects_location_groups_with_counter(self):
        soup = BeautifulSoup(MINIMAL_HTML, "html.parser")
        result = parse_inventory(soup)
        items = {it["name"]: it for it in result["items"]}

        assert "Daga" in items
        assert items["Daga"]["qty_backpack"] == 5, "Daga debe tener qty_backpack=5"
        assert items["Daga"]["qty_bag"] == 0
        assert items["Daga"]["quantity"] == 5

    def test_items_without_quantity_default_to_one(self):
        soup = BeautifulSoup(MINIMAL_HTML, "html.parser")
        result = parse_inventory(soup)
        items = {it["name"]: it for it in result["items"]}

        assert "Antorcha" in items
        assert items["Antorcha"]["qty_backpack"] == 1
        assert items["Antorcha"]["quantity"] == 1

    def test_others_location(self):
        soup = BeautifulSoup(MINIMAL_HTML, "html.parser")
        result = parse_inventory(soup)
        items = {it["name"]: it for it in result["items"]}

        assert "Herramientas de Calígrafo" in items
        assert items["Herramientas de Calígrafo"]["qty_bag"] == 1
        assert items["Herramientas de Calígrafo"]["qty_backpack"] == 0


class TestParseBackgroundDetails:
    def test_returns_strings_not_arrays(self):
        soup = BeautifulSoup(BACKGROUND_HTML, "html.parser")
        result = parse_background_details(soup)

        assert isinstance(result["personality_traits"], str)
        assert isinstance(result["ideals"], str)
        assert isinstance(result["bonds"], str)
        assert isinstance(result["flaws"], str)

    def test_extracts_content_from_headers(self):
        soup = BeautifulSoup(BACKGROUND_HTML, "html.parser")
        result = parse_background_details(soup)

        assert "plan para cuando las cosas salgan mal" in result["personality_traits"]
        assert "libertad" in result["ideals"]
        assert "hermano menor" in result["bonds"]
        assert "autoridad" in result["flaws"]

    def test_background_name_and_description(self):
        soup = BeautifulSoup(BACKGROUND_HTML, "html.parser")
        result = parse_background_details(soup)

        assert result["name"] == "Vagabundo"
        assert "vagabundo" in result["description"].lower()


class TestParseProficiencies:
    def test_generates_editor_format(self):
        soup = BeautifulSoup(PROFICIENCIES_HTML, "html.parser")
        result = parse_proficiencies(soup)

        assert "armor_flags" in result
        assert result["armor_flags"]["light"] is True
        assert result["armor_flags"]["medium"] is True
        assert result["armor_flags"]["shield"] is True
        assert result["armor_flags"]["heavy"] is False

        assert result["simple_weapons"] is True
        assert result["martial_weapons"] is True

        assert isinstance(result["other_competencies"], list)
        assert any("ladrón" in c for c in result["other_competencies"])

    def test_preserves_legacy_fields(self):
        soup = BeautifulSoup(PROFICIENCIES_HTML, "html.parser")
        result = parse_proficiencies(soup)

        assert "armor" in result
        assert "weapons" in result
        assert "tools" in result
        assert "raw" in result


class TestParseNotes:
    def test_has_all_expected_fields(self):
        result = parse_notes(None, {}, {})

        expected = [
            "other_possessions",
            "backstory",
            "organizations",
            "allies",
            "enemies",
            "additional_notes",
            "general",
            "physical_description",
            "other_notes",
        ]
        for key in expected:
            assert key in result, f"Falta clave: {key}"
            assert isinstance(result[key], str)


class TestParseCombat:
    def test_speed_fields_default_to_zero(self):
        soup = BeautifulSoup(COMBAT_HTML, "html.parser")
        result = parse_combat(soup)

        assert result["speed"]["swim_meters"] == 0
        assert result["speed"]["fly_meters"] == 0
        assert result["speed"]["climb_meters"] == 0
        assert result["speed"]["walking_meters"] == 9  # 30 pies * 0.3


class TestParseBasicInfo:
    def test_extracts_campaign(self):
        soup = BeautifulSoup(CAMPAIGN_HTML, "html.parser")
        result = parse_basic_info(soup)

        assert result["campaign"] == "Mi Campaña"

    def test_name_and_classes(self):
        soup = BeautifulSoup(CAMPAIGN_HTML, "html.parser")
        result = parse_basic_info(soup)

        assert result["name"] == "WebOns"
        assert len(result["classes"]) == 1
        assert result["classes"][0]["name"] == "Monje"
        assert result["classes"][0]["level"] == 2


class TestParseAppearance:
    def test_no_none_values(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        result = parse_appearance(soup)

        for key in ["age", "height", "weight", "eyes", "skin", "hair", "gender"]:
            assert result[key] is not None, f"{key} no debe ser None"
            assert isinstance(result[key], str), f"{key} debe ser string"
