# Aplicación de respuestas — Verificacion_TUPA_v10_3.xlsx + textos del tesista

Estado: **APLICADO**. Solo respuestas `utter_*`; NLU, ejemplos de entrenamiento e intenciones no se tocan; no se reentrena ni se evalúa.

- Respuestas que cambian: **19** de 55 (idénticas en `domain.yml` y `domain_v3.yml`).
- Con marcador [Verificar…]: **16 → 5**. Marcador quitado en 11: consulta_deuda_predial, estado_reclamo, impuesto_alcabala, mantenimiento_parques, pago_arbitrios, pago_predial_como, presentar_reclamo, queja_atencion, redes_sociales_mpsr, serenazgo_contacto, sugerencia.
- Siguen con marcador (5): constancia_domiciliaria, libro_reclamaciones, limpieza_via_publica, poda_arboles, reporte_alumbrado_publico.
- No se tocan (bloque E, `conservar`): libro_reclamaciones, limpieza_via_publica, poda_arboles, reporte_alumbrado_publico. De ellas contienen un nombre que el bloque D cambiaría y NO se cambia: libro_reclamaciones, poda_arboles, reporte_alumbrado_publico.

## Avisos

- utter_redes_sociales_mpsr: la fila del TUPA y el texto del tesista coinciden en la intención; gana el texto del tesista

## Diff por respuesta

### `utter_agradecimiento` — manual B

- **Antes:** ¡Con gusto! ¿Hay algo más en lo que te pueda ayudar?
- **Después:** ¡Un gusto ayudarte! Si necesitas algo más, aquí estoy.

### `utter_ayuda_chatbot` — sigla -> la municipalidad

- **Antes:** Puedo ayudarte con consultas sobre licencias, tributos municipales, trámites documentarios, defensa civil, registro civil, servicios públicos, reclamos e información general de la MPSR.
- **Después:** Puedo ayudarte con consultas sobre licencias, tributos municipales, trámites documentarios, defensa civil, registro civil, servicios públicos, reclamos e información general de la municipalidad.

### `utter_constancia_domiciliaria` — manual C5 (derivado: revisar)

- **Antes:** La constancia domiciliaria se tramita presentando tu DNI y un recibo de servicio (luz o agua) a tu nombre o de un familiar directo que viva contigo. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Después:** La constancia domiciliaria se tramita en la municipalidad. Necesitas una solicitud dirigida al Alcalde, tu DNI y un recibo de servicio. [Verificar costo y plazo con el TUPA vigente].

### `utter_consulta_deuda_predial` — manual C1

- **Antes:** Puedes consultar tu deuda de impuesto predial presentando tu DNI en la Plataforma de Atención, o a través del número de tu autoavalúo si lo tienes a la mano. [Verificar canal y procedimiento de consulta con el TUPA vigente de la MPSR].
- **Después:** Para consultar tu deuda de impuesto predial acércate a la Plataforma de Atención al Ciudadano, en la ventanilla de Orientación Tributaria / Rentas, con tu DNI y tu número de contribuyente. Si llevas tu autoavalúo, el trámite puede ser más rápido.

### `utter_denuncia_seguridad_ciudadana` — manual C7 (derivado: revisar)

- **Antes:** Para reportar un problema de seguridad ciudadana puedes comunicarte con serenazgo o acudir a la comisaría más cercana si se trata de una emergencia.
- **Después:** Para reportar un problema de seguridad ciudadana puedes comunicarte con serenazgo al 051 329001 (también al 051 329002 y 051 329003). La central de la municipalidad es el (051) 321201. Si es una emergencia, acude a la comisaría más cercana.

### `utter_despedida` — manual B

- **Antes:** ¡Gracias por tu consulta! Que tengas un buen día.
- **Después:** ¡Un gusto ayudarte! Que tengas un buen día. Si necesitas algo más de la municipalidad, escríbeme.

### `utter_estado_reclamo` — manual C14

- **Antes:** El estado de tu reclamo puede consultarse en mesa de partes indicando tu número de expediente. [Verificar canal de consulta con el TUPA vigente de la MPSR].
- **Después:** Puedes consultar el estado de tu trámite en Mesa de Partes con tu número de expediente, o en línea desde Trámite documentario / Seguimiento de trámites en la web: https://munisanroman.gob.pe/web/

### `utter_fuera_de_alcance` — sigla -> la municipalidad

- **Antes:** Soy un asistente especializado en trámites de la MPSR, así que no puedo ayudarte con eso. ¿Tienes alguna consulta sobre un trámite municipal?
- **Después:** Soy un asistente especializado en trámites de la municipalidad, así que no puedo ayudarte con eso. ¿Tienes alguna consulta sobre un trámite municipal?

### `utter_hablar_con_persona` — sigla -> la municipalidad

- **Antes:** Entiendo. Puedes acercarte a la Plataforma de Atención al Ciudadano de la MPSR o llamar a nuestra central telefónica para hablar con un funcionario.
- **Después:** Entiendo. Puedes acercarte a la Plataforma de Atención al Ciudadano de la municipalidad o llamar a nuestra central telefónica para hablar con un funcionario.

