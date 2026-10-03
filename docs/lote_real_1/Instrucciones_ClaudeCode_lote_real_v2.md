# Instrucciones para Claude Code — Lote 1 de lenguaje real, partición v3 y umbral de confianza (v2)

## Contexto

P11.1 no cumplió su criterio de salida: F1 ≈ 0.63–0.65 sobre lenguaje sintético (meta 0.75) y 44/54 en el smoke test. Causas: corpus sintético y un defecto de la partición P05 (cada intención quedó en validación **o** en test, así que el test mide solo 27 de 54 intenciones).

Estas decisiones las tomó el tesista y quedaron documentadas en `Nota_Desviacion_P11_1_v2` (el curso solo exige documentar errores, medidas y estado; no hay aprobación externa pendiente). Su estado inicial es *Planificado*. El plan (protocolo V1.2) es:

1. Recolectar un lote de frases reales (lote 1) para usarlas como **validación y test**.
2. Re-particionar: entrenamiento sintético, validación y test reales.
3. Añadir un umbral de confianza que responda "no entendí".

**Trabaja en carpetas versionadas y no sobrescribas nada vigente** (corpus v2, partición P05, `domain.yml`, `rasa_config.yml`, `logs/`, `evidencias/`).

## Reglas (no negociables)

1. Las frases del lote 1 **nunca entran al entrenamiento** en esta etapa.
2. Toda selección (grilla, umbral) se hace con la **validación real**. El **test real se evalúa una sola vez** por configuración final. Registra cuántas veces se tocó.
3. **Prohibido generar o "completar" frases reales con IA.** Si faltan frases, informa y detente.
4. No reportes la validación cruzada nativa de Rasa como estimación (tiene fuga de paráfrasis).
5. Todo resultado lleva IC95 % bootstrap. Si el F1 queda por debajo de 0.75, repórtalo tal cual, sin suavizar.
6. No subas modelos (`.tar.gz`) ni datos con información personal.
7. Cada parte termina con: incidencias en `incident_log.csv`, evidencias (salida + captura, patrón existente) y commit + push.
8. **Etiqueta cada resultado y cada cambio con su estado real: Ejecutado, Planificado o Simulado.** Nada simulado se presenta como real, y nada planificado se presenta como ejecutado. Actualiza esa tabla de estado en el README al cerrar cada parte.

---

## PARTE A — Preparación (hazla ya, sin datos reales)

**A1. Estructura.** Crea `docs/lote_real_1/` (el tesista pondrá ahí `situaciones_lote1_v1.csv` y los formularios), `corpus/real/`, `corpus/v3_real/`, `data/v3/`, `logs/v3_real/`, `evidencias/v3_real/`.

**A2. Plantillas CSV vacías en `corpus/real/`:**

- `lote1_participantes.csv`: `participant_code,form,age_range,vive_en_juliaca,tramite_12m`
- `lote1_respuestas.csv`: `participant_code,form,scenario_id,text`

**A3. `scripts/ingest_real_lote.py`.** Entradas: `situaciones_lote1_v1.csv`, participantes y respuestas.

- *Errores bloqueantes:* `scenario_id` inexistente; `form` de la respuesta distinto del formulario del participante o de la situación; dos respuestas del mismo participante a la misma situación.
- *Advertencias (van al reporte, no se corrigen solas):*
  - texto vacío o de menos de 3 caracteres (excepto saludo, despedida, agradecimiento, afirmar y negar);
  - posibles datos personales (DNI `\b\d{8}\b`, celular `\b9\d{8}\b`, correos, URLs, `@usuario`): márcalos para que el tesista los edite, **no los borres automáticamente**;
  - duplicados exactos tras normalizar (minúsculas, sin tildes ni signos) entre participantes distintos;
  - frases idénticas a alguna del corpus sintético;
  - cobertura por intención: lista las que tengan menos de 3 frases.
- *Salidas:*
  - `corpus/real/lote1_real_validado.csv` (`real_id` R0001…, `participant_code`, `scenario_id`, `intent_esperada`, `category`, `text`, `source="lenguaje real (lote 1)"`);
  - `logs/v3_real/ingesta_reporte.txt`;
  - `corpus/real/lote1_revision_etiquetas.csv` con `real_id,text,intent_esperada,intent_revisada,decision,comentario` (las tres últimas columnas vacías, para revisión humana; `decision` ∈ OK / CAMBIAR / DESCARTAR).
- *Modo `--aplicar-revision`:* lee las decisiones y genera `corpus/real/lote1_real_final.csv` (CAMBIAR usa `intent_revisada`; DESCARTAR excluye). Reporta el % cambiado y descartado. Si existe la columna `intent_revisora2` (segunda revisora en ≥ 20 % de las frases), calcula kappa de Cohen entre la etiqueta esperada y la revisión, y entre revisoras.

**A4. `scripts/split_corpus_v3.py`.** Entradas: `corpus/corpus_metadata.csv` vigente (sintético) y `corpus/real/lote1_real_final.csv`.

