# Erratas al protocolo V1.2 y a la Nota de Desviación (3 de octubre de 2026)

`scripts/verificar_referencias.py` compara las rutas y cifras de los documentos con los archivos del repositorio
(resultado: `evidencias/v3_real/verificacion_referencias.md`). Encontró **5 discrepancias**. En cuatro de ellas el repositorio es el correcto
y el texto del documento quedó desactualizado; la quinta es una imprecisión de redacción. **Los PDF y DOCX no se modificaron**: el protocolo V1.2 solo
existe como PDF y la nota debe seguir coincidiendo en sus dos formatos, así que estas erratas se aplican al reemitir los documentos.

Estado de todas: **Pendiente de aplicar en los documentos.** Ya están corregidas dentro del repositorio (README, `corpus/historico/LEEME.md`,
comentario de `scripts/expand_corpus.py`) y `verificar_referencias.py` las marca como «errata registrada».

---

## E1 — `corpus_metadata.csv (v2)` en la matriz (fila T03)

| | |
|---|---|
| **Dónde** | Protocolo V1.2, sección 4, fila **T03**, columna «Evidencia verificable»; también relevante para P11.1 / T06 / T07.1 |
| **Dice** | `corpus_metadata.csv (v2)` |
| **Debe decir** | `corpus_metadata.csv (v3: 708 frases; la v2, de 648, está en corpus/historico/corpus_metadata_v2_648.csv)` |
| **Por qué** | `corpus/corpus_metadata.csv` contiene hoy la **v3** (708 frases = v2 + 60 frases de `corpus/ampliacion_v3.csv`). Los resultados de P11.1 que cita el documento (F1 test 0.624 y 0.648; validación cruzada agrupada 0.655 y 0.637; smoke test 44/54) se obtuvieron con la **v3**, no con la v2 |
| **Evidencia** | `corpus/corpus_summary.json` (708 frases, 236 grupos); `evidencias/v3_corpus708/`; `logs/rasa_test.csv` |

## E2 — `dataset_split.csv (V1.1)` en la matriz (fila T05)

| | |
|---|---|
| **Dónde** | Protocolo V1.2, sección 4, fila **T05**, columna «Evidencia verificable» |
| **Dice** | `dataset_split.csv (V1.1); dataset_split_v3.csv (V1.2, planificado)` |
| **Debe decir** | `corpus/historico/dataset_split_v2_648.csv (V1.1, 648 frases); corpus/dataset_split.csv (partición del corpus v3, 708 frases); corpus/v3_real/dataset_split_v3.csv (V1.2, planificado)` |
| **Por qué** | `corpus/dataset_split.csv` es la partición del corpus v3 (546/81/81). La V1.1 vive en `corpus/historico/`. Ambas asignan la misma partición a las 648 frases comunes (verificado por el script) |

## E3 — «F1 test 0.634 → 0.624»

| | |
|---|---|
| **Dónde** | Protocolo V1.2, sección **5.3** («Medidas ya ejecutadas», 2.ª fila); Nota de Desviación, sección **4** («Medidas ya ejecutadas», 2.ª fila) |
| **Dice** | `Corrigió las 8 fallas; sin mejora global (F1 test 0.634 → 0.624)` |
| **Debe decir** | `Corrigió las 8 fallas; sin mejora global (F1 test 0.633 → 0.624)` (o, con más precisión, `0.6335 → 0.6241`) |
| **Por qué** | El valor exacto del F1 macro medio de Rasa/DIET con el corpus v2 es **0.63346**: a 3 decimales es 0.633. El «0.634» sale de redondear dos veces (0.6335 → 0.634) |
| **Evidencia** | `logs/v2_corpus648/rasa_test.csv` (media de las 5 semillas = 0.6334624…); `logs/rasa_test.csv` (0.6241406…) |

## E4 — Partición V1.1 «70/15/15»

| | |
|---|---|
| **Dónde** | Protocolo V1.2, sección **2.8** («Partición V1.1 (ejecutada): 70 % entrenamiento, 15 % validación y 15 % prueba …»); paso **P05** («Aplicar partición 70/15/15 …»); fila **T05**, columna «Configuración / control» («70/15/15; seed = 42 …») |
| **Dice** | `70 % entrenamiento, 15 % validación y 15 % prueba` / `70/15/15` |
| **Debe decir** | `partición por grupos (base_phrase_id) con semilla 42: con 4 grupos por intención, 3 pasan a entrenamiento y el cuarto se asigna alternadamente a validación o a prueba (486/81/81 frases = 75/12.5/12.5 %; nominal 70/15/15)` |
| **Por qué** | La partición ejecutada es 486/81/81 = 75/12.5/12.5 %. El mecanismo que describe el texto (3 de 4 grupos a entrenamiento, el cuarto alterna) sí coincide con los datos: las 54 intenciones tienen 4 grupos, 3 en entrenamiento, y el cuarto va 27 a validación y 27 a prueba. Ya figura en `incident_log.csv` |
| **Evidencia** | `corpus/historico/dataset_split_v2_648.csv`; `scripts/expand_corpus.py` |

## E5 — «37 incidencias registradas»

| | |
|---|---|
| **Dónde** | Protocolo V1.2, pasos **P16** y fila **T15** («Ejecutado (37 incidencias)»); Nota de Desviación, última línea («… con 37 incidencias registradas») |
| **Dice** | `37 incidencias` |
| **Debe decir** | `N incidencias a la fecha de entrega (registro vivo en incident_log.csv)`. Hoy: **41** |
| **Por qué** | `incident_log.csv` es un registro vivo y cada paso nuevo agrega filas; una cifra fija queda obsoleta enseguida. Conviene calcularla el día de la entrega con `python scripts/verificar_referencias.py` (fila «incidencias») o con `wc -l` del archivo menos el encabezado |

---

## Cómo comprobar que están aplicadas

Tras reemitir los documentos, actualizar las afirmaciones transcritas en `scripts/verificar_referencias.py` (lista `reg(...)` de cada fila) y ejecutarlo: las
5 filas deben pasar a OK y el resumen debe decir «DISCREPANCIA 0».
