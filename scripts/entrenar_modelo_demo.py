"""Entrena el modelo de DEMOSTRACIÓN del asistente: Rasa/DIET con la configuración del modelo congelado, pero SOLO con el corpus SINTÉTICO (data/nlu_train.yml, 546 frases).

No usa frases reales, no toca el modelo congelado ni ningún archivo protegido: entrena con una COPIA de la configuración (Rasa agrega `assistant_id` al archivo que recibe) y con una caché propia,
y guarda models/demo_vivo/DEMO-VIVO.tar.gz (carpeta ignorada por Git). Sirve para correr `asistente_local.py DEMO --demo` en cualquier equipo (p. ej. un Codespace) sin material sensible.

Uso:
    python scripts/entrenar_modelo_demo.py              # configuración oficial: 100 épocas (unos 5 min)
    python scripts/entrenar_modelo_demo.py --rapida     # DEMO RÁPIDA: 20 épocas (NO es la configuración oficial)
Después:
    python scripts/asistente_local.py DEMO --demo
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

import yaml

from common import ROOT

DEMO = ROOT / "models" / "demo_vivo"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rapida", action="store_true", help="20 épocas en lugar de 100 (DEMO RÁPIDA, no oficial)")
    a = ap.parse_args()
    DEMO.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((ROOT / "configs" / "rasa_config_lote2.yml").read_text(encoding="utf-8"))
    if a.rapida:
        for c in cfg["pipeline"]:
            if c["name"] == "DIETClassifier":
                c["epochs"] = 20
    copia = DEMO / ("config_rapida.yml" if a.rapida else "config_oficial_copia.yml")
    copia.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    cache = DEMO / "rasa_cache"
    shutil.rmtree(cache, ignore_errors=True)
    modelo = DEMO / "DEMO-VIVO.tar.gz"
    if modelo.exists():
        modelo.unlink()
    env = {**os.environ, "RASA_CACHE_DIRECTORY": str(cache), "TF_CPP_MIN_LOG_LEVEL": "3", "PYTHONWARNINGS": "ignore"}
    cmd = [sys.executable, "-m", "rasa", "train", "nlu", "--nlu", str(ROOT / "data" / "nlu_train.yml"), "--config", str(copia), "--domain", str(ROOT / "domain_v3.yml"), "--out", str(DEMO), "--fixed-model-name", "DEMO-VIVO"]
    print("Modo:", "DEMO RÁPIDA (20 épocas, NO oficial)" if a.rapida else "oficial (100 épocas)", "| datos: corpus SINTÉTICO (546 frases)")
    print("Comando:", " ".join(cmd))
    t0 = time.time()
    p = subprocess.run(cmd, env=env, cwd=ROOT)
    print(f"Duración: {time.time() - t0:.0f} s")
    if p.returncode != 0 or not modelo.exists():
        print("El entrenamiento NO terminó.")
        return 1
    print(f"Listo: {modelo}\nAhora puedes correr:  python scripts/asistente_local.py DEMO --demo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
