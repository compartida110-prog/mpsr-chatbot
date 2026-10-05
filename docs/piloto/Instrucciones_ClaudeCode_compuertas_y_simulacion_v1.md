# Instrucciones para Claude Code — Compuertas por avance y datos simulados (v1)

Contexto: el protocolo V1.4 reemplaza la «fecha de corte» por **compuertas de criterio** (sección 2.14, G1 a G7). Las etapas avanzan por resultados, no por fechas. Además, el tesista trabajará con **datos simulados** para demostrar el pipeline del curso. Mismas reglas de siempre: nada simulado como real, no editar la historia, no inventar datos.

## 1. Documentos

- Reemplaza en `docs/` el protocolo y la nota por los `_v7` (Word y PDF). Mueve los `_v6` a `docs/historico/`, sin borrarlos.
- Copia `Verificacion_TUPA_v4.xlsx` a `docs/tupa/` y mueve la v3 a `docs/tupa/historico/`. La v4 solo agrega una columna de marco general (no verificado); los datos verificados no cambian.
- Ejecuta `verificar_referencias.py` con los `_v7`. Resultado esperado: cero discrepancias. Si una afirmación citaba la «fecha de corte», actualízala a la sección 2.14 y reporta el cambio.

## 2. Auditoría de «fecha de corte»

Busca `fecha de corte`, `fecha límite` y `plazo` en README, `docs/`, instrucciones `.md`, `configs/` y docstrings o mensajes de `scripts/`. Clasifica cada coincidencia, como en la auditoría anterior:

- **HISTÓRICO** (filas pasadas de `incident_log.csv`, `evidencias/`, `docs/historico/`): no se edita.
- **VIGENTE**: se reemplaza con el cambio mínimo por «compuertas de avance (protocolo 2.14)». **No cambies lógica de scripts.**

Registra una incidencia nueva «Compuertas por avance», agregando una sola fila al final. Aclara que supera a la regla de fecha de corte de la incidencia «Piloto (diseño)», sin modificar esa fila.

## 3. `scripts/estado_compuertas.py` (tablero de avance)

Lee los artefactos del repositorio y escribe `logs/avance/estado_compuertas.md` (y `.json`) con una fila por compuerta: estado, evidencia, y la etiqueta **Real** o **Simulado**. Solo lee y **nunca escribe fuera de `logs/avance/`**.

| Compuerta | Cómo se evalúa |
|---|---|
| G1 | Reporte de ingesta del libro de transcripción: «Listo para la Parte B» (≥15 transcritos, 0 sin consentimiento, cada intención con ≥3 frases). |
| G2 | Ingesta sin errores bloqueantes y una marca explícita de que el tesista revisó el reporte de datos personales (archivo `logs/avance/revision_pii.txt` creado por el tesista). |
| G3 | Registro de evaluaciones del conjunto de prueba real: ciclos de refinamiento usados (máximo 2), mejora entre ciclos y F1 macro de la única evaluación final (≥0,75). |
| G4 | Resumen de la hoja del TUPA: filas Alta pendientes = 0, alertas = 0 y filas Corregir o Coincide sin confirmar = 0. |
| G5 | Existencia y validez de `logs/v3_real/modelo_congelado.json`, con fecha posterior a G3 y G4. |
| G6 | Registro del pre-piloto: 5–15 sesiones completas y alfa ≥ 0,70 (con advertencia si n es pequeño). |
| G7 | Registro de sesiones: elegibles y completas ≥ 60, o cierre declarado con ≥ 30. |

Estados posibles: **Cumplida**, **En curso**, **Pendiente (sin evidencia)** y **No cumplida**. Una compuerta evaluada con datos simulados se muestra como «Cumplida (Simulado)» y **nunca** cuenta como real. El tablero debe decir en el encabezado cuántas compuertas están cumplidas con datos reales: hoy, ninguna.

## 4. Modo de demostración con datos simulados

El tesista quiere poder ejecutar el flujo completo con datos simulados para el curso. Hoy `--permitir-simulado` escribe solo en una carpeta temporal. Agrega un modo de demostración que **no cambie el comportamiento por defecto**:

- Opción `--demo-simulada`, que implica `--permitir-simulado` y escribe en `evidencias/simulado_demostracion/<ejecución>/`.
- Cada archivo generado lleva en su primera línea o en un campo propio: `ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo`. Los CSV llevan además el sufijo `_SIMULADO`.
- **Nunca** escribe en `corpus/real/`, `logs/v3_real/`, `docs/lote_real_1/privado/` ni `docs/piloto/privado/`.
- No congela el modelo real: para la demostración usa un modelo de demostración con otro nombre de archivo y un `modelo_congelado_SIMULADO.json`.
- Archivos de entrada permitidos: `Lote1_Transcripcion_SIMULADO_v2.xlsx` y `Registro_Sesiones_Piloto_SIMULADO_v4.xlsx`, en `ejemplos_simulados/`.
- El tablero de la sección 3 puede leer esta carpeta, pero muestra sus resultados siempre como Simulado.

Implementa solo el modo; **no ejecutes la demostración completa** hasta que el tesista lo pida.

## 5. Prueba de humo (rótulo: Simulada)

Usa datos falsos en una carpeta temporal. Debe comprobar:

- el tablero sin evidencia: todas Pendiente, con «0 compuertas cumplidas con datos reales»;
- una compuerta cumplida con datos simulados: aparece «Cumplida (Simulado)» y no suma a las reales;
- G3 con más de 2 ciclos de refinamiento: aparece «No cumplida»;
- G5 con congelamiento anterior a G4: aparece «No cumplida»;
- `--demo-simulada`: escribe solo en `evidencias/simulado_demostracion/`, con el marcador SIMULADO en cada archivo, y se niega a escribir en las carpetas reales;
- sin `--demo-simulada`, el comportamiento anterior no cambia.

## 6. Cerrar

Actualiza el README (tabla de estado: «Tablero de compuertas», Ejecutado, y «Demostración simulada», Planificado), guarda las evidencias, ejecuta `verificar_referencias.py` y haz commit y push, sin datos personales.
