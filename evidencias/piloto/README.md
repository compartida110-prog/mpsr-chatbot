# Evidencias del piloto exploratorio (V1.3)

Estado: el piloto con personas está **Planificado**; aquí solo hay verificaciones del código y de los documentos.

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_smoke_piloto_SIMULADA.txt` y `capturas/01_smoke_piloto_SIMULADA.png` | Prueba de humo de `congelar_modelo.py` y `analizar_piloto.py` (29/29) | **Simulada**: registro, modelo y predictor falsos; no es un resultado del piloto |
| `salidas/02_verificar_referencias_v5.txt`, `capturas/02_verificar_referencias_v5.png` y `verificacion_referencias_v5.md` | `verificar_referencias.py` contra el protocolo V1.3 y la Nota (v5): 46 afirmaciones, 41 OK, 2 discrepancias | **Ejecutado** |

Discrepancias que informa la verificación (no se ocultan ni se corrigen en los documentos):

1. 42 incidencias en `incident_log.csv` frente a 41 en la Nota v5: la 42.ª es la fila «Piloto (diseño)» de este cambio, posterior a la Nota.
2. `docs/piloto/` no contiene aún el formulario de sesión asistida ni el registro de sesiones: el tesista debe aportarlos.

La verificación de la V1.2 (`../v3_real/verificacion_referencias.md`) no se modificó. Los resultados reales del piloto, cuando existan, irán en `logs/piloto/` y los datos personales en `docs/piloto/privado/` (ambos fuera de Git en el caso de los datos personales).

## Segunda tanda (documentos v6 y encabezados exactos)

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/03_smoke_piloto_plantilla_real_SIMULADA.txt` y `capturas/03_…png` | Prueba de humo (41/41) con encabezados exactos de la plantilla real y una copia de la plantilla real rellenada con datos falsos (`docs/piloto/ejemplos_simulados/`) | **Simulada**: no es un resultado del piloto |
| `salidas/04_verificar_referencias_v6.txt`, `capturas/04_…png` y `verificacion_referencias_v6.md` | `verificar_referencias.py` contra el protocolo V1.3 y la Nota (v6): 46 afirmaciones, 43 OK, 1 nota, 2 planificadas, **0 discrepancias** | **Ejecutado** |

Las dos discrepancias de la primera tanda (arriba) quedaron resueltas: los documentos v6 ya no citan un número de incidencias (el verificador lo muestra solo como dato informativo)
y el formulario y el registro ya están en `docs/piloto/`. Los archivos 01 y 02 se conservan tal como se generaron.

## Tercera tanda (registro y formulario v2)

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/05_smoke_piloto_plantilla_v2_SIMULADA.txt` y `capturas/05_…png` | Prueba de humo (43/43) con la plantilla v2 y el caso nuevo: el mismo registro con el encabezado en la fila 3 y en la fila 2 da el mismo resultado | **Simulada** |
| `salidas/06_verificar_referencias_v6_registro_v2.txt` y `capturas/06_…png` | `verificar_referencias.py` con los `_v6` y los archivos v2 de `docs/piloto/`; el informe `verificacion_referencias_v6.md` se regeneró | **Ejecutado** |
