# Verificación de las respuestas del chatbot contra el TUPA

**Estado: En curso** (compuerta G4 del protocolo 2.14).

| Archivo | Qué es |
|---|---|
| `Verificacion_TUPA_v4.xlsx` | Una fila por respuesta de trámite (44): compara la respuesta actual de `domain.yml` con el TUPA y otras fuentes oficiales. La v4 solo agrega una columna de **marco general orientativo (no verificado)**; los datos verificados no cambian respecto de la v3 |
| `historico/Verificacion_TUPA_v3.xlsx` | Versión anterior, sin la columna de marco general |

**Cómo se mide la compuerta G4** (hoja Resumen): filas de prioridad Alta pendientes = 0, filas con alerta = 0 y filas Corregir o Coincide sin confirmar por el tesista = 0. Las de prioridad Media
sin verificar conservan la marca [Verificar] y se declaran como limitación. Hoy: 10 de 44 verificadas, 23 Alta pendientes y 10 sin confirmar (ver `logs/avance/estado_compuertas.md`).

La búsqueda asistida no confirma nada por sí sola: la columna «Confirmado por el tesista» la llena el tesista. **No guardar el `.xlsx` con openpyxl** (se pierden validaciones y formato; los scripts solo lo leen).
Cuando el tesista guarde una versión nueva, va aquí (`Verificacion_TUPA_v5.xlsx`…) y la anterior pasa a `historico/`; el tablero lee la versión más alta.
