#!/usr/bin/env bash
# Instala las dependencias del proyecto en el Codespace (Python 3.10). No sube ni descarga datos privados.
set -e
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install ipykernel jupyter nbformat
python -m rasa --version
python - <<'PY'
import rasa, sklearn, pandas, numpy
print("OK · Rasa", rasa.__version__, "· scikit-learn", sklearn.__version__, "· pandas", pandas.__version__, "· numpy", numpy.__version__)
PY
echo "Siguiente paso: python scripts/entrenar_modelo_demo.py   y luego   python scripts/asistente_local.py DEMO --demo"
