# Ingesta del lote 2 — cifras e identificadores (sin frases)

- Participantes transcritos: **25** (P33, P57); formularios: {'A': 5, 'B': 5, 'C': 5, 'D': 5, 'E': 5}; frases validadas: **280** (ids Q0001–Q0280).
- Edad: {'18–29': 7, '30–44': 7, '45–59': 7, '60 a más': 4}.
- **Alerta de perfil — no vive en Juliaca:** 0 (todos «Sí»).
- Consentimiento: la ingesta bloquea cualquier participante Transcrito sin «Consentimiento firmado = Sí»; no hubo errores bloqueantes (los 25 lo tienen).
- Observación (no es criterio de inclusión): trámite en los últimos 12 meses = «No»: 10 -> ['P34', 'P37', 'P38', 'P41', 'P45', 'P47', 'P48', 'P50', 'P54', 'P56'].

- Frases por intención (esperada): mínimo 5, máximo 15; 0 intenciones con menos de 3; fuera_de_alcance 15.

| Intención | Frases |
|---|---|
| afirmar | 5 |
| agradecimiento | 5 |
| ayuda_chatbot | 5 |
| certificado_defensa_civil | 5 |
| certificado_posesion | 5 |
| constancia_domiciliaria | 5 |
| constancia_no_adeudo | 5 |
| consulta_deuda_predial | 5 |
| consulta_no_entendida | 5 |
| contacto_telefonico | 5 |
| copia_documento | 5 |
| costos_generales | 5 |
| denuncia_seguridad_ciudadana | 5 |
| despedida | 5 |
| estado_reclamo | 5 |
| estado_tramite | 5 |
| fraccionamiento_deuda | 5 |
| fuera_de_alcance | 15 |
| hablar_con_persona | 5 |
| horario_atencion_general | 5 |
| horario_mesa_partes | 5 |
| horario_recojo_basura | 5 |
| impuesto_alcabala | 5 |
| inspeccion_tecnica | 5 |
| libro_reclamaciones | 5 |
| licencia_edificacion_costo | 5 |
| licencia_edificacion_requisitos | 5 |
| licencia_funcionamiento_costo | 5 |
| licencia_funcionamiento_plazo | 5 |
| licencia_funcionamiento_requisitos | 5 |
| limpieza_via_publica | 5 |
| mantenimiento_parques | 5 |
| negar | 5 |
| pago_arbitrios | 5 |
| pago_predial_como | 5 |
| partida_defuncion | 5 |
| partida_matrimonio | 5 |
| partida_nacimiento | 5 |
| poda_arboles | 5 |
| presentar_reclamo | 5 |
| queja_atencion | 5 |
| rectificacion_partida | 5 |
| redes_sociales_mpsr | 5 |
| renovacion_licencia | 5 |
| repetir_informacion | 5 |
| reporte_alumbrado_publico | 5 |
| requisitos_defensa_civil | 5 |
| requisitos_generales | 5 |
| requisitos_matrimonio_civil | 5 |
| requisitos_mesa_partes | 5 |
| saludo | 5 |
| serenazgo_contacto | 5 |
| sugerencia | 5 |
| ubicacion_oficinas | 5 |

- **Frases idénticas (tras normalizar) a una de entrenamiento: 13** (se excluirían de la medición por coincidencia exacta, nunca por predicciones; split_lote2.py las registrará en el log):

| Frase del lote 2 | Participante | Situación | Entrenamiento (id) | Fuente | ¿Misma etiqueta? |
|---|---|---|---|---|---|
| Q0018 | P34 | S27 | R0144 | lenguaje real (lote 1) | sí |
| Q0025 | P35 | S08 | R0065 | lenguaje real (lote 1) | sí |
| Q0039 | P36 | S24 | R0044 | lenguaje real (lote 1) | sí |
| Q0087 | P40 | S38 | R0109 | lenguaje real (lote 1) | sí |
| Q0176 | P48 | S36 | U0421 | sintético | sí |
| Q0181 | P49 | S02 | U0013 | sintético | sí |
| Q0183 | P49 | S12 | U0133 | sintético | sí |
| Q0202 | P50 | S53 | U0601 | sintético | sí |
| Q0209 | P51 | S34 | U0398 | sintético | sí |
| Q0210 | P51 | S39 | R0159 | lenguaje real (lote 1) | sí |
| Q0212 | P51 | S49 | R0161 | lenguaje real (lote 1) | sí |
| Q0213 | P51 | S54 | U0677 | sintético | sí |
| Q0222 | P52 | S45 | U0529 | sintético | sí |

- **Frases repetidas dentro del lote (mismo texto normalizado): 0 grupos**.

No se evaluó nada ni se mostraron predicciones: la revisión de etiquetas se hace sin ver lo que predice el modelo.
