"""Utilidades compartidas por los scripts del Protocolo Experimental V1.1.

Centraliza rutas, normalización de texto (P06), métricas (P11) y el registro
de cada corrida en logs/ para cumplir la pregunta de control (sección 3.2):
corpus y versión, partición, código, configuración, semilla, predicciones e ID.
"""
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "corpus_metadata.csv"
AUDIT = ROOT / "corpus" / "corpus_audit.csv"
SPLIT = ROOT / "corpus" / "dataset_split.csv"
JERGA = ROOT / "configs" / "jerga_local.csv"
CONFIGS = ROOT / "configs"
DATA = ROOT / "data"
MODELS = ROOT / "models"
LOGS = ROOT / "logs"

CORPUS_COLUMNS = ["utterance_id", "text", "intent", "category", "source", "base_phrase_id", "split"]
SPLITS = ("train", "validation", "test")
REPETITION_SEEDS = [10, 20, 30, 40, 50]  # P10
BASE_SEED = 42  # P05, P07, P08
F1_TARGET = 0.85  # P11


# --------------------------------------------------------------------------- corpus

def load_corpus(path=CORPUS):
    """Lee el corpus como texto (sin convertir vacíos en NaN) y valida columnas."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    missing = [c for c in CORPUS_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: faltan columnas en {path}: {missing}")
    if df.empty:
        sys.exit(f"ERROR: {path} no tiene utterances. Completa el corpus (P02) antes de continuar.")
    for col in ("utterance_id", "text", "intent", "base_phrase_id"):
        empty = df[col].str.strip() == ""
        if empty.any():
            ids = df.loc[empty, "utterance_id"].tolist()[:10]
            sys.exit(f"ERROR: columna '{col}' vacía en {empty.sum()} filas (ej. {ids}).")
    dup_ids = df["utterance_id"][df["utterance_id"].duplicated()].unique()
    if len(dup_ids):
        sys.exit(f"ERROR: utterance_id repetidos: {list(dup_ids)[:10]}")
    return df


def load_split_corpus(path=CORPUS):
    """Corpus con la partición ya asignada (P05). Falla si falta la partición."""
    df = load_corpus(path)
    bad = ~df["split"].isin(SPLITS)
    if bad.any():
        sys.exit("ERROR: hay utterances sin partición válida. Ejecuta primero scripts/split_corpus.py (P05).")
    return df


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- P06

def load_jerga(path=JERGA):
    """Diccionario jerga local -> forma estándar (configs/jerga_local.csv)."""
    if not Path(path).exists():
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False, comment="#")
    return {strip_accents(k.lower().strip()): v.lower().strip()
            for k, v in zip(df["jerga"], df["estandar"]) if k.strip()}


def strip_accents(text):
    # Conserva la ñ: solo elimina tildes y diéresis.
    text = text.replace("ñ", "\0").replace("Ñ", "\1")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return text.replace("\0", "ñ").replace("\1", "Ñ")


_TOKEN_RE = re.compile(r"[a-z0-9ñ]+")


def normalize(text, jerga=None):
    """Minúsculas, sin tildes, sin signos y con jerga local reemplazada (P06)."""
    tokens = _TOKEN_RE.findall(strip_accents(text.lower()))
    if jerga:
        tokens = [jerga.get(t, t) for t in tokens]
    return " ".join(tokens)


# --------------------------------------------------------------------------- P11

def classification_metrics(y_true, y_pred):
    kw = dict(average="macro", zero_division=0)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, **kw),
        "recall_macro": recall_score(y_true, y_pred, **kw),
        "f1_macro": f1_score(y_true, y_pred, **kw),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
    }


# --------------------------------------------------------------------------- P15

def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "scripts", "configs"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return out + ("-modificado" if dirty else "")
    except Exception:
        return "desconocido"


def save_run(exp_id, eval_split, df_eval, y_pred, config, seed, corpus_path=CORPUS, extra=None):
    """Guarda predicciones, métricas y matriz de confusión de una corrida en logs/<exp_id>/."""
    out = LOGS / exp_id
    out.mkdir(parents=True, exist_ok=True)
    y_true = df_eval["intent"].tolist()
    metrics = classification_metrics(y_true, y_pred)

    pd.DataFrame({
        "utterance_id": df_eval["utterance_id"].values,
        "text": df_eval["text"].values,
        "intent": y_true,
        "predicted": list(y_pred),
        "correct": [t == p for t, p in zip(y_true, y_pred)],
    }).to_csv(out / f"predictions_{eval_split}.csv", index=False, encoding="utf-8")

    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(
        out / f"confusion_matrix_{eval_split}.csv", encoding="utf-8")

    record = {
        "experiment_id": exp_id,
        "evaluated_on": eval_split,
        "seed": seed,
        "metrics": metrics,
        "n_evaluated": len(y_true),
        "config": config,
        "corpus_file": str(Path(corpus_path).resolve().relative_to(ROOT)) if _inside_root(corpus_path) else str(corpus_path),
        "corpus_sha256": file_sha256(corpus_path),
        "git_commit": git_commit(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
    }
    if extra:
        record.update(extra)
    with open(out / f"metrics_{eval_split}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return metrics


def _inside_root(path):
    try:
        Path(path).resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def append_summary(path, row):
    """Agrega una fila a un CSV resumen (crea el encabezado si no existe)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


def print_metrics(title, m):
    print(f"  {title:<34} " + "  ".join(f"{k}={v:.4f}" for k, v in m.items()))


def aggregate(rows, keys=("accuracy", "precision_macro", "recall_macro", "f1_macro", "balanced_accuracy")):
    """Media y desviación estándar de las repeticiones (P10)."""
    return {k: (float(np.mean([r[k] for r in rows])), float(np.std([r[k] for r in rows], ddof=1)) if len(rows) > 1 else 0.0)
            for k in keys}
