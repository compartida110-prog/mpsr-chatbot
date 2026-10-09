# Informe del refinamiento previo al lote 2 (cifras; sin frases) — 2026-10-08/09

**Estado: EJECUTADO** (refinamiento y congelamiento). **El lote 2 NO se ingestó, NO se leyó y NO se evaluó.** G3 sigue «No cumplida, lote 1».

## 1. Límites cumplidos
- **Solo datos del lote 1** (185 frases activas), validación cruzada **agrupada por participante** (5 folds, StratifiedGroupKFold seed 42, 31 participantes). No se abrió `corpus/real_lote2/`.
- **Declarado antes de medir** (commit anterior a la medición): `logs/avance/ciclos_refinamiento_declaracion.csv`, ciclo 1 = frases sintéticas nuevas dirigidas a errores del lote 1 + umbral.
- **Entrenamiento:** 707 sintéticas + 185 reales **+ 51 sintéticas nuevas** del refinamiento (943 frases). No se agregó ninguna frase real elegida por mirar el test; ninguna de las 51 copia una frase real ni una sintética existente (comprobado tras normalizar).
- **SVM no se usó** (ni en las mediciones ni en el modelo): solo DIET.

## 2. F1 macro por ciclo (validación cruzada por participante, 185 frases)
| Ciclo | Cambio declarado | F1 macro | Mejora frente al anterior | Decisión |
|---|---|---|---|---|
| 0 (línea de base) | ninguno | **0,7866** | — | — |
| 1 | 51 frases sintéticas nuevas (despedida 8, agradecimiento 8, limpieza_via_publica 8, horario_recojo_basura 4, denuncia_seguridad_ciudadana 8, licencia_funcionamiento_requisitos 8, fuera_de_alcance 7) + umbral | **0,7987** (IC95 % por participantes 0,658–0,820; accuracy 0,795) | **+0,0121 (< 0,02)** | **Se detiene: no hay ciclo 2** (ciclos usados: 1 de 2) |

- La mejora (+0,012) es **menor que el 0,02** fijado y es **compatible con ruido** (185 frases, entrenamiento no determinista de DIET): no se puede afirmar que las frases nuevas mejoraron el modelo.
- Por intención (n pequeño, muy inestable): `denuncia_seguridad_ciudadana` pasó de 0,00 a 0,50 (n = 3) y `licencia_funcionamiento_requisitos` de 0,29 a 0,22 (n = 4); `despedida` sigue en 0,33 (n = 4) y `agradecimiento` en 0,62 → ≈ igual. Tabla completa: `logs/avance/cv_participantes_ciclo1_resumen.md`.
- **Lectura honesta:** estos F1 (0,787–0,799) **no son comparables con el 0,687 del test del lote 1**: en la validación cruzada el modelo se entrena también con las frases reales de *otros participantes* del lote 1, que es el régimen del lote 2. Aun así el intervalo llega a 0,66 y el criterio es 0,75: **G3 en el lote 2 es incierto**.

## 3. Umbral de confianza (no cambia el F1 macro)
Elegido con las predicciones de la validación cruzada del ciclo 1 (185 frases), misma regla que el lote 1 (aciertos − 2 × errores con respuesta): **t = 0,50** (puntaje 109 frente a 71 sin umbral; cobertura 81,6 %; precisión de lo respondido 90,7 %). Tabla: `logs/avance/umbral_lote2_reporte.txt`. En el lote 1 el umbral elegido había sido 0,60.

## 4. Congelamiento (antes de abrir el lote 2)
`logs/v3_real/lote2_congelado_previo.json` (2026-10-09 01:20 UTC; verificado con `congelar_modelo.py --verificar`: «intacto»):

| Archivo | sha256 |
|---|---|
| Modelo `models/rasa/LOTE2-FINAL.tar.gz` (DIET 100/64/20, seed 42, entrenamiento de 943 frases) | `be1a5ad06357b26370fc14f780f49cbf205b08dbe5fe3af383625e44f64b10d9` |
| Configuración `configs/rasa_config_lote2.yml` (FallbackClassifier t = 0,50, ambigüedad 0,1) | `e975783f2bcd6dac366b2ff53677c5221ef77044ec23fb615c3d763dcadbf9e4` |
| Dominio `domain_v3.yml` | `985f07e3d0e370df28f18ae9cd1e97ce888a32bf5cf34d88b795412748cd9a1f` |
| Entrenamiento `corpus/v3_lote2/entrenamiento_lote2.csv` | `c035252d63aa89e11295279b363c98d66b9f2e608008b82390b15ce40a6a4adc` |
| Umbral `logs/v3_real/lote2_umbral_congelado.json` | `410d9898240ae0ea5118e5d5010af195fa21d0a118c7967875875cd956f8fe4b` |

- `ingest_real_lote.py --lote 2`, `split_lote2.py` y `eval_lote2.py` **se niegan** a leer o evaluar el lote 2 si alguna de estas huellas cambia.
- ⚠️ **El dominio forma parte del congelamiento.** Cualquier cambio posterior en `domain_v3.yml` (por ejemplo, aplicar el dry-run 3 de `constancia_domiciliaria`, que sigue pendiente de tu «aplica») invalida el congelamiento y exige rehacerlo con `--forzar --motivo` (queda en `incident_log.csv`) **antes** de abrir el lote 2. Conviene decidir eso ahora.

## 5. Evaluación única (script listo, sin ejecutar)
`scripts/eval_lote2.py` (prueba de humo con datos falsos: `tests/smoke_lote2.py`, 43 de 43): F1 macro con IC95 % por frases y por participantes (y la media del bootstrap), F1 por intención con su n, cobertura y precisión con el umbral congelado, y la confusión despedida ↔ agradecimiento aparte. Se niega a repetirse (una sola vez). **No se ejecutó con el lote 2.**

## 6. Qué sigue (cuando tú avises)
1. Decidir si aplicar el dry-run 3 (constancia) **antes** de abrir el lote 2 (y, si sí, rehacer el congelamiento).
2. Ingesta del lote 2 (`ingest_real_lote.py --lote 2`), revisión de etiquetas, `split_lote2.py`, `eval_lote2.py` (una sola vez).
