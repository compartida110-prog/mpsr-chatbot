# Evidencias — P09 (domain.yml con respuestas completas)

Validación del `domain.yml` con las 54 respuestas (44 de trámites + 10 conversacionales)
sobre el corpus v2, el 2026-10-02, con el entorno de `requirements.txt`.

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 01 | `python -m rasa data validate --data data/nlu.yml data/rules.yml --domain domain.yml --config configs/rasa_config.yml` | sin conflictos (`exit=0`) | [txt](salidas/01_rasa_data_validate.txt) | [png](capturas/01_rasa_data_validate.png) |
| 02 | conteo de respuestas de `domain.yml` | 54/54, 0 `[PENDIENTE]`, 40 de 44 trámites con `[Verificar …]` | [txt](salidas/02_resumen_domain.txt) | [png](capturas/02_resumen_domain.png) |

**Estas respuestas NO están validadas con el TUPA real de la MPSR.** Las 44 respuestas de
trámites usan información típica de un TUPA municipal peruano. Cada una que afirma
requisitos, tasas, plazos, oficinas, canales o formas de pago lleva al final una nota
`[Verificar … con el TUPA vigente de la MPSR]`. Quedan sin nota solo 4 respuestas genéricas:
`denuncia_seguridad_ciudadana`, `horario_recojo_basura`, `requisitos_generales` y
`costos_generales`. No usarlas en el pre-piloto (P11.2) ni reportarlas como validadas hasta
contrastarlas con el TUPA oficial (ver `incident_log.csv`, fila `P09 (domain.yml)`).
