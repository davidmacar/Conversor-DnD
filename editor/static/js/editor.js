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
      this.character.attacks       ??= [];
      this.character.attacks.forEach(atk => {
        if (atk.damage_dice_type === undefined) {
          const src = atk.damage || atk.damage_display || '';
          const m = src.match(/^(\d+)(d\d+)\s*([+-]\s*\d+)?/i);
          atk.damage_dice_count = m ? (parseInt(m[1]) || 1) : 1;
          atk.damage_dice_type  = m ? m[2].toLowerCase() : 'd6';
          atk.damage_bonus      = m && m[3] ? parseInt(m[3].replace(/\s/g,'')) : 0;
        }
        delete atk.custom_bonuses;
        this.syncDamageDisplay(atk);
      });
      this.character.languages     ??= [];
      this.character.inventory     ??= {};
      this.character.inventory.items ??= [];
      this.character.inventory.currency ??= {};
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
      this.character.combat.speed.hour_text ??= '';
      this.character.combat.speed.day_text ??= '';
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
      for (const key of ['weapons', 'armor', 'tools']) {
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
      this.character.combat.ammunition ??= [];
      this.character.combat.speed.jump_long ??= 0;
      this.character.combat.speed.jump_high ??= 0;
      this.character.combat.speed.special_senses ??= '';
      this.character.proficiencies.simple_weapons ??= false;
      this.character.proficiencies.martial_weapons ??= false;
      this.character.appearance.summary ??= '';
      this.character.basic_info.creation_date ??= '';
      this.character.basic_info.next_level_xp ??= 0;
      this.character.background_details.birth_place ??= '';
      this.character.background_details.birth_date ??= '';
      this.character.background_details.page_ref ??= '';
      this.character.spellcasting.sorcery_points_max ??= 0;
      this.character.spellcasting.sorcery_points_used ??= 0;
      this.character.spellcasting.sorcery_pips ??= [];
      this.character.inventory.mounts ??= [];
      this.character.inventory.gems ??= [];
      this.character.inventory.loaned ??= [];
      this.character.inventory.currency.other_notes ??= '';
      this.character.notes.general ??= '';

      // Migrar spell slot pip_states
      for (const slot of Object.values(this.character.spellcasting.spell_slots || {})) {
        slot.total = Math.max(0, parseInt(slot.total, 10) || 0);
        const used = slot.used ?? this.countUsedPips(slot.pip_states);
        slot.used = Math.max(0, Math.min(slot.total, parseInt(used, 10) || 0));
        slot.pip_states = this.canonicalizePips(slot.pip_states, slot.total, 'used', slot.used);
        slot.used = this.countUsedPips(slot.pip_states);
      }
      // Migrar ammunition pip_states
      for (const ammo of this.character.combat.ammunition) {
        ammo.max = Math.max(0, parseInt(ammo.max, 10) || 0);
        const filled = Array.isArray(ammo.pip_states)
          ? this.countFilledPips(ammo.pip_states)
          : ammo.max;
        ammo.pip_states = this.canonicalizePips(ammo.pip_states, ammo.max, 'filled', filled);
      }
      // Migrar sorcery pips
      const max = Math.max(0, parseInt(this.character.spellcasting.sorcery_points_max, 10) || 0);
      const used = this.character.spellcasting.sorcery_points_used ?? this.countUsedPips(this.character.spellcasting.sorcery_pips);
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
        return Array.from({ length: safeMax }, (_, i) => i >= safeCount);
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
      return Array.isArray(pipStates) ? pipStates.filter(p => !p).length : 0;
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

      // mode='used' means false is active(used), true is inactive(available).
      if (mode === 'used') {
        const isActive = !next[i];
        if (!isActive) {
          for (let k = 0; k <= i; k += 1) next[k] = false;
        } else {
          for (let k = i; k < next.length; k += 1) next[k] = true;
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
        const walking = Number(speed.walking_meters) || 0;
        const kmPerHour = walking * 0.6;
        const kmPerDay = kmPerHour * 8;
        speed.hour_text = `${kmPerHour.toFixed(1)} km/h`;
        speed.day_text = `${kmPerDay.toFixed(1)} km/dia`;
        this.character.combat.speed = speed;
      }
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
        damage_type: '', damage: '1d6', damage_display: '1d6'
      });
    },

    removeAttack(i) { this.character.attacks.splice(i, 1); },

    syncDamageDisplay(atk) {
      const b = atk.damage_bonus;
      const bStr = b > 0 ? `+${b}` : b < 0 ? `${b}` : '';
      atk.damage = `${atk.damage_dice_count}${atk.damage_dice_type}${bStr}`;
      atk.attack_roll = `1d20${atk.attack_bonus >= 0 ? '+' : ''}${atk.attack_bonus}`;
      atk.damage_display = [atk.damage, atk.damage_type].filter(Boolean).join(' ');
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
        name: '', quantity: 1, weight_kg: null, is_weapon: false, location: ''
      });
    },

    removeItem(i) { this.character.inventory.items.splice(i, 1); },

    totalWeight() {
      return (this.character.inventory.items || [])
        .reduce((s, it) => s + ((it.weight_kg || 0) * (it.quantity || 1)), 0)
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
        const res = await fetch('/api/export-pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.character)
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

      const headerOffset = 82;
      const top = window.scrollY + el.getBoundingClientRect().top - headerOffset;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    },

    initScrollSpy() {
      const sections = document.querySelectorAll('.section-block[data-section]');
      if (!sections.length) return;
      const update = () => {
        const offset = 90;
        let current = sections[0]?.dataset?.section || 'identidad';
        for (const s of sections) {
          if (s.getBoundingClientRect().top <= offset) current = s.dataset.section;
        }
        this.activeSection = current;
        this.expandSectionSubnav(current);

        const subsectionCards = document.querySelectorAll(`#${current} > .dnd-card[id]`);
        let currentSub = '';
        for (const card of subsectionCards) {
          if (card.getBoundingClientRect().top <= offset + 80) currentSub = card.id;
        }
        this.activeSubsection = currentSub;
      };
      window.removeEventListener('scroll', this._scrollHandler);
      this._scrollHandler = update;
      window.addEventListener('scroll', update, { passive: true });
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
        name: '', max: 6, pip_states: this.buildPips(6, 6, 'filled')
      });
    },
    removeAmmo(i) { this.character.combat.ammunition.splice(i, 1); },
    ammoRange(i) {
      return Array.from({ length: Math.min(this.character.combat.ammunition[i]?.max || 0, 40) }, (_, j) => j);
    },
    toggleAmmoPip(i, j) {
      const ammo = this.character.combat.ammunition[i];
      const filled = this.countFilledPips(ammo.pip_states);
      ammo.pip_states = this.ensurePips(
        ammo.pip_states,
        ammo.max || 0,
        'filled',
        filled
      );
      ammo.pip_states = this.setPipCascade(ammo.pip_states, j, 'filled');
    },
    onAmmoMaxChange(i) {
      const ammo = this.character.combat.ammunition[i];
      ammo.max = Math.max(0, parseInt(ammo.max, 10) || 0);
      const filled = this.countFilledPips(ammo.pip_states);
      ammo.pip_states = this.canonicalizePips(ammo.pip_states, ammo.max, 'filled', filled);
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
        .filter(it => it.location === loc)
        .reduce((s, it) => s + ((it.weight_kg || 0) * (it.quantity || 1)), 0)
        .toFixed(1);
    },

    // ── Mount helpers ──────────────────────────────────────────────────────────

    addMount()        { this.character.inventory.mounts.push({ name: '', notes: '' }); },
    removeMount(i)    { this.character.inventory.mounts.splice(i, 1); },

    // ── Gem helpers ────────────────────────────────────────────────────────────

    addGem()          { this.character.inventory.gems.push({ name: '', value: '', quantity: 1 }); },
    removeGem(i)      { this.character.inventory.gems.splice(i, 1); },

    // ── Loaned item helpers ────────────────────────────────────────────────────

    addLoaned()       { this.character.inventory.loaned.push({ name: '', where: '', amount: '', when: '' }); },
    removeLoaned(i)   { this.character.inventory.loaned.splice(i, 1); },
  };
}
