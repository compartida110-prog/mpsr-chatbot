# Demostración simulada del flujo del curso

**Estado: Simulado.** Nada de esta carpeta es un hallazgo de campo, ni evidencia, ni cumple una compuerta real.

Cada subcarpeta es una ejecución de `python scripts/demostracion_simulada.py --demo-simulada` con los dos archivos simulados permitidos
(`docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx` y `docs/piloto/ejemplos_simulados/Registro_Sesiones_Piloto_SIMULADO_v4.xlsx`):

| Ejecución | Qué contiene |
|---|---|
| `20261005_demostracion/` | `INFORME_DEMOSTRACION_SIMULADA.md` (resultados por etapa, advertencias y fricciones encontradas), una subcarpeta por etapa (`01_ingesta` … `06_tablero`) y los registros de cada comando (`logs_etapas/`) |

Reglas: cada archivo lleva `ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo` (primera línea, columna o campo `ESTADO`, o metadatos del PNG) y el sufijo `_SIMULADO`; el modo no escribe en
`corpus/real/`, `logs/v3_real/` ni las carpetas privadas, y no congela el modelo real; los modelos Rasa entrenados se hacen en una carpeta temporal y se borran (no se suben `.tar.gz`).
Las frases del lote son generadas y las consultas de las sesiones son el texto de las tarjetas: **no miden lenguaje real ni evalúan un modelo**.

El tablero real (`logs/avance/estado_compuertas.md`) puede leer esta carpeta, pero muestra sus resultados siempre como «(Simulado)» y no los cuenta como reales.
