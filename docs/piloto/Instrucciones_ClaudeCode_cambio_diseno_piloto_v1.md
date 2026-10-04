# Instrucciones para Claude Code — Cambio de diseño del piloto (n = 60, sesión asistida) (v1)

## Contexto vigente (reemplaza cualquier contexto anterior sobre 120 personas)

El protocolo vigente es la **V1.3**. Solo cambia el piloto. Todo lo demás sigue igual.

| | Antes (V1.2, ahora solo planificado) | Ahora (V1.3, vigente) |
|---|---|---|
| Tamaño | 120 personas | **60 sesiones elegibles** (piloto exploratorio; margen de error ≈ 11,7 %; potencia 80 % para d ≈ 0,37) |
| Diseño | Dos visitas: línea base, recontacto y post-test | **Una sola sesión asistida** de unos 15 minutos |
| Línea base | Ficha P01 aplicada antes | **Parte 1** del formulario de sesión (recordada; mismo contenido que la Ficha P01) |
| Seguimiento | WhatsApp y código de emparejamiento | **Ninguno.** Solo código de sesión SA01, SA02… |
| Medición con el chatbot | Uso durante el piloto y luego encuesta | **3 tarjetas** de situación con cronómetro del aplicador, más encuesta de **9 ítems** en la misma visita |
| Satisfacción pareada | Sin ítem de emparejamiento | **Ítem 9**, con la misma redacción que P10 |

**No cambia:** el lote 1 de frases reales (15–25 personas; solo validación y test), la Parte B, el umbral de confianza, la compuerta F1 ≥ 0,75 sobre el conjunto real retenido, el alfa ≥ 0,70, el modelo congelado y las reglas anti-sesgo. El pre-piloto ahora ensaya el mismo procedimiento con 5 a 8 personas.

El **120** sobrevive solo como valor planificado de la V1.2 (documentos históricos, fórmula de tamaño de muestra) y en archivos simulados. **No lo uses como meta.**

## Reglas

1. Etiqueta cada resultado como Ejecutado, Planificado o Simulado. Nada simulado se presenta como real.
2. No edites la historia: filas pasadas de `incident_log.csv`, `evidencias/`, `corpus/historico/`, archivos simulados.
3. El registro real lleno y las hojas originales van **fuera del repositorio** (`docs/piloto/privado/`, en `.gitignore`).
4. **Las consultas de las sesiones no se usan para ajustar el modelo.** Son el conjunto de prueba final del modelo congelado, y se evalúa una sola vez.
5. No vuelvas a guardar los `.xlsx` con openpyxl: se pierden validaciones y formato.

---

## Tareas

### 1. Copiar los archivos nuevos

El tesista los coloca en una carpeta que puedas leer, o los adjunta.

- `Sesion_Asistida_Formulario_v1.docx` y `.pdf`, y `Registro_Sesiones_Piloto_v1.xlsx` (plantilla vacía) van a `docs/piloto/`.
- El protocolo V1.3 (`Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v5`) y la nota (`Nota_Desviacion_P11_1_v5`), en Word y PDF, van a `docs/`.
- Los `_v4` anteriores se mueven a `docs/historico/`, sin borrarlos.
- Crea `docs/piloto/privado/` y agrégalo a `.gitignore`.

### 2. Auditar las menciones al diseño anterior

Busca en README, `docs/`, instrucciones `.md`, `configs/`, `scripts/` (docstrings y mensajes) estos términos: `120`, `n=120`, `n = 120`, `WhatsApp`, `recontact`, `retención`, `pareado`, `dos visitas`, `P01 real`.

Genera `logs/v3_real/auditoria_diseno_120_vs_60.md` con una fila por coincidencia: archivo, línea, texto, clasificación y acción.

- **HISTÓRICO** (V1.1/V1.2, evidencias, incidencias pasadas, `corpus/historico/`, simulados): no se edita.
- **VIGENTE** (README, instrucciones, `LEEME`, docstrings, mensajes): se corrige con el cambio mínimo. **No cambies lógica de scripts.**

Los scripts del lote 1 (`ingest_real_lote.py`, `split_corpus_v3.py`, `eval_real.py`, `fallback_threshold.py`, `conciliar_seguimiento.py`) siguen siendo válidos: tratan el lote 1, no el piloto.

### 3. README

Actualiza la tabla de estado:

- Piloto exploratorio (sesión asistida, n = 60): *Planificado*.
- Materiales del piloto (formulario y registro): *Ejecutado*.
- Línea base P01 real con n = 120 y WhatsApp: *Reemplazado por la V1.3*.

Agrega una sección corta "Piloto exploratorio (V1.3)" con el procedimiento y los archivos de `docs/piloto/`.

### 4. Incidencia

Agrega a `incident_log.csv`:

