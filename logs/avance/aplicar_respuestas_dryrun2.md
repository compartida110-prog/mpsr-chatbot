# Dry-run de respuestas — Verificacion_TUPA_v10_4.xlsx + textos del tesista

Estado: **DRY-RUN (no se escribió ningún dominio)**. Solo respuestas `utter_*`; NLU, ejemplos de entrenamiento e intenciones no se tocan; no se reentrena ni se evalúa.

- Respuestas que cambian: **4** de 55 (idénticas en `domain.yml` y `domain_v3.yml`).
- Con marcador [Verificar…]: **5 → 1**. Marcador quitado en 4: libro_reclamaciones, limpieza_via_publica, poda_arboles, reporte_alumbrado_publico.
- Siguen con marcador (1): constancia_domiciliaria.
- No se tocan (bloque E, `conservar`): .

## Avisos

- utter_libro_reclamaciones: la fila del TUPA y el texto del tesista coinciden en la intención; gana el texto del tesista
- utter_saludo: no contiene «de la MPSR»
- utter_fuera_de_alcance: no contiene «de la MPSR»
- utter_hablar_con_persona: no contiene «de la MPSR»
- utter_ayuda_chatbot: no contiene «de la MPSR»

## Diff por respuesta

### `utter_libro_reclamaciones` — manual H4

- **Antes:** El libro de reclamaciones está disponible en la Plataforma de Atención; también puede existir una versión virtual. [Verificar si la MPSR cuenta con libro de reclamaciones virtual].
- **Después:** Puedes presentar tu reclamo en el Libro de Reclamaciones, en la sede de la municipalidad (Jr. Jáuregui N.° 321, Plaza de Armas). También existe una versión digital; para consultar cómo acceder, llama a la central: (051) 321201.

### `utter_limpieza_via_publica` — manual H2

- **Antes:** Para solicitar limpieza de una vía pública puedes comunicarte con el área de limpieza pública de la MPSR, indicando la calle y cuadra exacta. [Verificar área responsable y procedimiento con el TUPA vigente de la MPSR].
- **Después:** La limpieza de vías públicas está a cargo de la Gerencia de Gestión Ambiental y Residuos Sólidos de la municipalidad. Puedes presentar tu solicitud en Mesa de Partes indicando la calle y la cuadra, o acercarte a la sede en el Jr. Jáuregui N.° 321.

### `utter_poda_arboles` — manual H3

- **Antes:** La poda de árboles públicos se solicita ante el área de Servicios Públicos de la MPSR, indicando la ubicación exacta del árbol. [Verificar área responsable y procedimiento con el TUPA vigente de la MPSR].
- **Después:** La solicitud de poda de árboles se evalúa en la Gerencia de Gestión Ambiental y Residuos Sólidos. Presenta tu pedido en Mesa de Partes indicando la ubicación exacta del árbol, o acércate a la sede en el Jr. Jáuregui N.° 321. Si el árbol toca cables eléctricos, avisa también a Electro Puno: (051) 366066.

### `utter_reporte_alumbrado_publico` — manual H1

- **Antes:** Para reportar una falla de alumbrado público puedes comunicarte con el área de Servicios Públicos de la MPSR, indicando la ubicación exacta del poste o farola. [Verificar área responsable y procedimiento con el TUPA vigente de la MPSR].
- **Después:** El alumbrado público generalmente lo atiende Electro Puno, la empresa eléctrica. Puedes reportar la falla en su Central de Reclamos al (051) 366066 o en su portal de reclamos: https://www.electropuno.com.pe/virtual.php . También puedes llamar a su central al (051) 352552 o escribir a electropuno@electropuno.com.pe. Si un poste o cable representa riesgo eléctrico, llama de inmediato.

