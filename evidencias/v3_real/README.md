# Evidencias — preparación del lote real y de la partición v3 (Parte A, protocolo V1.2)

> **Estado: SIMULADO.** Todo lo de esta carpeta se ejecutó con **datos falsos** ("prueba falsa …") en una carpeta temporal,
> solo para comprobar que el flujo corre y detecta lo que debe. **No hay ningún resultado sobre lenguaje real**: la
> recolección del lote 1 (Parte B) está **Planificada**. Los datos falsos no se guardan en el repositorio.

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 01 | `python tests/smoke_lote_real.py` | **53/53 comprobaciones PASS** (5 min) | [txt](salidas/01_smoke_lote_real_DATOS_FALSOS.txt) | [png](capturas/01_smoke_lote_real_DATOS_FALSOS.png) |
| 01a | primer intento del mismo arnés | 52/53: el fallo era un falso positivo (ver abajo) | [txt](salidas/01a_smoke_lote_real_primer_intento_DATOS_FALSOS.txt) | [png](capturas/01a_smoke_lote_real_primer_intento_DATOS_FALSOS.png) |

**Qué comprueba el arnés** (`tests/smoke_lote_real.py`): ingesta (4 errores bloqueantes y las 6 advertencias: blanco, texto corto, datos
personales —que no se borran solos—, duplicados, frase idéntica al corpus sintético y cobertura < 3), revisión de etiquetas
(OK/CAMBIAR/DESCARTAR, % cambiado, kappa entre revisoras), partición v3 (54 intenciones en las 3 particiones, ninguna frase repetida, ningún
grupo en dos particiones, ninguna frase real en entrenamiento, reproducible con seed 42, y los casos que deben fallar), evaluación
(`--smoke`: IC95 %, McNemar, registro que impide evaluar el test dos veces), validación cruzada agrupada, umbral de confianza (tabla
t = 0.30–0.80, puntaje aciertos − 2 × errores, congelado, evaluación única en test, `--escribir-config`) y el dominio v3: `rasa data validate`
sin conflictos y un modelo con `FallbackClassifier` que responde `utter_no_entendi` a un texto sin sentido.

**Primer intento (01a).** La única comprobación que falló fue la de integridad del repositorio ("ningún archivo de `docs/lote_real_1`,
`corpus/real`, … cambió durante la prueba"): mientras corría, el tesista/asistente creó `docs/lote_real_1/LEEME.md` y `corpus/real/README.md`
(se comprobó por fecha de modificación: 06:32, dentro de la ventana de la prueba; los scripts no escribieron en el repositorio). Se mejoró el
mensaje del arnés para listar qué archivos cambiaron y se repitió sin tocar esas carpetas: 53/53.

**Pendiente (no es de esta etapa):** colocar `docs/lote_real_1/situaciones_lote1_v1.csv` (no estaba entre los archivos entregados; hay una plantilla
con las 56 situaciones y la intención en blanco), recolectar el lote 1 y ejecutar la Parte B.
