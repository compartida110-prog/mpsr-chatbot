# Seguimiento del lote 1 (participantes y formularios)

Libro de Excel para llevar la aplicación del lote 1. **Mide frases por intención, no personas**: la hoja *Blancos* registra las
situaciones que alguien dejó sin responder, y *Cobertura* cuenta las frases reales de cada una de las 54 intenciones (meta 4, mínimo 3).

| Archivo | Qué es | ¿Es evidencia? |
|---|---|---|
| `Seguimiento_Lote1_Participantes_PLANTILLA_v3.xlsx` | **Plantilla vigente, vacía** (P01–P25 en «Pendiente»). La fila de la parte inferior de *Participantes* es solo un ejemplo del formato | Plantilla |
| `ejemplos_simulados/…_SIMULADO_v3.xlsx` | Ejemplo con datos **ficticios** (22 «Transcritos», 16 blancos) para ver cómo se llenan y calculan las hojas | **No.** No hay frases reales detrás |
| `historico/…_SIMULADO_v2.xlsx` | Ejemplo simulado de la versión anterior (contaba personas por formulario) | **No** (superado por la v3) |
| `historico/…_completado.xlsx` | Plantilla de una versión anterior con la fila de ejemplo. **A pesar del nombre no es un seguimiento lleno**: no contiene participantes reales | No (superado por la v3) |

## Qué NO va al repositorio

El seguimiento **real** (con ocupación y residencia de personas) y las hojas de consentimiento **no se suben**. Guárdalos en
`docs/lote_real_1/privado/` (la carpeta está en `.gitignore`). `scripts/conciliar_seguimiento.py` exporta a
`corpus/real/lote1_participantes.csv` solo código, formulario, rango de edad, residencia y trámite: **sin ocupación**.

## Cómo se usa con los scripts

1. Aplica los formularios y anota el avance en tu copia de la plantilla (guárdala en `privado/`).
2. Transcribe las respuestas a `corpus/real/lote1_respuestas.csv`.
3. `python scripts/conciliar_seguimiento.py --seguimiento docs/lote_real_1/privado/<tu_archivo>.xlsx` cruza ambos: detecta una respuesta ausente que
   no figura como blanco, o un blanco que sí tiene respuesta. **Se niega a trabajar con un archivo simulado.**
4. Con la conciliación limpia sigue la Parte B (`scripts/ingest_real_lote.py`, …).
