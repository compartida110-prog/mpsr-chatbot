# Lote 1 de lenguaje real (protocolo V1.2, P02/T03.1)

**Estado: Planificado.** Los formularios y el catálogo están listos; todavía no se recolectaron frases reales.

| Archivo | Qué es |
|---|---|
| `Lote1_Formularios_lenguaje_real_v2.pdf` / `.docx` | Guía de aplicación (solo para el tesista) y los 5 formularios A–E con consentimiento informado. Cada participante responde a unas 11 situaciones con sus propias palabras |
| `situaciones_lote1_v1.csv` | **Catálogo del tesista** (56 situaciones, 54 intenciones; 12/11/11/11/11 por formulario). Es el que usa `scripts/ingest_real_lote.py`. Se verificó que el texto y el formulario de cada situación coinciden con los formularios (.docx y .pdf) |
| `Lote1_Transcripcion_v1.xlsx` | **Plantilla vacía** del libro de transcripción (pestañas Participantes, Respuestas, Cobertura, Situaciones, Resumen, Parametros y Notas). El tesista lo llena con las respuestas reales; el libro **lleno** va en `privado/` (no se sube). No se exporta a CSV desde Excel: `scripts/ingest_real_lote.py --libro` lo lee directamente |
| `ejemplos_simulados/` | Libro de transcripción de **prueba** con datos falsos (`Lote1_Transcripcion_SIMULADO_v2.xlsx`); los scripts lo rechazan salvo con `--permitir-simulado` |

## Esquema del catálogo `situaciones_lote1_v1.csv`

`scenario_id, form, categoria, intent_esperada, situacion`

- `scenario_id`: S01–S56; `form`: A–E (rotación: S01→A, S02→B, …, S06→A); `intent_esperada`: una de las 54 intenciones de `domain.yml`
  (56 situaciones = una por intención y tres para `fuera_de_alcance`). La etiqueta es **provisional**: después se revisa frase por frase.
- El script solo **exige** `scenario_id`, `form` e `intent_esperada`. La categoría de cada frase se toma del corpus sintético; si el catálogo trae
  `categoria` (o `category`) se contrasta con ella y cualquier diferencia se informa como advertencia.

## Flujo (Parte B de `Instrucciones_ClaudeCode_lote_real_v2.md`; solo cuando haya respuestas reales transcritas)

1. Transcribir cada respuesta tal cual (sin corregir ortografía) en `Lote1_Transcripcion_v1.xlsx` (copia llena en `privado/`): una fila por situación en Respuestas, Estado «Transcrito» y
   «Consentimiento firmado» = «Sí» en Participantes. Borrar solo los datos personales si aparecieran. Guardar las hojas originales (o una foto) como respaldo.
   Cuando el Resumen diga «Listo para la Parte B», ejecutar **solo** la ingesta con el libro: `python scripts/ingest_real_lote.py --libro docs/lote_real_1/privado/<libro lleno>.xlsx`.
   Genera `corpus/real/lote1_respuestas.csv`, `lote1_participantes.csv` y `lote1_blancos_derivados.csv`; **revisar el reporte completo antes de seguir** (advertencias, bloqueos, frases con alerta, cobertura).
2. (Con los CSV ya escritos a mano, sin libro: `python scripts/ingest_real_lote.py`.) La ingesta produce `corpus/real/lote1_real_validado.csv`, `logs/v3_real/ingesta_reporte.txt` y la plantilla de revisión.
3. Revisar las etiquetas frase por frase (`OK` / `CAMBIAR` / `DESCARTAR`) y `python scripts/ingest_real_lote.py --aplicar-revision`.
4. `python scripts/split_corpus_v3.py` → partición v3 (entrenamiento sintético; validación y test reales).
5. Evaluación y umbral, en este orden: `python scripts/eval_real.py --fase seleccion` → `python scripts/fallback_threshold.py` (elige y congela el umbral con la validación) →
   `python scripts/eval_real.py --fase test`, que evalúa el test **una sola vez** y, en la misma pasada, aplica el umbral congelado a las predicciones que acaba de guardar.
   Si el test ya se evaluó (con el umbral congelado antes), `python scripts/fallback_threshold.py --fase test` aplica el umbral a las **predicciones ya guardadas**: no entrena, no carga ningún modelo y
   no evalúa el test otra vez; la aplicación se anota aparte (`aplicaciones_de_umbral` en `test_registro.json`) y no suma una evaluación. Se niega si las predicciones no son las de la evaluación
   registrada (semillas, número de frases, huella SHA-256), si el umbral se congeló **después** del test, o si ya se aplicó (para repetirlo hace falta `--motivo-test-adicional`, que queda registrado).

