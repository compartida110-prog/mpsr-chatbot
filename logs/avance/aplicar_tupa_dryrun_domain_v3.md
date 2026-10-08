# Dry-run de aplicar_tupa.py — Verificacion_TUPA_v10_1.xlsx

Generado el 2026-10-07 20:12. **No se escribió domain.yml.** Entran 26 de 44 filas (Resultado = Corregir, texto corregido, confirmada por el tesista, sin alerta).

No entran: Pendiente: 9; No figura en la fuente: 7; Corregir sin confirmar: 2.

Hoja Resumen guardada: Confirmadas por el tesista = 26; Prioridad Alta pendientes = 0; Filas con alerta = 0; Corregir o Coincide sin confirmar por el tesista = 2. (Si difiere del recuento, la hoja se guardó antes de la última edición: ábrela y guárdala en Excel.)

| # | Intención | Prioridad | Tenía [Verificar] | Largo actual → nuevo | Avisos |
|---|---|---|---|---|---|
| 1 | `licencia_funcionamiento_requisitos` | Alta | no | 247 → 412 | — |
| 2 | `licencia_funcionamiento_costo` | Alta | sí | 215 → 128 | — |
| 3 | `licencia_funcionamiento_plazo` | Alta | sí | 182 → 251 | — |
| 4 | `licencia_edificacion_requisitos` | Alta | sí | 243 → 216 | — |
| 5 | `licencia_edificacion_costo` | Alta | sí | 162 → 196 | — |
| 6 | `renovacion_licencia` | Alta | no | 212 → 135 | — |
| 11 | `fraccionamiento_deuda` | Alta | no | 270 → 295 | — |
| 12 | `constancia_no_adeudo` | Alta | no | 243 → 223 | — |
| 13 | `requisitos_mesa_partes` | Alta | no | 217 → 197 | — |
| 14 | `estado_tramite` | Media | no | 188 → 166 | — |
| 15 | `horario_mesa_partes` | Media | sí | 123 → 185 | — |
| 16 | `copia_documento` | Alta | no | 243 → 295 | — |
| 17 | `certificado_posesion` | Alta | no | 216 → 362 | — |
| 19 | `certificado_defensa_civil` | Alta | no | 236 → 235 | — |
| 20 | `inspeccion_tecnica` | Alta | no | 225 → 267 | — |
| 21 | `requisitos_defensa_civil` | Alta | no | 258 → 334 | — |
| 24 | `partida_nacimiento` | Alta | no | 204 → 143 | — |
| 25 | `partida_matrimonio` | Alta | no | 226 → 143 | — |
| 26 | `partida_defuncion` | Alta | no | 222 → 297 | — |
| 27 | `rectificacion_partida` | Alta | no | 240 → 309 | — |
| 28 | `requisitos_matrimonio_civil` | Alta | no | 185 → 478 | — |
| 39 | `horario_atencion_general` | Media | sí | 126 → 204 | — |
| 40 | `ubicacion_oficinas` | Media | sí | 116 → 143 | — |
| 41 | `requisitos_generales` | Alta | no | 145 → 108 | — |
| 42 | `costos_generales` | Alta | no | 149 → 165 | — |
| 43 | `contacto_telefonico` | Media | sí | 126 → 82 | — |

## Texto actual y nuevo de cada fila

### 1. `utter_licencia_funcionamiento_requisitos`

- **Actual:** Para la licencia de funcionamiento necesitas: copia de tu DNI, el certificado de compatibilidad de uso, el certificado de Defensa Civil (ITSE) y el recibo de pago de la tasa correspondiente. [Verificar lista exacta con el TUPA vigente de la MPSR].
- **Nuevo:** El TUPA pide una solicitud de licencia con carácter de declaración jurada y una declaración de cumplimiento de las condiciones de seguridad. Para riesgo bajo o medio, la ITSE se realiza después de otorgar la licencia; para riesgo alto o muy alto, se realiza antes y se adjuntan documentos técnicos, como croquis, planos y plan de seguridad. La municipalidad determina el nivel de riesgo y los requisitos exactos.

### 2. `utter_licencia_funcionamiento_costo`

