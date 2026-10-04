# Instrucciones para Claude Code — Siguiente paso tras la auditoría del piloto (v1)

Contexto: la auditoría quedó en cero pendientes y la prueba de humo pasó 29/29. Lo que sigue cierra los cabos sueltos que tú mismo reportaste. Mismas reglas de siempre: nada simulado como real, no editar la historia, no inventar archivos.

## 1. Copiar los dos archivos que faltaban

El tesista te entregará `Sesion_Asistida_Formulario_v1.docx`, `Sesion_Asistida_Formulario_v1.pdf` y `Registro_Sesiones_Piloto_v1.xlsx`. Cópialos a `docs/piloto/`.

- Si no los recibes, **no los reemplaces con nada**: deja la verificación marcada "pendiente".
- No guardes el `.xlsx` con openpyxl.

## 2. Encabezados exactos en `analizar_piloto.py`

La fuente de verdad son los encabezados de la **fila 3 de la hoja Sesiones** del registro real. Con el archivo ya en `docs/piloto/`:

- Sustituye el reconocimiento por patrones por búsquedas de **encabezado exacto**. Conserva `--mapa-columnas` solo como respaldo.
- Lee también las hojas **Tarjetas** (tarjeta → intención esperada) y **Parametros** (tabla de conversión de rangos a minutos, modelo congelado).
- Agrega a la prueba de humo una comprobación nueva: todos los encabezados que usa el script existen en la plantilla real. Si falta uno, falla.
- Repite la prueba de humo con una **copia de la plantilla real** rellenada con datos falsos en una carpeta temporal. Rótulo: Simulada. No guardes nada en el repositorio.

## 3. `verificar_referencias.py`: dejar de afirmar un número de incidencias

Los documentos `_v6` ya no citan una cifra de incidencias (dicen "bitácora en `incident_log.csv`"), porque el número cambia con cada incidencia nueva.

- Quita la comparación de igualdad con el número de filas de `incident_log.csv`.
- El número de filas pasa a ser un dato **informativo** del reporte.
- La comprobación de `docs/piloto/` se mantiene: debe pasar a OK cuando los archivos estén copiados.

## 4. Documentos `_v6`

- Reemplaza en `docs/` el protocolo y la nota por los `_v6` (Word y PDF).
- Mueve los `_v5` a `docs/historico/`, sin borrarlos.
- Ejecuta `verificar_referencias.py` con los `_v6`. **Resultado esperado: cero discrepancias.** Si aparece alguna, repórtala y no la tapes.

## 5. Rango del pre-piloto

Vale el rango del protocolo: **5 a 15 personas**. Los 5 a 8 son solo el objetivo operativo por el plazo del curso, y están dentro del rango.

- Corrige el texto de las instrucciones o del README donde diga solo "5 a 8", para que diga "5 a 15 (objetivo operativo 5–8)".
- No cambies el protocolo.

## 6. Lo que NO debes hacer todavía

- No ejecutes `congelar_modelo.py` con el modelo real. Se congela solo después de la Parte B y del refinamiento, y justo antes de la primera sesión.
- No ejecutes la Parte B ni `analizar_piloto.py` con datos reales: aún no existen.

## 7. Subir

Haz commit y push, sin modelos ni datos personales. En el mensaje final entrega: el resultado de `verificar_referencias.py` con los `_v6` (cuántas afirmaciones OK y qué discrepancias, si las hay) y el resultado de la prueba de humo con la plantilla real.
