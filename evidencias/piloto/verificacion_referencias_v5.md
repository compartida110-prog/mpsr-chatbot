# Verificación de referencias y cifras — protocolo V1.3 (v5) y Nota de Desviación (v5)

Generado por `scripts/verificar_referencias.py`. Cada valor de la columna «Repositorio» se **recalcula** desde los archivos; las afirmaciones se transcribieron del protocolo V1.3 (v5) y de la Nota (v5), que este script no modifica.

**Resumen:** 46 afirmaciones · OK 41 · NOTA 1 · PLANIFICADO 2 · **DISCREPANCIA 2** (las erratas E1–E5 de la V1.2 ya están aplicadas en los documentos v5)

| # | Dónde se cita | El documento dice | Repositorio | Estado | Errata | Nota |
|---|---|---|---|---|---|---|
| 1 | Protocolo V1.3 | existe `README.md` | `README.md` | **OK** | — |  |
| 2 | Protocolo V1.3 | existe `corpus_audit.csv` | `corpus/corpus_audit.csv` | **OK** | — |  |
| 3 | Protocolo V1.3 | existe `domain.yml` | `domain.yml` | **OK** | — |  |
| 4 | Protocolo V1.3 | existe `rules.yml` | `data/rules.yml` | **OK** | — | se cita sin carpeta; está en data/ |
| 5 | Protocolo V1.3 | existe `incident_log.csv` | `incident_log.csv` | **OK** | — |  |
| 6 | Protocolo V1.3 | existe `logs/stats_modelos.txt` | `logs/stats_modelos.txt` | **OK** | — |  |
| 7 | Protocolo V1.3 | existe `logs/v2_corpus648/` | `logs/v2_corpus648` | **OK** | — |  |
| 8 | Protocolo V1.3 | existe `evidencias/p09_domain/` | `evidencias/p09_domain` | **OK** | — |  |
| 9 | Protocolo V1.3 | existe `evidencias/p11_1_pruebas/` | `evidencias/p11_1_pruebas` | **OK** | — |  |
| 10 | Protocolo V1.3 | existe `REPORTE_REEVALUACION.md` | `evidencias/v3_corpus708/REPORTE_REEVALUACION.md` | **NOTA** | — | se cita sin carpeta; está en evidencias/v3_corpus708/ (hay otro, de P11.1 con 324/648 frases, en evidencias/p11_1_pruebas/REPORTE_FALLAS.md) |
| 11 | Protocolo V1.3 | existe `evidencias/v3_real/` | `evidencias/v3_real` | **OK** | — |  |
| 12 | Protocolo V1.3 | existe `evidencias/v3_real/verificacion_referencias.md` | `evidencias/v3_real/verificacion_referencias.md` | **OK** | — |  |
| 13 | Protocolo V1.3 | existe `docs/ERRATAS_protocolo_V1.2.md` | `docs/ERRATAS_protocolo_V1.2.md` | **OK** | — |  |
| 14 | Protocolo V1.3 | existe `docs/piloto/` | `docs/piloto` | **OK** | — |  |
| 15 | Protocolo V1.3 | existen carpetas `logs/BASE-*` | 14 carpetas | **OK** | — |  |
| 16 | Protocolo V1.3 | existen carpetas `logs/RASA-*` | 17 carpetas | **OK** | — |  |
| 17 | Protocolo V1.3 (T03) | «corpus_metadata.csv (v3, 708 frases; la v2 en corpus/historico/)» | corpus_metadata.csv tiene 708 frases; la v2 está en corpus/historico/ | **OK** | — |  |
| 18 | Protocolo V1.3 (T05) | «dataset_split.csv (vigente, sobre el corpus v3)»; la V1.1 en corpus/historico/dataset_split_v2_648.csv | dataset_split.csv tiene 708 filas; la V1.1 está en corpus/historico/ | **OK** | — | el archivo actual asigna la misma partición que la V1.1 en 648 de las 648 frases comunes |
| 19 | Protocolo V1.3 (T05) | «dataset_split_v3.csv (V1.2, planificado)» | no existe todavía; lo generará scripts/split_corpus_v3.py en corpus/v3_real/ | **PLANIFICADO** | — | coherente con el estado Planificado |
| 20 | Seguimiento (Notas) / guía | existen `Lote1_Formularios_lenguaje_real_v2.pdf`, `situaciones_lote1_v1.csv` e `Instrucciones_ClaudeCode_lote_real_v2.md` | Lote1_Formularios_lenguaje_real_v2.pdf: sí, situaciones_lote1_v1.csv: sí, Instrucciones_ClaudeCode_lote_real_v2.md: sí | **OK** | — |  |
| 21 | Protocolo 2.3 / 5.5 | 54 intenciones (44 de trámites y 10 conversacionales) en 9 categorías | 54 intenciones (44 de trámites y 10 conversacionales), 9 categorías | **OK** | — |  |
| 22 | Protocolo 2.4.2 | 56 situaciones: una por intención y tres para fuera_de_alcance, en 5 formularios (A–E) | 56 situaciones, 54 intenciones, fuera_de_alcance x3 | **OK** | — |  |
| 23 | Seguimiento (Notas) | 12/11/11/11/11 situaciones por formulario | 12/11/11/11/11 | **OK** | — |  |
| 24 | Protocolo 2.4.2 | con 20 participantes cada situación queda respondida por 4 personas | 20 participantes / 5 formularios (rotación A–E) = 4 por formulario | **OK** | — |  |
| 25 | Protocolo P09 / T07; Nota | 54 de 54 respuestas redactadas; 40 de las 44 de trámites con [Verificar] | 54 respuestas sin [PENDIENTE] de 54; 40 de 44 con [Verificar] | **OK** | — |  |
| 26 | Protocolo 2.11 / P11.1 / T06; Nota | F1 macro en test (partición de P05): Rasa/DIET 0.624 y SVM 0.648 | Rasa/DIET 0.624 y SVM 0.648 (logs/rasa_test.csv, logs/baseline_test.csv) | **OK** | — |  |
| 27 | Protocolo 2.11 / P11.1; Nota | validación cruzada agrupada por base_phrase_id: Rasa/DIET 0.655 y SVM 0.637 | Rasa/DIET 0.655 y SVM 0.637 (logs/P11_1_crossval_agrupada/folds_metrics.csv) | **OK** | — |  |
| 28 | Protocolo 2.11; Nota | validación cruzada nativa de Rasa 0.778 (inflada por fuga) | 0.778 (evidencias/p11_1_pruebas/salidas/03_rasa_test_nlu_crossval.txt) | **OK** | — | la CV nativa se hizo con el corpus v2 (648 frases); la agrupada, con el v3 (708) |
| 29 | Protocolo 2.11 / P11.1; Nota | smoke test de las 54 intenciones con consultas nuevas: 44 de 54 | 44 de 54 (logs/P11_1_smoke_test_v3_nuevas) | **OK** | — |  |
| 30 | Protocolo 5.2; Nota | 4 aciertos ganados y 7 perdidos en el smoke test; McNemar p ≈ 0.55 | 4 ganados y 7 perdidos; McNemar exacto p = 0.549 | **OK** | — |  |
| 31 | Protocolo 2.10 / T07; Nota | en el smoke test, 9 de 10 errores habrían sido «no entendí» a costa de 6 de 44 aciertos (umbral 0.50) | 9 de 10 errores y 6 de 44 aciertos con confianza < 0.50 | **OK** | — |  |
| 32 | Protocolo 2.10 | umbral t entre 0.30 y 0.80 y puntaje = aciertos − 2 × errores con respuesta | scripts/fallback_threshold.py: t = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8], lambda = 2 | **OK** | — |  |
| 33 | Protocolo 5.2; Nota | horario_mesa_partes absorbió predicciones de requisitos_mesa_partes: exactitud 0.87 → 0.53 | 0.87 → 0.53 (predictions_test de las 5 semillas, v2 vs v3) | **OK** | — |  |
| 34 | Protocolo 5.2; Nota | «abrir un restaurante» se clasificó como fuera_de_alcance con 0.81 de confianza; la palabra aparecía una sola vez en el entrenamiento, en un ejemplo de fuera_de_alcance | detectó fuera_de_alcance con 0.81; «restaurante» aparece 1 vez/veces en el corpus v2 (fuera_de_alcance/train) | **OK** | — |  |
| 35 | Protocolo 5.3; Nota | ampliación del corpus: 60 frases, 20 grupos, 9 intenciones | 60 frases, 20 grupos, 9 intenciones | **OK** | — |  |
| 36 | Protocolo 5.3; Nota | la ampliación corrigió las 8 fallas | 8 de 8 intenciones que fallaban en el 1.er smoke test ahora son correctas (consultas originales, contaminadas) | **OK** | — |  |
| 37 | Protocolo 5.3; Nota | F1 test 0.633 → 0.624 (Rasa/DIET, corpus v2 → v3) | 0.6335 → 0.6241 | **OK** | — |  |
| 38 | Protocolo 2.8 / P05 / T05 | partición V1.1 (ejecutada): 486/81/81 = 75 % / 12,5 % / 12,5 % (el objetivo nominal era 70/15/15) | 486/81/81 frases = 75.0/12.5/12.5 % | **OK** | — | coincide con la V1.3 (errata E4 ya aplicada); el mecanismo descrito en 2.8 se verifica en la fila siguiente |
| 39 | Protocolo 2.8 | con 4 grupos por intención, 3 pasan a entrenamiento y el cuarto se asigna alternadamente a validación o a prueba | las 54 intenciones tienen 4 grupos, 3 en entrenamiento; el cuarto: 27 grupos a validación y 27 a prueba | **OK** | — |  |
| 40 | Protocolo 2.8 / 5.2; Nota | el test mide 27 de las 54 intenciones (3 frases cada una) y la validación las otras 27 | test: 27 intenciones con [3] frases; validación: 27 intenciones; sin solape: True | **OK** | — |  |
| 41 | Nota v5 (evidencias) | 41 incidencias registradas | 42 incidencias en incident_log.csv | **DISCREPANCIA** | — | la(s) 1 incidencia(s) posterior(es) a la fecha de los documentos (p. ej. la fila «Piloto (diseño)» del cambio a la V1.3) no están en la cifra de la Nota |
| 42 | Protocolo 2.4 (V1.3) | margen de error de una proporción ≈ 11,7 % con n = 60 y ≈ 7,5 % con n = 120 (N ≈ 400, confianza 95 %) | 11.7 % con n = 60 y 7.5 % con n = 120 (fórmula con corrección para población finita, p = q = 0,5) | **OK** | — |  |
| 43 | Protocolo 2.4 (V1.3) | con 60 pares, la t pareada detecta con 80 % de potencia (α = 0,05, dos colas) efectos de d ≈ 0,37 o mayores | d mínimo con 80 % de potencia (t pareada, dos colas, n = 60) = 0.368 | **OK** | — |  |
| 44 | Protocolo 5.4 (V1.3) | pruebas de humo con datos falsos (simuladas): 59/59 y 22/22 | 59/59 y 22/22 (últimas salidas guardadas en evidencias/v3_real/salidas/) | **OK** | — |  |
| 45 | Protocolo 5.5 (V1.3, fila de evidencias) | docs/piloto/ contiene los materiales del piloto: formulario de sesión asistida (guía, paquete por persona y 56 tarjetas) y registro de sesiones | docs/piloto/ existe, pero faltan: Sesion_Asistida_Formulario_v1.docx, Sesion_Asistida_Formulario_v1.pdf, Registro_Sesiones_Piloto_v1.xlsx | **DISCREPANCIA** | — | el tesista debe aportar estos archivos; no se inventaron |
| 46 | Protocolo 2.4 (V1.3) | piloto exploratorio (sesión asistida, n = 60): estado Planificado | no hay resultados reales: falta logs/piloto/analisis_piloto.json | **PLANIFICADO** | — | coherente con el estado Planificado |