- **Actual:** El costo de la licencia de funcionamiento depende del giro del negocio y del área del local. Puedes consultar el monto exacto en el TUPA de la MPSR o acercarte a la Plataforma de Atención. [Verificar monto vigente].
- **Nuevo:** El derecho de trámite depende del nivel de riesgo: S/ 169,80 (bajo), S/ 175,70 (medio), S/ 525,60 (alto) y S/ 893,70 (muy alto).

### 3. `utter_licencia_funcionamiento_plazo`

- **Actual:** El trámite de licencia de funcionamiento suele atenderse en un plazo de 10 a 15 días hábiles, según la complejidad del giro del negocio. [Verificar plazo exacto con el TUPA vigente].
- **Nuevo:** Para riesgo bajo o medio, la licencia se emite en 2 días hábiles y la ITSE posterior se atiende hasta en 9 días hábiles. Para riesgo alto o muy alto, la ITSE previa puede tomar hasta 7 días y la licencia se emite en 1 día más: 8 días hábiles en total.

### 4. `utter_licencia_edificacion_requisitos`

- **Actual:** Para la licencia de edificación necesitas: título de propiedad o documento que acredite posesión, planos de arquitectura firmados por un profesional colegiado, y el pago de la tasa correspondiente. [Verificar lista exacta con el TUPA vigente].
- **Nuevo:** Los requisitos de licencia de edificación dependen de la modalidad (A, B, C o D), el tipo de obra y sus características. Dime qué proyecto vas a realizar, su uso y área para orientarte sobre la ficha que corresponde.

### 5. `utter_licencia_edificacion_costo`

- **Actual:** El costo de la licencia de edificación varía según el tipo y tamaño de la obra. Puedes consultar el monto exacto en el TUPA de la MPSR. [Verificar monto vigente].
- **Nuevo:** El derecho de trámite de una licencia de edificación depende del procedimiento y la modalidad aplicable a la obra. Dime qué proyecto vas a realizar para identificar la ficha y su monto en el TUPA.

### 6. `utter_renovacion_licencia`

- **Actual:** Para renovar tu licencia de funcionamiento debes presentar tu licencia anterior, DNI vigente y el pago de la tasa de renovación. El trámite se realiza en la Plataforma de Atención. [Verificar requisitos exactos].
- **Nuevo:** La licencia de funcionamiento tiene vigencia indeterminada y no requiere renovación. El certificado ITSE sí debe renovarse cada 2 años.

### 11. `utter_fraccionamiento_deuda`

- **Actual:** Para fraccionar una deuda tributaria debes presentar una solicitud en mesa de partes, adjuntando tu DNI y el detalle de la deuda. La municipalidad evaluará una cuota inicial y un cronograma de pagos. [Verificar requisitos y procedimiento con el TUPA vigente de la MPSR].
- **Nuevo:** El fraccionamiento de deuda tributaria es gratuito y de aprobación automática si presentas la documentación completa. Se requiere una solicitud que indique la deuda; si actúa un representante, un poder específico; y una declaración jurada de compromiso de pago con firma legalizada ante notario.

### 12. `utter_constancia_no_adeudo`

- **Actual:** La constancia de no adeudo se tramita presentando tu DNI en la Plataforma de Atención; se emite una vez verificado que no tienes deudas pendientes por impuesto predial o arbitrios. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** La constancia de no adeudo es un servicio exclusivo. Presenta una solicitud firmada por el titular de la propiedad o su representante legal e indica el número de pago. Cuesta S/ 18,40 y el plazo máximo es de 5 días hábiles.

### 13. `utter_requisitos_mesa_partes`

- **Actual:** Para presentar un documento en mesa de partes necesitas tu solicitud (puede ser un formato simple), copia de tu DNI, y los anexos que sustenten tu pedido. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** Los requisitos para presentar un documento dependen del procedimiento al que va dirigido. El TUPA no establece una lista única para todos los escritos. Dime qué trámite necesitas y reviso su ficha.

### 14. `utter_estado_tramite`

