# Comparación de Campos: Web Editor ↔ PDF

> PDF de referencia: `Hoja-Personaje-Editable-Completa-ES.pdf` (937 campos, 2 páginas)
> Generado: 2026-03-15

## Leyenda
| Símbolo | Significado |
|---------|-------------|
| ✅ | Editable en web **y** exportado al PDF |
| ⚪ | Calculado automáticamente en web, exportado al PDF |
| 🌐 | Solo en la web (sin campo PDF equivalente) |
| 📄 | En PDF y mapeado, pero sin input editable en la web |
| ❌ | En PDF pero no mapeado en `fill_pdf.py` (campo en blanco al exportar) |

---

## PÁGINA 1

### 1. Cabecera — Identidad del Personaje

| Campo PDF | Campo web (x-model) | Etiqueta web | Estado |
|-----------|---------------------|--------------|--------|
| `Nombre-Personaje` | `character.basic_info.name` | Nombre del Personaje | ✅ |
| `Clase-Y-Nivel` | `cls.name` + `cls.level` (bucle multiclase) | Clase / Nivel | ✅ |
| `Trasfondo` | `character.basic_info.background` | Trasfondo | ✅ |
| `Especie` | `character.basic_info.species` | Especie | ✅ |
| `Alineamiento` | `character.basic_info.alignment` | Alineamiento | ✅ |
| `PX-Personaje` | `character.basic_info.experience_points` | Puntos de Experiencia | ✅ |
| `Tamano` | `character.appearance.size` | Tamaño | ✅ |
| `Nombre-Jugador` | `character.basic_info.player_name` | Nombre del Jugador | ✅ |
| `Vision` | `character.basic_info.vision` | Visión | ✅ |
| — | `character.basic_info.campaign` | Campaña / Aventura | 🌐 |
| — | `cls.subclass` | Subclase | 🌐 |

### 2. Puntuaciones de Habilidad

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Puntuacion-Fuerza` | `ability_scores.strength.score` | FUE (puntuación) | ✅ |
| `Modificador-Fuerza` | calculado de `.score` | FUE (mod) | ⚪ |
| `Puntuacion-Destreza` | `ability_scores.dexterity.score` | DES (puntuación) | ✅ |
| `Modificador-Destreza` | calculado | DES (mod) | ⚪ |
| `Puntuacion-Constitucion` | `ability_scores.constitution.score` | CON (puntuación) | ✅ |
| `Modificador-Constitucion` | calculado | CON (mod) | ⚪ |
| `Puntuacion-Inteligencia` | `ability_scores.intelligence.score` | INT (puntuación) | ✅ |
| `Modificador-Inteligencia` | calculado | INT (mod) | ⚪ |
| `Puntuacion-Sabiduria` | `ability_scores.wisdom.score` | SAB (puntuación) | ✅ |
| `Modificador-Sabiduria` | calculado | SAB (mod) | ⚪ |
| `Puntuacion-Carisma` | `ability_scores.charisma.score` | CAR (puntuación) | ✅ |
| `Modificador-Carisma` | calculado | CAR (mod) | ⚪ |

### 3. Inspiración y Bonificador de Competencia

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Check-Inspiracion-Heroica` | `basic_info.inspiration` (botón toggle) | ☆ Inspiración Heroica | ✅ |
| `Inspiracion-Heroica` (campo texto) | siempre vacío — el checkbox gestiona el estado | — | 📄 |
| `Bonificador-Competencia` | `character.proficiency_bonus` | Bon. Competencia | ✅ |

