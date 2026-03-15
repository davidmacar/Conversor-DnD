function characterEditor() {
  return {
    character: null,
    activeSection: 'personaje',
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
        atk.custom_bonuses ??= [];
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
      this.character.combat.shield_equipped    ??= false;
      this.character.combat.concentration      ??= { active: false, spell: '' };
      this.character.combat.exhaustion         ??= 0;
      this.character.appearance                ??= {};
      this.character.proficiencies             ??= {};
      this.character.basic_info                ??= {};
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
        // Migrar a pips independientes
        if (!Array.isArray(res.pip_states)) {
          res.pip_states = Array.from(
            { length: res.max || 0 },
            (_, i) => i < (res.current ?? res.max ?? 0)
          );
        }
        res.short_rest_note ??= '';
        res.long_rest_note  ??= '';
        res.recharge        ??= '';
      }
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

    abilityMod(abilityKey) {
      const score = this.character.ability_scores?.[abilityKey]?.score || 10;
      return this.modifier(score);
    },

    getPassivePerception() {
      return 10 + (this.character?.skills?.percepcion?.total ?? this.abilityMod('wisdom'));
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
      }
    },

    // ── Attack helpers ───────────────────────────────────────────────────────

    addAttack() {
      this.character.attacks.push({
        name: '', attack_bonus: 0, attack_roll: '1d20+0',
        damage_dice_count: 1, damage_dice_type: 'd6', damage_bonus: 0,
        damage_type: '', damage: '1d6', damage_display: '1d6',
        custom_bonuses: []
      });
    },

    removeAttack(i) { this.character.attacks.splice(i, 1); },

    syncDamageDisplay(atk) {
      const b = atk.damage_bonus;
      const bStr = b > 0 ? `+${b}` : b < 0 ? `${b}` : '';
      atk.damage = `${atk.damage_dice_count}${atk.damage_dice_type}${bStr}`;
      atk.attack_roll = `1d20${atk.attack_bonus >= 0 ? '+' : ''}${atk.attack_bonus}`;
      const extras = (atk.custom_bonuses || []).map(cb => cb.value).filter(Boolean).join(' ');
      atk.damage_display = [atk.damage, atk.damage_type, extras].filter(Boolean).join(' ');
    },

    addAtkBonus(i) { this.character.attacks[i].custom_bonuses.push({ name: '', value: '' }); },
    removeAtkBonus(i, j) { this.character.attacks[i].custom_bonuses.splice(j, 1); },

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
        pip_states: [true, true, true],
        short_rest_note: '', long_rest_note: ''
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
      if (!Array.isArray(res.pip_states) || res.pip_states.length !== res.max) {
        res.pip_states = Array.from({length: res.max}, (_, idx) => idx < res.current);
      }
      res.pip_states[i] = !res.pip_states[i];
      res.current = res.pip_states.filter(Boolean).length;
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
      const newLen = res.max || 0;
      if (!Array.isArray(res.pip_states)) {
        res.pip_states = Array.from({length: newLen}, () => true);
      } else if (newLen > res.pip_states.length) {
        for (let i = res.pip_states.length; i < newLen; i++) res.pip_states.push(true);
      } else {
        res.pip_states = res.pip_states.slice(0, newLen);
      }
      res.current = res.pip_states.filter(Boolean).length;
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

    toggleSTProficiency(key) {
      this.character.saving_throws[key].proficient = !this.character.saving_throws[key].proficient;
      this.updateAll();
    },

    toggleSkillProficiency(key) {
      this.character.skills[key].proficient = !this.character.skills[key].proficient;
      if (!this.character.skills[key].proficient) this.character.skills[key].expertise = false;
      this.updateAll();
    },

    toggleSkillExpertise(key) {
      if (!this.character.skills[key].proficient) return;
      this.character.skills[key].expertise = !this.character.skills[key].expertise;
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

    scrollToSection(id) {
      this.activeSection = id;
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    initScrollSpy() {
      const sections = document.querySelectorAll('.section-block[data-section]');
      if (!sections.length) return;
      const update = () => {
        const offset = 90;
        let current = sections[0]?.dataset?.section || 'personaje';
        for (const s of sections) {
          if (s.getBoundingClientRect().top <= offset) current = s.dataset.section;
        }
        this.activeSection = current;
      };
      window.removeEventListener('scroll', this._scrollHandler);
      this._scrollHandler = update;
      window.addEventListener('scroll', update, { passive: true });
      update();
    },
  };
}
