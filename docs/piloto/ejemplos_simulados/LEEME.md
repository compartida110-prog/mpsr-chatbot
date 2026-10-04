# Ejemplos simulados del piloto

**Estado: Simulado.** Nada de esta carpeta es un resultado del piloto.

| Archivo | Qué es |
|---|---|
| `Registro_Sesiones_Piloto_SIMULADO_v4.xlsx` | Copia de la plantilla del registro rellenada con datos **falsos** (60 sesiones elegibles; título «DATOS SIMULADOS»; consultas con el prefijo «[SIMULACIÓN…]») para probar el código |
| `historico/Registro_Sesiones_Piloto_DEMO_SINTETICA.xlsx` | Demo anterior (reemplazada por la v4); se conserva sin cambios |

Avisos:

1. **Es una demo simulada.** Se usa solo para probar el código (`tests/smoke_piloto.py`); ninguna de sus cifras es un resultado del asistente. Si alguna vez se muestran, van rotuladas **Simulado**.
2. **No sirve para evaluar el modelo.** Las consultas son el texto de la tarjeta con el prefijo «[SIMULACIÓN…]», así que la predicción sería trivial. El análisis con
   `--permitir-simulado` solo prueba que el código funciona.
3. **El encabezado está en la fila 2** (se borró la fila de leyenda). `scripts/analizar_piloto.py` busca «Código de sesión» en las primeras 10 filas, así que la lee igual que la plantilla (fila 3).
   Sin `--permitir-simulado` el script la rechaza.

Nota histórica: la demo anterior (`historico/`) mostraba «04» y «001» en los textos de meta del Resumen por el formato decimal que depende del idioma de Excel; la v2 del registro lo corrige y la v4 ya
no lo tiene. Esa demo no se editó.
