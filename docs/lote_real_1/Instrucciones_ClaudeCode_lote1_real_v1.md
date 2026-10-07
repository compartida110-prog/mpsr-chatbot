# Instrucciones para Claude Code — lote 1 REAL (v1)

Contexto: el tesista aplicó el lote 1 con personas reales y lo transcribió en `Lote1_Transcripcion_V1.2.xlsx` (25 participantes, P01–P25). **Estos datos son REALES.** No uses `--permitir-simulado` ni `--demo-simulada` en nada de este documento.

## Antes de empezar
1. Guarda el libro donde indique el `LEEME` del lote real (carpeta privada, la que ya excluye `.gitignore`). **No subas el libro ni frases reales a GitHub.** No modifiques el archivo original: trabaja sobre una copia.
2. Lee los totales **desde la hoja Respuestas (columna D), no desde los valores guardados de las fórmulas**: el archivo trae totales guardados desactualizados (decía 57 frases; recalculado son 169). Recalcula una copia con LibreOffice si necesitas el Resumen.
3. Valores esperados tras recalcular (repórtalos tal cual, aunque difieran): 25 participantes transcritos, 0 sin consentimiento «Sí», 169 frases, 0 alertas, 54 de 54 intenciones con ≥ 3 frases (5 con la meta de 4), estado «Listo para la Parte B». Si tus cifras difieren, **detente y repórtalo**; no ajustes nada para que coincidan.

## Pasos (en este orden)
**A. Ingesta real** (`ingest_real_lote.py --libro <copia>`). Reporta: participantes, frases validadas, blancos derivados, frases idénticas al corpus sintético (fuga) y cualquier alerta de datos personales. No descartes ni cambies frases por tu cuenta.

**B. Alto: pasos humanos.** Entrega al tesista, y espera, lo siguiente:
- la marca de revisión de datos personales (`logs/avance/revision_pii.txt`) la crea **solo el tesista**, después de leer el reporte;
- la revisión de etiquetas frase por frase (`--aplicar-revision`) la decide una persona. No la automatices ni la rotules como humana. Si hay segunda revisora en una submuestra, calcula kappa de Cohen; si no, declara que no se calculó.
- Para la revisión, señala al tesista estas frases cuya etiqueta parece no coincidir con la intención esperada (decide él): P04 S24, P10 S40, P14 S19, P15 S20, P19 S34, P19 S39, P21 S41, P22 S02, P23 S03.
- Señala también que P08, P24 y P25 marcaron `vive_en_juliaca = No` (el diseño pedía adultos de Juliaca): decide el tesista si se quedan o se declara como desviación.

**C. Solo cuando B esté hecho por el tesista:** partición V1.2/V1.3 (`split_corpus_v3.py`: entrenamiento sintético; validación y test = frases reales). Verifica y reporta: 54 intenciones en cada partición, sin frases repetidas entre particiones, y **si algún participante o situación (scenario_id) queda repartido entre validación y test** (posible fuga por autor); no cambies el criterio de partición sin avisar.

**D. Validación y umbral:** `eval_real.py --fase seleccion` (la grilla completa de Rasa y SVM, no la configuración fija de la demostración) y `fallback_threshold.py` sobre validación. Congela el umbral **antes** de tocar el test.

**E. Test, UNA sola vez** (`eval_real.py --fase test`). Registra el número de evaluaciones del test. Reporta F1 macro con IC95 % y McNemar frente a SVM. Con ~3 frases por intención, la validación y el test tendrán 1–2 por intención: **declara la alta varianza** en el reporte. No repitas el test ni bajes la meta (F1 ≥ 0.75) para forzar el paso.

**F. Tablero:** `estado_compuertas.py` (sin `--demo-simulada`). Informa qué compuertas reales quedan cumplidas y cuáles no. G4 (TUPA) y G5–G7 siguen pendientes; no fabricar evidencia.

## Reglas
- No cambiar `domain.yml` ni congelar el modelo: dependen de la hoja del TUPA confirmada por el tesista.
- Todo resultado real va a las carpetas reales; nada de `evidencias/simulado_demostracion/`.
- Corre las pruebas de humo existentes después de cada paso que toque código. Registra en `incident_log.csv` toda desviación.
- Si un paso falla, repórtalo con el mensaje de error; no lo rodees.
