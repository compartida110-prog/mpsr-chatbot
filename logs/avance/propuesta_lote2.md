# Lote 2 — prueba independiente de G3 (PLANIFICADO, NO ejecutado)

**Estado: PLANIFICADO.** No hay datos del lote 2 y nada de lo siguiente se ha medido. G3 sigue **No cumplida, lote 1** (F1 macro del test del lote 1 = 0,687; criterio 0,75, sin cambios).

> **Procedimiento CERRADO el 2026-10-08, antes de recoger datos. No se modifica después.** Si algo debe cambiar, se registra como desviación nueva, con fecha, en `incident_log.csv`, y no reemplaza este texto.
> Texto de la modificación a la regla V1.2 en el protocolo V1.6, sección 5.8 (según el tesista; no pude comparar el texto de esa sección con este procedimiento).

## 1. Participantes y formularios
- **Participantes:** P33–P57 (**25**; mínimo 20). Solo adultos que viven en Juliaca y que **no** respondieron los lotes 1, 1b ni 1c. Las ingestas y la partición rechazan cualquier otro código.
- **Formularios:** A–E (`Lote2_Formularios_lenguaje_real_v1`, del tesista). Catálogo: `docs/lote_real_2/situaciones_lote2_v1.csv` = las mismas 56 situaciones y formularios A–E del lote 1 (sin complementos F ni G). Si el documento del tesista difiere de ese CSV, se corrige el CSV **antes** de recoger datos.
- **Tamaño:** 5 personas por formulario ⇒ ~5 frases por situación (15 para `fuera_de_alcance`, que tiene 3 situaciones); unas 280 frases antes de blancos y descartes.
- **Carpeta privada:** `docs/lote_real_2/privado/` con el mismo `.gitignore` que `lote_real_1` (solo se versiona su `LEEME.md`); también quedan protegidos `corpus/real_lote2/`, `corpus/v3_lote2/`, `data/v3_lote2/nlu_*.yml`.
- **Ids:** las frases del lote 2 se llaman `Q0001…` (las del lote 1 son `R…`), para no mezclarlas.

## 2. Rol de los datos
- **Lote 2 = SOLO test.** No hay partición de validación del lote 2, no se usa para elegir hiperparámetros ni umbral.
- **Entrenamiento = 707 sintéticas + 185 reales activas del lote 1** (892 en total): el corpus sintético sin la copia U0554 y las frases reales del lote 1 sin R0136 (excluida) ni los 3 descartes (R0147, R0182, R0183). Se armó con `scripts/preparar_entrenamiento_lote2.py --solo-contar` (verificado el 2026-10-08: 707 + 185 = 892, sin leer nada del lote 2).
- **Esto modifica la regla V1.2** («las frases reales no se usan para entrenar») y se declara antes de medir. El test del lote 1 pasa a ser dato de desarrollo (ya se evaluó una vez; su resultado no se reutiliza para decidir ajustes).
- **Duplicados con el entrenamiento y entre frases del lote 2** (`scripts/split_lote2.py`; sin mirar el modelo ni sus errores; cada decisión va a un log con motivo y fecha, solo con identificadores):
  1. Entre frases del lote 2 con el mismo texto normalizado: el mismo procedimiento del lote 1 (misma etiqueta ⇒ se conserva el menor id y se descartan las demás; etiquetas distintas ⇒ se conserva la mayoritaria y se excluyen las otras; empate ⇒ se excluyen todas). Log: `docs/lote_real_2/log_cambios_lote2.csv`.
  2. Frase del lote 2 idéntica (tras normalizar) a una de entrenamiento: **se excluye de la medición** (queda en el corpus con split «excluida»). Log: `docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv`.
  - ⚠️ **Interpretación a confirmar por el tesista:** en el lote 1 el «mismo procedimiento» fue excluir la copia sintética del *entrenamiento* y conservar la frase real en test. En el lote 2 el modelo ya está congelado (ya vio esa frase de entrenamiento) y no se puede reentrenar sin romper el congelamiento, por eso se excluye la frase del *test*. Si se prefiere excluir la copia del entrenamiento, tendría que hacerse y volver a congelar **antes** de abrir el lote 2, y las copias aún no se conocen.
- Cada intención debe conservar al menos 3 frases con textos distintos en test; si no, la preparación se detiene (como en el lote 1).

## 3. Refinamiento previo (usa los ciclos que quedan: **0 de 2**)
- **Solo con datos del lote 1**, midiendo con **validación cruzada AGRUPADA POR PARTICIPANTE** (el análisis de sensibilidad ya existe: `scripts/crossval_participantes.py`; sus cifras actuales no cuentan para G3 ni son decisiones de ajuste).
- **Se detiene** cuando la mejora entre ciclos sea **< 0,02 de F1 macro** (regla del tablero).
- **Antes de cada ciclo** se declara por escrito qué se cambia, de entre: **umbral de confianza**, **corpus** (frases del entrenamiento) o **respuestas** (las respuestas no entran al NLU: no cambian el F1, solo la prueba de humo). La declaración va a `logs/avance/ciclos_refinamiento_declaracion.csv` (columnas `ciclo,fecha,cambio,descripcion,declarado_antes_de_medir`) y el resultado de cada ciclo (F1 macro de la validación cruzada por participante) a `logs/avance/ciclos_refinamiento.csv`, que lee el tablero. **Cada ciclo requiere la aprobación del tesista; no se abre ninguno sin ella.**
- **Prohibido** decidir cualquier ajuste mirando errores o confusiones del test del lote 1 ni, desde luego, del lote 2.

