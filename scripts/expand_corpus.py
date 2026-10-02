#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amplía el Corpus MPSR-Bot: de 2 a 4 grupos de paráfrasis por intención
(de ~6 a ~12 utterances/intención), usando plantillas de habla coloquial
de Juliaca/Puno combinadas con una frase-tema corta por intención.
También corrige la partición para asignar una proporción de grupos a
'train' (no siempre exactamente 1), aumentando los ejemplos de
entrenamiento por intención.
"""
import csv, random, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # raíz del repositorio

random.seed(42)

# Cargar el CORPUS original (grupos 1 y 2). generate_corpus.py no está en el
# repositorio; se reconstruye la misma estructura {categoría: {intención:
# [[variantes grupo 1], [variantes grupo 2]]}} desde el corpus v1 (324
# utterances), conservando el orden original de categorías, intenciones y textos.
CORPUS = {}
with open(ROOT / "corpus" / "historico" / "corpus_metadata_v1_324.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        groups_of_intent = CORPUS.setdefault(r["category"], {}).setdefault(r["intent"], {})
        groups_of_intent.setdefault(r["base_phrase_id"], []).append(r["text"])
CORPUS = {cat: {intent: list(g.values()) for intent, g in intents.items()} for cat, intents in CORPUS.items()}

# ---------------------------------------------------------------------------
# Frase-tema corta por intención (para generar grupos 3 y 4 vía plantillas).
# Las 10 intenciones conversacionales se amplían a mano (frases cortas).
# ---------------------------------------------------------------------------
TOPIC = {
 "licencia_funcionamiento_requisitos": "los requisitos para la licencia de funcionamiento",
 "licencia_funcionamiento_costo": "el costo de la licencia de funcionamiento",
 "licencia_funcionamiento_plazo": "el plazo de atención de la licencia de funcionamiento",
 "licencia_edificacion_requisitos": "los requisitos para la licencia de edificación",
 "licencia_edificacion_costo": "el costo de la licencia de edificación",
 "renovacion_licencia": "cómo renovar una licencia de funcionamiento",
 "consulta_deuda_predial": "mi deuda del impuesto predial",
 "pago_predial_como": "cómo pagar el impuesto predial",
 "pago_arbitrios": "cómo pagar los arbitrios municipales",
 "impuesto_alcabala": "el impuesto de alcabala",
 "fraccionamiento_deuda": "el fraccionamiento de una deuda tributaria",
 "constancia_no_adeudo": "la constancia de no adeudo",
 "requisitos_mesa_partes": "los requisitos de mesa de partes",
 "estado_tramite": "el estado de mi trámite",
 "horario_mesa_partes": "el horario de atención de mesa de partes",
 "copia_documento": "una copia certificada de un documento",
 "certificado_posesion": "el certificado de posesión",
 "constancia_domiciliaria": "la constancia domiciliaria",
 "certificado_defensa_civil": "el certificado de Defensa Civil",
 "inspeccion_tecnica": "la inspección técnica de seguridad (ITSE)",
 "requisitos_defensa_civil": "los requisitos de Defensa Civil",
 "denuncia_seguridad_ciudadana": "cómo reportar un problema de seguridad ciudadana",
 "serenazgo_contacto": "el contacto de serenazgo",
 "partida_nacimiento": "mi partida de nacimiento",
 "partida_matrimonio": "mi partida de matrimonio",
 "partida_defuncion": "una partida de defunción",
 "rectificacion_partida": "la rectificación de una partida",
 "requisitos_matrimonio_civil": "los requisitos para matrimonio civil",
 "horario_recojo_basura": "el horario de recojo de basura",
 "reporte_alumbrado_publico": "cómo reportar una falla de alumbrado público",
 "mantenimiento_parques": "el mantenimiento de un parque",
 "poda_arboles": "la poda de un árbol público",
 "limpieza_via_publica": "la limpieza de una vía pública",
 "presentar_reclamo": "cómo presentar un reclamo",
 "estado_reclamo": "el estado de mi reclamo",
 "libro_reclamaciones": "el libro de reclamaciones",
 "queja_atencion": "una queja sobre la atención recibida",
 "sugerencia": "cómo dejar una sugerencia a la municipalidad",
 "horario_atencion_general": "el horario de atención de la municipalidad",
 "ubicacion_oficinas": "la ubicación de la municipalidad",
 "requisitos_generales": "los requisitos generales para hacer un trámite",
 "costos_generales": "los costos de los trámites municipales",
 "contacto_telefonico": "el teléfono de contacto de la municipalidad",
 "redes_sociales_mpsr": "las redes sociales de la municipalidad",
}

TEMPLATES_G3 = [
    "Buenas, ¿me podría explicar {t}?",
    "Quisiera saber {t}.",
    "¿Usted me puede ayudar con {t}?",
]
TEMPLATES_G4 = [
    "Disculpe, ¿dónde consigo información sobre {t}?",
    "Oiga, ¿qué hay sobre {t}?",
    "Necesitaría orientación sobre {t}.",
]

# Ampliación a mano de las 10 intenciones conversacionales (grupos 3 y 4).
CONVERSACIONAL_EXTRA = {
    "saludo": [["Buenas tardes", "Hola, qué tal está", "Buenas, disculpe"],
               ["Oiga, buenas", "Hola, cómo le va", "Buenos días, disculpe la hora"]],
    "despedida": [["Muchas gracias, hasta luego", "Ya está, gracias", "Bueno, me retiro, gracias"],
                  ["Vale, gracias, chau", "Está bien, hasta otra", "Gracias, que esté bien"]],
    "agradecimiento": [["Mil gracias", "Qué bien, gracias", "Agradecido por la info"],
                        ["Bien ahí, gracias", "Gracias, eso necesitaba", "Buenísimo, gracias"]],
    "afirmar": [["Correcto", "Sí, así es", "Confirmado"],
                ["Exacto, eso es", "Sí señor/señorita", "Así mismo es"]],
    "negar": [["No, nada que ver", "Negativo", "No es así"],
              ["No, otra cosa quería", "No, disculpe", "No, para nada"]],
    "fuera_de_alcance": [["¿Cuál es la capital de Francia?", "¿Me ayudas con mi tarea?", "¿Qué partido juega hoy?"],
                          ["¿Sabes cocinar?", "¿Cuánto es 2 más 2?", "Recomiéndame una película"]],
    "hablar_con_persona": [["Quiero que me atienda una persona real", "Comuníqueme con un trabajador", "¿Hay alguien humano ahí?"],
                            ["Prefiero hablar con un funcionario", "¿Me puede pasar con alguien del área?", "Necesito atención humana, no un bot"]],
    "ayuda_chatbot": [["¿Qué funciones tienes?", "¿Qué consultas puedo hacerte?", "¿Para qué sirves exactamente?"],
                       ["¿Qué sabes responder?", "Cuéntame qué puedes hacer", "¿Qué tipo de ayuda das?"]],
    "consulta_no_entendida": [["No capté eso", "¿Cómo? no entendí", "Perdón, no quedó claro"],
                               ["¿A qué te refieres?", "No comprendí tu mensaje", "Explícalo de nuevo porfa"]],
    "repetir_informacion": [["¿Me repites por favor?", "No leí bien, repite", "Otra vez porfa"],
                             ["Mándamelo de nuevo", "Repite la info anterior", "¿Puedes volver a escribirlo?"]],
}

# ---------------------------------------------------------------------------
# Construir CORPUS ampliado (4 grupos por intención)
# ---------------------------------------------------------------------------
CORPUS_EXPANDED = {}
for category, intents in CORPUS.items():
    CORPUS_EXPANDED[category] = {}
    for intent, bases in intents.items():
        new_bases = list(bases)  # grupos 1 y 2 originales
        if intent in CONVERSACIONAL_EXTRA:
            new_bases.extend(CONVERSACIONAL_EXTRA[intent])
        else:
            t = TOPIC[intent]
            new_bases.append([tpl.format(t=t) for tpl in TEMPLATES_G3])
            new_bases.append([tpl.format(t=t) for tpl in TEMPLATES_G4])
        CORPUS_EXPANDED[category][intent] = new_bases

# ---------------------------------------------------------------------------
# Construir filas
# ---------------------------------------------------------------------------
rows = []
uid = 1
groups = []
for category, intents in CORPUS_EXPANDED.items():
    for intent, bases in intents.items():
        for b_idx, variants in enumerate(bases, start=1):
            base_phrase_id = f"{intent}__b{b_idx}"
            groups.append((base_phrase_id, intent, category))
            for text in variants:
                rows.append({
                    "utterance_id": f"U{uid:04d}", "text": text, "intent": intent,
                    "category": category,
                    "source": "construcción manual + plantillas coloquiales (pendiente contrastar con TUPA oficial)",
                    "base_phrase_id": base_phrase_id, "split": None,
                })
                uid += 1

print(f"Total utterances: {len(rows)}  (antes: 324)")
print(f"Total grupos: {len(groups)}  (antes: 108)")

# ---------------------------------------------------------------------------
# Partición MEJORADA: proporción ~70/15/15 POR INTENCIÓN (no solo 1 grupo a
# train). Con 4 grupos/intención: round(4*0.7)=3 a train, resto alterna
# validation/test.
# ---------------------------------------------------------------------------
intent_to_groups = {}
for bpid, intent, category in groups:
    intent_to_groups.setdefault(intent, []).append(bpid)

split_of_group = {}
alt_counter = 0
for intent in sorted(intent_to_groups.keys()):
    gs = intent_to_groups[intent][:]
    random.shuffle(gs)
    n_groups = len(gs)
    n_train = max(1, round(n_groups * 0.70))
    for g in gs[:n_train]:
        split_of_group[g] = "train"
    for g in gs[n_train:]:
        split_of_group[g] = "validation" if alt_counter % 2 == 0 else "test"
        alt_counter += 1

for r in rows:
    r["split"] = split_of_group[r["base_phrase_id"]]

# Verificaciones
check = {}
for r in rows:
    check.setdefault(r["base_phrase_id"], set()).add(r["split"])
leaks = {k: v for k, v in check.items() if len(v) > 1}
print(f"Grupos con fuga (debe ser 0): {len(leaks)}")

train_intents = {r["intent"] for r in rows if r["split"] == "train"}
all_intents = {r["intent"] for r in rows}
print(f"Intenciones sin ejemplos en train (debe ser 0): {len(all_intents - train_intents)}")

split_counts = {"train": 0, "validation": 0, "test": 0}
for r in rows:
    split_counts[r["split"]] += 1
print("Distribución:", split_counts)
print(f"Promedio ejemplos de TRAIN por intención: {split_counts['train']/len(all_intents):.1f}")

# ---------------------------------------------------------------------------
# Guardar archivos (mismo formato que antes)
# ---------------------------------------------------------------------------
with open(ROOT / "corpus" / "corpus_metadata.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["utterance_id","text","intent","category","source","base_phrase_id","split"])
    writer.writeheader(); writer.writerows(rows)

with open(ROOT / "corpus" / "dataset_split.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["utterance_id","intent","base_phrase_id","split","seed"])
    writer.writeheader()
    for r in rows:
        writer.writerow({"utterance_id": r["utterance_id"], "intent": r["intent"],
                          "base_phrase_id": r["base_phrase_id"], "split": r["split"], "seed": 42})

def build_nlu_yaml_text(selected_rows):
    by_intent = {}
    for r in selected_rows:
        by_intent.setdefault(r["intent"], []).append(r["text"])
    lines = ['version: "3.1"', "nlu:"]
    for intent, texts in sorted(by_intent.items()):
        lines.append(f"- intent: {intent}")
        lines.append("  examples: |")
        for t in texts:
            lines.append(f"    - {t.replace(chr(34), chr(92)+chr(34))}")
    return "\n".join(lines) + "\n"

with open(ROOT / "data" / "nlu_full.yml", "w", encoding="utf-8") as f:
    f.write(build_nlu_yaml_text(rows))
train_rows = [r for r in rows if r["split"] == "train"]
with open(ROOT / "data" / "nlu.yml", "w", encoding="utf-8") as f:
    f.write(build_nlu_yaml_text(train_rows))

summary = {
    "total_utterances": len(rows), "total_intents": len(all_intents),
    "total_categories": len(CORPUS_EXPANDED), "total_groups": len(groups),
    "split_counts": split_counts, "leaks_detected": len(leaks), "seed": 42,
    "avg_train_examples_per_intent": round(split_counts['train']/len(all_intents), 2),
}
with open(ROOT / "corpus" / "corpus_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("\nArchivos actualizados: corpus/corpus_metadata.csv, corpus/dataset_split.csv, data/nlu_full.yml, data/nlu.yml (solo train), corpus/corpus_summary.json")
print("(domain.yml y rules.yml no cambian: mismas 54 intenciones)")
