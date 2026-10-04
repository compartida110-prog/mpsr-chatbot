# Piloto exploratorio V1.3 (sesión asistida, n = 60)

**Estado: Planificado.** Los materiales ya están; las sesiones con personas todavía no se hicieron.

| Archivo | Qué es | Estado |
|---|---|---|
| `Sesion_Asistida_Formulario_v2.docx` / `.pdf` | Guía de aplicación, paquete por persona y 56 tarjetas de situación | **Ejecutado** (elaborado por el tesista) |
| `Registro_Sesiones_Piloto_v2.xlsx` | Plantilla vacía del registro (hojas Sesiones, Resumen, Tarjetas, Parametros, Calc, Notas). Los encabezados de la hoja Sesiones (fila 3; `analizar_piloto.py` los busca en las primeras 10 filas) son la fuente de verdad de `scripts/analizar_piloto.py` | **Ejecutado** (plantilla vacía) |
| `ejemplos_simulados/Registro_Sesiones_Piloto_DEMO_SINTETICA.xlsx` | Copia de la plantilla rellenada con datos **falsos** (60 sesiones, textos «[SIMULACIÓN…]») para probar el código; `analizar_piloto.py` la rechaza salvo con `--permitir-simulado` | **Simulado** |
| `historico/` | Versiones anteriores (`Registro_Sesiones_Piloto_v1.xlsx`, `Sesion_Asistida_Formulario_v1`): la v2 solo corrige dos textos de meta del Resumen (el formato decimal dependía del idioma de Excel: salía «Meta ≥ 04» y «Mínimo 001»); los encabezados no cambian | Reemplazadas por la v2 |
| `Instrucciones_ClaudeCode_*.md` (cambio de diseño, siguiente paso, ajustes al registro) | Instrucciones de los últimos pasos | Trazabilidad |
| `privado/` | Registro real lleno y hojas originales; **no se sube a GitHub** (`.gitignore`) | — |

**Todavía no:** el modelo no se congeló (se congela con `scripts/congelar_modelo.py` solo después de la Parte B y del refinamiento, justo antes de la primera sesión)
ni se ejecutó la Parte B ni el análisis con datos reales.

**No guardar los `.xlsx` con openpyxl**: se pierden validaciones y formato; los scripts solo los leen. Pre-piloto: 5 a 15 personas (objetivo operativo 5–8 por el plazo del curso).
