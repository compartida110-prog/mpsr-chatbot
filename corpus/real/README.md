# Frases reales del lote 1

**Estado: Planificado.** Solo existen las plantillas vacías; no hay ninguna frase real todavía.

| Archivo | Contenido |
|---|---|
| `lote1_participantes.csv` | `participant_code, form, age_range, vive_en_juliaca, tramite_12m` (sin nombres ni contacto) |
| `lote1_respuestas.csv` | `participant_code, form, scenario_id, text` — transcripción literal de lo que escribió cada participante |
| `lote1_real_validado.csv` | Generado por `scripts/ingest_real_lote.py` (real_id R0001…, intención esperada provisional) |
| `lote1_revision_etiquetas.csv` | Para la revisión humana: `decision` ∈ OK / CAMBIAR / DESCARTAR (más `intent_revisora2` opcional) |
| `lote1_real_final.csv` | Generado por `--aplicar-revision`; es la entrada de `scripts/split_corpus_v3.py` |

**Antes de subir cualquiera de estos archivos a GitHub:** leer `logs/v3_real/ingesta_reporte.txt` y confirmar que no hay datos personales
(DNI, celular, correo, URL, @usuario). Los scripts los marcan pero **nunca los borran solos**.
Las frases reales **no entran al entrenamiento** en esta etapa: son la validación y el test.
