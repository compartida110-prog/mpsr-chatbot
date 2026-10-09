# LEEME — Cuaderno de Colab «Avance MPSR v1»

Cuaderno de evidencia de tesis (Seminario de Tesis II): documenta y demuestra el código del proyecto `mpsr-chatbot` **sin acceso al repositorio ni a GitHub**. Cubre el flujo P01 → P11.2b.

## Archivos
| Archivo | Para qué | ¿Obligatorio? |
|---|---|---|
| `notebooks/Colab_Avance_MPSR_v1.ipynb` | El cuaderno (con las salidas guardadas de la última ejecución) | Sí |
| `colab_paquetes/MPSR_colab_publico.zip` | Código, corpus **sintético**, demostración **simulada**, resultados agregados. Sin frases ni registros reales | Sí |
| `colab_paquetes/MPSR_colab_privado.zip` | Predicciones del lote 2, particiones y registro del pre-piloto, **sin texto** y con códigos renombrados; y el modelo/entrenamiento congelados para verificar sus huellas | No (opcional) |
| `docs/Documentacion_Codigo_v1.md` | El mismo contenido en texto, para citar | No |

## Pasos (una sola vez)
1. En tu Google Drive crea una carpeta llamada **`MPSR_colab`** (exactamente así, dentro de «Mi unidad»).
2. Sube a esa carpeta `MPSR_colab_publico.zip`. Si quieres que el cuaderno **recalcule** (y no solo muestre) las etapas 4, 6, 7 y 10, sube también `MPSR_colab_privado.zip`. El privado es confidencial: no lo compartas.
3. Abre `Colab_Avance_MPSR_v1.ipynb` en <https://colab.research.google.com> (Archivo → Subir cuaderno) o desde Drive (clic derecho → Abrir con → Google Colaboratory).
4. Ejecuta **celda por celda, en orden** (Ctrl+Enter), o por etapas. La **primera celda de código** (etapa 1) debe correrse siempre primero: monta Drive (te pedirá autorizar), descomprime los paquetes y define las utilidades.
5. Al final, la **etapa 17** imprime la tabla «recalculado frente a reportado» y la lista de discrepancias.

## Qué necesita Rasa y qué no
**Nada de este cuaderno necesita Rasa.** El modelo se entrenó con Python 3.10 + Rasa 3.6 + TensorFlow 2.12, que el Colab actual no soporta; por eso las etapas 6 y 7 trabajan con las **huellas y las predicciones guardadas**. Entrenar DIET es opcional y solo ocurre si Rasa está instalado y defines `MPSR_ENTRENAR_DIET=1` (en Colab no ocurre).

## Si algo falla
| Síntoma | Qué hacer |
|---|---|
| `Falta …/MPSR_colab_publico.zip` | La carpeta debe llamarse exactamente `MPSR_colab` y estar en «Mi unidad»; el zip debe estar dentro. |
| Drive no se monta | Vuelve a ejecutar la primera celda y acepta los permisos; si persiste, Entorno de ejecución → Reiniciar y ejecutar de nuevo. |
| `KeyError`/`FileNotFoundError` en una etapa | Ejecutaste una etapa sin correr la primera celda de código. Corre desde la etapa 1. |
| Una celda dice «⚠ requiere paquete privado» | No es un error: no subiste `MPSR_colab_privado.zip`; se muestra el valor guardado. |
| Una cifra recalculada no coincide («NO») | Es una **discrepancia**: no la corrijas. Anótala (con la etapa y la cifra) y repórtala; revisa la etapa 17. |
| Un `.zip` se subió dos veces o con otro nombre | Borra los duplicados; los nombres deben ser exactos (`MPSR_colab_publico.zip`, `MPSR_colab_privado.zip`). |
| Las versiones de scikit-learn/numpy son otras | Normal: las métricas son fórmulas y no cambian. No se carga ningún modelo entrenado. |

## Qué NO hace el cuaderno
No vuelve a evaluar el test del lote 2 (la evaluación única ya se gastó), no ejecuta `analizar_piloto.py`, no entrena ni reemplaza el modelo congelado `LOTE2-FINAL v1`, no imprime frases ni filas por persona y no usa tokens ni contraseñas.

## Reconstruir los paquetes (solo desde el repositorio)
```
python scripts/construir_colab.py --correr-pruebas        # opcional: refresca los resultados de las pruebas (lento)
python scripts/construir_colab.py --todo --incluir-privado
```
