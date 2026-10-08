# Propuesta: respuestas de `despedida` y `agradecimiento` para un «gracias» suelto

**Estado: PROPUESTA, no aplicada.** No se tocó `domain.yml` ni `domain_v3.yml`.

## Problema
Un «gracias» suelto se usa tanto para agradecer como para despedirse, y las frases de los lotes lo confirman (varias respuestas de ambas situaciones son solo «gracias»). El modelo lo clasificará a veces como `agradecimiento` y a veces como `despedida`;
la confusión entre ambas es **esperable** y no es un error del chatbot, así que conviene que **cualquiera de las dos respuestas sirva para las dos lecturas**.

## Texto actual (idéntico en `domain.yml` y `domain_v3.yml`)
| Respuesta | Texto actual | Qué falla con un «gracias» suelto |
|---|---|---|
| `utter_agradecimiento` | ¡Con gusto! ¿Hay algo más en lo que te pueda ayudar? | Si la persona se estaba despidiendo, se le vuelve a preguntar como si siguiera la conversación (aceptable, pero no cierra). |
| `utter_despedida` | ¡Gracias por tu consulta! Que tengas un buen día. | Si la persona solo agradecía, la respuesta suena a eco («gracias» contestado con «gracias») y cierra la conversación sin ofrecer más ayuda. |

## Texto propuesto
| Respuesta | Texto propuesto | Por qué sirve para las dos lecturas |
|---|---|---|
| `utter_agradecimiento` | ¡Con gusto! Si necesitas algo más sobre algún trámite de la MPSR, aquí estoy. Si ya terminaste, ¡que tengas un buen día! | Atiende al que agradece (ofrece ayuda) y al que se despide (se cierra con un deseo). |
| `utter_despedida` | ¡Con gusto! Gracias por escribirnos. Que tengas un buen día; si te surge otra consulta sobre un trámite de la MPSR, escríbeme. | Responde al agradecimiento («con gusto»), cierra para el que se despide y deja la puerta abierta para el que quería seguir. |

Criterios: ambas empiezan con «¡Con gusto!» (responde al «gracias»), ninguna repite «gracias» como eco, las dos ofrecen ayuda y se cierran con cortesía, y no prometen nada que el chatbot no pueda cumplir. No llevan marca `[Verificar]` (no dependen del TUPA).

## Cómo se aplicaría (cuando lo apruebes)
Son dos respuestas conversacionales que **no** forman parte de las 26 del TUPA; se aplicarían aparte, en `domain.yml` y en `domain_v3.yml` (mismo texto), sin tocar el resto de las respuestas, y se verificaría con la prueba de humo de respuestas de las 54 intenciones.