### 4. Tiradas de Salvación

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Check-Competencia-Salvacion-Fuerza` | toggle → `saving_throws.strength.proficient` | • FUE | ✅ |
| `Modificador-Salvacion-Fuerza` | calculado | FUE total | ⚪ |
| `Check-Competencia-Salvacion-Destreza` | toggle → `saving_throws.dexterity.proficient` | • DES | ✅ |
| `Modificador-Salvacion-Destreza` | calculado | DES total | ⚪ |
| `Check-Competencia-Salvacion-Constitucion` | toggle → `saving_throws.constitution.proficient` | • CON | ✅ |
| `Modificador-Salvacion-Constitucion` | calculado | CON total | ⚪ |
| `Check-Competencia-Salvacion-Inteligencia` | toggle → `saving_throws.intelligence.proficient` | • INT | ✅ |
| `Modificador-Salvacion-Inteligencia` | calculado | INT total | ⚪ |
| `Check-Competencia-Salvacion-Sabiduria` | toggle → `saving_throws.wisdom.proficient` | • SAB | ✅ |
| `Modificador-Salvacion-Sabiduria` | calculado | SAB total | ⚪ |
| `Check-Competencia-Salvacion-Carisma` | toggle → `saving_throws.charisma.proficient` | • CAR | ✅ |
| `Modificador-Salvacion-Carisma` | calculado | CAR total | ⚪ |

### 5. Habilidades (Skills)

> El PDF mapea 18 habilidades. Por cada habilidad hay 3 campos: `Check-Competencia-{X}` + `Check-Pericia-{X}` + `Modificador-{X}`.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Check-Competencia-Acrobacias` + `Check-Pericia-Acrobacias` | toggle + "E" → `skills.acrobacias.proficient/.expertise` | Acrobacias (DES) | ✅ |
| `Modificador-Acrobacias` | calculado | total | ⚪ |
| `Check-Competencia-Atletismo` + `Check-Pericia-Atletismo` | `skills.atletismo.proficient/.expertise` | Atletismo (FUE) | ✅ |
| `Modificador-Atletismo` | calculado | total | ⚪ |
| `Check-Competencia-Conocimiento-Arcano` + Pericia | `skills.arcanos.proficient/.expertise` | Arcanos (INT) | ✅ |
| `Modificador-Conocimiento-Arcano` | calculado | total | ⚪ |
| `Check-Competencia-Engano` + Pericia | `skills.enganar.proficient/.expertise` | Engaño (CAR) | ✅ |
| `Modificador-Engano` | calculado | total | ⚪ |
| `Check-Competencia-Historia` + Pericia | `skills.historia.proficient/.expertise` | Historia (INT) | ✅ |
| `Modificador-Historia` | calculado | total | ⚪ |
| `Check-Competencia-Perspicacia` + Pericia | `skills.perspicacia.proficient/.expertise` | Perspicacia (SAB) | ✅ |
| `Modificador-Perspicacia` | calculado | total | ⚪ |
| `Check-Competencia-Intimidacion` + Pericia | `skills.intimidar.proficient/.expertise` | Intimidación (CAR) | ✅ |
| `Modificador-Intimidacion` | calculado | total | ⚪ |
| `Check-Competencia-Investigacion` + Pericia | `skills.investigacion.proficient/.expertise` | Investigación (INT) | ✅ |
| `Modificador-Investigacion` | calculado | total | ⚪ |
| `Check-Competencia-Medicina` + Pericia | `skills.medicina.proficient/.expertise` | Medicina (SAB) | ✅ |
| `Modificador-Medicina` | calculado | total | ⚪ |
| `Check-Competencia-Naturaleza` + Pericia | `skills.naturaleza.proficient/.expertise` | Naturaleza (INT) | ✅ |
| `Modificador-Naturaleza` | calculado | total | ⚪ |
| `Check-Competencia-Percepcion` + Pericia | `skills.percepcion.proficient/.expertise` | Percepción (SAB) | ✅ |
| `Modificador-Percepcion` | calculado | total | ⚪ |
| `Check-Competencia-Interpretacion` + Pericia | `skills.interpretacion.proficient/.expertise` | Interpretación (CAR) | ✅ |
| `Modificador-Interpretacion` | calculado | total | ⚪ |
| `Check-Competencia-Persuasion` + Pericia | `skills.persuasion.proficient/.expertise` | Persuasión (CAR) | ✅ |
| `Modificador-Persuasion` | calculado | total | ⚪ |
| `Check-Competencia-Religion` + Pericia | `skills.religion.proficient/.expertise` | Religión (INT) | ✅ |
| `Modificador-Religion` | calculado | total | ⚪ |
| `Check-Competencia-Juego-De-Manos` + Pericia | `skills.juego_de_manos.proficient/.expertise` | Juego de Manos (DES) | ✅ |
| `Modificador-Juego-De-Manos` | calculado | total | ⚪ |
| `Check-Competencia-Sigilo` + Pericia | `skills.sigilo.proficient/.expertise` | Sigilo (DES) | ✅ |
| `Modificador-Sigilo` | calculado | total | ⚪ |
| `Check-Competencia-Supervivencia` + Pericia | `skills.supervivencia.proficient/.expertise` | Supervivencia (SAB) | ✅ |
| `Modificador-Supervivencia` | calculado | total | ⚪ |
| `Check-Competencia-Trato-Con-Animales` + Pericia | `skills.trato_con_animales.proficient/.expertise` | Trato con Animales (SAB) | ✅ |
| `Modificador-Trato-Con-Animales` | calculado | total | ⚪ |