- **Actual:** Puedes consultar el estado de tu trámite presentando tu número de expediente en mesa de partes o en la Plataforma de Atención. [Verificar canal de consulta con el TUPA vigente de la MPSR].
- **Nuevo:** El portal oficial de la MPSR en gob.pe tiene un enlace directo llamado «Seguimiento de trámites». Lo encuentras en la sección de enlaces directos de la municipalidad.

### 15. `utter_horario_mesa_partes`

- **Actual:** Mesa de partes atiende de lunes a viernes en el horario de oficina de la municipalidad. [Verificar horario exacto vigente].
- **Nuevo:** La sede central atiende de lunes a viernes, de 8:00 a. m. a 1:00 p. m. y de 2:00 p. m. a 4:00 p. m. Confirma con la municipalidad si la Mesa de Partes Virtual tiene un horario distinto.

### 16. `utter_copia_documento`

- **Actual:** Para obtener una copia certificada de un documento presentado anteriormente, debes solicitarlo en mesa de partes indicando el número de expediente, y abonar la tasa correspondiente. [Verificar requisitos y tasa con el TUPA vigente de la MPSR].
- **Nuevo:** El servicio permite obtener copias certificadas de documentos que están en expedientes o archivos municipales. Presenta una solicitud con la información del documento e indica el número y la fecha del comprobante de pago. El costo varía por tamaño de hoja y el plazo es de hasta 15 días hábiles.

### 17. `utter_certificado_posesion`

- **Actual:** El certificado de posesión se tramita presentando una declaración jurada, croquis del predio y documentos que acrediten la posesión pacífica del terreno. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** La constancia de posesión se emite para acceder a agua, desagüe y electricidad. El TUPA pide solicitud, planos de ubicación/perimétrico/localización que cubran un radio de 550 metros, declaración jurada notarial de posesión, documento de propiedad, verificación del predio y visto bueno de la empresa prestadora. Cuesta S/ 85,80 y el plazo es de 10 días hábiles.

### 19. `utter_certificado_defensa_civil`

- **Actual:** El certificado de Defensa Civil (ITSE) se tramita presentando el plano de distribución del local, el certificado de medidas de seguridad y el pago de la tasa correspondiente. [Verificar requisitos y tasa con el TUPA vigente de la MPSR].
- **Nuevo:** En el TUPA el trámite se denomina ITSE (Inspección Técnica de Seguridad en Edificaciones). El certificado tiene vigencia de 2 años; el procedimiento, los requisitos, el costo y el plazo dependen del nivel de riesgo del establecimiento.

### 20. `utter_inspeccion_tecnica`

- **Actual:** Para solicitar una inspección técnica de seguridad (ITSE) debes presentar tu solicitud en mesa de partes; un inspector de Defensa Civil coordinará una visita al local. [Verificar procedimiento con el TUPA vigente de la MPSR].
- **Nuevo:** La ITSE se solicita con el formato correspondiente y los documentos exigidos para el nivel de riesgo del establecimiento. Para riesgo bajo o medio es posterior al inicio de actividades; para riesgo alto o muy alto es previa. El costo y el plazo varían según la ficha.

### 21. `utter_requisitos_defensa_civil`

- **Actual:** Los requisitos de Defensa Civil incluyen: plano de distribución, certificado de medición eléctrica, extintores vigentes y señalización de seguridad, entre otros, según el tipo de establecimiento. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** Los requisitos de ITSE dependen del nivel de riesgo. Para riesgo bajo o medio, el TUPA pide solicitud y declaración jurada de cumplimiento de condiciones de seguridad. Para riesgo alto o muy alto, también exige documentos técnicos, como croquis, planos, certificado de puesta a tierra, plan de seguridad y protocolos de mantenimiento.

### 24. `utter_partida_nacimiento`

- **Actual:** Puedes solicitar una copia de tu partida de nacimiento en la oficina de Registro Civil, presentando tu DNI y abonando la tasa correspondiente. [Verificar requisitos y tasa con el TUPA vigente de la MPSR].
- **Nuevo:** Para obtener una copia de una partida de nacimiento, paga el derecho de expedición de S/ 8,50. El plazo de atención del TUPA es de 1 día hábil.