## 4. Congelamiento (ANTES de abrir el lote 2)
- Se congelan el **modelo**, la **configuración**, el **dominio**, el **conjunto de entrenamiento final** (`corpus/v3_lote2/entrenamiento_lote2.csv`) y el **umbral de confianza**, con sus huellas **sha256**, en `logs/v3_real/lote2_congelado_previo.json` (`congelar_modelo.py --corpus corpus/v3_lote2/entrenamiento_lote2.csv --salida logs/v3_real/lote2_congelado_previo.json`).
- **Puerta en el código:** `ingest_real_lote.py --lote 2` y `split_lote2.py` se **niegan a leer** el lote 2 mientras ese congelamiento no exista o alguna huella haya cambiado (modelo, configuración, dominio, entrenamiento o umbral). Esa puerta se comprobó con datos falsos (`tests/smoke_lote2.py`).
- El congelamiento previo al lote 2 es distinto del congelamiento del piloto (G5, `modelo_congelado.json`): este último sigue exigiendo G3 y G4.

## 5. Evaluación (UNA sola vez)
- Se evalúa el test del lote 2 **una sola vez**, con el modelo y el umbral ya congelados; criterio **F1 macro ≥ 0,75** (sin cambios).
- Se reporta: **F1 macro** con **IC95 % bootstrap por frases y por participantes**, **F1 por intención** (con su n), **cobertura y precisión con el umbral** y la **confusión despedida ↔ agradecimiento aparte** (rotulada como esperable).
- **Si no se cumple:** G3 se informa como **no cumplida**; **no se baja el umbral ni se repite la evaluación**.
- **Tablero:** `estado_compuertas.py` muestra G3 como «No cumplida, lote 1» (medición actual) y registra «Medida en lote 2» aparte; G3 solo pasa a Cumplida con una medición ≥ 0,75 en el lote 2, congelada antes y evaluada una sola vez.

## 6. Limitaciones que se declaran desde ya
- Misma lista de situaciones que el lote 1: **independiente por personas, no por situaciones**.
- Muestra de conveniencia y pequeña (25 personas, ~280 frases): el F1 tendrá varianza alta; con ~5 frases por situación y ~5 por intención el IC seguirá siendo ancho.
- Revisión de etiquetas de una sola revisora (sin acuerdo entre revisores): el kappa solo mide etiqueta esperada frente a esa revisión.
- El entrenamiento incorpora frases reales del lote 1 (modifica la regla V1.2); las frases reales del lote 1 provienen de otras personas, no de las del lote 2.

## 7. Qué hay hecho y qué falta
- **Hecho (solo preparación, probado con datos FALSOS en `tests/smoke_lote2.py`):** carpeta `docs/lote_real_2/` y protecciones `.gitignore`; catálogo `situaciones_lote2_v1.csv`; `ingest_real_lote.py --lote 2` (P33–P57, ids `Q…`, archivos `lote2_*`, puerta de congelamiento); `preparar_entrenamiento_lote2.py`; `split_lote2.py` (solo test, sin validación, duplicados con log); tablero con «Medida en lote 2».
- **Falta (no se hizo):** el script de evaluación única del lote 2 (IC por frases y por participantes, F1 por intención, umbral, confusión del par); el refinamiento previo (0 de 2, requiere aprobación); congelar modelo y umbral; recolectar y transcribir el lote 2; actualizar la matriz y el protocolo si cambia algo; confirmar la interpretación de duplicados con el entrenamiento (punto 2).

---

# Anexo: candidata a intención nueva — recojo de basura (registrada el 2026-10-08)
No se crea ninguna intención ahora (no se toca NLU, ejemplos ni dominio). Hoy `horario_recojo_basura` ya existe como intención; lo que sería nuevo es una respuesta con datos por sector, que hoy no se puede dar con certeza.

- **Fuente:** croquis por sectores I a VI, en la carpeta de Drive de la municipalidad (revisada por el tesista), y la página oficial de Facebook (la secretaria indicó que los horarios están ahí).
- **Sector I-1:** 2 veces por semana, lunes y jueves, de 6:30 a 10:00 a. m. (croquis firmado por la «Gerencia de Gestión Ambiental y Residuos Sólidos»).
- **Pendiente:** copiar del croquis los datos de los sectores I-2 a I-6, II, III, IV, V y VI (recuadro inferior de cada imagen).
- **Decisión que falta:** si el chatbot puede responder por sector o solo dirigir al croquis y a Facebook; para responder por sector la persona debería indicar su sector, lo que implicaría una intención con entidad (no se hace en esta tarea).
