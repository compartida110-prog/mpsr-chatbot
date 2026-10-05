ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo
# Informe de la demostración simulada completa

_Actualizado el 2026-10-05 11:54: se agregó la etapa 3d (umbral aplicado a las predicciones del test ya guardadas) y su fricción; el resto no cambió._

**Todo lo de este informe es SIMULADO.** Ejecución `20261005_demostracion` (2026-10-05 11:21), 3141 s. Archivos de entrada: `Lote1_Transcripcion_SIMULADO_v2.xlsx` y `Registro_Sesiones_Piloto_SIMULADO_v4.xlsx`. Escrita solo en `evidencias/simulado_demostracion/20261005_demostracion/`; no se tocó `corpus/real/`, `logs/v3_real/` ni las carpetas privadas, y nada se registró como real.

## Advertencias

1. **Las frases del lote son generadas y no miden lenguaje real.** Las escribió quien preparó el libro de prueba (varias son idénticas a frases del corpus sintético); las cifras de las etapas 2 y 3 no dicen nada sobre cómo escribe la gente de Juliaca.
2. **Las consultas de las sesiones son el texto de las tarjetas**, con el prefijo «[SIMULACIÓN…]», así que acertarlas es trivial; además la prueba final de la etapa 5 usa un **predictor simulado**, no el modelo. Su exactitud no evalúa ningún modelo.
3. **Las compuertas aparecen como «Cumplida (Simulado)» y no cuentan como reales.** Hoy las compuertas cumplidas con datos reales siguen siendo 0 de 7 (`logs/avance/estado_compuertas.md`).
4. La revisión de etiquetas fue automática (no humana) y el modelo «congelado» es un marcador de texto con otro nombre; el modelo real no se congeló.

## Resultados por etapa

