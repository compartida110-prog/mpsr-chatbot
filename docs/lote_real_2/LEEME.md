# Lote 2 — prueba independiente de G3 (PLANIFICADO, sin datos)

**Estado: planificado. No hay datos del lote 2.** El procedimiento está cerrado en `logs/avance/propuesta_lote2.md` y se declara en el protocolo V1.6 (sección 5.8) antes de recoger nada.

| Archivo | Qué es |
|---|---|
| `situaciones_lote2_v1.csv` | Catálogo de situaciones: **las mismas 56 situaciones y formularios A–E del lote 1** (`situaciones_lote1_v1.csv`), sin los complementos F y G. Debe coincidir con `Lote2_Formularios_lenguaje_real_v1` del tesista; si ese documento difiere, se corrige este CSV **antes** de recoger datos. |
| `privado/` | Libro de transcripción lleno, seguimiento y consentimientos. No se versiona (solo su `LEEME.md`). |
| `log_cambios_lote2.csv`, `log_exclusion_entrenamiento_lote2.csv` | Se crean al preparar la partición (`scripts/split_lote2.py`): descartes por duplicado exacto y copias de entrenamiento idénticas a una frase del lote 2, con motivo y fecha (solo identificadores). |

Participantes **P33–P57** (25; mínimo 20), solo adultos que viven en Juliaca y que **no** respondieron los lotes 1, 1b ni 1c. Frases con ids `Q0001…` (no chocan con los `R…` del lote 1).

Scripts: `ingest_real_lote.py --lote 2`, `split_lote2.py`, y el tablero `estado_compuertas.py` (G3 registra «Medida en lote 2» aparte de la medición del lote 1). Todo se probó solo con datos FALSOS (`tests/smoke_lote2.py`).
