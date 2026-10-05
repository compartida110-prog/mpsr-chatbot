# Avance por compuertas (protocolo 2.14)

`estado_compuertas.md` y `estado_compuertas.json` los escribe `scripts/estado_compuertas.py` (solo lee el repositorio y solo escribe aquí). Estados: Cumplida, En curso,
Pendiente (sin evidencia) y No cumplida; una compuerta evaluada con datos simulados se muestra «Cumplida (Simulado)» y nunca cuenta como real.

**Archivos que crea el tesista** (el tablero solo los lee; ningún script los inventa):

| Archivo | Para qué | Compuerta |
|---|---|---|
| `revision_pii.txt` | Marca de que leyó el reporte de datos personales de la ingesta antes de subir cualquier archivo (su nombre y la fecha) | G2 |
| `ciclos_refinamiento.csv` | Un renglón por ciclo de refinamiento medido sobre validación: `ciclo,fecha,f1_macro_validacion` (máximo 2 ciclos; se detiene antes si la mejora es menor a 0,02) | G3 |
| `cierre_piloto.txt` | Declaración de cierre de la recolección con al menos 30 sesiones elegibles (si no se llegó a 60) | G7 |

No hay nada que escribir en este archivo ni en `estado_compuertas.*` a mano: se regeneran con `python scripts/estado_compuertas.py`.