**Las frases las deben escribir los participantes.** Si las redactan el tesista o una IA son sintéticas y no sirven para este lote.

## Revisión de etiquetas y lote 1b (complemento)

- **Revisión de etiquetas (lote 1 real):** el tesista revisó las 169 frases en `Revision_Etiquetas_Lote1_v1_1.xlsx` (privado). `python scripts/trasladar_revision.py --libro <ese libro>` las traslada a
  `corpus/real/lote1_revision_etiquetas.csv` comprobando antes que la frase y la intención esperada coincidan (se detiene si no). Es una revisión humana de una sola revisora: no hay kappa. Resultado: 158 OK, 11 CAMBIAR, 0 DESCARTAR.
  **Cuatro intenciones quedan con 2 frases** (mínimo 3), así que no se ejecuta `--aplicar-revision` ni la partición hasta reunir más.
- **Lote 1b (formulario F):** `Lote1b_Formulario_complemento_v1.docx` / `.pdf` reparte solo S02, S24, S34 y S39 a P26–P28 (el 4.º participante cubre descartes). `situaciones_lote1b_v1.csv` suma F a esas cuatro situaciones sin
  cambiar A–E ni el catálogo (`scripts/catalogo_formularios.py`); la ingesta y la conciliación aceptan F y los códigos P01–P28.
- **`Lote1_Transcripcion_V1.3.xlsx`:** libro **vacío** con las mismas hojas y fórmulas que la plantilla y filas para P26–P28 (rangos extendidos: Participantes 4:31, Respuestas 4:295; generado por `scripts/preparar_libro_v13.py`).
  Ábrelo y guárdalo una vez en Excel para que recalcule los totales (se entrega sin valores guardados en Resumen, Cobertura y Situaciones). Pasa ahí los 25 participantes y las frases nuevas, y guarda el libro lleno en `privado/`.

### Combinar los libros (V1.2 + lote 1b)

`python scripts/combinar_libros.py --base <libro con P26–P28> --fuente <libro con P01–P25> --salida docs/lote_real_1/privado/<nombre nuevo>.xlsx` copia **solo las celdas de entrada** de Participantes y Respuestas
a la base editando el XML (conserva validaciones, formato y fórmulas), se detiene sin escribir si algo no cuadra o si el destino ya tiene datos, y no modifica ni la base ni la fuente. El resultado queda sin valores guardados y con
recálculo completo al abrir: ábrelo y guárdalo una vez en Excel. `scripts/libro_xml.py` verifica además que las fórmulas de cada fila apunten a su propia fila (así se detectó el error antiguo de la columna «En blanco»
de P26–P28). **La ingesta solo procesa participantes con Estado = «Transcrito»**: si un participante tiene frases pero sigue «Pendiente», sus frases se ignoran (el reporte lo avisa).

### Lote 1c (complemento: formulario G)

Motivo: con los descartes previstos (un duplicado exacto y una frase ambigua), `agradecimiento` y `despedida` quedarían con 2 frases (mínimo 3, con textos distintos). El lote 1c reúne frases nuevas **solo de las situaciones S46 (despedida) y S47 (agradecimiento)**
con tres personas nuevas: **P29, P30, P31 y P32, formulario G** (ids nuevos; no se reutiliza ninguno). `situaciones_lote1c_v1.csv` suma G a esas dos situaciones sin cambiar A–F ni el catálogo.

- **Libro:** `python scripts/ampliar_libro.py --base <libro> --salida <libro nuevo> --codigos P29,P30,P31 --forma G --situaciones S46,S47` agrega los tres participantes (Estado «Pendiente») y 6 filas de respuestas, **sin datos**, a un libro vacío o ya lleno;
  los datos anteriores no cambian. Hay una copia ya ampliada en `privado/` (fuera de Git). Ábrela y guárdala una vez en Excel para que recalcule.
- **Ingesta:** `python scripts/ingest_real_lote.py --libro <libro> --nuevos P29,P30,P31`. Aparte de lo de siempre, el reporte avisa **«FRASE NUEVA que repite el texto normalizado de una existente»** y si un mismo texto aparece con intenciones esperadas distintas.
- **El formulario G impreso** (consentimiento y las dos situaciones) lo prepara el tesista; no forma parte del repositorio todavía.
- **Después de ingestar el 1c** se aplican, con motivo y fecha, el descarte de R0147 y la exclusión de R0136, se verifica que las 54 intenciones tengan al menos 3 frases con textos distintos y se recalculan los conteos antes de partir.
  Hasta entonces la partición y las etapas siguientes están en espera.
