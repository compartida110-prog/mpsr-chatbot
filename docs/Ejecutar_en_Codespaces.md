# Cómo ejecutar esta parte (Rasa y el asistente) — GitHub Codespaces

Colab **no** puede correr Rasa 3.6 (necesita Python 3.10 y TensorFlow 2.12). En un **Codespace** de GitHub sí: es un entorno Linux en la nube, con terminal y Jupyter, que se crea con **Python 3.10 y las versiones exactas del proyecto** (`.devcontainer/`). Aquí se puede **entrenar DIET, correr el asistente y ejecutar los cuadernos y las pruebas**, todo con datos **sintéticos**.

> **Estado de esta guía:** probada el 10-oct-2026 en un Codespace real (Python 3.10.18, Linux, 2 núcleos): el entorno se crea, Rasa 3.6 importa, `entrenar_modelo_demo.py --rapida` termina y `asistente_local.py DEMO --demo` responde. Hallazgo: instalar Jupyter junto a Rasa subía `packaging` y `prompt-toolkit` y Rasa dejaba de importar (`LegacyVersion`); `instalar.sh` ya los vuelve a fijar. Si el Codespace se creó con la versión anterior del script, corre `python -m pip install 'packaging==20.9' 'prompt-toolkit<3.0.29'`.

## 0. Lo que NO debe estar en el Codespace
El repositorio en GitHub **no** contiene (por `.gitignore`): el registro del pre-piloto, los logs de sesiones, las frases reales, las carpetas `privado/`, el modelo congelado `LOTE2-FINAL.tar.gz` (su vocabulario incluye frases reales del lote 1) ni los paquetes `.zip` privados. **No los subas.** Todo lo de abajo usa solo el corpus sintético.

## 1. Abrir el Codespace
1. En GitHub, abre el repositorio `compartida110-prog/mpsr-chatbot` → **Code → Codespaces → Create codespace on main**.
2. Espera a que termine «postCreateCommand» (instala `requirements.txt` + Jupyter; unos 5–10 min la primera vez). Debe imprimir `OK · Rasa 3.6.21 · scikit-learn 1.1.3 …`.
3. Para que la docente lo abra: **Settings → Collaborators** del repositorio (permiso de lectura) y compártele el enlace del repositorio; ella crea su propio Codespace.

## 2. Entrenar el modelo de demostración (solo datos sintéticos)
```bash
python scripts/entrenar_modelo_demo.py            # configuración oficial: DIET 100 épocas (≈ 5 min)
python scripts/entrenar_modelo_demo.py --rapida   # DEMO RÁPIDA: 20 épocas (NO es la configuración oficial)
```
Crea `models/demo_vivo/DEMO-VIVO.tar.gz` (carpeta ignorada por Git). Entrena con una **copia** de la configuración, nunca con la del modelo congelado.

## 3. Correr el asistente (modo demo)
```bash
python scripts/asistente_local.py DEMO --demo
```
- Escribe una consulta y Enter; `salir` para terminar.
- Muestra el aviso «MODO DEMO: modelo entrenado SOLO con datos sintéticos; NO es el modelo congelado».
- Aplica el mismo umbral `t = 0,50` (y ambigüedad 0,1) y responde con `utter_<intención>` de `domain_v3.yml` o «no entendí».
- El registro de la sesión queda en `models/demo_vivo/logs_demo/DEMO_log_*.csv` (ignorado por Git).
- Con un código `PPxx` el modo demo se **niega**: los `PPxx` son sesiones reales.

La sesión **real** del pre-piloto (código `PPxx`, modelo congelado, registro en `docs/piloto/privado/`) se hace **solo en la laptop del tesista**, no en el Codespace.

## 4. Cuadernos, demo y pruebas
```bash
python -m ipykernel install --user --name mpsr      # luego abre notebooks/colab_por_paso/*.ipynb con el kernel «mpsr» (VS Code → Jupyter)
for t in tests/smoke_*.py; do python $t | tail -3; done     # 9 pruebas de humo con datos falsos (≈ 25 min en total)
```
Para los cuadernos arrastra `MPSR_colab_publico.zip` (el paquete **público**, sin datos reales; no está en Git) a la raíz del Codespace: cada cuaderno lo descomprime solo (carpeta de trabajo `mpsr_trabajo/`, también ignorada por Git). El zip **privado** no se sube.

(Algunas pruebas —al menos `smoke_asistente.py`— leen el modelo **congelado** real y los archivos privados, que no están en el Codespace: allí fallarán. No es un defecto del código; esas pruebas se corren en la laptop del tesista.)

## 5. Qué ejecuta cada plataforma
| Parte | Laptop del tesista | Codespace | Colab |
|---|---|---|---|
| Cuadernos (cifras recalculadas, tablas, glosario) | sí | sí | sí |
| Entrenar DIET (modelo de demostración sintético) | sí | **sí** | no (sin Rasa) |
| `asistente_local.py DEMO --demo` | sí | **sí** | no |
| Sesión real `asistente_local.py PPxx` (modelo congelado) | **sí (única plataforma)** | no | no |
| Registro del pre-piloto y paquete privado | sí | no (no se sube) | opcional (zip privado, confidencial) |