- **Fecha:** 2026-10-03.
- **Experimento:** Piloto (diseño).
- **Incidencia:** el piloto planificado (120 personas, dos visitas, WhatsApp) no cabe en el plazo del curso (menos de 2 semanas), y el objetivo es mostrar viabilidad.
- **Decisión:** piloto exploratorio de 60 personas en una sola sesión asistida (V1.3), con modelo congelado, 3 tarjetas por persona y encuesta de 9 ítems.
- **Justificación:** decidido antes de recoger datos del piloto. La línea base es recordada (sesgo de recuerdo y de novedad) y mide el trámite mientras OE3 habla de consultas: se declara como limitación. Si en la fecha de corte el F1 real es menor que 0,75, el piloto se presenta como planificado.

### 5. `scripts/congelar_modelo.py`

- **Entradas:** `--modelo`, `--config`, `--domain`.
- **Salida:** `logs/v3_real/modelo_congelado.json` con el nombre y el sha256 del modelo, el sha256 de la configuración y del dominio, la versión de Rasa y de Python, la fecha UTC y el commit de git.
- No sobrescribe un congelamiento existente salvo con `--forzar --motivo "…"`, que además registra una incidencia.

### 6. `scripts/analizar_piloto.py`

**Entradas:** `--registro` (copia llena del registro), `--modelo-congelado` (el JSON del paso 5), `--catalogo` (`docs/lote_real_1/situaciones_lote1_v1.csv`), `--salida logs/piloto/`.

**Lectura:** por nombre de encabezado (fila 3 de Sesiones), solo lectura, con `data_only=True`. Si las fórmulas no tienen valor guardado, aborta con "abre y guarda el archivo en Excel". Usa solo las filas con `Elegible y completa = Sí` y código que empiece por `SA`.

**Rechazos:** si algún título de hoja contiene "SIMULADO", o si no hay filas elegibles, sale con error. Con `--permitir-simulado` escribe solo en una carpeta temporal y marca las salidas con `_SIMULADO`.

**Tiempo (OE3):**
- Diferencia por persona = minutos post − minutos pre.
- Shapiro-Wilk (α = 0,05) sobre las diferencias: si p > 0,05, t pareada; si no, Wilcoxon.
- Reporta estadístico, p, tamaño de efecto (d_z o r), medias y medianas, reducción de las medias y media de las reducciones individuales.
- IC95 % bootstrap de 1000 remuestreos con semilla 42.

**Satisfacción (OE4):**
- P10 contra el ítem 9, con el mismo procedimiento.
- Media de los ítems 1–8 con su IC.
- Alfa de Cronbach (ítems 1–8). Compáralo con `Resumen!B24` y avisa si difiere más de 0,01.

**Prueba final del modelo congelado:**
- Verifica que el hash del modelo coincide con `modelo_congelado.json`; si no, aborta.
- Por cada consulta (3 por sesión), obtiene la intención predicha y su confianza, y la compara con la intención esperada de su tarjeta (hoja Tarjetas).
- Reporta accuracy y F1 macro sobre las intenciones presentes, con n por intención, y estadísticas de confianza.
- IC por **bootstrap por conglomerados de sesión** (se remuestrean sesiones, no consultas).
- Si hay umbral congelado, reporta cobertura, precisión de lo respondido, errores atrapados y aciertos perdidos.
- Compara con el "¿correcta?" del aplicador y el "¿obtuvo lo que necesitaba?" de la persona (porcentaje de acuerdo).
- Se evalúa **una sola vez**. Lleva `logs/piloto/evaluaciones_prueba_final.log` y se niega a repetirla sin `--motivo`.

**Salidas:** `logs/piloto/analisis_piloto.json` y `.md`, y dos figuras (cajas de tiempo pre y post, histograma de diferencias). Todo rotulado **REAL** con el n efectivo. Si n < 60: "exploratorio, n = X". Nunca presentes los resultados como confirmatorios. Incluye las limitaciones: línea base recordada, sesgo de novedad, trámite frente a consulta, muestra de conveniencia.

### 7. Prueba de humo (`tests/smoke_piloto.py`)

Usa datos falsos en una carpeta temporal y un predictor falso inyectable (no el modelo real). Rótulo: **Simulada**. Nada se guarda en el repositorio, y la salida va a `evidencias/piloto/`. Debe comprobar:

- el caso normal;
- diferencias no normales, que deben llevar a Wilcoxon;
- el alfa, comparado con numpy;
- hash del modelo distinto, que debe abortar;
- un registro con "SIMULADO", que debe ser rechazado;
- una segunda ejecución de la prueba final, que debe negarse;
- la fila de ejemplo `EJ01`, que debe quedar excluida;
- n < 60, que debe rotularse "exploratorio".

### 8. Verificar y subir

- Ejecuta `verificar_referencias.py` con los documentos `_v5`. Debe dar cero discrepancias, porque las erratas E1 a E5 ya están aplicadas. Si la V1.3 introduce una discrepancia, repórtala y no la tapes.
- Haz commit y push, sin modelos ni datos personales.
- En el mensaje final entrega: la tabla de la auditoría (conteos por clasificación y lista de archivos editados) y el resultado de la prueba de humo.
