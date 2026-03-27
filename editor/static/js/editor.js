function characterEditor() {
  return {
    character: null,
    activeSection: 'identidad',
    activeSubsection: '',
    expandedSections: {
      identidad: true,
      atributos: false,
      combate: false,
      habilidades: false,
      conjuros: false,
      inventario: false
    },
    subsectionNav: {
      identidad: [
        { id: 'identidad-datos-basicos', label: 'Datos Basicos' },
        { id: 'identidad-apariencia-fisica', label: 'Apariencia Fisica' },
        { id: 'identidad-trasfondo', label: 'Trasfondo' },
        { id: 'identidad-religion', label: 'Religion' },
        { id: 'identidad-idiomas', label: 'Idiomas' }
      ],
      atributos: [
        { id: 'atributos-estadisticas-generales', label: 'Estadisticas Generales' },
        { id: 'atributos-habilidades', label: 'Puntuaciones de Habilidad' },
        { id: 'atributos-movimiento', label: 'Movimiento' },
        { id: 'atributos-puntos-golpe', label: 'Puntos de Golpe' },
        { id: 'atributos-carga', label: 'Capacidad de Carga' }
      ],
      combate: [
        { id: 'combate-protecciones', label: 'Protecciones' },
        { id: 'combate-ventajas', label: 'Ventajas, Resistencias e Inmunidades' },
        { id: 'combate-ataques', label: 'Armas y Municion' },
        { id: 'combate-recursos', label: 'Habilidades y Beneficios de Combate' },
        { id: 'combate-competencias', label: 'Competencias' }
      ],
      habilidades: [
        { id: 'habilidades-dotes', label: 'Dotes' },
        { id: 'habilidades-especie', label: 'Rasgos de Especie' },
        { id: 'habilidades-clase', label: 'Rasgos de Clase' },
        { id: 'habilidades-notas', label: 'Notas' }
      ],
      conjuros: [
        { id: 'conjuros-estadisticas', label: 'Estadisticas de Lanzamiento' },
        { id: 'conjuros-espacios', label: 'Espacios de Conjuros' },
        { id: 'conjuros-lista', label: 'Lista de Conjuros' }
      ],
      inventario: [
        { id: 'inventario-equipo', label: 'Equipo' },
        { id: 'inventario-dinero', label: 'Dinero' },
        { id: 'inventario-monturas', label: 'Monturas' },
        { id: 'inventario-gemas', label: 'Gemas y Tesoros' },
        { id: 'inventario-bienes', label: 'Bienes Prestados' }
      ]
    },
    portraitExpanded: false,
    portraitLoadError: false,
    DAMAGE_TYPES: ['contundente','cortante','perforante','ácido','frío','fuego','fuerza','necrótico','psíquico','radiante','rayo','trueno','veneno'],
    DICE_TYPES: ['d4','d6','d8','d10','d12','d20'],
    loading: true,
    saving: false,
    error: null,
    toast: null,
    characterList: [],
    // Import
    importModal: false,
    importUrl: '',
    importing: false,
    importError: null,
    // Export PDF
    exportingPdf: false,

    async init() {
      try {
        const res = await fetch('/api/character');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        this.character = await res.json();
        this._ensureArrays();
      } catch (e) {
        this.error = e.message;
      }
      this.loading = false;
      await this.$nextTick();
      this.setupSubsectionAnchors();
      this.initScrollSpy();
      this.loadCharacterList();
    },

    _ensureArrays() {
      if (!this.character) return;
      this.portraitLoadError = false;
      this.character.attacks       ??= [];
      this.character.attacks.forEach(atk => {
        if (atk.damage_dice_type === undefined) {
          const src = atk.damage || atk.damage_display || '';
          const m = src.match(/^(\d+)(d\d+)\s*([+-]\s*\d+)?/i);
          atk.damage_dice_count = m ? (parseInt(m[1]) || 1) : 1;
          atk.damage_dice_type  = m ? m[2].toLowerCase() : 'd6';
          atk.damage_bonus      = m && m[3] ? parseInt(m[3].replace(/\s/g,'')) : 0;
        }
        if (!Array.isArray(atk.properties)) {
          atk.properties = String(atk.properties || '')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);
        }
        atk.range_min = String(atk.range_min ?? '').trim();
        atk.range_max = String(atk.range_max ?? '').trim();
        if (!atk.range_min && !atk.range_max) {
          const legacyRange = String(atk.range || '').trim();
          if (legacyRange) {
            const [minRaw, maxRaw] = legacyRange.split('/').map(s => s.trim());
            atk.range_min = minRaw || '';
            atk.range_max = maxRaw && maxRaw !== minRaw ? maxRaw : '';
          }
        }
        this.syncAttackRangeText(atk);
        atk.notes = String(atk.notes || '').trim();
        delete atk.custom_bonuses;
        this.syncDamageDisplay(atk);
      });
      this.character.languages     ??= [];
      this.character.inventory     ??= {};
      this.character.inventory.items ??= [];
      this.character.inventory.items = this.character.inventory.items.map((item) => {
        const it = item && typeof item === 'object' ? item : {};
        const toInt = (v) => Math.max(0, parseInt(v, 10) || 0);

        let qtyEquipped = toInt(it.qty_equipped);
        let qtyBackpack = toInt(it.qty_backpack);
        let qtyBag = toInt(it.qty_bag);

        // Compatibilidad con JSON antiguo basado en quantity + location.
        if (qtyEquipped + qtyBackpack + qtyBag === 0) {
          const legacyQty = toInt(it.quantity);
          const legacyLoc = String(it.location || '').trim();
          if (legacyQty > 0) {
            if (legacyLoc === 'Equipado') qtyEquipped = legacyQty;
            else if (legacyLoc === 'Transportado') qtyBackpack = legacyQty;
            else qtyBag = legacyQty;
          }
        }

        return {
          ...it,
          name: String(it.name || ''),
          qty_equipped: qtyEquipped,
          qty_backpack: qtyBackpack,
          qty_bag: qtyBag,
          quantity: qtyEquipped + qtyBackpack + qtyBag,
          weight_kg: it.weight_kg === null || it.weight_kg === undefined || it.weight_kg === ''
            ? null
            : Number(it.weight_kg),
        };
      });
      this.character.inventory.currency ??= {};
      this.character.attacks.forEach(atk => {
        if (atk.range_min || atk.range_max) {
          return;
        }
        const inferredRange = this.attackRangeFromInventory(atk);
        if (!inferredRange.min && !inferredRange.max) {
          return;
        }
        atk.range_min = inferredRange.min;
        atk.range_max = inferredRange.max;
        this.syncAttackRangeText(atk);
      });
      this.character.resources     ??= {};
      this.character.spellcasting  ??= {};
      this.character.spellcasting.spells ??= {};
      this.character.spellcasting.spell_slots ??= {};
      this.character.background_details ??= {};
      this.character.background_details.personality_traits ??= [];
      this.character.background_details.ideals ??= [];
      this.character.background_details.bonds  ??= [];
      this.character.background_details.flaws  ??= [];
      this.character.notes ??= {};
      this.character.combat ??= {};
      this.character.combat.hit_points  ??= {};
      this.character.combat.hit_dice    ??= {};
      if (!this.character.combat.hit_dice.type) {
        const m = (this.character.combat.hit_dice.total || '').match(/^(\d+)?(d\d+)/i);
        this.character.combat.hit_dice.count = m ? (parseInt(m[1]) || 1) : 1;
        this.character.combat.hit_dice.type  = m ? m[2].toLowerCase() : 'd8';
      }
      this.character.combat.hit_dice.count ??= 1;
      this.character.combat.hit_dice.type  ??= 'd8';
      this.character.combat.hit_dice.used  ??= 0;
      this.character.combat.death_saves ??= { successes: 0, failures: 0 };
      this.character.combat.speed              ??= {};
      this.character.combat.speed.walking_meters ??= 0;
      this.character.combat.speed.swim_meters  ??= 0;
      this.character.combat.speed.fly_meters   ??= 0;
      this.character.combat.speed.climb_meters ??= 0;
      this.character.combat.shield_equipped    ??= false;
      this.character.combat.concentration      ??= { active: false, spell: '' };
      this.character.combat.exhaustion         ??= 0;
      this.character.combat.exhaustion = Math.max(0, Math.min(5, parseInt(this.character.combat.exhaustion, 10) || 0));
      this.character.appearance                ??= {};
      this.character.proficiencies             ??= {};
      this.character.basic_info                ??= {};
      if (!Array.isArray(this.character.basic_info.classes)) {
        this.character.basic_info.classes = [];
      }
      this.character.basic_info.classes = this.character.basic_info.classes
        .map((cls) => {
          const source = cls && typeof cls === 'object' ? cls : {};
          const parsedLevel = parseInt(source.level, 10);
          return {
            name: String(source.name ?? ''),
            subclass: String(source.subclass ?? ''),
            level: Math.max(1, Math.min(20, Number.isFinite(parsedLevel) ? parsedLevel : 1)),
          };
        });
      if (!this.character.basic_info.classes.length) {
        this.character.basic_info.classes.push({ name: '', subclass: '', level: 1 });
      }
      this.character.basic_info.player_name    ??= '';
      this.character.basic_info.vision         ??= '';
      this.character.notes.allies              ??= '';
      this.character.notes.enemies             ??= '';
      this.character.notes.backstory           ??= '';
      this.character.notes.physical_description ??= '';
      this.character.notes.other_notes          ??= '';
      this.character.notes.additional_notes     ??= '';
      this.character.background_details.deity             ??= '';
      this.character.background_details.deity_description ??= '';
      this.character.features_and_traits         ??= {};
      this.character.features_and_traits.class_features ??= [];
      this.character.features_and_traits.feats          ??= [];
      this.character.features_and_traits.species        ??= [];

      for (const st of Object.values(this.character.saving_throws || {})) {
        st.proficient = !!st.proficient;
      }
      for (const sk of Object.values(this.character.skills || {})) {
        sk.proficient = !!sk.proficient;
        sk.expertise  = !!sk.expertise && sk.proficient;
      }

      // Normalizar proficiencies: array o string → array
      for (const key of ['weapons', 'armor', 'tools', 'raw']) {
        const v = this.character.proficiencies[key];
        if (!Array.isArray(v)) {
          this.character.proficiencies[key] = v
            ? String(v).split(',').map(s => s.trim()).filter(Boolean)
            : [];
        }
      }

      // Migrar armor array a flags de checkboxes
      if (!this.character.proficiencies.armor_flags) {
        const arr = (this.character.proficiencies.armor || []).map(s => s.toLowerCase());
        this.character.proficiencies.armor_flags = {
          light:  arr.some(s => s.includes('ligera') || s.includes('light')),
          medium: arr.some(s => s.includes('media')  || s.includes('medium')),
          heavy:  arr.some(s => s.includes('pesada')  || s.includes('heavy')),
          shield: arr.some(s => s.includes('escudo')  || s.includes('shield')),
        };
      }

      const legacyCompetencyTexts = [];
      for (const key of ['tools', 'weapons', 'armor', 'raw']) {
        for (const entry of this.character.proficiencies[key] || []) {
          const text = String(entry || '').trim();
          if (text) legacyCompetencyTexts.push(text);
        }
      }

      const normalizedOtherCompetencies = Array.isArray(this.character.proficiencies.other_competencies)
        ? this.character.proficiencies.other_competencies
            .map((entry) => {
              if (typeof entry === 'string') {
                const raw = String(entry || '').trim();
                if (!raw) return null;
                const [title, ...rest] = raw.split(' - ');
                return {
                  title: String(title || '').trim(),
                  description: rest.join(' - ').trim(),
                };
              }
              const src = entry && typeof entry === 'object' ? entry : {};
              return {
                title: String(src.title ?? src.name ?? '').trim(),
                description: String(src.description ?? src.note ?? '').trim(),
              };
            })
            .filter((entry) => entry && (entry.title || entry.description))
        : [];

      if (!normalizedOtherCompetencies.length && legacyCompetencyTexts.length) {
        const seen = new Set();
        for (const text of legacyCompetencyTexts) {
          const key = text.toLowerCase();
          if (seen.has(key)) continue;
          seen.add(key);
          normalizedOtherCompetencies.push({ title: text, description: '' });
        }
      }
      this.character.proficiencies.other_competencies = normalizedOtherCompetencies;

      // Normalizar recursos: uses_current/uses_max → current/max
      for (const res of Object.values(this.character.resources || {})) {
        if (res.uses_max !== undefined && res.max === undefined) {
          res.max = res.uses_max; delete res.uses_max;
        }
        if (res.uses_current !== undefined && res.current === undefined) {
          res.current = res.uses_current; delete res.uses_current;
        }
        res.max = Math.max(0, parseInt(res.max, 10) || 0);
        const current = res.current ?? res.max;
        res.current = Math.max(0, Math.min(res.max, parseInt(current, 10) || 0));
        // Canonicalizar para evitar patrones no contiguos (ej: true,false,true,...).
        res.pip_states = this.canonicalizePips(res.pip_states, res.max, 'filled', res.current);
        res.current = this.countFilledPips(res.pip_states);
        const shortNote = String(res.short_rest_note ?? '').trim();
        const longNote  = String(res.long_rest_note ?? '').trim();
        if (!res.note) {
          if (shortNote && longNote) {
            res.note = `Corto: ${shortNote} | Largo: ${longNote}`;
          } else {
            res.note = shortNote || longNote || '';
          }
        }
        delete res.short_rest_note;
        delete res.long_rest_note;
        res.recharge        ??= '';
      }

      // ── Nuevos campos secciones v2 ─────────────────────────────────────────
      this.character.combat.protections ??= [];
      this.character.combat.advantages_resistances ??= [];
      this.character.combat.advantages_resistances = this.character.combat.advantages_resistances
        .map((adv) => {
          if (typeof adv === 'string') {
            return { category: '', description: String(adv || '') };
          }
          const source = adv && typeof adv === 'object' ? adv : {};
          return {
            category: String(source.category || ''),
            description: String(source.description || ''),
          };
        });
      this.character.combat.ammunition ??= [];
      this.character.combat.speed.jump_long ??= 0;
      this.character.combat.speed.jump_high ??= 0;
      this.character.combat.speed.special_senses ??= '';
      this.character.combat.speed.hour_text ??= '';
      this.character.combat.speed.day_text ??= '';
      if (!Array.isArray(this.character.combat.speed.special_entries)) {
        this.character.combat.speed.special_entries = this.splitNonEmptyLines(
          this.character.combat.speed.special_senses,
        );
      }
      this.character.proficiencies.simple_weapons ??= false;
      this.character.proficiencies.martial_weapons ??= false;
      this.character.appearance.summary ??= '';
      this.character.basic_info.creation_date ??= '';
      this.character.basic_info.next_level_xp ??= 0;
      this.character.background_details.birth_place ??= '';
      this.character.background_details.birth_date ??= '';
      this.character.background_details.description ??= '';
      this.character.background_details.page_ref ??= '';
      this.character.spellcasting.sorcery_points_max ??= 0;
      this.character.spellcasting.sorcery_points_used ??= 0;
      this.character.spellcasting.spells_prepared ??= 0;
      this.character.spellcasting.spells_known ??= 0;
      this.character.spellcasting.sorcery_pips ??= [];
      this.character.inventory.mounts ??= [];
      this.character.inventory.gems ??= [];
      this.character.inventory.gems = this.character.inventory.gems.map((gem) => {
        const srcGem = gem && typeof gem === 'object' ? gem : {};
        const value = srcGem.value ?? srcGem.value_gp ?? '';
        return {
          ...srcGem,
          name: String(srcGem.name || ''),
          value: String(value || ''),
          quantity: Math.max(0, parseInt(srcGem.quantity, 10) || 0),
          note: String(srcGem.note || ''),
        };
      });
      this.character.inventory.loaned ??= [];
      this.character.inventory.loaned = this.character.inventory.loaned.map((loan) => {
        const srcLoan = loan && typeof loan === 'object' ? loan : {};
        const rawAmount = srcLoan.amount ?? srcLoan.quantity ?? '';
        return {
          name: String(srcLoan.name || ''),
          where: String(srcLoan.where ?? srcLoan.to ?? ''),
          amount: String(rawAmount || ''),
          when: String(srcLoan.when ?? srcLoan.due ?? ''),
          notes: String(srcLoan.notes || ''),
        };
      });
      this.character.inventory.other_possessions ??= '';
      this.character.inventory.currency.other_notes ??= '';
      this.character.notes.general ??= '';
      this.character.notes.other_possessions ??= '';

      this.character.appearance.summary = this.mergeUniqueLines(
        this.character.appearance.summary,
        this.character.notes.physical_description,
      );
      this.character.notes.backstory = this.mergeUniqueLines(
        this.character.notes.backstory,
        this.character.background_details.description,
        this.character.notes.other_notes,
      );
      this.character.notes.general = this.mergeUniqueLines(
        this.character.notes.general,
        this.character.notes.additional_notes,
      );
      this.character.inventory.currency.other_notes = this.mergeUniqueLines(
        this.character.inventory.currency.other_notes,
        this.character.inventory.other_possessions,
      );

      // Sync legacy keys to preserve compatibility on save/export.
      this.character.notes.physical_description = this.character.appearance.summary;
      this.character.background_details.description = this.character.notes.backstory;
      this.character.notes.other_notes = this.character.notes.backstory;
      this.character.notes.additional_notes = this.character.notes.general;
      this.character.inventory.other_possessions = this.character.inventory.currency.other_notes;

      // Migrar spell slot pip_states
      for (const slot of Object.values(this.character.spellcasting.spell_slots || {})) {
        slot.total = Math.max(0, parseInt(slot.total, 10) || 0);
        const legacyUsed = Array.isArray(slot.pip_states)
          ? slot.pip_states.filter((p) => !p).length
          : 0;
        const used = slot.used ?? legacyUsed;
        slot.used = Math.max(0, Math.min(slot.total, parseInt(used, 10) || 0));
        slot.pip_states = this.canonicalizePips(slot.pip_states, slot.total, 'used', slot.used);
        slot.used = this.countUsedPips(slot.pip_states);
      }
      // Municion: en web solo se edita nombre + maximo.
      for (const ammo of this.character.combat.ammunition) {
        ammo.max = Math.max(0, parseInt(ammo.max, 10) || 0);
        ammo.name = String(ammo.name || '');
        delete ammo.pip_states;
      }
      // Migrar sorcery pips
      const max = Math.max(0, parseInt(this.character.spellcasting.sorcery_points_max, 10) || 0);
      const legacySorceryUsed = Array.isArray(this.character.spellcasting.sorcery_pips)
        ? this.character.spellcasting.sorcery_pips.filter((p) => !p).length
        : 0;
      const used = this.character.spellcasting.sorcery_points_used ?? legacySorceryUsed;
      this.character.spellcasting.sorcery_points_max = max;
      this.character.spellcasting.sorcery_points_used = Math.max(0, Math.min(max, parseInt(used, 10) || 0));
      this.character.spellcasting.sorcery_pips = this.canonicalizePips(
        this.character.spellcasting.sorcery_pips,
        max,
        'used',
        this.character.spellcasting.sorcery_points_used,
      );
      this.character.spellcasting.sorcery_points_used = this.countUsedPips(this.character.spellcasting.sorcery_pips);

      this.updateAll();
    },

    // ── Character list ───────────────────────────────────────────────────────

    async loadCharacterList() {
      try {
        const res = await fetch('/api/characters');
        if (res.ok) this.characterList = await res.json();
      } catch (_) {}
    },

    async loadCharacter(charId) {
      this.loading = true;
      try {
        const res = await fetch(`/api/character?id=${charId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        this.character = await res.json();
        this._ensureArrays();
        await this.$nextTick();
        this.setupSubsectionAnchors();
        this.initScrollSpy();
        this.showToast(`Personaje "${this.character.basic_info?.name}" cargado`, 'success');
      } catch (e) {
        this.showToast('Error al cargar: ' + e.message, 'error');
      }
      this.loading = false;
    },

    // ── Save ─────────────────────────────────────────────────────────────────

    async save() {
      this.saving = true;
      this.updateAll();
      try {
        const res = await fetch('/api/character', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.character)
        });
        await res.json();
        await this.loadCharacterList();
        this.showToast('Personaje guardado correctamente', 'success');
      } catch (e) {
        this.showToast('Error al guardar: ' + e.message, 'error');
      }
      this.saving = false;
    },

    showToast(msg, type = 'success') {
      this.toast = { msg, type };
      setTimeout(() => { this.toast = null; }, 3000);
    },

    // ── Modifier maths ───────────────────────────────────────────────────────

    modifier(score) {
      return Math.floor(((score || 10) - 10) / 2);
    },

    formatMod(mod) {
      if (mod === null || mod === undefined) return '+0';
      return mod >= 0 ? `+${mod}` : String(mod);
    },

    splitNonEmptyLines(value) {
      return String(value ?? '')
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
    },

    mergeUniqueLines(...values) {
      const seen = new Set();
      const merged = [];
      for (const value of values) {
        for (const line of this.splitNonEmptyLines(value)) {
          const key = line.toLowerCase();
          if (seen.has(key)) continue;
          seen.add(key);
          merged.push(line);
        }
      }
      return merged.join('\n');
    },

    modColor(val) {
      const n = parseFloat(val);
      if (isNaN(n) || n === 0) return 'mod-zero';
      return n > 0 ? 'mod-pos' : 'mod-neg';
    },

    formatSkillName(skillKey) {
      if (!skillKey) return '';
      return String(skillKey)
        .replace(/_/g, ' ')
        .toLowerCase()
        .replace(/\b\p{L}/gu, c => c.toUpperCase());
    },

    abilityMod(abilityKey) {
      const score = this.character.ability_scores?.[abilityKey]?.score || 10;
      return this.modifier(score);
    },

    getPassivePerception() {
      return 10 + (this.character?.skills?.percepcion?.total ?? this.abilityMod('wisdom'));
    },

    buildPips(max, count = 0, mode = 'filled') {
      const safeMax = Math.max(0, parseInt(max, 10) || 0);
      const safeCount = Math.max(0, Math.min(safeMax, parseInt(count, 10) || 0));
      if (mode === 'used') {
        return Array.from({ length: safeMax }, (_, i) => i < safeCount);
      }
      return Array.from({ length: safeMax }, (_, i) => i < safeCount);
    },

    resizePips(pipStates, newLen, fillValue = true) {
      const safeLen = Math.max(0, parseInt(newLen, 10) || 0);
      const next = Array.isArray(pipStates) ? pipStates.slice(0, safeLen) : [];
      while (next.length < safeLen) next.push(fillValue);
      return next;
    },

    countFilledPips(pipStates) {
      return Array.isArray(pipStates) ? pipStates.filter(Boolean).length : 0;
    },

    countUsedPips(pipStates) {
      return Array.isArray(pipStates) ? pipStates.filter(Boolean).length : 0;
    },

    canonicalizePips(pipStates, max, mode = 'filled', preferredCount = null) {
      const safeMax = Math.max(0, parseInt(max, 10) || 0);
      let count = preferredCount;
      if (count === null || count === undefined || count === '') {
        count = mode === 'used'
          ? this.countUsedPips(pipStates)
          : this.countFilledPips(pipStates);
      }
      return this.buildPips(safeMax, count, mode);
    },

    ensurePips(pipStates, max, mode, count = null) {
      return this.canonicalizePips(pipStates, max, mode, count);
    },

    setPipCascade(pipStates, index, mode = 'filled') {
      if (!Array.isArray(pipStates) || !pipStates.length) return [];
      const next = pipStates.slice();
      const i = Math.max(0, Math.min(next.length - 1, parseInt(index, 10) || 0));

      if (mode === 'used') {
        const isActive = !!next[i];
        if (!isActive) {
          for (let k = 0; k <= i; k += 1) next[k] = true;
        } else {
          for (let k = i; k < next.length; k += 1) next[k] = false;
        }
        return next;
      }

      const isActive = !!next[i];
      if (!isActive) {
        for (let k = 0; k <= i; k += 1) next[k] = true;
      } else {
        for (let k = i; k < next.length; k += 1) next[k] = false;
      }
      return next;
    },

    // ── Recompute all derived values ─────────────────────────────────────────

    updateAll() {
      if (!this.character) return;
      const pb = this.character.proficiency_bonus || 2;

      for (const [key, ab] of Object.entries(this.character.ability_scores || {})) {
        ab.modifier = this.modifier(ab.score);
      }

      for (const [key, st] of Object.entries(this.character.saving_throws || {})) {
        const mod = this.abilityMod(key);
        st.total = mod + (st.proficient ? pb : 0);
        st.roll  = `1d20${this.formatMod(st.total)}`;
      }

      for (const [key, skill] of Object.entries(this.character.skills || {})) {
        const mod  = this.abilityMod(skill.ability);
        const prof = skill.proficient ? pb : 0;
        const exp  = skill.expertise  ? pb : 0;
        skill.total = mod + prof + exp;
      }

      if (this.character.combat) {
        this.character.combat.initiative ??= this.abilityMod('dexterity');
        this.character.combat.exhaustion = Math.max(0, Math.min(5, parseInt(this.character.combat.exhaustion, 10) || 0));
        const hd = this.character.combat.hit_dice || {};
        hd.count = Math.max(1, parseInt(hd.count, 10) || 1);
        hd.used = Math.max(0, Math.min(hd.count, parseInt(hd.used, 10) || 0));
        this.character.combat.hit_dice = hd;

        const speed = this.character.combat.speed || {};
        const walkingMeters = Math.max(0, Number(speed.walking_meters) || 0);
        const speedHour = (walkingMeters * 600.0) / 1000.0;
        const speedDay = speedHour * 8.0;
        speed.hour_text = speedHour.toFixed(1);
        speed.day_text = speedDay.toFixed(1);
        speed.special_senses = this.mergeUniqueLines(
          ...(Array.isArray(speed.special_entries) ? speed.special_entries : []),
        );
        this.character.combat.speed = speed;
      }

    },

    updateSpellCounts() {
      const spellcasting = this.character?.spellcasting || {};
      const spells = spellcasting.spells || {};
      let known = 0;
      let prepared = 0;

      for (const [levelKey, entries] of Object.entries(spells)) {
        if (!Array.isArray(entries)) continue;
        known += entries.length;
        if (levelKey === 'cantrips') continue;
        prepared += entries.filter((sp) => !!sp?.prepared).length;
      }

      spellcasting.spells_known = known;
      spellcasting.spells_prepared = prepared;
      this.character.spellcasting = spellcasting;
    },

    hitDiceRange() {
      const total = Math.min(Math.max(parseInt(this.character.combat?.hit_dice?.count, 10) || 0, 0), 40);
      return Array.from({ length: total }, (_, i) => i);
    },

    toggleHitDieUsed(i) {
      const hd = this.character.combat?.hit_dice;
      if (!hd) return;

      const total = Math.max(0, parseInt(hd.count, 10) || 0);
      const current = Math.max(0, Math.min(total, parseInt(hd.used, 10) || 0));
      const target = (parseInt(i, 10) || 0) + 1;

      hd.used = current >= target ? Math.max(0, target - 1) : Math.min(total, target);
    },

    onHitDiceCountChange() {
      const hd = this.character.combat?.hit_dice;
      if (!hd) return;
      hd.count = Math.max(1, parseInt(hd.count, 10) || 1);
      hd.used = Math.max(0, Math.min(hd.count, parseInt(hd.used, 10) || 0));
    },

    // ── Attack helpers ───────────────────────────────────────────────────────

    addAttack() {
      this.character.attacks.push({
        name: '', attack_bonus: 0, attack_roll: '1d20+0',
        damage_dice_count: 1, damage_dice_type: 'd6', damage_bonus: 0,
        damage_type: '', range_min: '', range_max: '', range: '',
        damage: '1d6', damage_display: '1d6'
      });
    },

    removeAttack(i) { this.character.attacks.splice(i, 1); },

    formatDistance(rangeData) {
      if (!rangeData || typeof rangeData !== 'object') return '';
      const meters = Number(rangeData.meters);
      if (Number.isFinite(meters) && meters > 0) {
        return `${meters} m`;
      }
      const feet = Number(rangeData.feet);
      if (Number.isFinite(feet) && feet > 0) {
        return `${feet} ft`;
      }
      return '';
    },

    attackRangeFromInventory(atk) {
      const atkName = String(atk?.name || '').trim().toLowerCase();
      if (!atkName) {
        return { min: '', max: '' };
      }

      const items = Array.isArray(this.character?.inventory?.items)
        ? this.character.inventory.items
        : [];
      const item = items.find((it) => String(it?.name || '').trim().toLowerCase() === atkName);
      if (!item) {
        return { min: '', max: '' };
      }

      const normal = this.formatDistance(item.range_normal);
      const long = this.formatDistance(item.range_long);
      const min = normal || long || '';
      const max = long && long !== min ? long : '';
      return { min, max };
    },

    syncAttackRangeText(atk) {
      const min = String(atk?.range_min || '').trim();
      const max = String(atk?.range_max || '').trim();
      atk.range_min = min;
      atk.range_max = max;

      if (min && max) {
        atk.range = min === max ? min : `${min} / ${max}`;
      } else {
        atk.range = min || max || '';
      }
    },

    syncDamageDisplay(atk) {
      const b = atk.damage_bonus;
      const bStr = b > 0 ? `+${b}` : b < 0 ? `${b}` : '';
      atk.damage = `${atk.damage_dice_count}${atk.damage_dice_type}${bStr}`;
      atk.attack_roll = `1d20${atk.attack_bonus >= 0 ? '+' : ''}${atk.attack_bonus}`;
      atk.damage_display = [atk.damage, atk.damage_type].filter(Boolean).join(' ');
    },

    attackPropertiesText(atk) {
      const props = Array.isArray(atk?.properties) ? atk.properties : [];
      return props.join(', ');
    },

    onAttackPropertiesInput(atk, rawValue) {
      atk.properties = String(rawValue || '')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
    },

    // ── Spell helpers ────────────────────────────────────────────────────────

    spellLevelKey(level) { return level === 0 ? 'cantrips' : `level_${level}`; },

    getSpells(level) {
      return this.character.spellcasting.spells[this.spellLevelKey(level)] || [];
    },

    addSpell(level) {
      const k = this.spellLevelKey(level);
      if (!this.character.spellcasting.spells[k]) this.character.spellcasting.spells[k] = [];
      this.character.spellcasting.spells[k].push({
        name: '', school: '', casting_time: '', duration: '', components: '', prepared: false
      });
    },

    removeSpell(level, i) {
      const k = this.spellLevelKey(level);
      this.character.spellcasting.spells[k].splice(i, 1);
    },

    getSpellSlot(level) {
      return this.character.spellcasting.spell_slots[`level_${level}`] || null;
    },

    setSpellSlot(level, field, val) {
      const k = `level_${level}`;
      if (!this.character.spellcasting.spell_slots[k]) {
        this.character.spellcasting.spell_slots[k] = { total: 0, used: 0 };
      }
      this.character.spellcasting.spell_slots[k][field] = parseInt(val) || 0;
    },

    // ── Inventory helpers ────────────────────────────────────────────────────

    addItem() {
      this.character.inventory.items.push({
        name: '', qty_equipped: 0, qty_backpack: 1, qty_bag: 0, quantity: 1, weight_kg: null
      });
    },

    removeItem(i) { this.character.inventory.items.splice(i, 1); },

    itemTotalQuantity(item) {
      const eq = Math.max(0, parseInt(item?.qty_equipped, 10) || 0);
      const bp = Math.max(0, parseInt(item?.qty_backpack, 10) || 0);
      const bg = Math.max(0, parseInt(item?.qty_bag, 10) || 0);
      return eq + bp + bg;
    },

    onItemSlotChange(item) {
      if (!item) return;
      item.qty_equipped = Math.max(0, parseInt(item.qty_equipped, 10) || 0);
      item.qty_backpack = Math.max(0, parseInt(item.qty_backpack, 10) || 0);
      item.qty_bag = Math.max(0, parseInt(item.qty_bag, 10) || 0);
      item.quantity = this.itemTotalQuantity(item);
    },

    totalWeight() {
      return (this.character.inventory.items || [])
        .reduce((s, it) => s + ((it.weight_kg || 0) * this.itemTotalQuantity(it)), 0)
        .toFixed(1);
    },

    // ── Class helpers ───────────────────────────────────────────────────────

    addClass() {
      if (!this.character?.basic_info) return;
      if (!Array.isArray(this.character.basic_info.classes)) this.character.basic_info.classes = [];
      this.character.basic_info.classes.push({ name: '', subclass: '', level: 1 });
      this.updateAll();
    },

    removeClass(i) {
      if (!this.character?.basic_info) return;
      if (!Array.isArray(this.character.basic_info.classes)) {
        this.character.basic_info.classes = [{ name: '', subclass: '', level: 1 }];
        this.updateAll();
        return;
      }
      this.character.basic_info.classes.splice(i, 1);
      if (!this.character.basic_info.classes.length) {
        this.character.basic_info.classes.push({ name: '', subclass: '', level: 1 });
      }
      this.updateAll();
    },

    // ── Language helpers ─────────────────────────────────────────────────────

    addLanguage() { this.character.languages.push(''); },
    removeLanguage(i) { this.character.languages.splice(i, 1); },

    // ── Resource helpers ─────────────────────────────────────────────────────

    resourceEntries() {
      return Object.entries(this.character.resources || {});
    },

    addResource() {
      const k = `resource_${Date.now()}`;
      this.character.resources[k] = {
        name: 'Nuevo recurso', max: 3, current: 3,
        recharge: 'descanso largo',
        pip_states: this.buildPips(3, 3, 'filled'),
        note: ''
      };
      this.character.resources = { ...this.character.resources };
    },

    removeResource(key) {
      const r = { ...this.character.resources };
      delete r[key];
      this.character.resources = r;
    },

    toggleResPip(key, i) {
      const res = this.character.resources[key];
      res.pip_states = this.ensurePips(
        res.pip_states,
        res.max || 0,
        'filled',
        res.current ?? res.max ?? 0
      );
      res.pip_states = this.setPipCascade(res.pip_states, i, 'filled');
      res.current = this.countFilledPips(res.pip_states);
    },

    resRange(key) {
      const max = this.character.resources[key]?.max || 0;
      return Array.from({ length: Math.min(max, 30) }, (_, i) => i);
    },

    doRest(type) {
      for (const res of Object.values(this.character.resources || {})) {
        const r     = (res.recharge || '').toLowerCase();
        const short = r.includes('corto') || r.includes('short');
        const long  = r.includes('largo') || r.includes('long');
        const restore = type === 'long' ? (short || long) : short;
        if (restore) {
          res.pip_states = Array.from({ length: res.max || 0 }, () => true);
          res.current    = res.max || 0;
        }
      }
      this.character.resources = { ...this.character.resources };
    },

    onResMaxChange(key) {
      const res = this.character.resources[key];
      res.max = Math.max(0, parseInt(res.max, 10) || 0);
      res.current = Math.max(0, Math.min(res.max, parseInt(res.current, 10) || 0));
      res.pip_states = this.canonicalizePips(res.pip_states, res.max, 'filled', res.current);
      res.current = this.countFilledPips(res.pip_states);
    },

    // ── Feature / trait helpers ───────────────────────────────────────────────

    addFeature(section) {
      if (!this.character.features_and_traits[section])
        this.character.features_and_traits[section] = [];
      this.character.features_and_traits[section].push({ name: '', source: '', description: '' });
    },

    removeFeature(section, i) {
      this.character.features_and_traits[section].splice(i, 1);
    },

    addOtherCompetency() {
      if (!Array.isArray(this.character.proficiencies.other_competencies)) {
        this.character.proficiencies.other_competencies = [];
      }
      this.character.proficiencies.other_competencies.push({ title: '', description: '' });
    },

    removeOtherCompetency(i) {
      this.character.proficiencies.other_competencies.splice(i, 1);
    },

    // ── Proficiency / expertise toggles ──────────────────────────────────────

    toggleSTProficiency(key, nextValue = null) {
      const st = this.character.saving_throws[key];
      if (!st) return;
      st.proficient = nextValue === null ? !st.proficient : !!nextValue;
      this.updateAll();
    },

    toggleSkillProficiency(key, nextValue = null) {
      const skill = this.character.skills[key];
      if (!skill) return;
      skill.proficient = nextValue === null ? !skill.proficient : !!nextValue;
      if (!skill.proficient) skill.expertise = false;
      this.updateAll();
    },

    toggleSkillExpertise(key, nextValue = null) {
      const skill = this.character.skills[key];
      if (!skill) return;
      if (!skill.proficient) {
        skill.expertise = false;
        this.updateAll();
        return;
      }
      skill.expertise = nextValue === null ? !skill.expertise : !!nextValue;
      this.updateAll();
    },

    addSpeedSpecialEntry() {
      this.character.combat.speed.special_entries ??= [];
      this.character.combat.speed.special_entries.push('');
    },

    removeSpeedSpecialEntry(i) {
      this.character.combat.speed.special_entries.splice(i, 1);
    },

    // ── Ability score input ───────────────────────────────────────────────────

    onAbilityInput(key, val) {
      const n = parseInt(val);
      if (!isNaN(n)) {
        this.character.ability_scores[key].score = n;
        this.updateAll();
      }
    },

    // ── Utility ──────────────────────────────────────────────────────────────

    abilityLabel(key) {
      const m = { strength:'FUE', dexterity:'DES', constitution:'CON',
                  intelligence:'INT', wisdom:'SAB', charisma:'CAR' };
      return m[key] || key.toUpperCase().slice(0,3);
    },

    abilityName(key) {
      const m = { strength:'Fuerza', dexterity:'Destreza', constitution:'Constitución',
                  intelligence:'Inteligencia', wisdom:'Sabiduría', charisma:'Carisma' };
      return m[key] || key;
    },

    classesDisplay() {
      return (this.character?.basic_info?.classes || [])
        .map(c => `${c.name} ${c.level}`).join(' / ');
    },

    buildExportPayload() {
      const src = this.character || {};

      const classes = (src.basic_info?.classes || []).map((cls) => ({
        name: String(cls?.name || ''),
        subclass: String(cls?.subclass || ''),
        level: Math.max(1, parseInt(cls?.level, 10) || 1),
      }));
      const totalLevel = classes.reduce((sum, cls) => sum + (parseInt(cls.level, 10) || 0), 0);

      const ability_scores = {};
      for (const [key, ab] of Object.entries(src.ability_scores || {})) {
        ability_scores[key] = {
          score: parseInt(ab?.score, 10) || 0,
          modifier: parseInt(ab?.modifier, 10) || 0,
        };
      }

      const saving_throws = {};
      for (const [key, st] of Object.entries(src.saving_throws || {})) {
        const total = parseInt(st?.total, 10) || 0;
        saving_throws[key] = {
          proficient: !!st?.proficient,
          total,
          roll: `1d20${total >= 0 ? '+' : ''}${total}`,
        };
      }

      const skills = {};
      for (const [key, skill] of Object.entries(src.skills || {})) {
        const total = parseInt(skill?.total, 10) || 0;
        skills[key] = {
          name: String(skill?.name || ''),
          ability: String(skill?.ability || ''),
          proficient: !!skill?.proficient,
          expertise: !!skill?.expertise,
          total,
          roll: `1d20${total >= 0 ? '+' : ''}${total}`,
        };
      }

      const attacks = (src.attacks || []).map((atk) => {
        const attack_bonus = parseInt(atk?.attack_bonus, 10) || 0;
        const damage_dice_count = Math.max(1, parseInt(atk?.damage_dice_count, 10) || 1);
        const damage_dice_type = String(atk?.damage_dice_type || 'd6').toLowerCase();
        const damage_bonus = parseInt(atk?.damage_bonus, 10) || 0;
        const damage_type = String(atk?.damage_type || '').trim();
        const range_min = String(atk?.range_min || '').trim();
        const range_max = String(atk?.range_max || '').trim();
        let range = '';
        if (range_min && range_max) {
          range = range_min === range_max ? range_min : `${range_min} / ${range_max}`;
        } else {
          range = range_min || range_max || '';
        }

        const bonusText = damage_bonus > 0 ? `+${damage_bonus}` : damage_bonus < 0 ? `${damage_bonus}` : '';
        const damage = `${damage_dice_count}${damage_dice_type}${bonusText}`;
        const attack_roll = `1d20${attack_bonus >= 0 ? '+' : ''}${attack_bonus}`;
        const damage_display = [damage, damage_type].filter(Boolean).join(' ');

        return {
          name: String(atk?.name || ''),
          attack_bonus,
          attack_roll,
          damage_dice_count,
          damage_dice_type,
          damage_bonus,
          damage,
          damage_type,
          damage_display,
          range_min,
          range_max,
          range,
          weight: atk?.weight === null || atk?.weight === undefined || atk?.weight === ''
            ? null
            : Number(atk.weight),
          notes: String(atk?.notes || ''),
          properties: Array.isArray(atk?.properties)
            ? atk.properties.map((p) => String(p || '').trim()).filter(Boolean)
            : [],
        };
      });

      const resources = {};
      for (const [key, res] of Object.entries(src.resources || {})) {
        const max = Math.max(0, parseInt(res?.max, 10) || 0);
        const pip_states = this.canonicalizePips(res?.pip_states, max, 'filled', res?.current ?? max);
        resources[key] = {
          name: String(res?.name || ''),
          max,
          current: this.countFilledPips(pip_states),
          recharge: String(res?.recharge || ''),
          note: String(res?.note || ''),
          pip_states,
        };
      }

      const spell_slots = {};
      for (let level = 1; level <= 9; level += 1) {
        const key = `level_${level}`;
        const slot = src.spellcasting?.spell_slots?.[key] || {};
        const total = Math.max(0, parseInt(slot.total, 10) || 0);
        const pip_states = this.canonicalizePips(slot.pip_states, total, 'used', slot.used ?? 0);
        spell_slots[key] = {
          total,
          used: this.countUsedPips(pip_states),
          pip_states,
        };
      }

      const spells = { cantrips: [] };
      spells.cantrips = (src.spellcasting?.spells?.cantrips || []).map((sp) => ({
        name: String(sp?.name || ''),
        casting_time: String(sp?.casting_time || ''),
      }));
      for (let level = 1; level <= 9; level += 1) {
        const key = `level_${level}`;
        spells[key] = (src.spellcasting?.spells?.[key] || []).map((sp) => ({
          name: String(sp?.name || ''),
          casting_time: String(sp?.casting_time || ''),
          prepared: !!sp?.prepared,
        }));
      }

      const appearanceSummary = String(src.appearance?.summary || '');
      const storyText = String(src.notes?.backstory || '');
      const unifiedNotes = String(src.notes?.general || '');
      const otherPieces = String(src.inventory?.currency?.other_notes || '');

      const otherCompetencies = [];
      const seenOtherCompetencies = new Set();
      const pushOtherCompetency = (line) => {
        const value = String(line || '').trim();
        if (!value) return;
        const key = value.toLowerCase();
        if (seenOtherCompetencies.has(key)) return;
        seenOtherCompetencies.add(key);
        otherCompetencies.push(value);
      };

      for (const entry of src.proficiencies?.other_competencies || []) {
        const item = entry && typeof entry === 'object' ? entry : {};
        const title = String(item.title ?? item.name ?? '').trim();
        const description = String(item.description ?? item.note ?? '').trim();
        const line = [title, description].filter(Boolean).join(' - ');
        pushOtherCompetency(line);
      }

      if (!otherCompetencies.length) {
        for (const seq of [
          src.proficiencies?.tools || [],
          src.proficiencies?.weapons || [],
          src.proficiencies?.armor || [],
          src.proficiencies?.raw || [],
        ]) {
          for (const item of seq) {
            pushOtherCompetency(item);
          }
        }
      }

      return {
        basic_info: {
          name: String(src.basic_info?.name || ''),
          classes,
          total_level: totalLevel,
          background: String(src.basic_info?.background || ''),
          species: String(src.basic_info?.species || ''),
          alignment: String(src.basic_info?.alignment || ''),
          experience_points: Math.max(0, parseInt(src.basic_info?.experience_points, 10) || 0),
          next_level_xp: Math.max(0, parseInt(src.basic_info?.next_level_xp, 10) || 0),
          player_name: String(src.basic_info?.player_name || ''),
          vision: String(src.basic_info?.vision || ''),
          creation_date: String(src.basic_info?.creation_date || ''),
          inspiration: !!src.basic_info?.inspiration,
          portrait_url: String(src.basic_info?.portrait_url || ''),
        },
        appearance: {
          age: String(src.appearance?.age || ''),
          height: String(src.appearance?.height || ''),
          weight: String(src.appearance?.weight || ''),
          gender: String(src.appearance?.gender || ''),
          size: String(src.appearance?.size || ''),
          eyes: String(src.appearance?.eyes || ''),
          skin: String(src.appearance?.skin || ''),
          hair: String(src.appearance?.hair || ''),
          summary: String(src.appearance?.summary || ''),
        },
        background_details: {
          birth_place: String(src.background_details?.birth_place || ''),
          birth_date: String(src.background_details?.birth_date || ''),
          description: storyText,
          deity: String(src.background_details?.deity || ''),
          deity_description: String(src.background_details?.deity_description || ''),
          personality_traits: [...(src.background_details?.personality_traits || [])].map((v) => String(v || '')),
          ideals: [...(src.background_details?.ideals || [])].map((v) => String(v || '')),
          bonds: [...(src.background_details?.bonds || [])].map((v) => String(v || '')),
          flaws: [...(src.background_details?.flaws || [])].map((v) => String(v || '')),
        },
        notes: {
          allies: String(src.notes?.allies || ''),
          enemies: String(src.notes?.enemies || ''),
          backstory: storyText,
          general: unifiedNotes,
          physical_description: appearanceSummary,
          other_notes: storyText,
          additional_notes: unifiedNotes,
          other_possessions: '',
        },
        languages: [...(src.languages || [])].map((v) => String(v || '')).filter(Boolean),
        proficiency_bonus: Math.max(0, parseInt(src.proficiency_bonus, 10) || 0),
        ability_scores,
        saving_throws,
        skills,
        combat: {
          armor_class: Math.max(0, parseInt(src.combat?.armor_class, 10) || 0),
          initiative: parseInt(src.combat?.initiative, 10) || 0,
          speed: {
            walking_meters: Math.max(0, Number(src.combat?.speed?.walking_meters) || 0),
            swim_meters: Math.max(0, Number(src.combat?.speed?.swim_meters) || 0),
            fly_meters: Math.max(0, Number(src.combat?.speed?.fly_meters) || 0),
            climb_meters: Math.max(0, Number(src.combat?.speed?.climb_meters) || 0),
            jump_long: Math.max(0, Number(src.combat?.speed?.jump_long) || 0),
            jump_high: Math.max(0, Number(src.combat?.speed?.jump_high) || 0),
            hour_text: String(src.combat?.speed?.hour_text || ''),
            day_text: String(src.combat?.speed?.day_text || ''),
            special_senses: String(src.combat?.speed?.special_senses || ''),
          },
          shield_equipped: !!src.combat?.shield_equipped,
          concentration: {
            active: !!src.combat?.concentration?.active,
            spell: String(src.combat?.concentration?.spell || ''),
          },
          exhaustion: Math.max(0, Math.min(5, parseInt(src.combat?.exhaustion, 10) || 0)),
          hit_points: {
            maximum: Math.max(0, parseInt(src.combat?.hit_points?.maximum, 10) || 0),
            current: Math.max(0, parseInt(src.combat?.hit_points?.current, 10) || 0),
            temporary: Math.max(0, parseInt(src.combat?.hit_points?.temporary, 10) || 0),
          },
          hit_dice: {
            count: Math.max(0, parseInt(src.combat?.hit_dice?.count, 10) || 0),
            type: String(src.combat?.hit_dice?.type || ''),
            used: Math.max(0, parseInt(src.combat?.hit_dice?.used, 10) || 0),
            total: String(src.combat?.hit_dice?.total || ''),
          },
          death_saves: {
            successes: Math.max(0, Math.min(3, parseInt(src.combat?.death_saves?.successes, 10) || 0)),
            failures: Math.max(0, Math.min(3, parseInt(src.combat?.death_saves?.failures, 10) || 0)),
          },
          protections: (src.combat?.protections || []).map((prot) => ({
            name: String(prot?.name || ''),
            type: String(prot?.type || ''),
            ac_bonus: parseInt(prot?.ac_bonus, 10) || 0,
            equipped: !!prot?.equipped,
            weight_kg: prot?.weight_kg === null || prot?.weight_kg === undefined || prot?.weight_kg === ''
              ? null
              : Number(prot.weight_kg),
          })),
          advantages_resistances: (src.combat?.advantages_resistances || []).map((adv) => {
            if (typeof adv === 'string') {
              return { category: '', description: String(adv || '') };
            }
            return {
              category: String(adv?.category || ''),
              description: String(adv?.description || ''),
            };
          }),
          ammunition: (src.combat?.ammunition || []).map((ammo) => ({
            name: String(ammo?.name || ''),
            max: Math.max(0, parseInt(ammo?.max, 10) || 0),
            note: '',
          })),
        },
        attacks,
        proficiencies: {
          armor_flags: {
            light: !!src.proficiencies?.armor_flags?.light,
            medium: !!src.proficiencies?.armor_flags?.medium,
            heavy: !!src.proficiencies?.armor_flags?.heavy,
            shield: !!src.proficiencies?.armor_flags?.shield,
          },
          simple_weapons: !!src.proficiencies?.simple_weapons,
          martial_weapons: !!src.proficiencies?.martial_weapons,
          armor: [],
          weapons: [],
          tools: [],
          raw: otherCompetencies,
          other_competencies: (src.proficiencies?.other_competencies || []).map((entry) => {
            const item = entry && typeof entry === 'object' ? entry : {};
            return {
              title: String(item.title ?? item.name ?? '').trim(),
              description: String(item.description ?? item.note ?? '').trim(),
            };
          }).filter((entry) => entry.title || entry.description),
        },
        features_and_traits: {
          feats: (src.features_and_traits?.feats || []).map((feat) => ({
            name: String(feat?.name || ''),
            description: String(feat?.description || ''),
          })),
          species: (src.features_and_traits?.species || []).map((feat) => ({
            name: String(feat?.name || ''),
            source: String(feat?.source || ''),
            description: String(feat?.description || ''),
          })),
          class_features: (src.features_and_traits?.class_features || []).map((feat) => ({
            name: String(feat?.name || ''),
            source: String(feat?.source || ''),
            description: String(feat?.description || ''),
          })),
        },
        spellcasting: {
          spellcasting_ability: String(src.spellcasting?.spellcasting_ability || ''),
          spell_save_dc: parseInt(src.spellcasting?.spell_save_dc, 10) || 0,
          spell_attack_bonus: parseInt(src.spellcasting?.spell_attack_bonus, 10) || 0,
          spells_prepared: Math.max(0, parseInt(src.spellcasting?.spells_prepared, 10) || 0),
          spells_known: Math.max(0, parseInt(src.spellcasting?.spells_known, 10) || 0),
          sorcery_points_max: Math.max(0, parseInt(src.spellcasting?.sorcery_points_max, 10) || 0),
          sorcery_points_used: Math.max(0, parseInt(src.spellcasting?.sorcery_points_used, 10) || 0),
          sorcery_pips: this.canonicalizePips(
            src.spellcasting?.sorcery_pips,
            Math.max(0, parseInt(src.spellcasting?.sorcery_points_max, 10) || 0),
            'used',
            Math.max(0, parseInt(src.spellcasting?.sorcery_points_used, 10) || 0),
          ),
          spell_slots,
          spells,
        },
        inventory: {
          items: (src.inventory?.items || []).map((item) => {
            const qty_equipped = Math.max(0, parseInt(item?.qty_equipped, 10) || 0);
            const qty_backpack = Math.max(0, parseInt(item?.qty_backpack, 10) || 0);
            const qty_bag = Math.max(0, parseInt(item?.qty_bag, 10) || 0);
            return {
              name: String(item?.name || ''),
              qty_equipped,
              qty_backpack,
              qty_bag,
              quantity: qty_equipped + qty_backpack + qty_bag,
              weight_kg: item?.weight_kg === null || item?.weight_kg === undefined || item?.weight_kg === ''
                ? null
                : Number(item.weight_kg),
            };
          }),
          currency: {
            PP: Math.max(0, parseInt(src.inventory?.currency?.PP, 10) || 0),
            GP: Math.max(0, parseInt(src.inventory?.currency?.GP, 10) || 0),
            EP: Math.max(0, parseInt(src.inventory?.currency?.EP, 10) || 0),
            SP: Math.max(0, parseInt(src.inventory?.currency?.SP, 10) || 0),
            CP: Math.max(0, parseInt(src.inventory?.currency?.CP, 10) || 0),
            other_notes: otherPieces,
          },
          mounts: (src.inventory?.mounts || []).map((mount) => ({
            name: String(mount?.name || ''),
            notes: String(mount?.notes || ''),
          })),
          gems: (src.inventory?.gems || []).map((gem) => ({
            name: String(gem?.name || ''),
            value_gp: String(gem?.value_gp || gem?.value || ''),
            quantity: Math.max(0, parseInt(gem?.quantity, 10) || 0),
            note: String(gem?.note || ''),
          })),
          loaned: (src.inventory?.loaned || []).map((loan) => ({
            name: String(loan?.name || ''),
            to: String(loan?.where ?? loan?.to ?? ''),
            quantity: String(loan?.amount ?? loan?.quantity ?? ''),
            due: String(loan?.when ?? loan?.due ?? ''),
            notes: String(loan?.notes || ''),
          })),
          other_possessions: '',
        },
        resources,
      };
    },

    // ── Import from Nivel20 ───────────────────────────────────────────────────

    async importCharacter() {
      const url = this.importUrl.trim();
      if (!url) return;
      this.importing    = true;
      this.importError  = null;
      try {
        const res = await fetch('/api/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || 'Error al importar');
        this.character = data;
        this._ensureArrays();
        this.importModal = false;
        this.importUrl   = '';
        await this.$nextTick();
        this.initScrollSpy();
        await this.loadCharacterList();
        this.showToast(`"${data.basic_info?.name}" importado correctamente`, 'success');
      } catch (e) {
        this.importError = e.message;
      }
      this.importing = false;
    },

    // ── Export PDF ────────────────────────────────────────────────────────────

    async exportPdf() {
      this.exportingPdf = true;
      this.updateAll();
      try {
        const exportPayload = this.buildExportPayload();
        const res = await fetch('/api/export-pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(exportPayload)
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.message || 'Error al generar PDF');
        }
        const blob   = await res.blob();
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objUrl;
        a.download = `${this.character.basic_info?.name || 'personaje'}_hoja.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objUrl);
        this.showToast('PDF generado y descargado', 'success');
      } catch (e) {
        this.showToast('Error PDF: ' + e.message, 'error');
      }
      this.exportingPdf = false;
    },

    // ── Scroll-spy ────────────────────────────────────────────────────────────

    setupSubsectionAnchors() {
      for (const [sectionId, subList] of Object.entries(this.subsectionNav)) {
        const cards = document.querySelectorAll(`#${sectionId} > .dnd-card`);
        subList.forEach((sub, index) => {
          if (cards[index]) cards[index].id = sub.id;
        });
      }
    },

    isSectionExpanded(sectionId) {
      return !!this.expandedSections?.[sectionId];
    },

    toggleSectionSubnav(sectionId) {
      this.expandedSections[sectionId] = !this.isSectionExpanded(sectionId);
    },

    expandSectionSubnav(sectionId) {
      if (!sectionId) return;
      this.expandedSections[sectionId] = true;
    },

    scrollToSection(id) {
      const el = document.getElementById(id);
      if (!el) return;

      const parentSection = el.classList.contains('section-block')
        ? el.dataset.section
        : el.closest('.section-block')?.dataset?.section;

      if (parentSection) {
        this.activeSection = parentSection;
        this.expandSectionSubnav(parentSection);
      }
      this.activeSubsection = id.includes('-') ? id : '';

      this.$nextTick(() => {
        const headerOffset = this.currentHeaderOffset();
        const top = window.scrollY + el.getBoundingClientRect().top - headerOffset;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
      });
    },

    currentHeaderOffset() {
      const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 70;
      const tabsHeight = document.querySelector('.top-tabs-shell')?.offsetHeight || 0;
      const offset = navbarHeight + tabsHeight + 14;

      // Keep CSS anchor offsets in sync with the real sticky header height.
      document.documentElement.style.setProperty('--section-scroll-offset', `${offset}px`);
      document.documentElement.style.setProperty('--card-scroll-offset', `${offset + 6}px`);

      return offset;
    },

    initScrollSpy() {
      const sections = document.querySelectorAll('.section-block[data-section]');
      if (!sections.length) return;
      const update = () => {
        const offset = this.currentHeaderOffset();
        let current = sections[0]?.dataset?.section || 'identidad';
        for (const s of sections) {
          if (s.getBoundingClientRect().top <= offset) current = s.dataset.section;
        }
        this.activeSection = current;
        this.expandSectionSubnav(current);

        const subsectionCards = document.querySelectorAll(`#${current} > .dnd-card[id]`);
        let currentSub = '';
        for (const card of subsectionCards) {
          if (card.getBoundingClientRect().top <= offset + 20) currentSub = card.id;
        }
        this.activeSubsection = currentSub;
      };

      window.removeEventListener('scroll', this._scrollHandler);

      this._scrollHandler = () => {
        if (this._scrollTicking) return;
        this._scrollTicking = true;
        window.requestAnimationFrame(() => {
          this._scrollTicking = false;
          update();
        });
      };

      window.addEventListener('scroll', this._scrollHandler, { passive: true });

      window.removeEventListener('resize', this._resizeHandler);
      this._resizeHandler = () => {
        this.currentHeaderOffset();
        update();
      };
      window.addEventListener('resize', this._resizeHandler, { passive: true });

      update();
    },

    // ── Protection helpers ────────────────────────────────────────────────────

    addProtection() {
      this.character.combat.protections.push({ name: '', type: '', ac_bonus: 0, equipped: false, weight_kg: null });
    },
    removeProtection(i) { this.character.combat.protections.splice(i, 1); },

    // ── Advantage / resistance helpers ───────────────────────────────────────

    addAdvantage() {
      this.character.combat.advantages_resistances.push({ category: '', description: '' });
    },
    removeAdvantage(i) { this.character.combat.advantages_resistances.splice(i, 1); },

    // ── Ammunition helpers ────────────────────────────────────────────────────

    addAmmo() {
      this.character.combat.ammunition.push({
        name: '', max: 20
      });
    },
    removeAmmo(i) { this.character.combat.ammunition.splice(i, 1); },
    onAmmoMaxChange(i) {
      const ammo = this.character.combat.ammunition[i];
      ammo.max = Math.max(0, parseInt(ammo.max, 10) || 0);
    },

    // ── Spell slot pip helpers ────────────────────────────────────────────────

    slotRange(level) {
      const total = this.character.spellcasting.spell_slots?.[`level_${level}`]?.total || 0;
      return Array.from({ length: Math.min(total, 20) }, (_, i) => i);
    },
    toggleSlotPip(level, j) {
      const k = `level_${level}`;
      const slot = this.character.spellcasting.spell_slots[k];
      if (!slot) return;
      slot.pip_states = this.ensurePips(slot.pip_states, slot.total || 0, 'used', slot.used || 0);
      slot.pip_states = this.setPipCascade(slot.pip_states, j, 'used');
      slot.used = this.countUsedPips(slot.pip_states);
    },
    onSlotTotalChange(level) {
      const k = `level_${level}`;
      if (!this.character.spellcasting.spell_slots[k]) {
        this.character.spellcasting.spell_slots[k] = { total: 0, used: 0, pip_states: [] };
      }
      const slot = this.character.spellcasting.spell_slots[k];
      slot.total = Math.max(0, parseInt(slot.total, 10) || 0);
      slot.used = Math.max(0, Math.min(slot.total, parseInt(slot.used, 10) || 0));
      slot.pip_states = this.canonicalizePips(slot.pip_states, slot.total, 'used', slot.used);
      slot.used = this.countUsedPips(slot.pip_states);
    },

    // ── Sorcery point pip helpers ─────────────────────────────────────────────

    sorceryRange() {
      return Array.from({ length: Math.min(this.character.spellcasting.sorcery_points_max || 0, 30) }, (_, i) => i);
    },
    toggleSorceryPip(j) {
      const sp = this.character.spellcasting;
      sp.sorcery_pips = this.ensurePips(
        sp.sorcery_pips,
        sp.sorcery_points_max || 0,
        'used',
        sp.sorcery_points_used || 0
      );
      sp.sorcery_pips = this.setPipCascade(sp.sorcery_pips, j, 'used');
      sp.sorcery_points_used = this.countUsedPips(sp.sorcery_pips);
    },
    onSorceryMaxChange() {
      const sp = this.character.spellcasting;
      const max = Math.max(0, parseInt(sp.sorcery_points_max, 10) || 0);
      sp.sorcery_points_max = max;
      sp.sorcery_points_used = Math.max(0, Math.min(max, parseInt(sp.sorcery_points_used, 10) || 0));
      sp.sorcery_pips = this.canonicalizePips(sp.sorcery_pips, max, 'used', sp.sorcery_points_used);
      sp.sorcery_points_used = this.countUsedPips(sp.sorcery_pips);
    },

    // ── Carrying capacity ─────────────────────────────────────────────────────

    carryingCapacity() {
      const str = this.character.ability_scores?.strength?.score || 10;
      return {
        normal:   (str * 7.5).toFixed(1),
        overload: (str * 15).toFixed(1),
        max:      (str * 22.5).toFixed(1),
        push:     (str * 30).toFixed(1),
      };
    },

    // ── Inventory weight helpers ───────────────────────────────────────────────

    weightByLocation(loc) {
      return (this.character.inventory.items || [])
        .reduce((s, it) => {
          const qty = loc === 'Equipado'
            ? (parseInt(it.qty_equipped, 10) || 0)
            : loc === 'Transportado'
              ? (parseInt(it.qty_backpack, 10) || 0)
              : (parseInt(it.qty_bag, 10) || 0);
          return s + ((it.weight_kg || 0) * qty);
        }, 0)
        .toFixed(1);
    },

    totalByLocation(loc) {
      return (this.character.inventory.items || [])
        .reduce((s, it) => {
          if (loc === 'Equipado') return s + (parseInt(it.qty_equipped, 10) || 0);
          if (loc === 'Transportado') return s + (parseInt(it.qty_backpack, 10) || 0);
          return s + (parseInt(it.qty_bag, 10) || 0);
        }, 0);
    },

    totalItemsCount() {
      return (this.character.inventory.items || [])
        .reduce((s, it) => s + this.itemTotalQuantity(it), 0);
    },

    // ── Mount helpers ──────────────────────────────────────────────────────────

    addMount()        { this.character.inventory.mounts.push({ name: '', notes: '' }); },
    removeMount(i)    { this.character.inventory.mounts.splice(i, 1); },

    // ── Gem helpers ────────────────────────────────────────────────────────────

    addGem()          { this.character.inventory.gems.push({ name: '', value: '', quantity: 1, note: '' }); },
    removeGem(i)      { this.character.inventory.gems.splice(i, 1); },

    // ── Loaned item helpers ────────────────────────────────────────────────────

    addLoaned()       { this.character.inventory.loaned.push({ name: '', where: '', amount: '', when: '', notes: '' }); },
    removeLoaned(i)   { this.character.inventory.loaned.splice(i, 1); },
  };
}
