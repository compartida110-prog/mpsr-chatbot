#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P07 del Protocolo V1.1: Experimento baseline (TF-IDF + SVM) sobre el
Corpus MPSR-Bot real (324 utterances, 54 intenciones, 9 categorías).
EJECUCIÓN REAL (no simulada) -- los resultados de este script son
el desempeño genuino del baseline sobre el corpus de arranque actual.
"""
import csv, json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # raíz del repositorio
OUT = ROOT / "logs" / "EXP_BASELINE_SVM_S42_2026"
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, balanced_accuracy_score, confusion_matrix,
                              classification_report)

SEED = 42
np.random.seed(SEED)

rows = list(csv.DictReader(open(ROOT / "corpus" / "corpus_metadata.csv", encoding="utf-8")))

train = [r for r in rows if r["split"] == "train"]
val   = [r for r in rows if r["split"] == "validation"]
test  = [r for r in rows if r["split"] == "test"]

print(f"train={len(train)}  validation={len(val)}  test={len(test)}")

X_train_text = [r["text"] for r in train]
y_train = [r["intent"] for r in train]
X_val_text = [r["text"] for r in val]
y_val = [r["intent"] for r in val]
X_test_text = [r["text"] for r in test]
y_test = [r["intent"] for r in test]

# ---------------------------------------------------------------------------
# Vectorizador TF-IDF (fijado en configs/baseline_config.json: max_features=5000,
# ngram_range=(1,2)) -- se ajusta SOLO con el train, conforme a la regla 3.1.
# ---------------------------------------------------------------------------
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train = vectorizer.fit_transform(X_train_text)
X_val = vectorizer.transform(X_val_text)
X_test = vectorizer.transform(X_test_text)

# ---------------------------------------------------------------------------
# Grilla fijada en el protocolo: SVM kernel lineal, C in {0.1, 1, 10}.
# Selección por mejor F1-macro en VALIDACIÓN (nunca en test).
# ---------------------------------------------------------------------------
results_grid = []
best = {"C": None, "f1_val": -1, "model": None}
for C in [0.1, 1, 10]:
    clf = SVC(kernel="linear", C=C, random_state=SEED)
    clf.fit(X_train, y_train)
    pred_val = clf.predict(X_val)
    f1_val = f1_score(y_val, pred_val, average="macro", zero_division=0)
    results_grid.append({"C": C, "f1_macro_validation": round(f1_val, 4)})
    print(f"SVM C={C}: F1-macro (validation) = {f1_val:.4f}")
    if f1_val > best["f1_val"]:
        best = {"C": C, "f1_val": f1_val, "model": clf}

print(f"\n>>> Mejor C según validación: {best['C']} (F1-macro val={best['f1_val']:.4f})")

# Alternativa: regresión logística (C=1.0, max_iter=1000) -- valor fijo, sin grilla
logreg = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
logreg.fit(X_train, y_train)
pred_val_logreg = logreg.predict(X_val)
f1_val_logreg = f1_score(y_val, pred_val_logreg, average="macro", zero_division=0)
print(f"Regresión logística (C=1.0): F1-macro (validation) = {f1_val_logreg:.4f}")

# ---------------------------------------------------------------------------
# Evaluación FINAL sobre TEST -- solo con el modelo ya seleccionado (SVM mejor C)
# ---------------------------------------------------------------------------
final_model = best["model"]
pred_test = final_model.predict(X_test)

metrics_test = {
    "accuracy": round(accuracy_score(y_test, pred_test), 4),
    "precision_macro": round(precision_score(y_test, pred_test, average="macro", zero_division=0), 4),
    "recall_macro": round(recall_score(y_test, pred_test, average="macro", zero_division=0), 4),
    "f1_macro": round(f1_score(y_test, pred_test, average="macro", zero_division=0), 4),
    "balanced_accuracy": round(balanced_accuracy_score(y_test, pred_test), 4),
}

print("\n=== MÉTRICAS FINALES SOBRE TEST (baseline TF-IDF+SVM, C=%s) ===" % best["C"])
for k, v in metrics_test.items():
    print(f"{k}: {v}")

report = classification_report(y_test, pred_test, zero_division=0)
print("\n--- Classification report (test) ---")
print(report)

# ---------------------------------------------------------------------------
# Guardar resultados (reproducibilidad, P15)
# ---------------------------------------------------------------------------
output = {
    "experimento": "EXP_BASELINE_SVM_S42_2026",
    "fecha_ejecucion": "2026-10-01",
    "corpus": f"corpus_metadata.csv ({len(rows)} utterances, {len({r['intent'] for r in rows})} intenciones, {len({r['category'] for r in rows})} categorías)",
    "seed": SEED,
    "split_sizes": {"train": len(train), "validation": len(val), "test": len(test)},
    "vectorizador": {"tipo": "TfidfVectorizer", "max_features": 5000, "ngram_range": [1, 2]},
    "grilla_C": results_grid,
    "mejor_C_por_validacion": best["C"],
    "f1_macro_validacion_mejor_modelo": round(best["f1_val"], 4),
    "alternativa_logreg_f1_macro_validacion": round(f1_val_logreg, 4),
    "metricas_test_final": metrics_test,
    "nota": "EJECUCIÓN REAL sobre el corpus de arranque (324 utterances). No es el corpus final de la tesis -- los valores de F1 reportados aquí son preliminares y se espera que mejoren al ampliar el corpus con más ejemplos reales por intención, según lo documentado en la Sección 2.4 del protocolo."
}
with open(OUT / "resultado_baseline_P07.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

with open(OUT / "resultado_baseline_P07_classification_report.txt", "w", encoding="utf-8") as f:
    f.write(report)

print("\nArchivos guardados: resultado_baseline_P07.json, resultado_baseline_P07_classification_report.txt")
