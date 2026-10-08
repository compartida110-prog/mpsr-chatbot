"""Conciliación del seguimiento del lote 1 (xlsx) con las respuestas transcritas (CSV).

Cruza lo que el tesista anota en el seguimiento (hojas Participantes y Blancos) con lo que transcribe en
corpus/real/lote1_respuestas.csv. Para cada participante en estado «Transcrito» se espera una respuesta por cada
situación de su formulario, salvo las registradas en la hoja Blancos. Detecta:
  * una respuesta ausente que NO figura como blanco;
  * una situación registrada como blanco que SÍ tiene respuesta;
  * participantes Transcritos sin ninguna respuesta, y respuestas de participantes que no están en el seguimiento
    o que no están en estado Transcrito;
  * blancos que apuntan a un participante o a una situación inexistente, o a una situación de otro formulario;
  * respuestas a situaciones que no existen o que no son del formulario del participante.
También informa la cobertura real por intención (meta y mínimo de la hoja Resumen) y si ya se cumple la condición
para iniciar la Parte B.

Se NIEGA a trabajar con un seguimiento simulado o sintético (SIMULADO, SINTÉTICO, SINTETICO o DEMO en el título, en Participantes, en Blancos o en cualquier
columna Observaciones): los datos simulados no son evidencia. Con --permitir-simulado lo lee solo para probar el código, escribe únicamente en una carpeta temporal
y rotula las salidas como SIMULADO.

Exporta corpus/real/lote1_participantes.csv (participant_code, form, age_range, vive_en_juliaca, tramite_12m) solo de
los participantes Transcritos y SIN ocupación, fecha ni observaciones.

Código de salida: 0 = conciliado; 1 = hay discrepancias; 2 = archivo simulado o entrada inválida (sin salidas).

Uso:
    python scripts/conciliar_seguimiento.py --seguimiento docs/lote_real_1/privado/Seguimiento_Lote1_Participantes_real.xlsx
"""
import argparse
import re
import sys
import warnings
from pathlib import Path

import pandas as pd

import catalogo_formularios as cf
import deteccion_simulado as ds
from common import LOGS, ROOT

warnings.filterwarnings("ignore", message="Data Validation extension")
import openpyxl  # noqa: E402

ESTADOS = ["Pendiente", "Entregado", "Respondido", "Transcrito"]
HDR_PART, HDR_BLANC = 3, 3  # fila de encabezados de Participantes y de Blancos
COL = {"codigo": 1, "edad": 5, "ocupacion": 6, "vive": 7, "tramite": 8, "estado": 9, "fecha": 10, "obs": 14}
CODIGO = re.compile(r"^P\d{2}$")


def forma_de(codigo):
    n = int(codigo[1:])
    return "G" if n > 28 else "F" if n > 25 else "ABCDE"[(n - 1) % 5]  # misma rotación que la hoja Participantes; P26–P28 son el lote 1b (formulario F)


def texto(v):
    return "" if v is None else str(v).strip()


def es_simulado(wb):
    """Devuelve el motivo si el libro parece simulado o sintético (SIMULADO, SINTÉTICO, SINTETICO o DEMO en hojas, títulos, Participantes, Blancos u Observaciones); si no, ''."""
    return ds.revisar_libro(wb, hojas_datos=("Participantes", "Blancos"))