### `utter_impuesto_alcabala` — manual C4 (derivado: revisar)

- **Antes:** El impuesto de alcabala se paga cuando compras un inmueble, y corresponde al 3% del valor de transferencia (con un tramo inicial inafecto equivalente a 10 UIT). Se cancela dentro del mes siguiente a la compra. [Verificar tasa, monto inafecto y plazo de pago con el TUPA y la normativa vigentes].
- **Después:** El impuesto de alcabala se paga cuando compras un inmueble, y corresponde al 3% del valor de transferencia (con un tramo inicial inafecto equivalente a 10 UIT). Se cancela dentro del mes siguiente a la compra. Para más información, acércate a la ventanilla de Orientación Tributaria / Rentas.

### `utter_mantenimiento_parques` — manual C9

- **Antes:** Puedes solicitar el mantenimiento de un parque presentando tu pedido en mesa de partes o comunicándote con el área de Servicios Públicos, indicando la ubicación del parque. [Verificar área responsable y procedimiento con el TUPA vigente de la MPSR].
- **Después:** Presenta una solicitud en Mesa de Partes indicando la ubicación del parque. Si es urgente, acércate a la Gerencia de Servicios Públicos y Medio Ambiente.

### `utter_pago_arbitrios` — manual C3

- **Antes:** Los arbitrios municipales (limpieza pública, parques y jardines, serenazgo) se pagan junto con el impuesto predial o de forma independiente en caja de la municipalidad. [Verificar forma y lugar de pago con el TUPA vigente de la MPSR].
- **Después:** Los arbitrios municipales se pueden pagar junto con el impuesto predial o por separado, en las ventanillas de Caja o en las agencias municipales.

### `utter_pago_predial_como` — manual C2

- **Antes:** El impuesto predial se puede pagar en caja de la municipalidad o en los bancos autorizados que tengan convenio con la MPSR. [Verificar si existe opción de pago en línea].
- **Después:** Puedes pagar tu impuesto predial en las ventanillas de Caja de la municipalidad o en sus agencias: Complejo Deportivo La Capilla, Agencia Municipal San Pablo, Agencia Municipal Rodolfo Diesel, Agencia Municipal Tambopata, Agencia Municipal Néstor Cáceres Velásquez y MAC Juliaca (Real Plaza).

### `utter_presentar_reclamo` — manual C13

- **Antes:** Puedes presentar un reclamo en mesa de partes, mediante un escrito simple indicando los hechos y adjuntando tu DNI, o a través del libro de reclamaciones si corresponde. [Verificar procedimiento con el TUPA vigente de la MPSR].
- **Después:** Puedes presentar tus quejas, reclamos o sugerencias en Mesa de Partes, con un escrito simple que indique los hechos y adjuntando tu DNI. También puedes usar la Mesa de Partes Virtual: https://san-roman.siamsoft.pe/portal-ciudadano

### `utter_queja_atencion` — manual C16

- **Antes:** Si tuviste un problema con la atención recibida, puedes presentar tu queja en mesa de partes o directamente en el libro de reclamaciones, detallando lo ocurrido. [Verificar procedimiento con el TUPA vigente de la MPSR].
- **Después:** Puedes presentar tu queja por la atención recibida en Mesa de Partes, detallando lo ocurrido.

### `utter_redes_sociales_mpsr` — manual C18

- **Antes:** La Municipalidad Provincial de San Román publica información e trámites en su página web institucional y en sus redes sociales oficiales. [Verificar enlaces vigentes].
- **Después:** Puedes encontrar a la municipalidad en su web https://munisanroman.gob.pe/web/, en Facebook (https://web.facebook.com/munisanromanjuliaca), Instagram (https://www.instagram.com/muni_san_roman/) y TikTok (https://www.tiktok.com/@munisanroman).

### `utter_saludo` — sigla -> la municipalidad

- **Antes:** ¡Hola! Soy el asistente virtual de la MPSR. ¿En qué trámite te puedo ayudar hoy?
- **Después:** ¡Hola! Soy el asistente virtual de la municipalidad. ¿En qué trámite te puedo ayudar hoy?

### `utter_serenazgo_contacto` — manual C6

- **Antes:** Puedes comunicarte con serenazgo de la MPSR a través de su línea de atención. [Verificar número vigente con la municipalidad].
- **Después:** Puedes comunicarte con serenazgo al 051 329001 (también al 051 329002 y 051 329003). La central de la municipalidad es el (051) 321201. Si es una emergencia, acude a la comisaría más cercana.

### `utter_sugerencia` — manual C17

- **Antes:** Puedes dejar tu sugerencia en mesa de partes mediante un documento simple, o a través de los canales de atención ciudadana de la MPSR. [Verificar canal de recepción con la MPSR].
- **Después:** Puedes dejar tu sugerencia en Mesa de Partes mediante un documento simple, o por los canales de atención ciudadana de la municipalidad.