### 6. Percepción Pasiva y Competencias de Armadura

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Percepcion-Pasiva` | calculado (10 + skills.percepcion.total) | — | ⚪ |
| `Check-Competencia-Armadura-Ligera` | `proficiencies.armor_flags.light` | ☑ Ligera | ✅ |
| `Check-Competencia-Armadura-Media` | `proficiencies.armor_flags.medium` | ☑ Media | ✅ |
| `Check-Competencia-Armadura-Pesada` | `proficiencies.armor_flags.heavy` | ☑ Pesada | ✅ |
| `Check-Competencia-Escudo` | `proficiencies.armor_flags.shield` | ☑ Escudo | ✅ |
| `Check-Escudo` | `combat.shield_equipped` | Escudo equipado | ✅ |
| `Competencia-Armas` | `proficiencies.weapons` (textarea) | Armas | ✅ |
| `Competencia-Herramientas` | `proficiencies.tools` (textarea) | Herramientas | ✅ |

### 7. Estadísticas de Combate

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Clase-Armadura` | `combat.armor_class` | Clase de Armadura | ✅ |
| `Iniciativa` | `combat.initiative` | Iniciativa | ✅ |
| `Velocidad` | `combat.speed.walking_meters` | Velocidad (m) | ✅ |
| — | `combat.speed.swim_meters` | Nadando (m) | 🌐 |
| — | `combat.speed.fly_meters` | Volando (m) | 🌐 |
| — | `combat.speed.climb_meters` | Trepando (m) | 🌐 |

### 8. Puntos de Golpe

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Puntos-Golpe-Maximo` | `combat.hit_points.maximum` | Máximo | ✅ |
| `Puntos-Golpe-Actuales` | `combat.hit_points.current` | Actuales | ✅ |
| `Puntos-Golpe-Temporales` | `combat.hit_points.temporary` | Temporales | ✅ |
| — | `combat.shield_equipped` | Escudo equipado (checkbox) | 🌐 |
| — | `combat.exhaustion` | Agotamiento (0–10) | 🌐 |
| — | `combat.concentration.active` | Concentrando (checkbox) | 🌐 |
| — | `combat.concentration.spell` | En qué conjuro (texto) | 🌐 |

### 9. Dados de Golpe y Tiradas de Muerte

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Dados-Golpe-Maximos` | `combat.hit_dice.count` + `combat.hit_dice.type` | Dados de Golpe (NdX) | ✅ |
| `Dados-Golpe-Gastados` | — | — | ❌ |
| `Check-Dado-Golpe.1`–`20` | derivado de `combat.hit_dice.remaining` en fill_pdf.py | — | 📄 |
| — | `combat.hit_dice.used` (número) | Usados hoy | 🌐 |
| `Check-Salvacion-Muerte.Exito.1`–`3` | `combat.death_saves.successes` (círculos clickables) | Éxitos | ✅ |
| `Check-Salvacion-Muerte.Fallo.1`–`3` | `combat.death_saves.failures` (círculos clickables) | Fallos | ✅ |