| Etapa | Estado | Resultado | Tiempo | Notas |
|---|---|---|---|---|
| 1. Ingesta del libro (--libro, --demo-simulada) | Ejecutada | 25 participantes Transcritos; 273 frases validadas; 7 blancos derivados; 12 frases idénticas al corpus sintético (fuga); «Listo para la Parte B»: SÍ (transcritos 25/15, intenciones con menos de 3 frases: 0) | 2 s | — |
| 1b. Revisión de etiquetas SIMULADA y --aplicar-revision | Ejecutada | 261 OK, 12 DESCARTAR → 261 frases en lote1_real_final.csv. Sin segunda revisora ni kappa: no hubo revisión humana | 2 s | La «revisión» es automática: no mide la calidad de las etiquetas. |
| 2. Partición v3 con el lote simulado (split_corpus_v3.py) | Ejecutada | entrenamiento 708 (sintético), validación 110 y test 151 (frases del lote simulado); 54 intenciones en cada partición; sin frases repetidas entre particiones | 2 s | Verificaciones de la partición superadas (si fallaran, el script no escribe). |
| 3a. Evaluación en validación con la configuración ya elegida (eval_real.py --fase seleccion --configuracion-fija) | Ejecutada | Rasa/DIET 150,64,20: F1 macro validación = 0.8436; SVM (C = 10): F1 macro validación = 0.7475. Una combinación por método; no se repitió la grilla (12 combinaciones de Rasa y 3 de SVM) | 466 s | — |
| 3b. Umbral de confianza elegido sobre validación (fallback_threshold.py) | Ejecutada | t = 0.5; puntaje en validación 76.0 (sin umbral: 62.0) | 2 s | Se eligió y se congeló solo con la validación, antes de evaluar el test; se aplicó al test después, ver 3d. |
| 3c. Evaluación del test, UNA sola vez (eval_real.py --fase test) | Ejecutada | Rasa/DIET F1 macro test = 0.8206 (IC95 % [0.7318, 0.8452]); SVM = 0.8094 (IC95 % [0.7122, 0.8507]). Veces evaluado: {'rasa': 1, 'svm': 1} | 2656 s | Cifras sobre frases generadas: no miden lenguaje real. |
| 3d. Umbral aplicado a las predicciones del test ya guardadas (fallback_threshold.py --fase test --demo-simulada) | Ejecutada **después** de la primera pasada, en la misma carpeta | t = 0.5: cobertura 84.2%, precisión de lo respondido 91.8% (sin umbral 83.2%), errores atrapados 15.0 y respuestas correctas perdidas 8.8 por semilla; puntaje 96.0 (sin umbral 74.8) | 2 s | No se reentrenó ni se evaluó el test otra vez: veces evaluado sigue en {'rasa': 1, 'svm': 1}. |
| 4. Modelo de demostración congelado (congelar_modelo.py --demo-simulada) | Ejecutada | modelo_demostracion_SIMULADO.tar.gz (sha256 024eaa6df478…), umbral t = 0.5; no es el modelo real y no existe logs/v3_real/modelo_congelado.json | 2 s | El «modelo» es un archivo de texto con otro nombre: no se guarda ningún modelo Rasa entrenado. |
| 5. Análisis del registro de sesiones simulado (analizar_piloto.py --demo-simulada) | Ejecutada | n = 60 sesiones elegibles (EJ01 excluida); tiempo: Wilcoxon de rangos con signo (unilateral), p = 8.145e-12, reducción de medias 98.1 %; satisfacción: alfa de Cronbach (ítems 1–8) = 0.549, ítem 9 frente a P10 p = 0.0005216; prueba final con un predictor SIMULADO: accuracy 0.606, F1 macro 0.513 (180 consultas) | 8 s | Las consultas son el texto de la tarjeta con el prefijo «[SIMULACIÓN…]»: acertarlas es trivial y el predictor es simulado, no el modelo. |
| 6. Tablero de compuertas (estado_compuertas.py --demo-simulada) | Ejecutada | Compuertas cumplidas con datos REALES: 0 de 7; con datos simulados: 3. G1 Cumplida (Simulado); G2 En curso (Simulado); G3 Cumplida (Simulado); G4 Pendiente (sin evidencia); G5 En curso (Simulado); G6 Pendiente (sin evidencia); G7 Cumplida (Simulado) | 2 s | Las compuertas «Cumplida (Simulado)» no cuentan como reales. |

### Etapa 3d: el umbral se aplicó después, a las predicciones ya guardadas

**SIMULADO.** Esta etapa se ejecutó el 2026-10-05 11:52, **después** de la pasada principal (que terminó sin aplicar el umbral al test), en la misma carpeta `03_evaluacion/` y sin repetir la demostración.

- **Qué hizo:** leyó las predicciones de test con confianza que `eval_real.py` guardó en su evaluación única (10, 20, 30, 40, 50: 5 semillas, 151 frases cada una) y les aplicó t = 0.5, congelado el 2026-10-05 10:37:31 con la validación, **antes** de la evaluación del test (2026-10-05 11:21:17).
- **Qué no hizo:** no reentrenó, no cargó ningún modelo (la fase solo lee CSV) y no evaluó el test otra vez. El registro del test sigue en `{'rasa': 1, 'svm': 1}`; la aplicación consta aparte en `aplicaciones_de_umbral` y no suma una evaluación.
- **Comprobado:** la huella SHA-256 combinada de las predicciones guardadas fue la misma antes y después de aplicar el umbral, y no apareció ninguna carpeta de modelos temporal. Integridad por huella por semilla: **no disponible** para esta ejecución (las huellas se registran desde este ajuste; aquí se verificaron las semillas y el número de frases).
- **Resultado simulado:** con el umbral se responden menos consultas (cobertura 84.2%) pero con más precisión (91.8% frente a 83.2%). Son frases generadas: no dicen nada sobre lenguaje real.
- **En el flujo real:** `eval_real.py --fase test` aplica el umbral en la misma pasada si ya hay uno congelado antes del test, y `fallback_threshold.py --fase test` lo aplica después sobre las predicciones guardadas (documentado en el `LEEME` del lote real y en el docstring de ambos scripts).

