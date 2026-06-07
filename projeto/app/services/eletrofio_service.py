import requests
import urllib3
import numpy as np

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon"
TIMEOUT = 30

_NIVEL_INFO = {
    "critico":   {"label": "Crítico",   "icon": "🔴"},
    "alto":      {"label": "Alto",      "icon": "🟠"},
    "atencao":   {"label": "Atenção",   "icon": "🟡"},
    "normal":    {"label": "Normal",    "icon": "🟢"},
    "sem_dados": {"label": "Sem dados", "icon": "⚪"},
}

CRITICIDADE_LABEL = {
    "C": "Crítica",
    "A": "Alta",
    "M": "Média",
    "B": "Baixa",
    "I": "Info",
}


def _get(params: dict):
    resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT, verify=False)
    resp.raise_for_status()
    return resp.json()


def _fetch_telemetria(dispositivo_id: int) -> dict | None:
    try:
        resp = requests.get(
            BASE_URL,
            params={"route": "telemetria", "dispositivoId": dispositivo_id},
            timeout=8,
            verify=False,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _calcular_risco(raw: dict | None) -> dict:
    if not raw or not raw.get("datasets"):
        return {"nivel": "sem_dados", "score": 0, "motivos": []}

    labels = raw.get("labels", [])
    if len(labels) < 5:
        return {"nivel": "sem_dados", "score": 0, "motivos": []}

    KEY_MAP = {
        "Temperatura Ambiente":  "temp",
        "Setpoint Ambiente":     "setpoint",
        "Status Degelo":         "degelo",
        "L1 - Superaquecimento": "superaquecimento",
    }
    series = {}
    for ds in raw["datasets"]:
        lbl = ds.get("label", "")
        if lbl in KEY_MAP:
            vals = [v for v in ds.get("values", []) if v is not None]
            if len(vals) >= 5:
                series[KEY_MAP[lbl]] = np.array(vals, dtype=float)

    motivos = []
    score = 0

    temp = series.get("temp")
    setpoint = series.get("setpoint")
    if temp is not None:
        amp = float(np.nanmax(temp) - np.nanmin(temp))
        if setpoint is not None:
            min_len = min(len(temp), len(setpoint))
            erro = float(np.nanmean(temp[:min_len] - setpoint[:min_len]))
            if erro > 5:
                motivos.append(f"Temp {erro:+.1f}°C acima do setpoint")
                score += 2
            elif erro > 2:
                motivos.append(f"Temp {erro:+.1f}°C acima do setpoint")
                score += 1
        if amp > 10:
            motivos.append(f"Alta variação de temp ({amp:.1f}°C)")
            score += 1

    degelo = series.get("degelo")
    if degelo is not None:
        bin_deg = (degelo > 0.5).astype(int)
        ciclos = int(np.sum(np.diff(bin_deg, prepend=0) == 1))
        if ciclos > 5:
            motivos.append(f"Ciclos de degelo excessivos ({ciclos})")
            score += 1

    sup = series.get("superaquecimento")
    if sup is not None:
        sup_mean = float(np.nanmean(sup))
        if sup_mean > 20:
            motivos.append(f"Superaquecimento elevado ({sup_mean:.1f}°C)")
            score += 1

    if score >= 3:
        nivel = "critico"
    elif score == 2:
        nivel = "alto"
    elif score == 1:
        nivel = "atencao"
    else:
        nivel = "normal"

    return {"nivel": nivel, "score": score, "motivos": motivos}


def analisar_risco_loja(loja_id: int, max_devices: int = 6) -> list:
    try:
        todos = _get({"route": "alarmes"})
    except Exception:
        return []

    alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]
    if not alarmes_loja:
        return []

    ordem_crit = {"C": 0, "A": 1, "M": 2, "B": 3, "I": 4}
    alarmes_loja.sort(key=lambda x: ordem_crit.get(x.get("criticidade", "I"), 9))

    seen = set()
    devices = []
    for a in alarmes_loja:
        did = a.get("dispositivoId")
        if did and did not in seen:
            seen.add(did)
            devices.append({
                "dispositivoId": did,
                "dispositivoNm": a.get("dispositivoNm", str(did)),
                "criticidade":   a.get("criticidade", "I"),
            })
        if len(devices) >= max_devices:
            break

    resultado = []
    for d in devices:
        raw = _fetch_telemetria(d["dispositivoId"])
        risco = _calcular_risco(raw)
        nivel = risco["nivel"]
        resultado.append({
            "dispositivoId": d["dispositivoId"],
            "dispositivoNm": d["dispositivoNm"],
            "criticidade":   d["criticidade"],
            "risco_nivel":   nivel,
            "risco_label":   _NIVEL_INFO.get(nivel, {}).get("label", nivel),
            "risco_icon":    _NIVEL_INFO.get(nivel, {}).get("icon", ""),
            "risco_score":   risco["score"],
            "risco_motivos": risco["motivos"],
        })

    return resultado