> ⚠ Los `Check-Dado-Golpe.N` son 20 checkboxes individuales en el PDF. En la web se gestiona con un número entero "Usados hoy"; fill_pdf.py los convierte automáticamente.

### 10. Ataques y Armas

> El PDF tiene exactamente 5 filas. La web admite armas ilimitadas; solo las primeras 5 se exportan.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Arma-1-Nombre` – `Arma-5-Nombre` | `attacks[i].name` (bucle) | Nombre del ataque | ✅ |
| `Arma-1-Bonificador-Ataque` – `Arma-5-Bonificador-Ataque` | `attacks[i].attack_bonus` | Bono Atq. | ✅ |
| `Arma-1-Dano-Tipo` – `Arma-5-Dano-Tipo` | `attacks[i].damage_display` (calculado) | Daño / Tipo | ✅ |
| `Arma-1-Notas` – `Arma-5-Notas` | — | — | ❌ |
| — | `attacks[i].damage_dice_count` + `damage_dice_type` | Dados de daño | 🌐 |
| — | `attacks[i].damage_bonus` | Bonus plano | 🌐 |
| — | `attacks[i].damage_type` | Tipo de daño | 🌐 |
| — | `attacks[i].custom_bonuses[j].name/.value` | Bonos personalizados | 🌐 |

> ⚠ `Arma-N-Notas` (campo de notas por arma) no tiene equivalente web — no implementado.

### 11. Competencias e Idiomas (columna derecha pág. 1)

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Idiomas` | `languages` (lista concatenada) | Idiomas | ✅ |
| `Idioma.1`–`Idioma.4` | `languages[0..3]` | (entradas individuales) | ✅ |
| `Atributos-Especie` | `features_and_traits.species` (lista) | Rasgos de Especie | ✅ |
| `Rasgos-Clase-1` | primera mitad de `features_and_traits.class_features` | Rasgos de Clase | ✅ |
| `Rasgos-Clase-2` | segunda mitad de `features_and_traits.class_features` | Rasgos de Clase | ✅ |
| `Dotes` | `features_and_traits.feats` (lista) | Dotes | ✅ |

> ⚠ En la web cada rasgo tiene `name`, `source` y `description` enriquecida. En el PDF se vuelca como texto plano concatenado.

---

## PÁGINA 2

### 12. Datos del Personaje — Apariencia

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Dato-Personaje.Edad` | `appearance.age` | Edad | ✅ |
| `Dato-Personaje.Altura` | `appearance.height` | Altura | ✅ |
| `Dato-Personaje.Peso` | `appearance.weight` | Peso | ✅ |
| `Dato-Personaje.Ojos` | `appearance.eyes` | Ojos | ✅ |
| `Dato-Personaje.Piel` | `appearance.skin` | Piel | ✅ |
| `Dato-Personaje.Pelo` | `appearance.hair` | Cabello | ✅ |
| `Dato-Personaje.Genero` | `appearance.gender` | Género | ✅ |
| `Dato-Personaje.Tamano` | derivado de `basic_info.species` (SPECIES_SIZE) | — | ⚪ |

### 13. Datos del Personaje — Personalidad

> El PDF tiene slots fijos (3 por categoría). La web admite listas libres; solo los primeros 3 se exportan.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Dato-Personaje.Rasgo-Personalidad-1`–`3` | `background_details.personality_traits[0..2]` | Rasgos de Personalidad | ✅ |
| `Dato-Personaje.Ideal-1`–`3` | `background_details.ideals[0..2]` | Ideales | ✅ |
| `Dato-Personaje.Vinculo-1`–`3` | `background_details.bonds[0..2]` | Vínculos | ✅ |
| `Dato-Personaje.Defecto-1`–`3` | `background_details.flaws[0..2]` | Defectos | ✅ |