## No verificable con el repositorio (no se comprobó)

Cifras y afirmaciones que dependen de datos externos o de pasos aún no ejecutados: el tamaño planificado n = 120 de la V1.2 y su fórmula (el piloto V1.3 usa n = 60), antecedentes (Vargas Ríos, 2022), línea base y post-test de P01 y P12–P14 (simulados), las fórmulas del registro de sesiones (16 resultados contra un cálculo independiente: el registro no está en el repositorio), Alfa de Cronbach, recolección del lote 1, partición V1.2, evaluación sobre lenguaje real y umbral de confianza (planificados), y la redacción metodológica.

## Discrepancias (se informan tal cual; no se corrigen los documentos)

- **sin errata** · **Nota v5 (evidencias)** — «41 incidencias registradas»: el repositorio tiene 42 incidencias en incident_log.csv. la(s) 1 incidencia(s) posterior(es) a la fecha de los documentos (p. ej. la fila «Piloto (diseño)» del cambio a la V1.3) no están en la cifra de la Nota
- **sin errata** · **Protocolo 5.5 (V1.3, fila de evidencias)** — «docs/piloto/ contiene los materiales del piloto: formulario de sesión asistida (guía, paquete por persona y 56 tarjetas) y registro de sesiones»: el repositorio tiene docs/piloto/ existe, pero faltan: Sesion_Asistida_Formulario_v1.docx, Sesion_Asistida_Formulario_v1.pdf, Registro_Sesiones_Piloto_v1.xlsx. el tesista debe aportar estos archivos; no se inventaron