def buscar_contexto_loja(loja_id: int) -> str:
    try:
        alarmes = _get({"route": "alarmes"})
    except Exception as e:
        return f"Não foi possível obter alarmes da loja {loja_id}: {e}"

    try:
        unidades = _get({"route": "unidades"})
    except Exception:
        unidades = []

    alarmes_loja = [a for a in alarmes if a.get("lojaId") == loja_id]
    unidade = next((u for u in unidades if u.get("lojaId") == loja_id), None)

    if not alarmes_loja and not unidade:
        return f"Nenhum dado encontrado para a loja {loja_id}."

    lines = [f"=== DADOS DA LOJA {loja_id} ==="]

    loja_nome = ""
    if alarmes_loja:
        loja_nome = alarmes_loja[0].get("lojaNm", "")
    if unidade:
        loja_nome = unidade.get("lojaNm", loja_nome)

    if loja_nome:
        lines.append(f"Nome: {loja_nome}")

    if not alarmes_loja:
        lines.append("Nenhum alarme ativo para esta loja.")
        return "\n".join(lines)

    contagem: dict[str, int] = {}
    sem_tratativa = 0
    for a in alarmes_loja:
        crit = a.get("criticidade", "I")
        contagem[crit] = contagem.get(crit, 0) + 1
        if a.get("eventoDhCad") is None:
            sem_tratativa += 1

    lines.append(f"Total de alarmes ativos: {len(alarmes_loja)}")
    lines.append("Alarmes por criticidade:")
    for crit in ["C", "A", "M", "B", "I"]:
        if crit in contagem:
            lines.append(f"  - {CRITICIDADE_LABEL[crit]}: {contagem[crit]}")
    lines.append(f"Alarmes sem tratativa: {sem_tratativa}")

    criticos = [a for a in alarmes_loja if a.get("criticidade") in ("C", "A")]
    if criticos:
        lines.append("Alarmes críticos e altos:")
        for a in criticos[:10]:
            crit = a.get("criticidade", "I")
            dispositivo = a.get("dispositivoNm", "N/A")
            descricao = a.get("alarmeDesc", "N/A")
            tempo = a.get("tempo", "N/A")
            lines.append(
                f"  [{CRITICIDADE_LABEL[crit]}] {dispositivo}: {descricao} (tempo: {tempo})"
            )

    return "\n".join(lines)


CRIT_CONFIG = {
    "C": {"label": "Crítica",  "color": "#ef4444"},
    "A": {"label": "Alta",     "color": "#f97316"},
    "M": {"label": "Média",    "color": "#eab308"},
    "B": {"label": "Baixa",    "color": "#3b82f6"},
    "I": {"label": "Info",     "color": "#6c757d"},
}


def buscar_alarmes_loja(loja_id: int) -> dict:
    """Retorna dados estruturados de alarmes para o dashboard da loja."""
    try:
        todos = _get({"route": "alarmes"})
    except Exception:
        todos = []

    alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]

    loja_nome = alarmes_loja[0].get("lojaNm", f"Unidade {loja_id}") if alarmes_loja else f"Unidade {loja_id}"

    por_crit = {k: {"count": 0, "label": v["label"], "color": v["color"]} for k, v in CRIT_CONFIG.items()}
    sem_tratativa = 0
    linhas = []

    for a in alarmes_loja:
        crit = a.get("criticidade", "I")
        if crit in por_crit:
            por_crit[crit]["count"] += 1
        if not a.get("eventoDhCad"):
            sem_tratativa += 1
        linhas.append({
            "criticidade":   crit,
            "crit_label":    CRIT_CONFIG.get(crit, CRIT_CONFIG["I"])["label"],
            "tag":           a.get("dispositivoNm", ""),
            "alarme_desc":   a.get("alarmeDesc", ""),
            "tempo":         a.get("tempo", ""),
            "sem_tratativa": not a.get("eventoDhCad"),
        })

    ordem = {"C": 0, "A": 1, "M": 2, "B": 3, "I": 4}
    linhas.sort(key=lambda x: ordem.get(x["criticidade"], 9))

    return {
        "loja_id":   loja_id,
        "loja_nome": loja_nome,
        "stats": {
            "total":         len(alarmes_loja),
            "por_crit":      por_crit,
            "sem_tratativa": sem_tratativa,
        },
        "alarmes": linhas,
    }
