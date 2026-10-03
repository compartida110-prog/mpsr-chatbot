# Verificación de referencias y cifras — protocolo V1.2 y Nota de Desviación

Generado por `scripts/verificar_referencias.py`. Cada valor de la columna «Repositorio» se **recalcula** desde los archivos; las afirmaciones se transcribieron del protocolo V1.2 (PDF) y de la Nota (DOCX), que este script no modifica.

**Resumen:** 37 afirmaciones · OK 30 · NOTA 1 · PLANIFICADO 1 · **DISCREPANCIA 5**

| # | Dónde se cita | El documento dice | Repositorio | Estado | Nota |
|---|---|---|---|---|---|
| 1 | Protocolo V1.2 | existe `README.md` | `README.md` | **OK** |  |
| 2 | Protocolo V1.2 | existe `corpus_audit.csv` | `corpus/corpus_audit.csv` | **OK** |  |
| 3 | Protocolo V1.2 | existe `domain.yml` | `domain.yml` | **OK** |  |
| 4 | Protocolo V1.2 | existe `rules.yml` | `data/rules.yml` | **OK** | se cita sin carpeta; está en data/ |
| 5 | Protocolo V1.2 | existe `incident_log.csv` | `incident_log.csv` | **OK** |  |
| 6 | Protocolo V1.2 | existe `logs/stats_modelos.txt` | `logs/stats_modelos.txt` | **OK** |  |
| 7 | Protocolo V1.2 | existe `logs/v2_corpus648/` | `logs/v2_corpus648` | **OK** |  |
| 8 | Protocolo V1.2 | existe `evidencias/p09_domain/` | `evidencias/p09_domain` | **OK** |  |
| 9 | Protocolo V1.2 | existe `evidencias/p11_1_pruebas/` | `evidencias/p11_1_pruebas` | **OK** |  |
| 10 | Protocolo V1.2 | existe `REPORTE_REEVALUACION.md` | `evidencias/v3_corpus708/REPORTE_REEVALUACION.md` | **NOTA** | se cita sin carpeta; está en evidencias/v3_corpus708/ (hay otro, de P11.1 con 324/648 frases, en evidencias/p11_1_pruebas/REPORTE_FALLAS.md) |
| 11 | Protocolo V1.2 | existen carpetas `logs/BASE-*` | 14 carpetas | **OK** |  |
| 12 | Protocolo V1.2 | existen carpetas `logs/RASA-*` | 17 carpetas | **OK** |  |
| 13 | Protocolo V1.2 (T03) | «corpus_metadata.csv (v2)» es el corpus de 648 frases | corpus_metadata.csv tiene 708 frases (es la v3); la v2 está en corpus/historico/corpus_metadata_v2_648.csv | **DISCREPANCIA** | el documento cita la versión v2 con un nombre de archivo que hoy contiene la v3 |
| 14 | Protocolo V1.2 (T05) | «dataset_split.csv (V1.1)» es la partición V1.1 (ejecutada) | dataset_split.csv tiene 708 filas (partición de la v3); la V1.1 está en corpus/historico/dataset_split_v2_648.csv | **DISCREPANCIA** | el archivo actual asigna la misma partición que la V1.1 en 648 de las 648 frases comunes |
| 15 | Protocolo V1.2 (T05) | «dataset_split_v3.csv (V1.2, planificado)» | no existe todavía; lo generará scripts/split_corpus_v3.py en corpus/v3_real/ | **PLANIFICADO** | coherente con el estado Planificado |
| 16 | Seguimiento (Notas) / guía | existen `Lote1_Formularios_lenguaje_real_v2.pdf`, `situaciones_lote1_v1.csv` e `Instrucciones_ClaudeCode_lote_real_v2.md` | Lote1_Formularios_lenguaje_real_v2.pdf: sí, situaciones_lote1_v1.csv: sí, Instrucciones_ClaudeCode_lote_real_v2.md: sí | **OK** |  |
| 17 | Protocolo 2.3 / 5.5 | 54 intenciones (44 de trámites y 10 conversacionales) en 9 categorías | 54 intenciones (44 de trámites y 10 conversacionales), 9 categorías | **OK** |  |
| 18 | Protocolo 2.4.2 | 56 situaciones: una por intención y tres para fuera_de_alcance, en 5 formularios (A–E) | 56 situaciones, 54 intenciones, fuera_de_alcance x3 | **OK** |  |
| 19 | Seguimiento (Notas) | 12/11/11/11/11 situaciones por formulario | 12/11/11/11/11 | **OK** |  |
| 20 | Protocolo 2.4.2 | con 20 participantes cada situación queda respondida por 4 personas | 20 participantes / 5 formularios (rotación A–E) = 4 por formulario | **OK** |  |
| 21 | Protocolo P09 / T07; Nota | 54 de 54 respuestas redactadas; 40 de las 44 de trámites con [Verificar] | 54 respuestas sin [PENDIENTE] de 54; 40 de 44 con [Verificar] | **OK** |  |
| 22 | Protocolo 2.11 / P11.1 / T06; Nota | F1 macro en test (partición de P05): Rasa/DIET 0.624 y SVM 0.648 | Rasa/DIET 0.624 y SVM 0.648 (logs/rasa_test.csv, logs/baseline_test.csv) | **OK** |  |
| 23 | Protocolo 2.11 / P11.1; Nota | validación cruzada agrupada por base_phrase_id: Rasa/DIET 0.655 y SVM 0.637 | Rasa/DIET 0.655 y SVM 0.637 (logs/P11_1_crossval_agrupada/folds_metrics.csv) | **OK** |  |
| 24 | Protocolo 2.11; Nota | validación cruzada nativa de Rasa 0.778 (inflada por fuga) | 0.778 (evidencias/p11_1_pruebas/salidas/03_rasa_test_nlu_crossval.txt) | **OK** | la CV nativa se hizo con el corpus v2 (648 frases); la agrupada, con el v3 (708) |
| 25 | Protocolo 2.11 / P11.1; Nota | smoke test de las 54 intenciones con consultas nuevas: 44 de 54 | 44 de 54 (logs/P11_1_smoke_test_v3_nuevas) | **OK** |  |
| 26 | Protocolo 5.2; Nota | 4 aciertos ganados y 7 perdidos en el smoke test; McNemar p ≈ 0.55 | 4 ganados y 7 perdidos; McNemar exacto p = 0.549 | **OK** |  |
| 27 | Protocolo 2.10 / T07; Nota | en el smoke test, 9 de 10 errores habrían sido «no entendí» a costa de 6 de 44 aciertos (umbral 0.50) | 9 de 10 errores y 6 de 44 aciertos con confianza < 0.50 | **OK** |  |
| 28 | Protocolo 2.10 | umbral t entre 0.30 y 0.80 y puntaje = aciertos − 2 × errores con respuesta | scripts/fallback_threshold.py: t = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8], lambda = 2 | **OK** |  |
| 29 | Protocolo 5.2; Nota | horario_mesa_partes absorbió predicciones de requisitos_mesa_partes: exactitud 0.87 → 0.53 | 0.87 → 0.53 (predictions_test de las 5 semillas, v2 vs v3) | **OK** |  |
| 30 | Protocolo 5.2; Nota | «abrir un restaurante» se clasificó como fuera_de_alcance con 0.81 de confianza; la palabra aparecía una sola vez en el entrenamiento, en un ejemplo de fuera_de_alcance | detectó fuera_de_alcance con 0.81; «restaurante» aparece 1 vez/veces en el corpus v2 (fuera_de_alcance/train) | **OK** |  |
| 31 | Protocolo 5.3; Nota | ampliación del corpus: 60 frases, 20 grupos, 9 intenciones | 60 frases, 20 grupos, 9 intenciones | **OK** |  |
| 32 | Protocolo 5.3; Nota | la ampliación corrigió las 8 fallas | 8 de 8 intenciones que fallaban en el 1.er smoke test ahora son correctas (consultas originales, contaminadas) | **OK** |  |
| 33 | Protocolo 5.3; Nota | F1 test 0.634 → 0.624 (Rasa/DIET, corpus v2 → v3) | 0.6335 → 0.6241 | **DISCREPANCIA** | el valor exacto de v2 es 0.6335 (se redondea a 0.633) |
| 34 | Protocolo 2.8 / P05 / T05 | partición V1.1 (ejecutada): 70 % entrenamiento, 15 % validación y 15 % prueba | 486/81/81 frases = 75.0/12.5/12.5 % | **DISCREPANCIA** | con 4 grupos por intención la partición posible es 75/12.5/12.5; ya está registrado en incident_log.csv; el mecanismo descrito en 2.8 (3 grupos a train y 1 alternado) se verifica en la fila siguiente |
| 35 | Protocolo 2.8 | con 4 grupos por intención, 3 pasan a entrenamiento y el cuarto se asigna alternadamente a validación o a prueba | las 54 intenciones tienen 4 grupos, 3 en entrenamiento; el cuarto: 27 grupos a validación y 27 a prueba | **OK** |  |
| 36 | Protocolo 2.8 / 5.2; Nota | el test mide 27 de las 54 intenciones (3 frases cada una) y la validación las otras 27 | test: 27 intenciones con [3] frases; validación: 27 intenciones; sin solape: True | **OK** |  |
| 37 | Protocolo P16 / T15; Nota | 37 incidencias registradas | 39 incidencias en incident_log.csv | **DISCREPANCIA** | el tesista decidió ajustar la cifra una sola vez en la entrega final |

