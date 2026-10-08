# Respuestas que se mantienen con marcador [Verificar…] (bloque E, 2026-10-08)

No se cambia su texto. Fuentes: «Hoja_Consulta_Municipalidad_v4.xlsx» (llamada a la secretaria el 08/10/2026), hoja «Canales oficiales», hoja «Recojo de basura» y `Verificacion_TUPA_v10_2.xlsx`. Lo que sigue es lo que dijo cada fuente, sin interpretar.

## libro_reclamaciones — respuesta ambigua
- **Texto actual:** «El libro de reclamaciones está disponible en la Plataforma de Atención; también puede existir una versión virtual. [Verificar si la MPSR cuenta con libro de reclamaciones virtual].»
- **Pregunta hecha:** ¿dónde está el libro físico?, ¿existe versión virtual?, ¿cuál es el enlace?
- **Secretaria (llamada):** «Si.» (una sola palabra a una pregunta de varias partes: no dice dónde está, ni si hay versión virtual, ni enlace).
- **TUPA v10_2 (fila 36):** propone «Corregir» a «cuenta con un Libro de Reclamaciones virtual, al que puedes entrar desde su portal institucional o desde su página en gob.pe»; **no está confirmada por el tesista**.
- **Estado:** pendiente. Las respuestas de `presentar_reclamo` y `queja_atencion` ya no mencionan el libro.
- **Nombre:** conserva «Plataforma de Atención» (sin «al Ciudadano») porque el texto no se toca.

## reporte_alumbrado_publico — la fuente contradice el texto
- **Texto actual:** «…comunicarte con el área de Servicios Públicos de la MPSR, indicando la ubicación exacta del poste o farola. [Verificar área responsable y procedimiento…].»
- **Secretaria:** «Creo que eso debe corresponderle a electro puno» (expresó duda: «creo»).
- **Estado:** pendiente. Hay que confirmar con la municipalidad o con Electro Puno quién recibe los reportes de alumbrado público.

## poda_arboles — la fuente contradice el texto
- **Texto actual:** «La poda de árboles públicos se solicita ante el área de Servicios Públicos de la MPSR, indicando la ubicación exacta del árbol. [Verificar…].»
- **Secretaria:** «No sabria decirte excatamente, pero por normativa esta prohibido la poda de árboles de lugares públicos.»
- **Estado:** pendiente. Hay que verificar la normativa y si existe algún procedimiento de autorización antes de mantener o cambiar el texto.

## limpieza_via_publica — nombre del área dudoso
- **Texto actual:** «…comunicarte con el área de limpieza pública de la MPSR, indicando la calle y cuadra exacta. [Verificar…].»
- **Secretaria:** «Creo que esto le compete a Gerencia de Servicios Públicos y Medio Ambiente.»
- **Croquis de recojo de basura (carpeta de Drive):** se firma como «Gerencia de Gestión Ambiental y Residuos Sólidos».
- **Estado:** pendiente. Los dos nombres no coinciden; falta confirmar cuál se usa en las respuestas.

## constancia_domiciliaria — marcador solo para costo y plazo
- **Secretaria:** se tramita en la municipalidad; necesita solicitud dirigida al Alcalde (además de DNI y recibo, según el texto del tesista).
- **TUPA v10_2 (fila 18):** «No figura en la fuente» (el TUPA no menciona expresamente una constancia domiciliaria): costo y plazo no se pueden tomar de ahí.
- **Estado:** la respuesta conserva un marcador «[Verificar costo y plazo con el TUPA vigente]» (redacción de Claude).

## Otros datos de la hoja de consulta, sin usar en respuestas
- WhatsApp contact center 932049915 (la secretaria dijo que no suele ser efectivo): no se usa.
- Subgerencia de Gestión de Residuos Sólidos 962341074 (solo en un listado externo): no se usa.
- YouTube institucional (inactivo hace 7 años): no se usa.
- Libro de reclamaciones, alumbrado, poda y limpieza: ver arriba.

---

# Actualización 2026-10-08 (v10_4): textos del tesista para las cuatro respuestas pendientes — DRY-RUN, aún NO aplicados

Estado: el tesista dio textos exactos y pidió quitar el marcador [Verificar] de estas cuatro. Se aplican solo después de su «aplica» (informe: `logs/avance/aplicar_respuestas_dryrun2.md`). Fuentes según el tesista; Claude no verificó por su cuenta los datos de Electro Puno.

| Respuesta | Qué dice el texto nuevo | Fuente declarada |
|---|---|---|
| `reporte_alumbrado_publico` | Lo atiende Electro Puno: Central de Reclamos (051) 366066, portal de reclamos, central (051) 352552 y su correo; riesgo eléctrico: llamar de inmediato | Datos de Electro Puno entregados por el tesista; la secretaria había dicho «creo que debe corresponderle a Electro Puno» (llamada 08/10/2026) |
| `limpieza_via_publica` | A cargo de la Gerencia de Gestión Ambiental y Residuos Sólidos; solicitud en Mesa de Partes (calle y cuadra) o en la sede, Jr. Jáuregui N.° 321 | Croquis de recojo de basura (firma de esa gerencia) y dirección del portal oficial; la secretaria había dicho «Gerencia de Servicios Públicos y Medio Ambiente» (con «creo») |
| `poda_arboles` | Se evalúa en la Gerencia de Gestión Ambiental y Residuos Sólidos; Mesa de Partes o sede; si toca cables, avisar a Electro Puno (051) 366066 | Decisión del tesista; la secretaria había dicho que la poda en lugares públicos está prohibida por normativa (sin precisar): el texto nuevo no menciona esa prohibición |
| `libro_reclamaciones` | Libro en la sede (Jr. Jáuregui N.° 321, Plaza de Armas); existe versión digital; para el acceso, llamar a la central (051) 321201 | Dirección y central del portal oficial; la secretaria solo respondió «Si.»; la v10_4 propone una redacción propia que el texto manual reemplaza |

Condiciones que cumple el texto: sin nombres ni celulares de funcionarios, sin el correo mpsrj@munisanroman.gob.pe y sin «MPSR».

Sigue con marcador solo `constancia_domiciliaria` ([Verificar costo y plazo]): costo y plazo sin fuente; el requisito «recibo de servicio» tampoco está confirmado, aunque el texto vigente lo menciona (queda como observación; no se cambió el texto).

**Aplicado el 2026-10-08** (informe `logs/avance/aplicar_respuestas_aplicado2.md`, TUPA v10_4): las cuatro respuestas quedaron con los textos del tesista y `constancia_domiciliaria` con su texto nuevo y el marcador [Verificar costo y plazo]. Es la única respuesta con marcador.

---

## Actualización — `constancia_domiciliaria` sin marcador (DRY-RUN 3, aún NO aplicado)

- **Texto propuesto por el tesista:** se tramita en la municipalidad, con solicitud dirigida al Alcalde y DNI; costo aproximado de S/ 10 a S/ 35; entrega en 1 a 3 días; consultar en ventanilla el monto exacto y si piden otro documento. Sin marcador [Verificar]. Informe: `logs/avance/aplicar_respuestas_dryrun3.md`.
- **Origen del costo (S/ 10–35) y del plazo (1–3 días):** lo indicado por el tesista el 08/10/2026. **No figuran en el TUPA publicado** (la fila 18 de la hoja de verificación dice «No figura en la fuente»). Son datos sin fuente documental.
- **Requisito «recibo de servicio»:** sigue **sin confirmar**; el texto nuevo ya no lo menciona y remite a la ventanilla para otros documentos.
