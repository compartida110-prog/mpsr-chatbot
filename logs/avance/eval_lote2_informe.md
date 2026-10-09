# Evaluación única del lote 2 (cifras; sin frases)

- Frases de test: 267 de 25 participantes. Modelo congelado (sha256 be1a5ad06357…), umbral t = 0.5.
- **F1 macro = 0.9072** | IC95 % por frases [0.8626, 0.9290] (media del bootstrap 0.8980) | IC95 % por participantes [0.8524, 0.9385] (media 0.8997) | accuracy 0.8876.
- Criterio F1 macro ≥ 0.75: **CUMPLE** (punto); límite inferior del IC por frases ≥ 0.75.
- Con el umbral: cobertura 98.9%, precisión de lo respondido 89.8%; respondidas 264 (237 aciertos, 27 errores); abstenciones 3 (3 errores atrapados, 0 correctas perdidas).
- Confusión despedida ↔ agradecimiento (esperable): {'despedida': {'n': 5, 'predicha_despedida': 4, 'predicha_agradecimiento': 0, 'otra': 1}, 'agradecimiento': {'n': 5, 'predicha_despedida': 1, 'predicha_agradecimiento': 4, 'otra': 0}}
- SVM baseline (informativo; G3 se mide solo con DIET): F1 macro = 0.8925 | IC95 % por frases [0.8417, 0.9171] | por participantes [0.8368, 0.9215] | accuracy 0.8727; McNemar exacto (solo SVM acierta 10, solo DIET acierta 14): p = 0.541

| Intención | n | F1 |
|---|---|---|
| afirmar | 5 | 1.00 |
| agradecimiento | 5 | 0.89 |
| ayuda_chatbot | 4 | 1.00 |
| certificado_defensa_civil | 5 | 1.00 |
| certificado_posesion | 5 | 0.89 |
| constancia_domiciliaria | 5 | 0.80 |
| constancia_no_adeudo | 4 | 1.00 |
| consulta_deuda_predial | 5 | 0.89 |
| consulta_no_entendida | 5 | 0.89 |
| contacto_telefonico | 5 | 0.91 |
| copia_documento | 5 | 1.00 |
| costos_generales | 5 | 1.00 |
| denuncia_seguridad_ciudadana | 5 | 0.67 |
| despedida | 5 | 0.80 |
| estado_reclamo | 5 | 1.00 |
| estado_tramite | 5 | 0.89 |
| fraccionamiento_deuda | 5 | 1.00 |
| fuera_de_alcance | 15 | 0.64 |
| hablar_con_persona | 4 | 1.00 |
| horario_atencion_general | 4 | 0.89 |
| horario_mesa_partes | 5 | 0.91 |
| horario_recojo_basura | 5 | 1.00 |
| impuesto_alcabala | 5 | 1.00 |
| inspeccion_tecnica | 5 | 1.00 |
| libro_reclamaciones | 4 | 1.00 |
| licencia_edificacion_costo | 5 | 1.00 |
| licencia_edificacion_requisitos | 5 | 1.00 |
| licencia_funcionamiento_costo | 4 | 0.89 |
| licencia_funcionamiento_plazo | 5 | 0.57 |
| licencia_funcionamiento_requisitos | 5 | 1.00 |
| limpieza_via_publica | 5 | 1.00 |
| mantenimiento_parques | 5 | 1.00 |
| negar | 4 | 1.00 |
| pago_arbitrios | 5 | 1.00 |
| pago_predial_como | 4 | 0.75 |
| partida_defuncion | 5 | 0.89 |
| partida_matrimonio | 5 | 0.75 |
| partida_nacimiento | 4 | 1.00 |
| poda_arboles | 5 | 1.00 |
| presentar_reclamo | 4 | 0.89 |
| queja_atencion | 5 | 0.89 |
| rectificacion_partida | 4 | 1.00 |
| redes_sociales_mpsr | 5 | 0.75 |
| renovacion_licencia | 5 | 0.89 |
| repetir_informacion | 5 | 1.00 |
| reporte_alumbrado_publico | 5 | 1.00 |
| requisitos_defensa_civil | 5 | 1.00 |
| requisitos_generales | 5 | 1.00 |
| requisitos_matrimonio_civil | 5 | 1.00 |
| requisitos_mesa_partes | 5 | 0.89 |
| saludo | 4 | 0.80 |
| serenazgo_contacto | 5 | 0.89 |
| sugerencia | 4 | 1.00 |
| ubicacion_oficinas | 5 | 1.00 |
