# Ejemplos simulados del piloto

**Estado: Simulado.** Nada de esta carpeta es un resultado del piloto.

| Archivo | Qué es |
|---|---|
| `Registro_Sesiones_Piloto_DEMO_SINTETICA.xlsx` | Copia de la plantilla del registro rellenada con datos **falsos** (60 sesiones; textos «[SIMULACIÓN…]») para probar el código |

Avisos:

1. **No sirve para evaluar el modelo.** Las consultas de la demo son el texto de la tarjeta con el prefijo «[SIMULACIÓN…]», así que la predicción sería trivial. El análisis con
   `--permitir-simulado` solo prueba que el código funciona; sus cifras no se usan en ningún reporte como resultado del asistente. Si alguna vez se muestran, van rotuladas **Simulado**.
2. **Los textos de meta del Resumen muestran «04» y «001».** Es el formato decimal que depende del idioma de Excel y que corrige la v2 del registro (`Registro_Sesiones_Piloto_v2.xlsx`,
   que concatena los valores directamente). La demo no se edita.
3. **El encabezado está en la fila 2** (se borró la fila de leyenda). `scripts/analizar_piloto.py` busca «Código de sesión» en las primeras 10 filas, así que lee la demo igual que la plantilla.