def leer_seguimiento(wb, exigir_blancos=True):
    if not ({"Participantes", "Blancos"} if exigir_blancos else {"Participantes"}) <= set(wb.sheetnames):
        sys.exit("ERROR: el libro no tiene las hojas Participantes y Blancos (¿es la plantilla v3?). "
                 "(Sin hoja Blancos hay que pasar --blancos-derivados con los blancos del libro de transcripción.)")
    ws = wb["Participantes"]
    if texto(ws.cell(HDR_PART, 1).value) != "Código":
        sys.exit(f"ERROR: se esperaba el encabezado 'Código' en la fila {HDR_PART} de Participantes (¿es la plantilla v3?).")
    part = []
    for r in range(HDR_PART + 1, ws.max_row + 1):
        c = texto(ws.cell(r, 1).value)
        if not CODIGO.match(c):  # la tabla termina en la primera fila sin código (la fila de ejemplo queda fuera)
            break
        part.append({"codigo": c, "fila": r, "form": forma_de(c), **{k: texto(ws.cell(r, v).value) for k, v in COL.items() if k != "codigo"}})
    bl = []
    if "Blancos" in wb.sheetnames:
        wb_ = wb["Blancos"]
        for r in range(HDR_BLANC + 1, wb_.max_row + 1):
            c, s = texto(wb_.cell(r, 1).value), texto(wb_.cell(r, 2).value)
            if c or s:
                bl.append({"codigo": c, "sit": s, "fila": r})
    params = {"meta": 4, "minimo": 3, "min_part": 15}
    if "Resumen" in wb.sheetnames:
        rs = wb["Resumen"]
        for clave, fila in (("meta", 5), ("minimo", 6), ("min_part", 7)):
            v = rs.cell(fila, 2).value
            if isinstance(v, (int, float)):
                params[clave] = int(v)
    return pd.DataFrame(part), pd.DataFrame(bl, columns=["codigo", "sit", "fila"]), params


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seguimiento", default=str(ROOT / "docs" / "lote_real_1" / "privado" / "Seguimiento_Lote1_Participantes_real.xlsx"))
    ap.add_argument("--situaciones", default=str(ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"))
    ap.add_argument("--respuestas", default=str(ROOT / "corpus" / "real" / "lote1_respuestas.csv"))
    ap.add_argument("--out-participantes", default=str(ROOT / "corpus" / "real" / "lote1_participantes.csv"))
    ap.add_argument("--log-dir", default=str(LOGS / "v3_real"))
    ap.add_argument("--blancos-derivados", default="", help="lote1_blancos_derivados.csv del libro de transcripción (ingest_real_lote.py --libro): fuente de los blancos; "
                    "si el seguimiento también tiene hoja Blancos, se comparan e informan las diferencias")
    ap.add_argument("--permitir-simulado", action="store_true", help="solo para pruebas: acepta un libro simulado y escribe en una carpeta temporal")
    a = ap.parse_args()

    seg_path = Path(a.seguimiento)
    if not seg_path.exists():
        sys.exit(f"ERROR: no existe el seguimiento {seg_path}.")
    wb = openpyxl.load_workbook(seg_path, data_only=False)
    motivo = es_simulado(wb)
    if motivo and a.permitir_simulado:
        tmp = ds.destino_temporal(a.log_dir, "conciliar_simulado_")
        a.log_dir = str(tmp)
        if not ds.es_temporal(a.out_participantes):
            a.out_participantes = str(tmp / "participantes_SIMULADO.csv")
        print(f"AVISO (--permitir-simulado): libro SIMULADO ({motivo}). Las salidas van a la carpeta temporal {tmp} y no son evidencia.")
    elif motivo:
        msg = (f"ME NIEGO a conciliar {seg_path.name}: parece un seguimiento SIMULADO ({motivo}).\n"
               "Los datos simulados no son evidencia. Usa el seguimiento de la aplicación real (partiendo de la plantilla vacía). "
               "No se generó ninguna salida.")
        print(msg)
        sys.exit(2)

    part, bl, params = leer_seguimiento(wb, exigir_blancos=not a.blancos_derivados)
    dif_blancos = []
    if a.blancos_derivados:
        if not Path(a.blancos_derivados).exists():
            sys.exit(f"ERROR: no existe {a.blancos_derivados}.")
        der = pd.read_csv(a.blancos_derivados, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if not {"participant_code", "scenario_id"} <= set(der.columns):
            sys.exit(f"ERROR: a {a.blancos_derivados} le faltan las columnas participant_code y scenario_id.")
        der_set = set(zip(der["participant_code"], der["scenario_id"]))
        if len(bl):  # el seguimiento también trae hoja Blancos: se compara; no se edita ningún archivo
            seg_set = set(zip(bl["codigo"], bl["sit"]))
            dif_blancos = ([f"({c}, {s}): figura en la hoja Blancos del seguimiento pero el libro de transcripción NO lo tiene como blanco" for c, s in sorted(seg_set - der_set)]
                           + [f"({c}, {s}): el libro de transcripción lo tiene en blanco pero NO figura en la hoja Blancos del seguimiento" for c, s in sorted(der_set - seg_set)])
        bl = pd.DataFrame([{"codigo": c, "sit": s, "fila": i + 2} for i, (c, s) in enumerate(zip(der["participant_code"], der["scenario_id"]))], columns=["codigo", "sit", "fila"])
    cat = pd.read_csv(a.situaciones, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    resp = pd.read_csv(a.respuestas, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for c in ("participant_code", "form", "scenario_id", "text"):
        if c not in resp.columns:
            sys.exit(f"ERROR: a {a.respuestas} le falta la columna '{c}'.")
    resp["text"] = resp["text"].str.strip()
    sit_form = cf.formas_por_situacion(cat, a.situaciones)  # {situación: {formularios}}; el formulario F se suma a A–E
    sit_intent = cat.set_index("scenario_id")["intent_esperada"].to_dict()
    por_form = cf.por_formulario(sit_form)
    codigos = set(part["codigo"]) if len(part) else set()
    form_part = dict(zip(part["codigo"], part["form"])) if len(part) else {}
    estado = dict(zip(part["codigo"], part["estado"])) if len(part) else {}
    D = {k: [] for k in ("ausente", "blanco_con_respuesta", "transcrito_sin_respuestas", "resp_sin_participante", "resp_no_transcrito",
                         "blanco_invalido", "resp_situacion_invalida", "estado_invalido", "datos_incompletos", "blanco_duplicado", "blancos_distintos")}

    # ---- participantes
    for p in part.itertuples():
        if p.estado not in ESTADOS:
            D["estado_invalido"].append(f"{p.codigo} (fila {p.fila}): estado '{p.estado}' no es uno de {ESTADOS}")
        if p.estado == "Transcrito" and not (p.edad and p.vive and p.tramite):
            D["datos_incompletos"].append(f"{p.codigo}: Transcrito sin rango de edad / residencia / trámite (se exportarían en blanco)")
    # ---- blancos
    vistos = set()
    for b in bl.itertuples():
        if b.codigo not in codigos:
            D["blanco_invalido"].append(f"Blancos fila {b.fila}: participante '{b.codigo}' no existe en Participantes")
        elif b.sit not in sit_form:
            D["blanco_invalido"].append(f"Blancos fila {b.fila}: situación '{b.sit}' no existe en el catálogo")
        elif form_part[b.codigo] not in sit_form[b.sit]:
            D["blanco_invalido"].append(f"Blancos fila {b.fila}: {b.sit} es del formulario {cf.etiqueta(sit_form[b.sit])} y {b.codigo} usó el {form_part[b.codigo]}")
        if (b.codigo, b.sit) in vistos:
            D["blanco_duplicado"].append(f"Blancos fila {b.fila}: ({b.codigo}, {b.sit}) repetido")
        vistos.add((b.codigo, b.sit))
    blancos = {c: set(g["sit"]) for c, g in bl.groupby("codigo")} if len(bl) else {}
    # ---- respuestas
    for r in resp.itertuples():
        if r.participant_code not in codigos:
            D["resp_sin_participante"].append(f"{r.participant_code} / {r.scenario_id}: el participante no está en el seguimiento")
        elif estado[r.participant_code] != "Transcrito":
            D["resp_no_transcrito"].append(f"{r.participant_code} / {r.scenario_id}: hay respuestas pero el seguimiento dice '{estado[r.participant_code]}'")
        if r.scenario_id not in sit_form:
            D["resp_situacion_invalida"].append(f"{r.participant_code} / {r.scenario_id}: situación inexistente")
        elif r.participant_code in form_part and form_part[r.participant_code] not in sit_form[r.scenario_id]:
            D["resp_situacion_invalida"].append(f"{r.participant_code} / {r.scenario_id}: la situación es del formulario {cf.etiqueta(sit_form[r.scenario_id])} y el participante usó el {form_part[r.participant_code]}")
    con_texto = {(r.participant_code, r.scenario_id) for r in resp.itertuples() if r.text}
    codigos_resp = set(resp["participant_code"])
    # ---- conciliación por participante transcrito
    n_transcritos = 0
    for p in part.itertuples():
        if p.estado != "Transcrito":
            continue
        n_transcritos += 1
        if p.codigo not in codigos_resp:
            D["transcrito_sin_respuestas"].append(f"{p.codigo} (formulario {p.form}): Transcrito pero sin ninguna fila en {Path(a.respuestas).name}")
            continue
        for s in sorted(por_form.get(p.form, set())):
            tiene = (p.codigo, s) in con_texto
            es_blanco = s in blancos.get(p.codigo, set())
            if not tiene and not es_blanco:
                D["ausente"].append(f"{p.codigo} / {s}: no hay respuesta y NO figura en Blancos")
            if tiene and es_blanco:
                D["blanco_con_respuesta"].append(f"{p.codigo} / {s}: figura como blanco pero SÍ tiene respuesta")

    # ---- cobertura real por intención
    reales = {}
    for (c, s) in con_texto:
        if c in form_part and estado.get(c) == "Transcrito" and s in sit_intent and form_part[c] in sit_form[s]:
            reales[sit_intent[s]] = reales.get(sit_intent[s], 0) + 1
    intents = sorted(set(cat["intent_esperada"]))
    cob = {i: reales.get(i, 0) for i in intents}
    bajo_min = [i for i, n in cob.items() if n < params["minimo"]]
    bajo_meta = [i for i, n in cob.items() if params["minimo"] <= n < params["meta"]]

    # ---- reporte
    nombres = {"ausente": "Respuesta ausente que NO figura como blanco", "blanco_con_respuesta": "Blanco que SÍ tiene respuesta",
               "transcrito_sin_respuestas": "Participante Transcrito sin respuestas", "resp_sin_participante": "Respuestas de participantes que no están en el seguimiento",
               "resp_no_transcrito": "Respuestas de participantes que no están en estado Transcrito", "blanco_invalido": "Blancos inválidos",
               "blanco_duplicado": "Blancos repetidos", "resp_situacion_invalida": "Respuestas a situaciones inválidas",
               "estado_invalido": "Estados inválidos", "datos_incompletos": "Datos incompletos para exportar",
               "blancos_distintos": "Blancos del seguimiento distintos de los derivados del libro de transcripción"}
    D["blancos_distintos"] = dif_blancos
    n_disc = sum(len(v) for v in D.values())
    L = [f"CONCILIACIÓN DEL SEGUIMIENTO — {seg_path.name}", "",
         f"Participantes en el seguimiento: {len(part)} | Transcritos: {n_transcritos} | blancos registrados: {len(bl)} | filas de respuestas: {len(resp)} ({len(con_texto)} con texto)",
         f"Parámetros del seguimiento: meta {params['meta']} frases por intención, mínimo {params['minimo']}, participantes transcritos mínimos {params['min_part']}", ""]
    for k, nombre in nombres.items():
        L.append(f"[{'OK ' if not D[k] else 'REVISAR'}] {nombre}: {len(D[k])}")
        L += [f"        - {x}" for x in D[k][:25]]
        if len(D[k]) > 25:
            L.append(f"        ... y {len(D[k]) - 25} más")
    L += ["", f"Cobertura real: {len(intents) - len(bajo_min) - len(bajo_meta)} intenciones con la meta, {len(bajo_meta)} con el mínimo, {len(bajo_min)} por debajo del mínimo"
          + (f" -> {bajo_min}" if bajo_min else "")]
    listo = n_transcritos >= params["min_part"] and not bajo_min and n_disc == 0
    L.append(f"¿Listo para la Parte B? {'SÍ' if listo else 'NO'} (transcritos {n_transcritos}/{params['min_part']}, "
             f"intenciones bajo el mínimo: {len(bajo_min)}, discrepancias: {n_disc})")
    # ---- exportación sin ocupación
    exp = part[part["estado"] == "Transcrito"][["codigo", "form", "edad", "vive", "tramite"]].sort_values("codigo")
    exp.columns = ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"]
    out = Path(a.out_participantes)
    out.parent.mkdir(parents=True, exist_ok=True)
    exp.to_csv(out, index=False, encoding="utf-8")
    L += ["", f"Exportados {len(exp)} participantes Transcritos a {out} (sin ocupación, fecha ni observaciones)."]
    log = Path(a.log_dir) / "conciliacion_reporte.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    sys.exit(0 if n_disc == 0 else 1)


if __name__ == "__main__":
    main()