## Tablero de compuertas de la demostración

| Compuerta | Estado | Datos | Nota |
|---|---|---|---|
| **G1** Lote 1 completo | **Cumplida (Simulado)** | Simulado | Transcritos 25/15 (≥ 15); intenciones con menos de 3 frases: 0. |
| **G2** Parte B ejecutada | **En curso (Simulado)** | Simulado | Ingesta sin errores bloqueantes; falta la marca del tesista logs/avance/revision_pii.txt (archivo con su nombre y fecha, después de leer el reporte de datos personales). |
| **G3** Calidad con lenguaje real | **Cumplida (Simulado)** | Simulado | Ciclos de refinamiento: 0/2. Única evaluación del test real: F1 macro = 0.8206 (≥ 0.75). |
| **G4** Respuestas verificadas | **Pendiente (sin evidencia)** | — | — |
| **G5** Modelo congelado | **En curso (Simulado)** | Simulado | Modelo de demostración congelado; no hay evidencia simulada de G3 o G4 con la que compararlo. |
| **G6** Pre-piloto | **Pendiente (sin evidencia)** | — | — |
| **G7** Sesiones | **Cumplida (Simulado)** | Simulado | 60 sesiones elegibles y completas (meta 60). |

Compuertas cumplidas con datos reales: **0 de 7**; con datos simulados: 3 (no cuentan como reales).

## Aislamiento verificado

Se comprobó con SHA-256, antes y después, 55 archivos de `corpus/real/`, `logs/v3_real/`, `docs/lote_real_1/privado/`, `docs/piloto/privado/`, `logs/avance/`, `data/`, `corpus/v3_real/`, `models/`: **ninguno cambió**. Los modelos Rasa se entrenaron en una carpeta temporal fuera del repositorio y se borraron; la carpeta de la ejecución no contiene ningún `.tar.gz` de Rasa.

## Fricciones encontradas

Obstáculos del flujo, con la medida tomada y su estado. La ejecución completa no falló en el primer intento; la mayoría se detectó al diseñar la demostración, y las limitaciones son propias de trabajar con datos simulados.

