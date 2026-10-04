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