### 14. Datos del Personaje — Deidad, Aliados, Apariencia Física, Trasfondo Libre

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Dato-Personaje.Deidad-Dominio` | `background_details.deity` | Deidad / Dominio | ✅ |
| `Dato-Personaje.Descripcion-Deidad` | `background_details.deity_description` | Descripción de la deidad | ✅ |
| `Dato-Personaje.Amigo-Aliado-1`–`3` | `notes.allies` (partido en líneas) | Aliados y organizaciones | ✅ |
| `Dato-Personaje.Enemigo-1`–`3` | `notes.enemies` (partido en líneas) | Enemigos | ✅ |
| `Dato-Personaje.Apariencia-1`–`3` | `notes.physical_description` (partido en líneas) | Descripción Física | ✅ |
| `Dato-Personaje.Trasfondo-Otros-1` | `background_details.description` | — | 📄 |
| `Dato-Personaje.Trasfondo-Otros-2`–`7` | `notes.other_notes` (partido en líneas) | Notas Adicionales | ✅ |
| — | `notes.backstory` | Historia del personaje | 🌐 |

> ⚠ `backstory` solo existe en la web; el PDF no tiene un campo de texto libre largo para la historia.
> ⚠ `Deidad-Dominio` y `Descripcion-Deidad` también existen como campos "planos" fuera de la jerarquía `Dato-Personaje` y se mapean igual.

### 15. Monedas

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Piezas.Cobre` | `inventory.currency.CP` | Cobre | ✅ |
| `Piezas.Plata` | `inventory.currency.SP` | Plata | ✅ |
| `Piezas.Electro` | `inventory.currency.EP` | Electro | ✅ |
| `Piezas.Oro` | `inventory.currency.GP` | Oro | ✅ |
| `Piezas.Platino` | `inventory.currency.PP` | Platino | ✅ |

### 16. Inventario

> El PDF tiene 47 filas fijas. La web admite ítems ilimitados; solo los primeros 47 se exportan.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Objeto-Nombre.1`–`47` | `inventory.items[i].name` | Objeto | ✅ |
| `Objeto-Cantidad.1`–`47` | `inventory.items[i].quantity` | Cant. | ✅ |
| `Objeto-Puesto.1`–`47` (✓ Equipado) | `items[i].location == "Equipado"` | Ubicación | ✅ |
| `Objeto-Mochila.1`–`47` (✓ Transportado) | `items[i].location == "Transportado"` | Ubicación | ✅ |
| `Objeto-Bolsa.1`–`47` (✓ Otros) | `items[i].location == "Otros"` | Ubicación | ✅ |
| — | `inventory.items[i].weight_kg` | Peso (kg) | 🌐 |

> ⚠ En la web `location` es un selector único (—/Equipado/Transportado/Otros). El PDF usa 3 checkboxes independientes por fila.

### 17. Conjuros — Estadísticas de Lanzamiento

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Caracteristica-Clase-Lanzador-Conjuro` | `spellcasting.spellcasting_ability` | Habilidad de Conjuración | ✅ |
| `Clase-Lanzador-Conjuros` | derivado de `basic_info.classes[0].name` | — | ⚪ |
| `Aptitud-Magica` | `spellcasting.spell_attack_bonus` | Bono de Ataque Conj. | ✅ |
| `CD-Salvacion-Conjuros` | `spellcasting.spell_save_dc` | CD de Salvación | ✅ |
| `Puntos-Hechiceria-Max` | recurso con "ki"/"concentraci"/"hechiceria" en nombre | (desde Recursos) | 📄 |
| `Puntos-Hechiceria-Gastados` | `max - current` del mismo recurso | (desde Recursos) | 📄 |
| `Conjuros-Concidos` (sic en PDF) | conteo total de conjuros | — | ⚪ |
| `Conjuros-Preparados` | conteo de conjuros con `prepared=True` | — | ⚪ |
| `Modificador-Aptitud-Magica` | — | — | ❌ *campo fantasma — no existe en el PDF* |
| `Bonificador-Ataque-Conjuros` | — | — | ❌ *campo fantasma — no existe en el PDF* |

