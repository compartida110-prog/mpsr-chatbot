# Evidencias: revisión de etiquetas del lote 1 y soporte del formulario F (lote 1b)

Solo hay salidas de pruebas con datos **falsos** y de la verificación; ninguna frase real ni el libro de revisión están aquí (están en `docs/lote_real_1/privado/` y `corpus/real/`, fuera de Git).

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_smoke_transcripcion_SIMULADA.txt` | Transcripción (33/33): incluye P26–P28 en F, situaciones que F no reparte, consentimiento y el libro V1.3 vacío | **Simulada** |
| `salidas/02_…` a `05_…` | Conciliación 28/28, compuertas 67/67, piloto 51/51 y lote real 78/78, repetidas tras el cambio | **Simulada** |
| `salidas/06_verificar_referencias_v8.txt` | `verificar_referencias.py` con los documentos v8 | **Ejecutado** |

El traslado de la revisión de etiquetas (169 de 169 emparejadas; 158 OK, 11 CAMBIAR, 0 DESCARTAR) es un resultado **real** y consta solo en cifras en `incident_log.csv`.

## Segunda tanda (libro combinado y corrección de referencias)

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/07_…` a `11_…` y capturas | Transcripción (42/42; ahora con `combinar_libros.py` y el verificador de referencias de fila), conciliación 28/28, compuertas 67/67, piloto 51/51 y lote real 78/78 | **Simulada** |
| `salidas/12_verificar_referencias_v8.txt` | `verificar_referencias.py` | **Ejecutado** |

El libro combinado real (28 participantes, 181 frases) y su ingesta están fuera de Git; aquí solo constan cifras en `incident_log.csv`.