### 25. `utter_partida_matrimonio`

- **Actual:** La partida de matrimonio se solicita en la oficina de Registro Civil, indicando los datos del matrimonio (fecha, nombres de los contrayentes) y presentando tu DNI. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** Para obtener una copia de una partida de matrimonio, paga el derecho de expedición de S/ 8,50. El plazo de atención del TUPA es de 1 día hábil.

### 26. `utter_partida_defuncion`

- **Actual:** Para inscribir o solicitar una partida de defunción debes presentar el certificado médico de defunción y el DNI del fallecido, en la oficina de Registro Civil. [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** Inscribir una defunción es distinto de pedir una copia del acta. La inscripción es gratuita, se atiende en 1 día hábil y los requisitos dependen del caso (defunción ordinaria, muerte violenta, mandato judicial o muerte presunta). La copia de una partida cuesta S/ 8,50 y se atiende en 1 día hábil.

### 27. `utter_rectificacion_partida`

- **Actual:** Para rectificar un dato en una partida debes presentar una solicitud en Registro Civil junto con los documentos que sustenten la corrección (DNI, partida original, entre otros). [Verificar requisitos exactos con el TUPA vigente de la MPSR].
- **Nuevo:** El TUPA contempla la rectificación administrativa, judicial y notarial de partidas. La ficha pide el oficio judicial o parte notarial, la sentencia certificada o escritura pública correspondiente y el pago. El derecho es S/ 34,80 y el plazo de atención es de 5 días hábiles. La vía aplicable depende del caso.

### 28. `utter_requisitos_matrimonio_civil`

- **Actual:** Para matrimonio civil se requiere: DNI de ambos contrayentes, certificados de nacimiento actualizados, y en algunos casos certificado médico prenupcial. [Verificar requisitos vigentes].
- **Nuevo:** Para mayores de edad, el TUPA pide pliego matrimonial, partidas de nacimiento, certificados de domicilio, documentos de identidad de la pareja y testigos, pago por publicación del edicto y pago del trámite. Hay requisitos adicionales para divorciados, viudos o extranjeros. El plazo es de 15 días hábiles. La tarifa es S/ 125,30 en instalaciones municipales de lunes a viernes, S/ 220,00 en esas instalaciones sábados, domingos y feriados, o S/ 370,00 fuera de la municipalidad.

### 39. `utter_horario_atencion_general`

- **Actual:** La Municipalidad Provincial de San Román atiende de lunes a viernes en horario de oficina. [Verificar horario exacto vigente].
- **Nuevo:** La sede central atiende de lunes a viernes, de 8:00 a. m. a 1:00 p. m. y de 2:00 p. m. a 4:00 p. m. Las agencias municipales pueden tener un horario distinto; confirma el horario de la sede que visitarás.

### 40. `utter_ubicacion_oficinas`

- **Actual:** La Municipalidad Provincial de San Román se encuentra en la Plaza de Armas de Juliaca. [Verificar dirección exacta].
- **Nuevo:** La sede central de la Municipalidad Provincial de San Román está en el Jr. Jáuregui N.° 321, Centro Cívico, referencia Plaza de Armas, Juliaca.

### 41. `utter_requisitos_generales`

- **Actual:** Para la mayoría de trámites municipales necesitarás presentar tu DNI vigente; algunos trámites piden además documentos adicionales según el caso.
- **Nuevo:** Los requisitos dependen del trámite. Dime cuál necesitas y reviso los documentos que pide su ficha del TUPA.

### 42. `utter_costos_generales`

- **Actual:** Los costos de los trámites municipales están establecidos en el TUPA (Texto Único de Procedimientos Administrativos), disponible en la municipalidad.
- **Nuevo:** Los costos dependen de cada trámite: algunos son gratuitos y otros tienen un derecho específico indicado en el TUPA. Dime cuál necesitas y reviso el monto aplicable.

### 43. `utter_contacto_telefonico`

- **Actual:** Puedes comunicarte con la Municipalidad Provincial de San Román a través de su central telefónica. [Verificar número vigente].
- **Nuevo:** La central telefónica de la Municipalidad Provincial de San Román es (051) 321201.

