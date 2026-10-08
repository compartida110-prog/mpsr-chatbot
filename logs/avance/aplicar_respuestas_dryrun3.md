# Dry-run de respuestas — Verificacion_TUPA_v10_4.xlsx + textos del tesista

Estado: **DRY-RUN (no se escribió ningún dominio)**. Solo respuestas `utter_*`; NLU, ejemplos de entrenamiento e intenciones no se tocan; no se reentrena ni se evalúa.

- Respuestas que cambian: **1** de 55 (idénticas en `domain.yml` y `domain_v3.yml`).
- Con marcador [Verificar…]: **1 → 0**. Marcador quitado en 1: constancia_domiciliaria.
- Siguen con marcador (0): .
- No se tocan (bloque E, `conservar`): .

## Avisos

- utter_saludo: no contiene «de la MPSR»
- utter_fuera_de_alcance: no contiene «de la MPSR»
- utter_hablar_con_persona: no contiene «de la MPSR»
- utter_ayuda_chatbot: no contiene «de la MPSR»

## Diff por respuesta

### `utter_constancia_domiciliaria` — manual C5c

- **Antes:** La constancia domiciliaria se tramita en la municipalidad. Necesitas una solicitud dirigida al Alcalde y tu DNI. Consulta en ventanilla si piden algún otro documento. [Verificar costo y plazo]
- **Después:** La constancia domiciliaria se tramita en la municipalidad. Necesitas una solicitud dirigida al Alcalde y tu DNI. El costo es de aproximadamente S/ 10 a S/ 35 y se entrega en 1 a 3 días. Consulta en ventanilla el monto exacto y si piden algún otro documento.

