# Instrucciones para Claude Code — revisión de etiquetas y lote 1b (v1)

Contexto: el tesista terminó la revisión de etiquetas del lote 1 REAL en `Revision_Etiquetas_Lote1_v1_1.xlsx` (hoja `Revision`; 169 frases: 158 OK, 11 CAMBIAR, 0 DESCARTAR). Al recalcular la hoja `Cobertura`, **4 intenciones quedan con 2 frases** (mínimo 3): `licencia_funcionamiento_costo`, `partida_nacimiento`, `presentar_reclamo` y `horario_atencion_general`. Por eso G1 no se cumple hasta reunir más frases: el tesista aplicará un complemento (lote 1b, formulario F, 4 situaciones, personas P26–P28). **Estos datos son REALES: nada de simulación, y ninguna frase ni el Excel van a GitHub.**

## Archivos que recibes
- `Revision_Etiquetas_Lote1_v1_1.xlsx` (decisiones del tesista; privado)
- `Lote1b_Formulario_complemento_v1.docx` y `.pdf` (formulario F)

## Tareas (en este orden)

**1. Trasladar las decisiones a `corpus/real/lote1_revision_etiquetas.csv`.**
- Empareja por `participant_code` + `scenario_id`. Antes de escribir, comprueba que la frase y la intención esperada de cada fila coinciden con las del CSV; si alguna no coincide, **detente y repórtalo**.
- Copia la decisión (OK/CAMBIAR) y, en CAMBIAR, la intención correcta, con el formato que ya usa tu script. No cambies ninguna decisión ni la rotules como automática: es revisión humana de una sola revisora (sin segunda revisora, kappa no calculado; decláralo).
- Comprueba: 169 emparejadas, 158 OK, 11 CAMBIAR, 0 DESCARTAR.

**2. Informe de cobertura tras la revisión, sin cerrar nada.**
- Calcula cuántas frases quedan por intención con esas decisiones. Resultado esperado: 4 intenciones con 2 frases (las de arriba). Reporta si difiere.
- **No ejecutes `--aplicar-revision` ni las etapas C–F** (partición, grilla, umbral, test, tablero) mientras haya intenciones por debajo de 3. Si tu script ya tiene un modo de verificación sin escribir, úsalo; si no, no lo fuerces.

**3. Soportar el formulario F (lote 1b).**
- El formulario F reparte solo las situaciones S02, S24, S34 y S39 (cada una con su intención esperada del catálogo). Hoy el catálogo y la ingesta asignan cada situación a un solo formulario (A–E): revisa dónde se valida el par formulario–situación (ingesta, plantilla del libro, conciliación con el seguimiento, pruebas de humo) y haz que acepte F sin cambiar A–E.
- Instala los archivos del formulario F donde estén los de A–E y actualiza el README.
- Prepara `Lote1_Transcripcion_V1.3.xlsx` a partir de la plantilla/estructura de la V1.2: mismas hojas y fórmulas, con filas para P26–P28 (formulario F, las 4 situaciones cada uno), **extendiendo los rangos de las fórmulas** (hoy `Respuestas!$A$4:$A$283` y similares) y recalculando para que los totales guardados no queden desactualizados. Entrégalo **vacío** (sin datos reales); el tesista pasará a ese libro sus 25 participantes y las frases nuevas, o te indicará cómo combinarlos.
- Si cambias código, corre las pruebas de humo y reporta el resultado.

**4. Registro.** Registra en `incident_log.csv`, solo con cifras: «Lote 1: revisión de etiquetas (11 cambios, 0 descartes); 4 intenciones bajo el mínimo; lote 1b (formulario F) planificado».

## Reglas
- No uses `--permitir-simulado` ni `--demo-simulada`.
- No modifiques `domain.yml`, no congeles modelo ni toques el libro original.
- No bajes el mínimo de 3 frases ni devuelvas frases a su etiqueta anterior para llegar a 3.
- Si un paso falla, repórtalo con el error; no lo rodees.
- Al terminar, resume: decisiones trasladadas, cobertura, qué cambió en el código y qué le toca ahora al tesista.
