# Evidencias — preparación del lote real y de la partición v3 (Parte A, protocolo V1.2)

> **Estado: SIMULADO** para las ejecuciones 01–03: se hicieron con **datos falsos** ("prueba falsa …") en una carpeta temporal, solo para
> comprobar que el flujo corre y detecta lo que debe. **No hay ningún resultado sobre lenguaje real**: la recolección del lote 1 (Parte B)
> está **Planificada**. Los datos falsos no se guardan en el repositorio. La ejecución 04 es una verificación **real** (estado Ejecutado)
> de las rutas y cifras del protocolo contra los archivos del repositorio.

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 01 | `python tests/smoke_lote_real.py` (catálogo falso) | **53/53 comprobaciones PASS** (5 min) | [txt](salidas/01_smoke_lote_real_DATOS_FALSOS.txt) | [png](capturas/01_smoke_lote_real_DATOS_FALSOS.png) |
| 01a | primer intento del mismo arnés | 52/53: el fallo era un falso positivo (ver abajo) | [txt](salidas/01a_smoke_lote_real_primer_intento_DATOS_FALSOS.txt) | [png](capturas/01a_smoke_lote_real_primer_intento_DATOS_FALSOS.png) |
| 02 | mismo arnés con el **catálogo real** del tesista (`situaciones_lote1_v1.csv`) y 6 comprobaciones nuevas | **59/59 comprobaciones PASS** (6 min) | [txt](salidas/02_smoke_lote_real_catalogo_real_DATOS_FALSOS.txt) | [png](capturas/02_smoke_lote_real_catalogo_real_DATOS_FALSOS.png) |
| 03 | `python tests/smoke_conciliar.py` (seguimiento v3 + respuestas FALSAS) | **22/22 comprobaciones PASS**: detecta ausentes y blancos con respuesta, se niega con SIMULADO_v3/v2, exporta sin ocupación | [txt](salidas/03_smoke_conciliar_seguimiento_DATOS_FALSOS.txt) | [png](capturas/03_smoke_conciliar_seguimiento_DATOS_FALSOS.png) |
| 04 | `python scripts/verificar_referencias.py` | 37 afirmaciones del protocolo V1.2 y la nota: 30 OK, 5 discrepancias (ver [verificacion_referencias.md](verificacion_referencias.md)) | [txt](salidas/04_verificar_referencias.txt) | [png](capturas/04_verificar_referencias.png) |



Las ejecuciones 03 usan datos **falsos** (estado Simulado); la 04 es una verificación real sobre el repositorio (estado Ejecutado).

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

**Catálogo real (ejecución 02).** El primer arnés usaba un catálogo falso porque `situaciones_lote1_v1.csv` no estaba entre los archivos entregados. Al recibirlo (columnas `scenario_id, form, categoria, intent_esperada, situacion`) se verificó que: tiene 56 situaciones, 54 intenciones (solo `fuera_de_alcance` x3) y 12/11/11/11/11 por formulario; sus intenciones coinciden con `domain.yml`; el texto y el formulario de cada situación son idénticos a los de los formularios (.docx, por ID) y aparecen literalmente en el PDF; y su `categoria` coincide con la del corpus en las 56 filas. `ingest_real_lote.py` ya leía las columnas que exige (`scenario_id`, `form`, `intent_esperada`); se adaptó para reconocer `categoria` (alias de `category`) y contrastarla con el corpus (advertencia [7]), sin tocar el archivo. Se reemplazó la plantilla por el catálogo y se repitió el arnés usándolo: 59/59 (6 comprobaciones nuevas: columnas y cobertura del catálogo real, alias `category`, intención en blanco -> bloquea, categoría distinta -> advertencia, y categorías del catálogo real = 0 diferencias).

**Pendiente (no es de esta etapa):** recolectar el lote 1 y ejecutar la Parte B.