## No verificable con el repositorio (no se comprobó)

Cifras y afirmaciones que dependen de datos externos o de pasos aún no ejecutados: tamaño de muestra n = 120 y su fórmula, antecedentes (Vargas Ríos, 2022), línea base y post-test de P01 y P12–P14 (simulados), Alfa de Cronbach, recolección del lote 1, partición V1.2, evaluación sobre lenguaje real y umbral de confianza (planificados), y la redacción metodológica.

## Discrepancias a resolver antes de la entrega

- **Protocolo V1.2 (T03)** — ««corpus_metadata.csv (v2)» es el corpus de 648 frases»: el repositorio tiene corpus_metadata.csv tiene 708 frases (es la v3); la v2 está en corpus/historico/corpus_metadata_v2_648.csv. el documento cita la versión v2 con un nombre de archivo que hoy contiene la v3
- **Protocolo V1.2 (T05)** — ««dataset_split.csv (V1.1)» es la partición V1.1 (ejecutada)»: el repositorio tiene dataset_split.csv tiene 708 filas (partición de la v3); la V1.1 está en corpus/historico/dataset_split_v2_648.csv. el archivo actual asigna la misma partición que la V1.1 en 648 de las 648 frases comunes
- **Protocolo 5.3; Nota** — «F1 test 0.634 → 0.624 (Rasa/DIET, corpus v2 → v3)»: el repositorio tiene 0.6335 → 0.6241. el valor exacto de v2 es 0.6335 (se redondea a 0.633)
- **Protocolo 2.8 / P05 / T05** — «partición V1.1 (ejecutada): 70 % entrenamiento, 15 % validación y 15 % prueba»: el repositorio tiene 486/81/81 frases = 75.0/12.5/12.5 %. con 4 grupos por intención la partición posible es 75/12.5/12.5; ya está registrado en incident_log.csv; el mecanismo descrito en 2.8 (3 grupos a train y 1 alternado) se verifica en la fila siguiente
- **Protocolo P16 / T15; Nota** — «37 incidencias registradas»: el repositorio tiene 39 incidencias en incident_log.csv. el tesista decidió ajustar la cifra una sola vez en la entrega final