| Fricción | Detectada | Medida tomada | Estado |
|---|---|---|---|
| La ingesta advirtió 12 frases del lote simulado idénticas a frases del corpus sintético: pasarían a validación/test y provocarían fuga (la partición se niega a continuar con ellas) | durante la ejecución | En la revisión de etiquetas SIMULADA se descartaron (DESCARTAR), como haría una revisora; el resto se marcó OK | Resuelta en la demostración |
| No hay revisión humana de etiquetas en una demostración: --aplicar-revision exige una decisión por frase y la persona que las toma no existe | por diseño | Se simuló una revisión automática (todas OK salvo las fugas, DESCARTAR) y se rotuló como simulada en cada fila; los resultados siguientes no dicen nada sobre la calidad de las etiquetas | Limitación declarada |
| Los modelos Rasa entrenados en la evaluación son archivos .tar.gz pesados; si quedaran en models/ o en evidencias/ podrían subirse al repositorio | al diseñar | Se entrenaron en una carpeta temporal fuera del repositorio, que se borra al terminar; el modelo congelado de la demostración es un marcador de texto con otro nombre | Resuelta |
| Marcar cada archivo al terminar su etapa cambia nombres (_SIMULADO) y agrega la columna ESTADO a los CSV: la etapa siguiente ya no encontraría sus entradas | al diseñar | Cada etapa escribe sin marcar y el marcado se hace una sola vez al final (opción interna --demo-sin-marcar); el tablero, que sí necesita los nombres marcados, se ejecuta después | Resuelta |
| congelar_modelo.py --demo-simulada trataba --salida como carpeta aunque se le pasara un archivo .json: habría creado una carpeta con el nombre del archivo | al diseñar | --salida acepta una carpeta o un .json de la carpeta de demostración (se usa la carpeta); cubierto por la prueba de humo | Resuelta |
| eval_real.py solo sabía recorrer la grilla completa (12 combinaciones de Rasa/DIET y 3 valores de C del SVM), que la demostración no debe repetir | al diseñar | Se agregaron --configuracion-fija (150,64,20) y --svm-c (10); sin ellas el comportamiento no cambia | Resuelta |
| El marcado renombró el «modelo» .tar.gz y el congelamiento quedó apuntando a un archivo que ya no existía | en un ensayo previo | Los nombres que ya contienen _SIMULADO no se renombran, y el congelamiento de demostración no referencia archivos que se modifican al marcar (el umbral se copia adentro) | Resuelta |
| El marcado no cubría los .yml (la configuración de cada entrenamiento de Rasa), que podían quedar sin marcador | al diseñar | Los .yml llevan el marcador como comentario en la primera línea (siguen siendo YAML válido) | Resuelta |
| El tablero buscaba los archivos simulados un solo nivel adentro, habría mezclado ejecuciones distintas y además evaluaba el mundo real | al diseñar | Búsqueda recursiva restringida a la carpeta de la ejecución y, en el modo de demostración, el mundo real no se evalúa | Resuelta |
| Los registros de entrenamiento y de las etapas guardaban rutas absolutas del equipo con el nombre de usuario de Windows | durante la ejecución | Se reemplazan por rutas relativas al repositorio y «<usuario>» antes del marcado final (el congelamiento de demostración sigue siendo verificable) | Resuelta |
| La demostración tardó 52 minutos: el test entrena Rasa/DIET con 5 semillas de 150 épocas (2656 s) y la validación otro modelo (466 s) | durante la ejecución | No se redujo: bajar las semillas cambiaría el procedimiento de repeticiones del protocolo. Se ejecutó en segundo plano | Limitación declarada |
| G2 (marca del tesista), G4 (hoja del TUPA) y G6 (registro de pre-piloto) no pueden cumplirse con datos simulados: dependen de una acción humana o de archivos que la demostración no simula | por diseño | Quedan «En curso (Simulado)» o «Pendiente (sin evidencia)»; no se fabricó ninguna marca humana | Limitación declarada |
| G3 sale «Cumplida (Simulado)» con 0 ciclos de refinamiento registrados porque la demostración no refina; el F1 alto sale de frases generadas, muy parecidas a las del entrenamiento | por diseño | Se advierte en este informe; no cuenta como real | Limitación declarada |
| La prueba final de las sesiones usa un predictor SIMULADO (el modelo congelado de demostración es un marcador de texto) y las consultas son el texto de las tarjetas | por diseño | Se rotula en este informe y en el análisis; su exactitud no evalúa ningún modelo | Limitación declarada |
| `fallback_threshold.py --fase test` anotaba la aplicación del umbral como una evaluación más del test (`rasa_umbral`), lo que se leía como una segunda evaluación, y no comprobaba que las predicciones fueran las de la evaluación única ni que el umbral se hubiera congelado antes del test | al verificar el flujo | La aplicación se anota aparte (`aplicaciones_de_umbral`) y no suma una evaluación; se comprueba que sean las mismas semillas, el mismo número de frases y la misma huella SHA-256, y que el umbral sea anterior al test; `eval_real.py --fase test` lo aplica en la misma pasada si ya hay un umbral congelado | Resuelta |
| En esta primera pasada de la demostración el umbral se eligió solo con la validación y no se aplicó al test (por instrucción) | por instrucción | Se aplicó después, sobre las predicciones ya guardadas y en la misma carpeta, con `fallback_threshold.py --fase test --demo-simulada` (1,7 s, sin reentrenar ni evaluar de nuevo; etapa 3d). Esas predicciones se guardaron antes de que se registraran huellas: la integridad se comprobó por semillas y número de frases, no por huella | Resuelta (integridad por huella: limitación declarada) |
