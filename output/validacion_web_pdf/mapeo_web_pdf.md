# Mapeo Web -> PDF (Resumen)

Este documento resume el mapeo por categorias. El mapeo exhaustivo, ruta por ruta de todos los campos del JSON web, esta en:

- output/validacion_web_pdf/iter_01_web_to_pdf_map.json
- output/validacion_web_pdf/iter_02_web_to_pdf_map.json

## Cobertura por iteracion

- Rutas web analizadas: 895
- Rutas web con destino PDF: 367
- Rutas web sin destino PDF en plantilla actual: 528
- Campos esperados por mapeo: 318
- Campos con coincidencia exacta en PDF generado: 291
- Mapeos definidos pero sin widget fisico en plantilla: 27
- Discrepancias de valor: 0

## Principales equivalencias

### Identidad
- basic_info.name -> Nombre-Personaje
- basic_info.classes[*] -> Clase-Y-Nivel
- basic_info.background -> Trasfondo
- basic_info.species -> Especie
- basic_info.alignment -> Alineamiento
- basic_info.experience_points -> PX-Personaje

### Caracteristicas y tiradas
- ability_scores.{ability}.score -> Puntuacion-{Habilidad}
- ability_scores.{ability}.modifier -> Modificador-{Habilidad}
- saving_throws.{ability}.total -> Modificador-Salvacion-{Habilidad}
- saving_throws.{ability}.proficient -> Check-Competencia-Salvacion-{Habilidad}
- skills.{skill}.total -> Modificador-{Skill}
- skills.{skill}.proficient -> Check-Competencia-{Skill}
- skills.{skill}.expertise -> Check-Pericia-{Skill}

### Combate
- combat.armor_class -> Clase-Armadura
- combat.initiative -> Iniciativa
- combat.speed.walking_meters -> Velocidad
- combat.hit_points.current -> Puntos-Golpe-Actuales
- combat.hit_points.maximum -> Puntos-Golpe-Maximo
- combat.hit_points.temporary -> Puntos-Golpe-Temporales
- combat.death_saves.successes/failures -> Check-Salvacion-Muerte.*
- combat.hit_dice.remaining -> Check-Dado-Golpe.1..20

### Ataques
- attacks[0..4].name -> Arma-{i}-Nombre
- attacks[0..4].attack_bonus -> Arma-{i}-Bonificador-Ataque (sin widget en plantilla)
- attacks[0..4].damage, damage_type -> Arma-{i}-Dano-Tipo (sin widget en plantilla)
- attacks[0..4].properties[*] -> Arma-{i}-Notas

### Competencias
- proficiencies.armor_flags.* -> Check-Competencia-Armadura-*
- proficiencies.armor[*] -> Check-Competencia-Armadura-* (fallback por texto)
- proficiencies.weapons[*] -> Competencia-Armas (sin widget en plantilla)
- proficiencies.tools[*] -> Competencia-Herramientas (sin widget en plantilla)

### Rasgos y dotes
- features_and_traits.species[*].* -> Atributos-Especie (sin widget en plantilla)
- features_and_traits.feats[*].* -> Dotes (sin widget en plantilla)
- features_and_traits.class_features[*].* -> Rasgos-Clase-1 / Rasgos-Clase-2 (sin widget en plantilla)

### Inventario y dinero
- inventory.currency.CP/SP/EP/GP/PP -> Piezas.Cobre/Plata/Electro/Oro/Platino
- inventory.items[0..46].name -> Objeto-Nombre.{i}
- inventory.items[0..46].quantity -> Objeto-Cantidad.{i}
- inventory.items[0..46].location -> Objeto-Puesto/Mochila/Bolsa.{i}

### Idiomas
- languages -> Idiomas (sin widget en plantilla)
- languages[0..3] -> Idioma.1..4

### Trasfondo y notas
- background_details.personality_traits[0..2] -> Dato-Personaje.Rasgo-Personalidad-1..3
- background_details.ideals[0..2] -> Dato-Personaje.Ideal-1..3
- background_details.bonds[0..2] -> Dato-Personaje.Vinculo-1..3
- background_details.flaws[0..2] -> Dato-Personaje.Defecto-1..3
- background_details.description -> Dato-Personaje.Trasfondo-Otros-1
- notes.other_notes -> Dato-Personaje.Trasfondo-Otros-2..7
- notes.allies -> Dato-Personaje.Amigo-Aliado-1..3
- notes.enemies -> Dato-Personaje.Enemigo-1..3
- notes.physical_description -> Dato-Personaje.Apariencia-1..3

### Conjuros
- spellcasting.spellcasting_ability -> Caracteristica-Clase-Lanzador-Conjuro
- spellcasting.spell_attack_bonus -> Aptitud-Magica
- spellcasting.spell_save_dc -> CD-Salvacion-Conjuros
- spellcasting.spell_slots.level_{n}.total -> Total-Espacios-Conjuro.{n}
- spellcasting.spells.cantrips[i].name -> Nombre-Conjuro-Nivel-0.{i}
- spellcasting.spells.level_{n}[i].name -> Nombre-Conjuro-Nivel-{n}.{i}
- spellcasting.spells.level_{n}[i].prepared -> Check-Preparado-Conjuro-Nivel-{n}.{i}

## Grupos sin destino PDF (plantilla actual)

- inventory.gems[*]
- inventory.mounts[*]
- inventory.loaned[*]
- inventory.other_possessions
- combat.advantages_resistances[*]
- combat.ammunition[*]
- combat.concentration.*
- combat.exhaustion
- combat.speed.swim_meters/fly_meters/climb_meters/jump_long/jump_high/special_senses
- notes.general, notes.backstory, notes.organizations, notes.additional_notes, notes.other_possessions
- appearance.summary
- basic_info.campaign, basic_info.creation_date, basic_info.next_level_xp
- background_details.birth_place, background_details.birth_date, background_details.page_ref
- resources.* (solo se aprovecha una proyeccion parcial para puntos de hechiceria)
- spellcasting.sorcery_points_*, spellcasting.sorcery_pips
