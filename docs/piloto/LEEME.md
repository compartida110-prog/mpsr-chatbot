# Piloto exploratorio V1.3 (sesión asistida, n = 60)

**Estado: Planificado.** Los materiales ya están; las sesiones con personas todavía no se hicieron.

| Archivo | Qué es | Estado |
|---|---|---|
| `Sesion_Asistida_Formulario_v3.docx` / `.pdf` | Guía de aplicación, paquete por persona y 56 tarjetas de situación. La v3 cambia solo la casilla de la lista de control: ahora habla de las compuertas de avance (protocolo 2.14) en vez de la «fecha de corte» | **Ejecutado** (elaborado por el tesista) |
| `Registro_Sesiones_Piloto_v2.xlsx` | Plantilla vacía del registro (hojas Sesiones, Resumen, Tarjetas, Parametros, Calc, Notas). Los encabezados de la hoja Sesiones (fila 3; `analizar_piloto.py` los busca en las primeras 10 filas) son la fuente de verdad de `scripts/analizar_piloto.py` | **Ejecutado** (plantilla vacía) |
| `ejemplos_simulados/Registro_Sesiones_Piloto_SIMULADO_v4.xlsx` | Copia de la plantilla rellenada con datos **falsos** (60 sesiones, textos «[SIMULACIÓN…]») para probar el código; `analizar_piloto.py` la rechaza salvo con `--permitir-simulado`. La demo anterior está en `ejemplos_simulados/historico/` | **Simulado** |
| `historico/` | Versiones anteriores (`Registro_Sesiones_Piloto_v1.xlsx`, `Sesion_Asistida_Formulario_v1` y `_v2`; la v2 del formulario solo conserva la casilla de la «fecha de corte» que reemplazó la v3). La v2 del registro: la v2 solo corrige dos textos de meta del Resumen (el formato decimal dependía del idioma de Excel: salía «Meta ≥ 04» y «Mínimo 001»); los encabezados no cambian | Reemplazadas por la v2 |
| `Instrucciones_ClaudeCode_*.md` (cambio de diseño, siguiente paso, ajustes al registro) | Instrucciones de los últimos pasos | Trazabilidad |
| `privado/` | Registro real lleno y hojas originales; **no se sube a GitHub** (`.gitignore`) | — |
| `../../scripts/asistente_local.py` | Asistente de consola para el pre-piloto: carga solo el NLU congelado (`LOTE2-FINAL`), verifica `congelar_modelo.py --verificar` antes de arrancar, aplica t = 0,50 y responde con `domain_v3.yml`; guarda un registro CSV por sesión (PPxx) en `privado/`. Comando: `python scripts/asistente_local.py PP01`. Prueba: `tests/smoke_asistente.py` (datos falsos) | **Ejecutado** (probado con datos falsos) |
| `../../scripts/preparar_registro_prepiloto.py` | Copia la plantilla a `privado/Registro_Sesiones_Prepiloto.xlsx` (el nombre que lee el tablero para G6) y anota en Parametros el modelo congelado y su fecha, editando el XML (sin openpyxl) | **Ejecutado** |

**Estado al 8 de octubre de 2026:** el modelo ya está congelado (`logs/v3_real/modelo_congelado.json`, G5 cumplida; `LOTE2-FINAL v1`, 2026-10-08 22:17); faltan el pre-piloto (G6) y las sesiones (G7). Con `analizar_piloto.py` no se analiza el registro del pre-piloto: gastaría la prueba final única del modelo congelado; para G6 basta el tablero (`estado_compuertas.py`).

**No guardar los `.xlsx` con openpyxl**: se pierden validaciones y formato; los scripts solo los leen. Pre-piloto: 5 a 15 personas (objetivo operativo 5–8 por el plazo del curso).
