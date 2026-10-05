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
5. `python scripts/eval_real.py` y `python scripts/fallback_threshold.py` (selección en validación; el test se evalúa una sola vez).

**Las frases las deben escribir los participantes.** Si las redactan el tesista o una IA son sintéticas y no sirven para este lote.
