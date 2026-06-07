import requests
from app.config import ML_API_BASE_URL

_NIVEL_INFO = {
    "critico":   {"label": "Crítico",   "icon": "🔴"},
    "alto":      {"label": "Alto",      "icon": "🟠"},
    "atencao":   {"label": "Atenção",   "icon": "🟡"},
    "normal":    {"label": "Normal",    "icon": "🟢"},
    "sem_dados": {"label": "Sem dados", "icon": "⚪"},
}

CRIT_CONFIG = {
    "C": {"label": "Crítica",  "color": "#ef4444"},
    "A": {"label": "Alta",     "color": "#f97316"},
    "M": {"label": "Média",    "color": "#eab308"},
    "B": {"label": "Baixa",    "color": "#3b82f6"},
    "I": {"label": "Info",     "color": "#6c757d"},
}

CRITICIDADE_LABEL = {
    "C": "Crítica", "A": "Alta", "M": "Média", "B": "Baixa", "I": "Info",
}


def _ml_get(path: str, timeout: int = 10) -> dict | None:
    try:
        resp = requests.get(f"{ML_API_BASE_URL}{path}", timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _get_alarmes() -> list:
    result = _ml_get("/api/alarmes")
    if result and result.get("status") == "ok":
        return result.get("dados", [])
    return []


def _fetch_telemetria_features(dispositivo_id: int) -> dict | None:
    result = _ml_get(f"/api/telemetria/{dispositivo_id}", timeout=8)
    if result and result.get("status") == "ok":
        return result.get("features") or {}
    return None


def _calcular_risco(feats: dict | None) -> dict:
    if not feats:
        return {"nivel": "sem_dados", "score": 0, "motivos": []}

    motivos = []
    score = 0

    amp = float(feats.get("temp_amplitude") or 0)
    tendencia = float(feats.get("temp_tendencia") or 0)

    if amp > 10:
        motivos.append(f"Alta variação de temp ({amp:.1f}°C)")
        score += 1

    if tendencia > 0.5:
        motivos.append(f"Temperatura subindo ({tendencia:.2f}°C/leitura)")
        score += 2
    elif tendencia > 0.2:
        motivos.append(f"Temperatura em elevação ({tendencia:.2f}°C/leitura)")
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
    # Tenta /api/dashboard/risco primeiro (quando disponível na ML API)
    risco_data = _ml_get("/api/dashboard/risco")
    if risco_data and risco_data.get("status") == "ok":
        dados = risco_data.get("dados", [])
        resultado = []
        for d in dados:
            if d.get("loja_id") != loja_id:
                continue
            nivel = d.get("risco_nivel", "sem_dados")
            resultado.append({
                "dispositivoId": d.get("dispositivo_id"),
                "dispositivoNm": d.get("tag", str(d.get("dispositivo_id", ""))),
                "criticidade":   d.get("criticidade", "I"),
                "risco_nivel":   nivel,
                "risco_label":   _NIVEL_INFO.get(nivel, {}).get("label", nivel),
                "risco_icon":    _NIVEL_INFO.get(nivel, {}).get("icon", ""),
                "risco_score":   d.get("risco_score", 0),
                "risco_motivos": d.get("risco_motivos", []),
            })
            if len(resultado) >= max_devices:
                break
        if resultado:
            return resultado

    # Fallback: /api/alarmes + /api/telemetria/<id>
    todos = _get_alarmes()
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
        feats = _fetch_telemetria_features(d["dispositivoId"])
        risco = _calcular_risco(feats)
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
    todos = _get_alarmes()
    alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]

    if not alarmes_loja:
        return f"Nenhum dado encontrado para a loja {loja_id}."

    loja_nome = alarmes_loja[0].get("lojaNm", "")
    contagem: dict[str, int] = {}
    sem_tratativa = 0
    for a in alarmes_loja:
        crit = a.get("criticidade", "I")
        contagem[crit] = contagem.get(crit, 0) + 1
        if a.get("eventoDhCad") is None:
            sem_tratativa += 1

    lines = [f"=== DADOS DA LOJA {loja_id} ==="]
    if loja_nome:
        lines.append(f"Nome: {loja_nome}")
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


def buscar_alarmes_loja(loja_id: int) -> dict:
    todos = _get_alarmes()
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
