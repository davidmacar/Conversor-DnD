#!/usr/bin/env python3
"""Rebuild index.html sections"""
import os

filepath = r'c:\Users\david\Desktop\DnD\Conversor DnD\editor\templates\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Use partial marker to avoid encoding issues
MAIN_START_PARTIAL = 'MAIN CONTENT'
MAIN_END   = '  </main><!-- /.main-content -->'

# Find full line containing MAIN CONTENT marker
import re
m = re.search(r'  <!-- [^\n]+ MAIN CONTENT [^\n]+ -->\n  <main class="main-content">', content)
if not m:
    raise ValueError("Could not find MAIN CONTENT marker")
idx_start = m.start()
idx_end   = content.index(MAIN_END) + len(MAIN_END)
print(f"Start: {idx_start}, End: {idx_end}, file len: {len(content)}")

NEW_MAIN = r"""  <!-- ─── MAIN CONTENT ────────────────────────────────── -->
  <main class="main-content">

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 1: IDENTIDAD
    ══════════════════════════════════════════════════ -->
    <section id="identidad" class="section-block" data-section="identidad">
      <div class="section-header">
        <div class="section-title">✦ Identidad del Personaje ✦</div>
      </div>

      <!-- Datos Básicos -->
      <div class="dnd-card id-card">
        <div class="id-hero-layout">
          <div class="id-portrait-col">
            <div class="id-portrait"
                 :class="{'portrait-zoomable': character.basic_info?.portrait_url}"
                 @click="character.basic_info?.portrait_url && (portraitExpanded = true)">
              <template x-if="character.basic_info?.portrait_url">
                <img :src="character.basic_info.portrait_url" :alt="character.basic_info.name">
              </template>
              <template x-if="!character.basic_info?.portrait_url">
                <span>🧙</span>
              </template>
            </div>
            <input type="text" x-model="character.basic_info.portrait_url"
                   class="id-portrait-url" placeholder="URL imagen…">
          </div>
          <div class="id-fields-col">
            <div class="char-field">
              <label>Nombre del Personaje</label>
              <input type="text" x-model="character.basic_info.name" class="id-name-input">
            </div>
            <template x-for="(cls, ci) in (character.basic_info?.classes || [])" :key="ci">
              <div class="id-class-row">
                <div class="char-field">
                  <label>Clase</label>
                  <input type="text" x-model="cls.name">
                </div>
                <div class="char-field">
                  <label>Subclase</label>
                  <input type="text" x-model="cls.subclass" placeholder="—">
                </div>
                <div class="char-field">
                  <label>Nivel</label>
                  <input type="number" x-model.number="cls.level" min="1" max="20"
                         @change="updateAll()">
                </div>
              </div>
            </template>
            <div class="field-row-3">
              <div class="field-group">
                <label class="field-label">Especie</label>
                <input type="text" x-model="character.basic_info.species">
              </div>
              <div class="field-group">
                <label class="field-label">XP Actual</label>
                <input type="number" x-model.number="character.basic_info.experience_points" min="0">
              </div>
              <div class="field-group">
                <label class="field-label">XP Siguiente Nivel</label>
                <input type="number" x-model.number="character.basic_info.next_level_xp" min="0">
              </div>
            </div>
            <div class="field-row-3">
              <div class="field-group">
                <label class="field-label">Nombre del Jugador</label>
                <input type="text" x-model="character.basic_info.player_name">
              </div>
              <div class="field-group">
                <label class="field-label">Visión</label>
                <input type="text" x-model="character.basic_info.vision">
              </div>
              <div class="field-group">
                <label class="field-label">Fecha Creación</label>
                <input type="text" x-model="character.basic_info.creation_date" placeholder="DD/MM/AAAA">
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Apariencia Física -->
      <div class="dnd-card">
        <div class="dnd-card-header">Apariencia Física</div>
        <div class="field-row-4">
          <div class="field-group">
            <label class="field-label">Edad</label>
            <input type="text" x-model="character.appearance.age">
          </div>
          <div class="field-group">
            <label class="field-label">Altura</label>
            <input type="text" x-model="character.appearance.height">
          </div>
          <div class="field-group">
            <label class="field-label">Peso</label>
            <input type="text" x-model="character.appearance.weight">
          </div>
          <div class="field-group">
            <label class="field-label">Género</label>
            <input type="text" x-model="character.appearance.gender">
          </div>
        </div>
        <div class="field-row-4">
          <div class="field-group">
            <label class="field-label">Tamaño</label>
            <input type="text" x-model="character.appearance.size">
          </div>
          <div class="field-group">
            <label class="field-label">Ojos</label>
            <input type="text" x-model="character.appearance.eyes">
          </div>
          <div class="field-group">
            <label class="field-label">Piel</label>
            <input type="text" x-model="character.appearance.skin">
          </div>
          <div class="field-group">
            <label class="field-label">Pelo</label>
            <input type="text" x-model="character.appearance.hair">
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Descripción / Resumen de apariencia</label>
          <textarea x-model="character.appearance.summary" rows="2" class="notes-textarea"></textarea>
        </div>
      </div>

      <!-- Trasfondo -->
      <div class="dnd-card">
        <div class="dnd-card-header">Trasfondo</div>
        <div class="field-row-3">
          <div class="field-group">
            <label class="field-label">Nombre del Trasfondo</label>
            <input type="text" x-model="character.basic_info.background">
          </div>
          <div class="field-group">
            <label class="field-label">Lugar de Nacimiento</label>
            <input type="text" x-model="character.background_details.birth_place">
          </div>
          <div class="field-group">
            <label class="field-label">Fecha de Nacimiento</label>
            <input type="text" x-model="character.background_details.birth_date" placeholder="DD/MM/AAAA">
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Alineamiento</label>
          <input type="text" x-model="character.basic_info.alignment" style="max-width:220px">
        </div>
        <div class="trait-group">
          <div class="trait-header">
            <span>Rasgos de Personalidad</span>
            <button class="btn-add-small" @click="character.background_details.personality_traits.push('')">+</button>
          </div>
          <template x-for="(t, i) in character.background_details.personality_traits" :key="i">
            <div class="trait-row">
              <input type="text" x-model="character.background_details.personality_traits[i]">
              <button class="btn-remove" @click="character.background_details.personality_traits.splice(i,1)">×</button>
            </div>
          </template>
        </div>
        <div class="field-row-2">
          <div class="trait-group">
            <div class="trait-header">
              <span>Ideales</span>
              <button class="btn-add-small" @click="character.background_details.ideals.push('')">+</button>
            </div>
            <template x-for="(t, i) in character.background_details.ideals" :key="i">
              <div class="trait-row">
                <input type="text" x-model="character.background_details.ideals[i]">
                <button class="btn-remove" @click="character.background_details.ideals.splice(i,1)">×</button>
              </div>
            </template>
          </div>
          <div class="trait-group">
            <div class="trait-header">
              <span>Vínculos</span>
              <button class="btn-add-small" @click="character.background_details.bonds.push('')">+</button>
            </div>
            <template x-for="(t, i) in character.background_details.bonds" :key="i">
              <div class="trait-row">
                <input type="text" x-model="character.background_details.bonds[i]">
                <button class="btn-remove" @click="character.background_details.bonds.splice(i,1)">×</button>
              </div>
            </template>
          </div>
        </div>
        <div class="trait-group">
          <div class="trait-header">
            <span>Defectos</span>
            <button class="btn-add-small" @click="character.background_details.flaws.push('')">+</button>
          </div>
          <template x-for="(t, i) in character.background_details.flaws" :key="i">
            <div class="trait-row">
              <input type="text" x-model="character.background_details.flaws[i]">
              <button class="btn-remove" @click="character.background_details.flaws.splice(i,1)">×</button>
            </div>
          </template>
        </div>
        <div class="field-row-2">
          <div class="field-group">
            <label class="field-label">Amigos y Aliados</label>
            <textarea x-model="character.notes.allies" rows="3" class="notes-textarea"></textarea>
          </div>
          <div class="field-group">
            <label class="field-label">Enemigos</label>
            <textarea x-model="character.notes.enemies" rows="3" class="notes-textarea"></textarea>
          </div>
        </div>
        <div class="field-group">
          <label class="field-label">Historia del Personaje</label>
          <textarea x-model="character.notes.backstory" rows="5" class="notes-textarea"></textarea>
        </div>
      </div>

      <!-- Religión -->
      <div class="dnd-card">
        <div class="dnd-card-header">Religión</div>
        <div class="field-row-2">
          <div class="field-group">
            <label class="field-label">Deidad / Dominio</label>
            <input type="text" x-model="character.background_details.deity">
          </div>
          <div class="field-group">
            <label class="field-label">Descripción de la Deidad</label>
            <input type="text" x-model="character.background_details.deity_description">
          </div>
        </div>
      </div>

      <!-- Idiomas -->
      <div class="dnd-card">
        <div class="dnd-card-header">
          Idiomas
          <button class="btn-add-small ml-auto" @click="addLanguage()">+ Idioma</button>
        </div>
        <div class="lang-list">
          <template x-for="(lang, i) in character.languages" :key="i">
            <div class="trait-row">
              <input type="text" x-model="character.languages[i]" placeholder="Idioma">
              <button class="btn-remove" @click="removeLanguage(i)">×</button>
            </div>
          </template>
          <div class="empty-state" x-show="!character.languages?.length">Sin idiomas</div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 2: ATRIBUTOS
    ══════════════════════════════════════════════════ -->
    <section id="atributos" class="section-block" data-section="atributos">
      <div class="section-header">
        <div class="section-title">✦ Atributos & Habilidades ✦</div>
      </div>

      <!-- Estadísticas Generales -->
      <div class="dnd-card">
        <div class="dnd-card-header">Estadísticas Generales</div>
        <div class="stats-grid-5">
          <div class="stat-box">
            <div class="stat-label">Inspiración</div>
            <button class="insp-btn" :class="{active: character.basic_info?.inspiration}"
                    @click="character.basic_info.inspiration = !character.basic_info.inspiration">
              <span x-text="character.basic_info?.inspiration ? '★' : '☆'"></span>
            </button>
          </div>
          <div class="stat-box">
            <div class="stat-label">Perc. Pasiva</div>
            <div class="stat-value mod-pos" x-text="getPassivePerception()"></div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Bon. Competencia</div>
            <div class="stat-value">
              <input type="number" x-model.number="character.proficiency_bonus"
                     min="2" max="6" class="stat-input text-center">
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Iniciativa</div>
            <div class="stat-value">
              <input type="number" x-model.number="character.combat.initiative"
                     class="stat-input text-center">
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Clase de Armadura</div>
            <div class="stat-value">
              <input type="number" x-model.number="character.combat.armor_class"
                     min="0" class="stat-input text-center">
            </div>
          </div>
        </div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Puntuaciones de Habilidad</div>
        <div class="ability-groups-grid">
          <template x-for="[key, ab] in Object.entries(character.ability_scores || {})" :key="key">
            <div class="ability-group">
              <div class="ability-group-header">
                <div class="ability-score-big">
                  <input type="number" :value="ab.score"
                         @change="onAbilityInput(key, $event.target.value)"
                         min="1" max="30">
                  <span class="ab-label" x-text="abilityLabel(key)"></span>
                </div>
                <div>
                  <div style="font-size: calc(13px * var(--font-scale));color:var(--text-dim)" x-text="abilityName(key)"></div>
                </div>
                <div class="ability-mod-badge" :class="modColor(ab.modifier)"
                     x-text="formatMod(ab.modifier)"></div>
              </div>
              <div class="ability-group-body">
                <div class="ability-sv-row">
                  <input type="checkbox"
                         class="ui-checkbox ui-checkbox--circle"
                         :checked="!!character.saving_throws?.[key]?.proficient"
                         @change="toggleSTProficiency(key, $event.target.checked)"
                         title="Competencia en salvación"
                         aria-label="Competencia en salvación">
                  <span class="sv-label">Salvación</span>
                  <span class="sv-val" :class="modColor(character.saving_throws?.[key]?.total)"
                        x-text="formatMod(character.saving_throws?.[key]?.total)"></span>
                </div>
                <template x-for="[sk, skill] in Object.entries(character.skills || {}).filter(([,s]) => s.ability === key)" :key="sk">
                  <div class="skill-row">
                    <input type="checkbox"
                           class="ui-checkbox ui-checkbox--circle"
                           :checked="!!skill.proficient"
                           @change="toggleSkillProficiency(sk, $event.target.checked)"
                           title="Competencia"
                           aria-label="Competencia">
                    <input type="checkbox"
                           class="ui-checkbox ui-checkbox--circle ui-checkbox--expertise"
                           :checked="!!skill.expertise"
                           :disabled="!skill.proficient"
                           @change="toggleSkillExpertise(sk, $event.target.checked)"
                           :title="skill.proficient ? 'Pericia' : 'Requiere competencia'"
                           aria-label="Pericia">
                    <span class="skill-name" x-text="formatSkillName(sk)"></span>
                    <span class="skill-total" :class="modColor(skill.total)"
                          x-text="formatMod(skill.total)"></span>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Movimiento -->
      <div class="dnd-card">
        <div class="dnd-card-header">Movimiento</div>
        <div class="speed-grid">
          <div class="speed-cell">
            <label class="field-label">Base (m)</label>
            <input type="number" x-model.number="character.combat.speed.walking_meters" min="0">
          </div>
          <div class="speed-cell">
            <label class="field-label">Nadando (m)</label>
            <input type="number" x-model.number="character.combat.speed.swim_meters" min="0">
          </div>
          <div class="speed-cell">
            <label class="field-label">Volando (m)</label>
            <input type="number" x-model.number="character.combat.speed.fly_meters" min="0">
          </div>
          <div class="speed-cell">
            <label class="field-label">Trepando (m)</label>
            <input type="number" x-model.number="character.combat.speed.climb_meters" min="0">
          </div>
          <div class="speed-cell">
            <label class="field-label">Salto Long. (m)</label>
            <input type="number" x-model.number="character.combat.speed.jump_long" min="0">
          </div>
          <div class="speed-cell">
            <label class="field-label">Salto Alt. (m)</label>
            <input type="number" x-model.number="character.combat.speed.jump_high" min="0">
          </div>
        </div>
        <div class="field-group mt12">
          <label class="field-label">Sentidos y Movimiento Especiales</label>
          <input type="text" x-model="character.combat.speed.special_senses"
                 placeholder="Ej: Visión en la oscuridad 18m">
        </div>
        <div class="hp-extras-row mt12">
          <span class="field-label" style="min-width:fit-content">Agotamiento:</span>
          <div class="counter-pips counter-pips--exhaustion">
            <template x-for="n in [0,1,2,3,4,5,6,7,8,9,10]" :key="n">
              <div class="death-circle counter-pip counter-pip--exhaustion"
                   :class="{filled: character.combat.exhaustion >= n && n > 0}"
                   @click="character.combat.exhaustion = (character.combat.exhaustion === n ? n-1 : n)"
                   x-text="n"
                   style="cursor:pointer"></div>
            </template>
          </div>
          <span class="mod-zero" style="font-size: calc(13px * var(--font-scale))"
                x-text="`Nivel ${character.combat.exhaustion}`"></span>
        </div>
      </div>

      <!-- Puntos de Golpe -->
      <div class="dnd-card">
        <div class="dnd-card-header">Puntos de Golpe</div>
        <div class="hp-grid">
          <div class="hp-box hp-max">
            <div class="hp-label">Máximo</div>
            <input type="number" x-model.number="character.combat.hit_points.maximum"
                   class="hp-input" min="0">
          </div>
          <div class="hp-box hp-cur">
            <div class="hp-label">Actuales</div>
            <input type="number" x-model.number="character.combat.hit_points.current"
                   class="hp-input">
          </div>
          <div class="hp-box hp-tmp">
            <div class="hp-label">Temporales</div>
            <input type="number" x-model.number="character.combat.hit_points.temporary"
                   class="hp-input">
          </div>
        </div>
        <div class="field-row-2 mt12">
          <div class="field-group">
            <label class="field-label">Dados de Golpe</label>
            <div class="dice-row">
              <input type="number" x-model.number="character.combat.hit_dice.count"
                     min="1" style="width:54px" class="text-center">
              <span style="font-size: calc(16px * var(--font-scale));color:var(--text-dim)">×</span>
              <select x-model="character.combat.hit_dice.type">
                <template x-for="d in DICE_TYPES" :key="d">
                  <option :value="d" x-text="d"></option>
                </template>
              </select>
            </div>
          </div>
          <div class="field-group">
            <label class="field-label">Dados Gastados Hoy</label>
            <div class="hit-dice-used-pips counter-pips">
              <template x-for="i in hitDiceRange()" :key="i">
                <div class="counter-pip counter-pip--resource"
                     :class="{filled: character.combat.hit_dice.used > i}"
                     @click="toggleHitDieUsed(i)"></div>
              </template>
            </div>
          </div>
        </div>
        <div class="death-saves-row mt12">
          <div class="death-group">
            <div class="death-label">Tiradas de Muerte — Éxitos</div>
            <div class="death-circles counter-pips">
              <template x-for="n in [1,2,3]" :key="n">
                <div class="death-circle success counter-pip counter-pip--death-success"
                     :class="{filled: character.combat.death_saves.successes >= n}"
                     @click="character.combat.death_saves.successes = (character.combat.death_saves.successes === n ? n-1 : n)">
                </div>
              </template>
            </div>
          </div>
          <div class="death-group">
            <div class="death-label">Fracasos</div>
            <div class="death-circles counter-pips">
              <template x-for="n in [1,2,3]" :key="n">
                <div class="death-circle failure counter-pip counter-pip--death-failure"
                     :class="{filled: character.combat.death_saves.failures >= n}"
                     @click="character.combat.death_saves.failures = (character.combat.death_saves.failures === n ? n-1 : n)">
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Capacidad de Carga -->
      <div class="dnd-card">
        <div class="dnd-card-header">Capacidad de Carga</div>
        <div class="carry-capacity-grid">
          <div class="carry-box">
            <div class="carry-label">Cargado</div>
            <div class="carry-val" x-text="carryingCapacity().normal"></div>
            <div class="carry-unit">kg</div>
          </div>
          <div class="carry-box">
            <div class="carry-label">Muy Cargado</div>
            <div class="carry-val" x-text="carryingCapacity().overload"></div>
            <div class="carry-unit">kg</div>
          </div>
          <div class="carry-box">
            <div class="carry-label">Carga Máxima</div>
            <div class="carry-val" x-text="carryingCapacity().max"></div>
            <div class="carry-unit">kg</div>
          </div>
          <div class="carry-box">
            <div class="carry-label">Empujar / Arrastrar</div>
            <div class="carry-val" x-text="carryingCapacity().push"></div>
            <div class="carry-unit">kg</div>
          </div>
        </div>
      </div>

    </section>

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 3: COMBATE
    ══════════════════════════════════════════════════ -->
    <section id="combate" class="section-block" data-section="combate">
      <div class="section-header">
        <div class="section-title">✦ Combate ✦</div>
      </div>

      <!-- Protecciones -->
      <div class="dnd-card">
        <div class="dnd-card-header">
          Protecciones
          <button class="btn-add-small ml-auto" @click="addProtection()">+ Añadir</button>
        </div>
        <div class="row-head protection-head-row">
          <span>Nombre</span><span>Tipo</span><span>Bono CA</span><span>Equipado</span><span></span>
        </div>
        <template x-for="(prot, i) in character.combat.protections" :key="i">
          <div class="protection-row">
            <input type="text" x-model="prot.name" placeholder="Nombre">
            <input type="text" x-model="prot.type" placeholder="Tipo">
            <input type="number" x-model.number="prot.ac_bonus">
            <input type="checkbox" x-model="prot.equipped" title="Equipado" class="ui-checkbox cb-center">
            <button class="btn-remove" @click="removeProtection(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.combat.protections?.length">Sin protecciones</div>
      </div>

      <!-- Ventajas, Resistencias e Inmunidades -->
      <div class="dnd-card">
        <div class="dnd-card-header">
          Ventajas, Resistencias e Inmunidades
          <button class="btn-add-small ml-auto" @click="addAdvantage()">+ Añadir</button>
        </div>
        <template x-for="(adv, i) in character.combat.advantages_resistances" :key="i">
          <div class="advantage-row">
            <select x-model="adv.category">
              <option value="">— Categoría —</option>
              <option>Ventaja</option>
              <option>Resistencia</option>
              <option>Inmunidad</option>
              <option>Vulnerabilidad</option>
            </select>
            <input type="text" x-model="adv.description" placeholder="Descripción">
            <button class="btn-remove" @click="removeAdvantage(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.combat.advantages_resistances?.length">Sin ventajas / resistencias</div>
      </div>

      <!-- Ataques y Munición -->
      <div class="dnd-card">
        <div class="dnd-card-header">
          Ataques y Armas
          <button class="btn-add-small ml-auto" @click="addAttack()">+ Ataque</button>
        </div>
        <template x-for="(atk, i) in character.attacks" :key="i">
          <div class="attack-card">
            <div class="attack-top">
              <input type="text" x-model="atk.name" placeholder="Nombre del ataque" class="atk-name">
              <button class="btn-remove" @click="removeAttack(i)">×</button>
            </div>
            <div class="attack-row">
              <div class="field-group">
                <label class="field-label">Bono Ataque</label>
                <input type="number" x-model.number="atk.attack_bonus"
                       @input="syncDamageDisplay(atk)" style="width:70px">
              </div>
              <div class="field-group">
                <label class="field-label">Dados Daño</label>
                <div class="dice-row">
                  <input type="number" x-model.number="atk.damage_dice_count" min="1"
                         @input="syncDamageDisplay(atk)" style="width:46px">
                  <select x-model="atk.damage_dice_type" @change="syncDamageDisplay(atk)">
                    <template x-for="d in DICE_TYPES" :key="d">
                      <option :value="d" x-text="d"></option>
                    </template>
                  </select>
                  <span style="color:var(--text-dim)">+</span>
                  <input type="number" x-model.number="atk.damage_bonus"
                         @input="syncDamageDisplay(atk)" style="width:52px">
                </div>
              </div>
              <div class="field-group">
                <label class="field-label">Tipo Daño</label>
                <select x-model="atk.damage_type" @change="syncDamageDisplay(atk)">
                  <option value="">—</option>
                  <template x-for="dt in DAMAGE_TYPES" :key="dt">
                    <option :value="dt" x-text="dt"></option>
                  </template>
                </select>
              </div>
              <div class="field-group">
                <label class="field-label">Alcance</label>
                <input type="text" x-model="atk.range" placeholder="1.5m" style="width:80px">
              </div>
              <div class="field-group">
                <label class="field-label">Peso (kg)</label>
                <input type="number" x-model.number="atk.weight" min="0" step="0.1" style="width:70px">
              </div>
            </div>
            <div class="field-group">
              <label class="field-label">Notas</label>
              <input type="text" x-model="atk.notes" placeholder="Propiedades, condiciones…">
            </div>
            <div class="attack-summary">
              <span class="atk-roll-badge" x-text="atk.attack_roll || '1d20+0'"></span>
              <span class="dmg-display" x-text="atk.damage_display || atk.damage || '—'"></span>
            </div>
          </div>
        </template>
        <div class="empty-state" x-show="!character.attacks?.length">Sin ataques</div>

        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:16px;margin-bottom:8px">
          <span class="ammo-section-title">Munición</span>
          <button class="btn-add-small" @click="addAmmo()">+ Munición</button>
        </div>
        <template x-for="(ammo, i) in character.combat.ammunition" :key="i">
          <div class="ammo-row">
            <div class="ammo-header">
              <input type="text" x-model="ammo.name" placeholder="Tipo de munición">
              <span style="font-size: calc(12px * var(--font-scale));color:var(--text-dim)">Máx:</span>
              <input type="number" x-model.number="ammo.max" min="1" @change="onAmmoMaxChange(i)">
              <button class="btn-remove" @click="removeAmmo(i)">×</button>
            </div>
            <div class="ammo-pips counter-pips">
              <template x-for="j in ammoRange(i)" :key="j">
                <div class="ammo-pip counter-pip" :class="{filled: ammo.pip_states?.[j]}"
                     @click="toggleAmmoPip(i, j)"></div>
              </template>
            </div>
          </div>
        </template>
        <div class="empty-state" x-show="!character.combat.ammunition?.length">Sin munición</div>
      </div>

      <!-- Habilidades y Beneficios de Combate -->
      <div class="dnd-card">
        <div class="dnd-card-header">
          Habilidades y Beneficios de Combate
          <button class="btn-add-small ml-auto" @click="addResource()">+ Recurso</button>
        </div>
        <template x-for="[key, res] in resourceEntries()" :key="key">
          <div class="resource-card">
            <div class="res-title-row">
              <input type="text" x-model="res.name" class="res-name-input">
              <button class="btn-remove" @click="removeResource(key)">×</button>
            </div>
            <div class="res-data-row">
              <div class="res-max-field">
                <span class="res-field-label">Máximo</span>
                <input type="number" x-model.number="res.max" min="0" class="res-max-input"
                       @change="onResMaxChange(key)">
              </div>
              <div class="res-recharge-field">
                <span class="res-field-label">Descanso</span>
                <select x-model="res.recharge" class="res-recharge-select">
                  <option value="">—</option>
                  <option value="turno">Por Turno</option>
                  <option value="otro">Otro</option>
                </select>
              </div>
              <div class="res-counter-field">
                <span class="res-field-label">Contador</span>
                <div class="res-pips counter-pips">
                  <template x-for="i in resRange(key)" :key="i">
                    <div class="res-pip counter-pip counter-pip--resource" :class="{filled: res.pip_states?.[i]}"
                         @click="toggleResPip(key, i)"></div>
                  </template>
                </div>
              </div>
              <div class="res-notes-field">
                <span class="res-field-label">Notas</span>
                <input type="text" class="res-note-input" x-model="res.note" placeholder="Notas del recurso">
              </div>
            </div>
          </div>
        </template>
        <div class="empty-state" x-show="resourceEntries().length === 0">Sin recursos de clase</div>
      </div>

      <!-- Competencias -->
      <div class="dnd-card">
        <div class="dnd-card-header">Competencias</div>
        <div class="armor-flags-row">
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.armor_flags.light" class="ui-checkbox">
            Armadura Ligera
          </label>
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.armor_flags.medium" class="ui-checkbox">
            Armadura Media
          </label>
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.armor_flags.heavy" class="ui-checkbox">
            Armadura Pesada
          </label>
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.armor_flags.shield" class="ui-checkbox">
            Escudo
          </label>
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.simple_weapons" class="ui-checkbox">
            Armas Simples
          </label>
          <label class="armor-flag-check">
            <input type="checkbox" x-model="character.proficiencies.martial_weapons" class="ui-checkbox">
            Armas Marciales
          </label>
        </div>
        <div class="field-row-2 mt12">
          <div class="field-group">
            <label class="field-label">Otras (herramientas, instrumentos…)</label>
            <textarea :value="(character.proficiencies.tools||[]).join(', ')"
                      @input="character.proficiencies.tools = $event.target.value.split(',').map(s=>s.trim()).filter(Boolean)"
                      rows="3" class="notes-textarea"></textarea>
          </div>
          <div class="field-group">
            <label class="field-label">Armas (competencia adicional)</label>
            <textarea :value="(character.proficiencies.weapons||[]).join(', ')"
                      @input="character.proficiencies.weapons = $event.target.value.split(',').map(s=>s.trim()).filter(Boolean)"
                      rows="3" class="notes-textarea"></textarea>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 4: OTRAS HABILIDADES
    ══════════════════════════════════════════════════ -->
    <section id="habilidades" class="section-block" data-section="habilidades">
      <div class="section-header">
        <div class="section-title">✦ Otras Habilidades ✦</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Dotes
          <button class="btn-add-small ml-auto" @click="addFeature('feats')">+ Dote</button>
        </div>
        <template x-for="(feat, i) in character.features_and_traits.feats" :key="i">
          <div class="feature-block">
            <div class="feature-header-row">
              <input type="text" x-model="feat.name" placeholder="Nombre" class="feat-name">
              <button class="btn-remove" @click="removeFeature('feats', i)">×</button>
            </div>
            <textarea x-model="feat.description" placeholder="Descripción…" rows="2"
                      class="notes-textarea"></textarea>
          </div>
        </template>
        <div class="empty-state" x-show="!character.features_and_traits.feats?.length">Sin dotes</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Rasgos de Especie
          <button class="btn-add-small ml-auto" @click="addFeature('species')">+ Rasgo</button>
        </div>
        <template x-for="(ft, i) in character.features_and_traits.species" :key="i">
          <div class="feature-block">
            <div class="feature-header-row">
              <input type="text" x-model="ft.name" placeholder="Nombre" class="feat-name">
              <input type="text" x-model="ft.source" placeholder="Fuente"
                     style="width:110px;font-size: calc(12px * var(--font-scale))">
              <button class="btn-remove" @click="removeFeature('species', i)">×</button>
            </div>
            <textarea x-model="ft.description" placeholder="Descripción…" rows="2"
                      class="notes-textarea"></textarea>
          </div>
        </template>
        <div class="empty-state" x-show="!character.features_and_traits.species?.length">Sin rasgos de especie</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Rasgos de Clase
          <button class="btn-add-small ml-auto" @click="addFeature('class_features')">+ Rasgo</button>
        </div>
        <template x-for="(ft, i) in character.features_and_traits.class_features" :key="i">
          <div class="feature-block">
            <div class="feature-header-row">
              <input type="text" x-model="ft.name" placeholder="Nombre" class="feat-name">
              <input type="text" x-model="ft.source" placeholder="Fuente"
                     style="width:110px;font-size: calc(12px * var(--font-scale))">
              <button class="btn-remove" @click="removeFeature('class_features', i)">×</button>
            </div>
            <textarea x-model="ft.description" placeholder="Descripción…" rows="2"
                      class="notes-textarea"></textarea>
          </div>
        </template>
        <div class="empty-state" x-show="!character.features_and_traits.class_features?.length">Sin rasgos de clase</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Notas</div>
        <div class="field-group">
          <label class="field-label">Notas Generales</label>
          <textarea x-model="character.notes.general" rows="6" class="notes-textarea"
                    placeholder="Apuntes varios, efectos activos, recordatorios…"></textarea>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 5: CONJUROS
    ══════════════════════════════════════════════════ -->
    <section id="conjuros" class="section-block" data-section="conjuros">
      <div class="section-header">
        <div class="section-title">✦ Conjuros ✦</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Estadísticas de Lanzamiento</div>
        <div class="spellcasting-main-grid">
          <div class="spellcasting-main-row spellcasting-main-row--top">
            <div class="field-group spellcasting-field">
              <label class="field-label">Habilidad de Conjuración</label>
              <select x-model="character.spellcasting.spellcasting_ability">
                <option value="">—</option>
                <option value="intelligence">Inteligencia (INT)</option>
                <option value="wisdom">Sabiduría (SAB)</option>
                <option value="charisma">Carisma (CAR)</option>
              </select>
            </div>
            <div class="field-group spellcasting-field">
              <label class="field-label">CD Salvación</label>
              <input type="number" x-model.number="character.spellcasting.spell_save_dc">
            </div>
            <div class="field-group spellcasting-field">
              <label class="field-label">Bono de Ataque</label>
              <input type="number" x-model.number="character.spellcasting.spell_attack_bonus">
            </div>
            <div class="field-group spellcasting-field">
              <label class="field-label">Conjuros Preparados</label>
              <input type="number" x-model.number="character.spellcasting.spells_prepared" min="0">
            </div>
          </div>
          <div class="spellcasting-main-row spellcasting-main-row--bottom">
            <div class="field-group spellcasting-field">
              <label class="field-label">Conjuros Conocidos</label>
              <input type="number" x-model.number="character.spellcasting.spells_known" min="0">
            </div>
            <div class="field-group spellcasting-field">
              <label class="field-label">Puntos de Hechicería (Máximo)</label>
              <input type="number" x-model.number="character.spellcasting.sorcery_points_max"
                     min="0" @change="onSorceryMaxChange()">
            </div>
            <div class="field-group spellcasting-field spellcasting-counter-field">
              <label class="field-label">Contador</label>
              <div class="sorcery-pips sorcery-pips--inline counter-pips" x-show="character.spellcasting.sorcery_points_max > 0">
                <template x-for="j in sorceryRange()" :key="j">
                  <div class="sorcery-pip counter-pip counter-pip--sorcery"
                       :class="{used: !character.spellcasting.sorcery_pips?.[j]}"
                       @click="toggleSorceryPip(j)"></div>
                </template>
              </div>
              <div class="spellcasting-counter-empty" x-show="character.spellcasting.sorcery_points_max <= 0">—</div>
            </div>
          </div>
        </div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Espacios de Conjuros</div>
        <template x-for="level in [1,2,3,4,5,6,7,8,9]" :key="level">
          <div class="slot-row">
            <span class="slot-level-label" x-text="`Nv ${level}`"></span>
            <input type="number" class="slot-total-input"
                   :value="character.spellcasting.spell_slots?.[`level_${level}`]?.total || 0"
                   min="0" max="9"
                   @change="setSpellSlot(level, 'total', $event.target.value); onSlotTotalChange(level)">
            <div class="slot-pips counter-pips">
              <template x-for="j in slotRange(level)" :key="j">
                <div class="slot-pip counter-pip counter-pip--slot"
                     :class="{used: !character.spellcasting.spell_slots?.[`level_${level}`]?.pip_states?.[j]}"
                     @click="toggleSlotPip(level, j)"></div>
              </template>
            </div>
          </div>
        </template>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Lista de Conjuros</div>

        <div class="spell-level-block">
          <div class="spell-level-header">
            Trucos (Nivel 0)
            <button class="btn-add-small" @click="addSpell(0)">+</button>
          </div>
          <template x-for="(sp, i) in getSpells(0)" :key="i">
            <div class="spell-row">
              <input type="text" x-model="sp.name" placeholder="Nombre del truco" style="flex:2">
              <input type="text" x-model="sp.casting_time" placeholder="Lanzamiento" style="width:100px">
              <button class="btn-remove" @click="removeSpell(0, i)">×</button>
            </div>
          </template>
          <div class="empty-state" x-show="!getSpells(0).length">Sin trucos</div>
        </div>

        <template x-for="level in [1,2,3,4,5,6,7,8,9]" :key="level">
          <div class="spell-level-block">
            <div class="spell-level-header">
              <span x-text="`Nivel ${level}`"></span>
              <button class="btn-add-small" @click="addSpell(level)">+</button>
            </div>
            <template x-for="(sp, i) in getSpells(level)" :key="i">
              <div class="spell-row">
                <input type="checkbox" class="ui-checkbox ui-checkbox--circle"
                       x-model="sp.prepared" title="Preparado" aria-label="Conjuro preparado">
                <input type="text" x-model="sp.name" placeholder="Nombre" style="flex:2">
                <input type="text" x-model="sp.casting_time" placeholder="Tiempo" style="width:90px">
                <button class="btn-remove" @click="removeSpell(level, i)">×</button>
              </div>
            </template>
            <div class="empty-state" x-show="!getSpells(level).length"
                 x-text="`Sin conjuros de nivel ${level}`"></div>
          </div>
        </template>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════
         SECCIÓN 6: INVENTARIO
    ══════════════════════════════════════════════════ -->
    <section id="inventario" class="section-block" data-section="inventario">
      <div class="section-header">
        <div class="section-title">✦ Inventario ✦</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Equipo
          <button class="btn-add-small ml-auto" @click="addItem()">+ Objeto</button>
        </div>
        <div class="row-head inventory-head-row">
          <span>Nombre</span><span>Cant.</span><span class="inv-col-location">Ubicación</span><span class="inv-col-weight">Peso kg</span><span></span>
        </div>
        <template x-for="(item, i) in character.inventory.items" :key="i">
          <div class="inventory-item-row">
            <input type="text" x-model="item.name" placeholder="Nombre">
            <input type="number" x-model.number="item.quantity" min="1" class="text-center">
            <select x-model="item.location" class="item-location">
              <option value="">—</option>
              <option value="Equipado">Equipado</option>
              <option value="Transportado">Transportado</option>
              <option value="Otros">Bolsa/Otros</option>
            </select>
            <input type="number" x-model.number="item.weight_kg" min="0" step="0.1" placeholder="—" class="item-weight">
            <button class="btn-remove" @click="removeItem(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.inventory.items?.length">Sin objetos</div>
        <div class="weight-summary">
          <span>Equipado: <b x-text="weightByLocation('Equipado')"></b> kg</span>
          <span>Transportado: <b x-text="weightByLocation('Transportado')"></b> kg</span>
          <span>Otros: <b x-text="weightByLocation('Otros')"></b> kg</span>
          <span>Total: <b x-text="totalWeight()"></b> kg</span>
        </div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">Dinero</div>
        <div class="currency-grid">
          <div class="currency-box pp-box">
            <div class="currency-label">PP</div>
            <input type="number" x-model.number="character.inventory.currency.PP" min="0">
            <div class="currency-name">Platino</div>
          </div>
          <div class="currency-box gp-box">
            <div class="currency-label">PO</div>
            <input type="number" x-model.number="character.inventory.currency.GP" min="0">
            <div class="currency-name">Oro</div>
          </div>
          <div class="currency-box ep-box">
            <div class="currency-label">PE</div>
            <input type="number" x-model.number="character.inventory.currency.EP" min="0">
            <div class="currency-name">Electro</div>
          </div>
          <div class="currency-box sp-box">
            <div class="currency-label">PA</div>
            <input type="number" x-model.number="character.inventory.currency.SP" min="0">
            <div class="currency-name">Plata</div>
          </div>
          <div class="currency-box cp-box">
            <div class="currency-label">PC</div>
            <input type="number" x-model.number="character.inventory.currency.CP" min="0">
            <div class="currency-name">Cobre</div>
          </div>
        </div>
        <div class="field-group mt12">
          <label class="field-label">Otros valores / Notas</label>
          <textarea x-model="character.inventory.currency.other_notes" rows="2" class="notes-textarea"
                    placeholder="Joyas sin valorar, deudas, fondos de gremio…"></textarea>
        </div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Monturas
          <button class="btn-add-small ml-auto" @click="addMount()">+ Montura</button>
        </div>
        <template x-for="(mount, i) in character.inventory.mounts" :key="i">
          <div class="mount-row">
            <input type="text" x-model="mount.name" placeholder="Nombre">
            <input type="text" x-model="mount.notes" placeholder="Notas">
            <button class="btn-remove" @click="removeMount(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.inventory.mounts?.length">Sin monturas</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Gemas y Tesoros
          <button class="btn-add-small ml-auto" @click="addGem()">+ Gema</button>
        </div>
        <template x-for="(gem, i) in character.inventory.gems" :key="i">
          <div class="gem-row">
            <input type="text" x-model="gem.name" placeholder="Descripción">
            <input type="text" x-model="gem.value" placeholder="Valor">
            <input type="number" x-model.number="gem.quantity" min="1" style="width:60px">
            <button class="btn-remove" @click="removeGem(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.inventory.gems?.length">Sin gemas ni tesoros</div>
      </div>

      <div class="dnd-card">
        <div class="dnd-card-header">
          Bienes Prestados, Depositados o Alquilados
          <button class="btn-add-small ml-auto" @click="addLoaned()">+ Bien</button>
        </div>
        <div class="row-head loaned-head-row">
          <span>Descripción</span><span class="loaned-head-extra">Dónde</span><span class="loaned-head-extra">Cuánto</span><span class="loaned-head-extra">Cuándo</span><span></span>
        </div>
        <template x-for="(loan, i) in character.inventory.loaned" :key="i">
          <div class="loaned-row">
            <input type="text" x-model="loan.name" placeholder="Descripción">
            <input type="text" x-model="loan.where" placeholder="Dónde" class="loaned-extra">
            <input type="text" x-model="loan.amount" placeholder="Cuánto" class="loaned-extra">
            <input type="text" x-model="loan.when" placeholder="Cuándo" class="loaned-extra">
            <button class="btn-remove" @click="removeLoaned(i)">×</button>
          </div>
        </template>
        <div class="empty-state" x-show="!character.inventory.loaned?.length">Sin bienes prestados</div>
      </div>
    </section>

  </main><!-- /.main-content -->"""

new_content = content[:idx_start] + NEW_MAIN + content[idx_end:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Written {len(new_content)} chars (was {len(content)})")
print("Done!")
