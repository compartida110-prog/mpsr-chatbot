# Corpus y particiones históricas

| Archivo | Qué es | Frases | Partición (train/val/test) |
|---|---|---|---|
| `corpus_metadata_v1_324.csv`, `dataset_split_v1_324.csv` | Corpus v1 (2 grupos por intención) | 324 | 162/81/81 |
| `corpus_metadata_v2_648.csv`, `dataset_split_v2_648.csv` | Corpus v2 (4 grupos por intención); **es la partición «V1.1» del protocolo** | 648 | 486/81/81 = 75/12.5/12.5 % |

El corpus **vigente** (v3, 708 frases = v2 + `corpus/ampliacion_v3.csv`) está en `corpus/corpus_metadata.csv` y `corpus/dataset_split.csv`
(546/81/81; validación y test idénticos a los de v2). La partición V1.1 no es 70/15/15: con 4 grupos por intención, 3 van a entrenamiento y el cuarto
alterna entre validación y prueba (ver `scripts/expand_corpus.py`).