- **Train v3** = todas las frases sintéticas (incluidos los grupos que en P05 estaban en validación y test sintéticos), con `source=sintético`.
- **Real:** por intención con *n* frases reales, `n_val = max(1, n//2)` y el resto a test. Asigna al azar con seed 42 (ordena por `real_id` y baraja). Cada frase real es su propio grupo: `base_phrase_id = REAL_<real_id>`.
- *Asserts:*
  - las 54 intenciones presentes en train, validación y test;
  - ninguna frase (normalizada) repetida entre particiones;
  - ningún `base_phrase_id` en dos particiones;
  - informe de *n* por intención y partición; avisa si alguna intención tiene menos de 2 frases reales.
- *Salidas versionadas:* `corpus/v3_real/corpus_metadata_v3.csv`, `corpus/v3_real/dataset_split_v3.csv`, `corpus/v3_real/resumen_v3.json`, `data/v3/nlu_train.yml`, `data/v3/nlu_validation.yml`, `data/v3/nlu_test.yml`. No toques `corpus/dataset_split.csv` ni `data/nlu*.yml` vigentes.

**A5. `scripts/eval_real.py`.** Reutiliza `scripts/common.py` y el flujo de P07/P08/P10:

- Grilla en validación (seed 42): SVM con C ∈ {0.1, 1, 10}; Rasa/DIET con la grilla completa del protocolo.
- Selección por F1 macro en validación.
- Repeticiones de la configuración ganadora con seeds 10–50, evaluadas en test.
- Métricas: F1 macro (54 intenciones), accuracy, balanced accuracy, F1 por intención y las 10 confusiones principales.
- IC95 % por bootstrap sobre frases (1000 remuestreos, seed 42) para F1 macro y accuracy.
- Comparación Rasa vs SVM: McNemar exacto pareado sobre las mismas frases, y diferencia de F1 con IC bootstrap pareado.
- Como métrica secundaria de continuidad, conserva la validación cruzada agrupada sintética (`StratifiedGroupKFold`).
- Guarda en `logs/v3_real/` con los IDs de experimento del patrón existente.

**A6. Umbral de confianza.**

- `domain_v3.yml`: copia de `domain.yml` + intención `nlu_fallback` + `utter_no_entendi` ("No estoy seguro de haber entendido tu consulta. ¿Puedes reformularla o decirme qué trámite necesitas?").
- `data/v3/rules_v3.yml`: regla `nlu_fallback` → `utter_no_entendi`.
- `configs/rasa_config_v3_fallback.yml`: configuración ganadora + `FallbackClassifier` (`threshold=t`, `ambiguity_threshold=0.1`) después de `DIETClassifier`.
- `scripts/fallback_threshold.py`: con predicciones y confianzas en la **validación real**, para t ∈ {0.30, 0.40, 0.50, 0.60, 0.70, 0.80} calcula respondidas, aciertos respondidos, errores respondidos, abstenciones (correctas perdidas / errores atrapados), cobertura y precisión de lo respondido.
  - **Puntaje = aciertos respondidos − 2 × errores respondidos** (λ = 2, fijado antes de ver resultados).
  - Elige el t de mayor puntaje (empate: mayor cobertura), congélalo y evalúalo **una sola vez** en test real. Incluye la tabla completa en el reporte.
- Mantén `domain.yml` y `rasa_config.yml` vigentes como línea base y trabaja con las versiones v3. Promuévelas a vigentes solo si el puntaje del umbral en la validación real mejora, y documenta esa decisión en `incident_log.csv`.

**A7. Prueba de humo** de los scripts con datos de PRUEBA temporales en `/tmp`, claramente falsos y sin commitear. Solo verifica que el flujo corre.

**A8.** Registra una incidencia ("preparación del lote real y de la partición v3"), guarda evidencias y haz commit + push (solo scripts y plantillas).

---

## PARTE B — Con datos reales (cuando el tesista entregue las respuestas transcritas)

**Solo se ejecuta si el tesista recolecta el lote 1 dentro del curso.** Si no lo hace, no ejecutes la Parte B ni uses datos sustitutos: documenta B como *Planificada* en el reporte, con el motivo.

**B1.** Ejecuta la ingesta. Si alguna intención queda con menos de 3 frases reales, detente e informa; no completes.

**B2.** Entrega `lote1_revision_etiquetas.csv` al tesista y espera sus decisiones. Luego corre `--aplicar-revision` y reporta el % de etiquetas cambiadas (es un hallazgo en sí mismo).

**B3.** Partición v3 (A4) con todas las verificaciones.

**B4.** Evaluación real (A5): grilla SVM y grilla Rasa (≈ 1 h 40 min; ejecútala en segundo plano), selección en validación y repeticiones en test, **una sola vez**.

**B5.** Umbral (A6): elígelo en validación y evalúalo una vez en test. Recomienda al tesista una prueba manual con `rasa shell` (10–15 min) antes del pre-piloto.

**B6.** Reporte `REPORTE_V3_LENGUAJE_REAL.md` con:

- F1 macro (IC95 %) de Rasa y SVM en validación y test reales;
- comparación con el ≈ 0.65 sintético;
- confusiones principales;
- cobertura contra precisión del umbral;
- veredicto sobre el criterio del pre-piloto formal (F1 ≥ 0.75: sí o no, sin suavizar; Alfa de Cronbach pendiente);
- limitaciones (muestra de conveniencia, particiones pequeñas).

**B7.** Incidencias, evidencias en `evidencias/v3_real/` y commit + push (sin modelos). En el mensaje final, indica cuántas veces se evaluó el test real y por qué.
