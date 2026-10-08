# Propuesta para el lote 2 (planificada, NO ejecutada)

**Estado: PLANIFICADO.** Nada de lo siguiente se ha hecho. G3 sigue NO cumplida (F1 macro del test del lote 1 = 0,687; criterio 0,75, sin cambios).

## 1. Intención nueva candidata: recojo de basura
No se crea ninguna intención ahora (no se toca NLU, ejemplos ni dominio). Hoy `horario_recojo_basura` ya existe como intención; lo que sería nuevo es una respuesta con datos por sector, que hoy no se puede dar con certeza.

Datos recogidos (08/10/2026):
- **Fuente:** croquis por sectores I a VI, en la carpeta de Drive de la municipalidad (revisada por el tesista), y la página oficial de Facebook (la secretaria indicó que los horarios están ahí).
- **Sector I-1:** 2 veces por semana, lunes y jueves, de 6:30 a 10:00 a. m. (croquis firmado por la «Gerencia de Gestión Ambiental y Residuos Sólidos»).
- **Pendiente:** copiar del croquis los datos de los sectores I-2 a I-6, II, III, IV, V y VI (recuadro inferior de cada imagen).
- **Pendiente de decidir:** nombre del área (la secretaria dijo «Gerencia de Servicios Públicos y Medio Ambiente»; el croquis, «Gerencia de Gestión Ambiental y Residuos Sólidos»).
- **Decisión que falta:** si el chatbot puede responder por sector o solo dirigir al croquis y a Facebook; para responder por sector la persona debería indicar su sector, lo que implicaría una intención con entidad (no se hace en esta tarea).

## 2. Plan del lote 2 (para decidir antes de ejecutar)
1. **Declarar la desviación de protocolo ANTES de medir.** El protocolo V1.5 evalúa una sola vez con el test del lote 1; el plan del lote 2 cambia el diseño de evaluación (entrenar con reales del lote 1) y debe quedar escrito como desviación, con fecha, antes de entrenar o evaluar cualquier cosa.
2. **Entrenamiento:** corpus sintético vigente + frases reales del lote 1 (validación y test del lote 1 pasan a entrenamiento; las excluidas/descartadas del log siguen fuera; las copias sintéticas idénticas a una real siguen excluidas del entrenamiento).
3. **Validación:** para elegir hiperparámetros y umbral, validación cruzada dejando participantes fuera dentro del lote 1 (o una validación reservada del lote 2), definida antes de ver resultados.
4. **Test nuevo e independiente:** frases de personas distintas del lote 1, con las mismas reglas de recolección y revisión de etiquetas (kappa solo si hay segunda revisora), con al menos 3 frases por intención (idealmente más de 2 en el test para que el F1 por intención y el IC sean estables).
5. **Una sola evaluación del test nuevo**, con el criterio de F1 macro ≥ 0,75 sin cambios y el umbral de fallback congelado antes de evaluar.
6. **Reportar siempre** que el test del lote 1 ya se usó una vez y que sus resultados no se reutilizan para decidir ajustes.
7. **Tamaño del lote 2:** por decidir; con 54 intenciones y la meta de al menos 3 frases por intención en el test, se necesitan como mínimo unas 162 frases útiles tras descartes (ajustar por la proporción de descartes del lote 1).
8. **Compuertas:** G3 solo se evalúa con el test nuevo; G4 y G5 siguen su curso (el modelo real no se congela antes de G3 y G4).

## 3. Limitaciones del lote 1 que el lote 2 debería mejorar
- 48 de 54 intenciones tuvieron solo 2 frases en el test (IC muy ancho y sesgado hacia abajo).
- 28 de 31 participantes y 52 de 56 situaciones aparecen en validación y en test (cada frase fue su propio grupo).
- Revisión de etiquetas de una sola revisora (sin acuerdo entre revisores).
