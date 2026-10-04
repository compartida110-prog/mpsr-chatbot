# Instrucciones para Claude Code — Ajustes al registro y al formulario del piloto (v1)

Mismas reglas de siempre: nada simulado como real, no editar la historia, no inventar archivos.

## 1. Reemplazar por la v2

Copia a `docs/piloto/`: `Registro_Sesiones_Piloto_v2.xlsx` y `Sesion_Asistida_Formulario_v2` (Word y PDF). Mueve los `_v1` a `docs/piloto/historico/`, sin borrarlos.

Motivo: en la hoja Resumen, los textos de meta usaban `TEXT` con formato decimal, que depende del idioma de Excel. En el Excel del tesista salía "Meta ≥ 04" y "Mínimo 001" en vez de 4 y 0,7. La v2 los concatena directamente. **Solo cambian esos dos textos y las referencias de nombre v1 → v2. Los encabezados no cambian.**

## 2. Referencias de nombre

Actualiza `v1 → v2` en `scripts/`, `tests/`, README y mensajes (rutas por defecto y textos). **No cambies lógica.**

## 3. Fila del encabezado

La demo tiene el encabezado en la fila 2, porque se borró la fila de leyenda. El registro real puede sufrir lo mismo cuando el tesista lo edite en Excel.

- `analizar_piloto.py` debe localizar la fila de encabezados buscando `Código de sesión` en las **primeras 10 filas**, no en la fila 3 fija. Confirma si ya lo hace.
- Agrega a la prueba de humo: una copia de la plantilla con el encabezado en la fila 3 y otra con el encabezado en la fila 2 deben dar **el mismo resultado**. Si no se encuentra el encabezado, el script aborta con un mensaje claro.

## 4. Uso de la demo sintética

- Se queda en `docs/piloto/ejemplos_simulados/`. Agrega a su `LEEME` dos avisos:
  - Las consultas de la demo son el texto de la tarjeta con el prefijo "[SIMULACIÓN…]". **No sirven para evaluar el modelo**, porque la predicción sería trivial. El análisis con `--permitir-simulado` solo prueba el código.
  - Los textos de meta del Resumen de la demo muestran "04" y "001" por el formato de idioma que corrige la v2. No se edita la demo.
- No uses sus cifras en ningún reporte como resultado del asistente. Si se muestra, va rotulada **Simulado**.

## 5. Verificar y subir

- Repite la prueba de humo con la plantilla v2 y el caso nuevo del paso 3.
- Ejecuta `verificar_referencias.py`. Resultado esperado: cero discrepancias.
- Commit y push, sin modelos ni datos personales. En el mensaje final entrega el resultado de ambas pruebas.
