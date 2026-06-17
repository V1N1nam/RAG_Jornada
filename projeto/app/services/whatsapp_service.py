import os
import requests

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "rag-evolution-key")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "rag-bot")

# Número do time de suporte técnico (formato internacional sem espaços/traços para a API)
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "")
SUPPORT_PHONE_DISPLAY = os.getenv("SUPPORT_PHONE_DISPLAY", "00 00000-0000")


def send_message(phone: str, text: str) -> bool:
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": phone, "text": text}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[send_message] status={resp.status_code} body={resp.text[:300]}", flush=True)
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[send_message] exception={e}", flush=True)
        return False


def notificar_tecnico(
    customer_phone: str,
    loja_id: int | None,
    loja_nome: str,
    resumo_alarmes: str,
    ultima_mensagem: str,
    protocolo: str = "",
) -> bool:
    """
    Envia mensagem de contexto para o número de suporte técnico quando um chamado é aberto.
    Retorna False silenciosamente se SUPPORT_PHONE não estiver configurado.
    """
    if not SUPPORT_PHONE:
        print("[notificar_tecnico] SUPPORT_PHONE não configurado, pulando notificação.", flush=True)
        return False

    unidade = f"{loja_id}" + (f" — {loja_nome}" if loja_nome else "") if loja_id else "não informada"

    linhas = ["🔔 *Novo chamado de suporte técnico*", ""]
    if protocolo:
        linhas.append(f"🔑 *Protocolo:* #{protocolo}")
    linhas += [
        f"📱 *Cliente:* {customer_phone}",
        f"📍 *Unidade:* {unidade}",
    ]
    if resumo_alarmes:
        linhas.append(f"⚠️ *Alarmes:* {resumo_alarmes}")
    if ultima_mensagem:
        msg = ultima_mensagem[:200] + "..." if len(ultima_mensagem) > 200 else ultima_mensagem
        linhas.append(f"💬 *Solicitação:* {msg}")
    linhas.append("")
    linhas.append("_Aberto via chatbot de suporte_")

    return send_message(SUPPORT_PHONE, "\n".join(linhas))
