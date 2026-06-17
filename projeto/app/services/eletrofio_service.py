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


def buscar_dashboard_loja(loja_id: int) -> dict:
    risco_raw      = _ml_get("/api/dashboard/risco")
    financeiro_raw = _ml_get("/api/dashboard/financeiro")
    saude_raw      = _ml_get("/api/dashboard/saude")
    modelo_raw     = _ml_get("/api/dashboard/modelo")

    # Risco — filtrado por loja_id
    risco_dados = (risco_raw or {}).get("dados", [])
    risco_loja  = [d for d in risco_dados if d.get("loja_id") == loja_id]
    loja_nome   = risco_loja[0].get("loja_nome", f"Unidade {loja_id}") if risco_loja else f"Unidade {loja_id}"

    # Financeiro — filtrado por loja_nome
    fin_raw     = ((financeiro_raw or {}).get("dados") or {})
    fin_devices = fin_raw.get("devices", [])
    fin_loja    = [d for d in fin_devices if d.get("loja_nome") == loja_nome]
    fin_totais  = {
        "exposicao_diaria": sum(d.get("exposicao_diaria", 0) for d in fin_loja),
        "economia_diaria":  sum(d.get("economia_diaria", 0) for d in fin_loja),
        "custo_intervencao": sum(d.get("custo_intervencao", 0) for d in fin_loja),
    }

    # Saúde — acha a entrada da loja pelo nome
    saude_dados   = ((saude_raw or {}).get("dados") or {})
    saude_por_loja = saude_dados.get("por_loja", [])
    saude_loja    = next((l for l in saude_por_loja if l.get("nome") == loja_nome), None)

    # Modelo — global, top 8 features
    modelo_dados = ((modelo_raw or {}).get("dados") or {})

    return {
        "loja_id":   loja_id,
        "loja_nome": loja_nome,
        "risco":     risco_loja,
        "financeiro": {"devices": fin_loja, "totais": fin_totais},
        "saude":     saude_loja,
        "modelo": {
            "feature_importance": modelo_dados.get("feature_importance", [])[:8],
            "modelo_info":        modelo_dados.get("modelo_info", {}),
            "score_medio":        modelo_dados.get("score_medio"),
            "n_devices_scored":   modelo_dados.get("n_devices_scored"),
        },
    }


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


# Sessão em memória: phone → lista ordenada de alarmes mostrados ao usuário.
# Permite resolver "digite 2 para detalhes" sem nova ida ao banco.
_alarmes_sessao: dict[str, list[dict]] = {}


def salvar_alarmes_sessao(phone: str, alarmes: list[dict]) -> None:
    _alarmes_sessao[phone] = alarmes


def buscar_alarme_por_indice(phone: str, index: int) -> dict | None:
    alarmes = _alarmes_sessao.get(phone, [])
    if 1 <= index <= len(alarmes):
        return alarmes[index - 1]
    return None


def formatar_lista_alarmes_numerada(loja_id: int) -> tuple[str, list[dict]]:
    """
    Retorna (contexto_para_llm, lista_alarmes).
    contexto_para_llm inclui resumo + lista numerada para o LLM.
    lista_alarmes é a ordem exata exibida (para resolução por índice).
    """
    todos = _get_alarmes()
    alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]
    if not alarmes_loja:
        return f"Nenhum alarme ativo para a unidade {loja_id}.", []

    loja_nome = alarmes_loja[0].get("lojaNm", "")

    contagem: dict[str, int] = {}
    sem_tratativa = 0
    for a in alarmes_loja:
        crit = a.get("criticidade", "I")
        contagem[crit] = contagem.get(crit, 0) + 1
        if a.get("eventoDhCad") is None:
            sem_tratativa += 1

    ordem_crit = {"C": 0, "A": 1, "M": 2, "B": 3, "I": 4}
    alarmes_loja.sort(key=lambda x: ordem_crit.get(x.get("criticidade", "I"), 9))
    alarmes_a_listar = alarmes_loja[:10]

    lines = [f"=== DADOS DA LOJA {loja_id} ==="]
    if loja_nome:
        lines.append(f"Nome: {loja_nome}")
    lines.append(f"Total de alarmes ativos: {len(alarmes_loja)}")
    lines.append(f"Alarmes sem tratativa: {sem_tratativa}")
    lines.append("Resumo por criticidade:")
    for crit in ["C", "A", "M", "B", "I"]:
        if crit in contagem:
            lines.append(f"  - {CRITICIDADE_LABEL[crit]}: {contagem[crit]}")

    lines.append(f"\nALARMES ATIVOS NUMERADOS (total: {len(alarmes_loja)}):")
    for i, a in enumerate(alarmes_a_listar, start=1):
        crit = a.get("criticidade", "I")
        desc = a.get("alarmeDesc", "N/A")
        disp = a.get("dispositivoNm", "N/A")
        tempo = a.get("tempo", "")
        tempo_str = f" — {tempo}" if tempo else ""
        lines.append(f"  {i}. [{CRITICIDADE_LABEL[crit]}] {disp}: {desc}{tempo_str}")

    if len(alarmes_loja) > 10:
        lines.append(f"  (+ {len(alarmes_loja) - 10} outros alarmes de menor criticidade)")

    return "\n".join(lines), alarmes_a_listar


