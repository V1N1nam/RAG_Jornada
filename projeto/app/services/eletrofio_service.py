import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon"
TIMEOUT = 30

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
