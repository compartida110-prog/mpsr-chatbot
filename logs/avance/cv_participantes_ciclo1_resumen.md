# Validación cruzada dejando participantes fuera — ANÁLISIS DE SENSIBILIDAD (no cuenta para G3 ni para decisiones de ajuste; incluye frases del test)

185 frases reales de 31 participantes; 5 folds por participante (StratifiedGroupKFold, seed 42); en cada fold se entrena con las 758 sintéticas + las reales de los demás participantes.

## RASA
- F1 macro global (54 intenciones, predicciones de todos los folds juntas): **0.7987**, IC95 % por bootstrap de participantes [0.6578, 0.8198]; accuracy 0.7946.
- F1 macro por fold: 0.667, 0.854, 0.676, 0.682, 0.611 (media 0.698, DE 0.092; solo intenciones presentes en cada fold, con pocas frases por fold: no es comparable con el global); n por fold: 35, 48, 33, 27, 42.
- Nota: con intenciones de 3 a 6 frases reales, el F1 por intención y el IC son muy inestables; se reporta el n de cada una.

| Intención | n (frases reales) | F1 | Aciertos |
|---|---|---|---|
| afirmar | 3 | 1.00 | 3 |
| agradecimiento | 6 | 0.57 | 4 |
| ayuda_chatbot | 3 | 0.67 | 2 |
| certificado_defensa_civil | 3 | 0.80 | 2 |
| certificado_posesion | 3 | 0.86 | 3 |
| constancia_domiciliaria | 3 | 0.86 | 3 |
| constancia_no_adeudo | 3 | 0.86 | 3 |
| consulta_deuda_predial | 4 | 0.86 | 3 |
| consulta_no_entendida | 3 | 0.86 | 3 |
| contacto_telefonico | 3 | 0.80 | 2 |
| copia_documento | 3 | 1.00 | 3 |
| costos_generales | 3 | 0.67 | 2 |
| denuncia_seguridad_ciudadana | 3 | 0.50 | 2 |
| despedida | 4 | 0.33 | 1 |
| estado_reclamo | 3 | 0.86 | 3 |
| estado_tramite | 4 | 0.86 | 3 |
| fraccionamiento_deuda | 3 | 1.00 | 3 |
| fuera_de_alcance | 6 | 0.50 | 2 |
| hablar_con_persona | 3 | 0.67 | 2 |
| horario_atencion_general | 5 | 0.91 | 5 |
| horario_mesa_partes | 3 | 0.80 | 2 |
| horario_recojo_basura | 3 | 0.75 | 3 |
| impuesto_alcabala | 4 | 0.40 | 1 |
| inspeccion_tecnica | 3 | 0.80 | 2 |
| libro_reclamaciones | 4 | 0.89 | 4 |
| licencia_edificacion_costo | 3 | 0.80 | 2 |
| licencia_edificacion_requisitos | 3 | 0.86 | 3 |
| licencia_funcionamiento_costo | 5 | 1.00 | 5 |
| licencia_funcionamiento_plazo | 3 | 0.50 | 1 |
| licencia_funcionamiento_requisitos | 4 | 0.22 | 1 |
| limpieza_via_publica | 3 | 0.80 | 2 |
| mantenimiento_parques | 3 | 0.80 | 2 |
| negar | 3 | 1.00 | 3 |
| pago_arbitrios | 3 | 1.00 | 3 |
| pago_predial_como | 3 | 0.86 | 3 |
| partida_defuncion | 4 | 0.86 | 3 |
| partida_matrimonio | 3 | 0.86 | 3 |
| partida_nacimiento | 5 | 1.00 | 5 |
| poda_arboles | 3 | 1.00 | 3 |
| presentar_reclamo | 5 | 0.80 | 4 |
| queja_atencion | 4 | 0.50 | 2 |
| rectificacion_partida | 3 | 1.00 | 3 |
| redes_sociales_mpsr | 3 | 0.86 | 3 |
| renovacion_licencia | 4 | 0.89 | 4 |
| repetir_informacion | 3 | 1.00 | 3 |
| reporte_alumbrado_publico | 3 | 1.00 | 3 |
| requisitos_defensa_civil | 3 | 0.86 | 3 |
| requisitos_generales | 3 | 0.67 | 2 |
| requisitos_matrimonio_civil | 3 | 0.80 | 2 |
| requisitos_mesa_partes | 3 | 1.00 | 3 |
| saludo | 3 | 0.86 | 3 |
| serenazgo_contacto | 3 | 0.80 | 2 |
| sugerencia | 3 | 1.00 | 3 |
| ubicacion_oficinas | 3 | 0.50 | 2 |