def formatar_detalhe_alarme_selecionado(alarme: dict, indice: int) -> str:
    """Formata o contexto detalhado de um alarme selecionado pelo usuário."""
    crit = alarme.get("criticidade", "I")
    sem_trat = alarme.get("eventoDhCad") is None
    return "\n".join([
        f"=== ALARME SELECIONADO (#{indice}) ===",
        f"Dispositivo: {alarme.get('dispositivoNm', 'N/A')}",
        f"Descrição: {alarme.get('alarmeDesc', 'N/A')}",
        f"Criticidade: {CRITICIDADE_LABEL.get(crit, crit)}",
        f"Tempo ativo: {alarme.get('tempo', 'N/A')}",
        f"Tratativa pendente: {'Sim' if sem_trat else 'Não'}",
    ])


def buscar_resumo_chamado(loja_id: int) -> tuple[str, str]:
    """
    Retorna (loja_nome, resumo_alarmes) para compor a notificação ao técnico.
    Falha silenciosa: retorna strings vazias em caso de erro.
    """
    try:
        todos = _get_alarmes()
        alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]
        if not alarmes_loja:
            return f"Unidade {loja_id}", "sem alarmes ativos no momento"
        loja_nome = alarmes_loja[0].get("lojaNm", "")
        contagem: dict[str, int] = {}
        for a in alarmes_loja:
            crit = a.get("criticidade", "I")
            contagem[crit] = contagem.get(crit, 0) + 1
        partes = [
            f"{contagem[c]} {CRITICIDADE_LABEL[c].lower()}"
            for c in ["C", "A", "M", "B"]
            if c in contagem
        ]
        resumo = f"{len(alarmes_loja)} alarme(s) ativo(s): {', '.join(partes)}" if partes else f"{len(alarmes_loja)} alarme(s) ativo(s)"
        return loja_nome, resumo
    except Exception:
        return "", ""


def buscar_detalhes_alarme_especifico(loja_id: int, query: str) -> str:
    """
    Busca alarmes da loja que melhor correspondem ao texto do usuário.
    Retorna string formatada para uso como contexto no LLM.
    Pontuação: cada palavra com 3+ chars que aparece na descrição ou dispositivo conta 2pts.
    """
    todos = _get_alarmes()
    alarmes_loja = [a for a in todos if a.get("lojaId") == loja_id]
    if not alarmes_loja:
        return ""

    palavras = [w for w in query.lower().split() if len(w) >= 3]

    def _score(a: dict) -> int:
        desc = (a.get("alarmeDesc") or "").lower()
        disp = (a.get("dispositivoNm") or "").lower()
        return sum(2 for w in palavras if w in desc or w in disp)

    scored = sorted(
        ((s, a) for a in alarmes_loja if (s := _score(a)) > 0),
        key=lambda x: (-x[0], {"C": 0, "A": 1, "M": 2, "B": 3, "I": 4}.get(x[1].get("criticidade", "I"), 9)),
    )

    if not scored:
        return ""

    lines = ["=== DETALHES DO ALARME ==="]
    for _, a in scored[:3]:
        crit = a.get("criticidade", "I")
        sem_trat = a.get("eventoDhCad") is None
        lines += [
            f"Dispositivo: {a.get('dispositivoNm', 'N/A')}",
            f"Descrição do alarme: {a.get('alarmeDesc', 'N/A')}",
            f"Criticidade: {CRITICIDADE_LABEL.get(crit, crit)}",
            f"Tempo ativo: {a.get('tempo', 'N/A')}",
            f"Tratativa pendente: {'Sim' if sem_trat else 'Não'}",
            "",
        ]
    return "\n".join(lines).strip()


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
            "dispositivo_id": a.get("dispositivoId"),
            "loja_id":        loja_id,
            "loja_nome":      loja_nome,
            "criticidade":    crit,
            "crit_label":     CRIT_CONFIG.get(crit, CRIT_CONFIG["I"])["label"],
            "tag":            a.get("dispositivoNm", ""),
            "alarme_desc":    a.get("alarmeDesc", ""),
            "tempo":          a.get("tempo", ""),
            "sem_tratativa":  not a.get("eventoDhCad"),
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
