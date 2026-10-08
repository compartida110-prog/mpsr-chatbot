# Propuesta (v3): respuestas de `despedida` y `agradecimiento` para un «gracias» suelto

**Estado: PROPUESTA con los textos del tesista (v3), a la espera de su confirmación; NO aplicada.** No se tocó `domain.yml` ni `domain_v3.yml`. La revisa el tesista.

## Problema
Un «gracias» suelto se usa tanto para agradecer como para despedirse; las dos intenciones se confunden de forma esperable. Por eso ambas respuestas deben servir para un «gracias» y también para «chau», «hasta luego» o «ya listo», y la de despedida no debe sonar a que contesta un agradecimiento que no hubo.

## Texto actual (idéntico en `domain.yml` y `domain_v3.yml`)
| Respuesta | Texto actual | Observación |
|---|---|---|
| `utter_despedida` | ¡Gracias por tu consulta! Que tengas un buen día. | **Empieza con «Gracias»**: hace eco si la persona agradeció. |
| `utter_agradecimiento` | ¡Con gusto! ¿Hay algo más en lo que te pueda ayudar? | Responde bien al agradecimiento, pero no cierra si la persona se despedía. |

## Texto propuesto
| Respuesta | Texto propuesto |
|---|---|
| `utter_agradecimiento` | ¡Un gusto ayudarte! Si necesitas algo más, aquí estoy. |
| `utter_despedida` | ¡Un gusto ayudarte! Que tengas un buen día. Si necesitas algo más de la municipalidad, escríbeme. |

## Verificaciones sobre el texto propuesto
- Apertura común «¡Un gusto ayudarte!» en las dos (en vez de «¡Con gusto!»): vale para un «gracias» y para una despedida.
- **Ninguna de las dos contiene «gracias»** (ni como eco ni de otra forma); se retiró el «Gracias por tu consulta» actual de la despedida y el «Gracias por escribirnos» de la propuesta anterior.
- **Ninguna contiene «MPSR»**; donde hace falta nombrar a la institución dice «la municipalidad». La sigla queda solo en nombres de archivo, código y comentarios.
- Segunda frase de `utter_agradecimiento`: una sola línea corta («Si necesitas algo más, aquí estoy.»), apta para chat por celular.
- Se mantiene el tuteo y el tono de las demás respuestas; no prometen nada que el chatbot no pueda cumplir y no llevan marca `[Verificar]` (no dependen del TUPA).

## Aparte
`logs/avance/listado_mpsr_en_respuestas.md` lista (solo lectura) las 34 respuestas de los `domain` que hoy dicen «MPSR», incluidas las del TUPA. Es una decisión tuya si se reemplaza por «la municipalidad»; no se cambió nada.

## Cómo se aplicaría (cuando lo apruebes)
Se aplicarían aparte de las 26 del TUPA, en `domain.yml` y `domain_v3.yml` (mismo texto), sin tocar el resto, y se verificaría con la prueba de humo de respuestas de las 54 intenciones.