### 18. Conjuros — Espacios por Nivel

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Total-Espacios-Conjuro.1`–`9` | `spellcasting.spell_slots.level_N.total` | Nivel N — Total | ✅ |
| — | `spellcasting.spell_slots.level_N.used` | Nivel N — Usados | 🌐 |

> ⚠ El PDF almacena solo el total de espacios. Los usados (gastos durante la partida) solo existen en la web.

### 19. Conjuros — Trucos (Nivel 0)

> El PDF tiene 7 slots para trucos. La web admite lista libre.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Nombre-Conjuro-Nivel-0.1`–`7` | `spellcasting.spells.cantrips[i].name` | Nombre del truco | ✅ |
| — | `spells.cantrips[i].casting_time` | Tiempo de lanzamiento | 🌐 |

### 20. Conjuros por Nivel (1–9)

> Slots fijos en PDF: N1=11, N2=10, N3=9, N4=9, N5=8, N6=8, N7=7, N8=7, N9=7 (76 total + 7 trucos = 83).
> La web admite listas de longitud libre por nivel.

| Campo PDF | Campo web | Etiqueta web | Estado |
|-----------|-----------|--------------|--------|
| `Nombre-Conjuro-Nivel-{N}.{i}` | `spellcasting.spells.level_N[i].name` | Nombre del conjuro | ✅ |
| `Check-Preparado-Conjuro-Nivel-{N}.{i}` | `spells.level_N[i].prepared` (toggle) | • (preparado) | ✅ |
| — | `spells.level_N[i].casting_time` | Tiempo de lanzamiento | 🌐 |

---

## SECCIÓN ESPECIAL — Recursos de Clase (solo web)

> Los recursos de clase **no tienen campo directo en el PDF**, salvo la derivación automática de Ki/Hechicería.

| Campo web | Descripción | Estado |
|-----------|-------------|--------|
| `resources[key].name` | Nombre del recurso (ej. "Puntos Ki") | 🌐 |
| `resources[key].max` | Máximo de usos | 🌐 |
| `resources[key].current` | Usos disponibles | 🌐 |
| `resources[key].pip_states[]` | Estado individual de cada pip (disponible/gastado) | 🌐 |
| `resources[key].recharge` | Tipo de recarga (corto / largo / manual) | 🌐 |
| `resources[key].short_rest_note` | Nota de descanso corto | 🌐 |
| `resources[key].long_rest_note` | Nota de descanso largo | 🌐 |
| `resources[key].trigger` | Condición de activación | 🌐 |

> ⚠ Excepción: si el recurso contiene "ki", "hechiceria" o "concentraci" en el nombre,
> sus valores `max` y `max - current` se exportan automáticamente a `Puntos-Hechiceria-Max/Gastados`.

---

## Resumen de Gaps

### Campos del PDF sin mapeo en fill_pdf.py (❌)

| Campo PDF | Motivo |
|-----------|--------|
| `Arma-1-Notas` – `Arma-5-Notas` | Sin equivalente en la web |
| `Dados-Golpe-Gastados` | La web usa número entero, no campo de texto |
| `Modificador-Aptitud-Magica` | Campo fantasma — no existe físicamente en el PDF |
| `Bonificador-Ataque-Conjuros` | Campo fantasma — no existe físicamente en el PDF |
| ~329 campos restantes (de 937) | Duplicados, campos de layout vacíos, o variantes no usadas |

### Campos web sin reflejo en el PDF (🌐 principales)

| Campo web | Sección web |
|-----------|-------------|
| `basic_info.campaign` | Identidad |
| `basic_info.classes[].subclass` | Identidad |
| `combat.speed.swim/fly/climb_meters` | Estadísticas |
| `combat.exhaustion` | Combate |
| `combat.concentration.active/.spell` | Combate |
| `combat.hit_dice.used` (número) | Combate |
| `inventory.items[i].weight_kg` | Inventario |
| `spellcasting.spell_slots.level_N.used` | Conjuros |
| `spells[level][i].casting_time` | Conjuros |
| `notes.backstory` | Trasfondo |
| Todos los campos de Recursos (`resources[*]`) | Recursos |
| `attacks[i].custom_bonuses` | Combate |

---

*Generado a partir de `scripts/fill_pdf.py → build_field_map()` y `editor/templates/index.html`*
