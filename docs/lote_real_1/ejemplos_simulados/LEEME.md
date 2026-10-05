# Ejemplos simulados del lote 1

**Estado: Simulado.** Nada de esta carpeta es evidencia ni un resultado del lote 1.

| Archivo | Qué es |
|---|---|
| `Lote1_Transcripcion_SIMULADO_v2.xlsx` | Libro de transcripción del lote 1 rellenado con datos **falsos** (título «SIMULADO»; Observaciones «Dato sintético de prueba»; frases de prueba) |

Para qué sirve: probar que `scripts/ingest_real_lote.py` (opción `--libro`), `scripts/conciliar_seguimiento.py` y `scripts/analizar_piloto.py` **rechazan** los libros simulados
(`tests/smoke_lote_real.py`). No se usa para entrenar, validar ni evaluar nada; sus frases no entran al corpus.

Cómo se detectan los datos simulados (`scripts/deteccion_simulado.py`): se rechaza todo libro con «SIMULADO», «SINTÉTICO», «SINTETICO» o «DEMO» (sin distinguir mayúsculas ni tildes)
en el nombre o el título de una hoja, en cualquier celda de texto de Participantes (o Sesiones, Blancos, Respuestas) o en una columna Observaciones. Un libro que solo tenía la marca en
Observaciones, con el título limpio, también se rechaza. Las frases de las personas (columna `text`) no se escanean, para que una frase real con «demo» o «demora» no se rechace;
solo se revisa el marcador «[SIMULACIÓN …]» al inicio. Con `--permitir-simulado` los scripts los leen **solo para probar el código** y escriben únicamente en una carpeta temporal.
