# Evidencias: preparación del lote 1c y dry-run de domain_v3.yml

Solo hay salidas de pruebas con datos **falsos** y verificaciones; ninguna frase real está aquí.

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_…` a `06_…` y capturas | Transcripción 51/51 (con lote 1c y `ampliar_libro.py`), conciliación 28/28, compuertas 67/67, piloto 51/51, `aplicar_tupa` 6/6 y lote real 78/78 | **Simulada** |
| `salidas/07_verificar_referencias_v8.txt` | `verificar_referencias.py` | **Ejecutado** |

El diff de `domain_v3.yml` con las 26 respuestas (sin aplicar) está en `logs/avance/aplicar_tupa_dryrun_domain_v3.diff`.

## Segunda tanda (ingesta del lote 1c, descartes y partición con log)

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/08_…` a `13_…` y capturas | Transcripción 51/51, conciliación 28/28, compuertas 67/67, piloto 51/51, lote real 86/86 (ahora con el log de cambios, duplicados exactos, 3 textos distintos por intención, limitación de reparto y la confusión despedida ↔ agradecimiento) y aplicar_tupa 6/6 | **Simulada** |
| `salidas/14_verificar_referencias_v8.txt` | `verificar_referencias.py` | **Ejecutado** |

Los resultados reales (ingesta del lote 1c y conteos) constan solo en cifras en `incident_log.csv`; las frases están fuera de Git.
