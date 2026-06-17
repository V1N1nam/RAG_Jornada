import os
from datetime import datetime

from langchain_openai import ChatOpenAI

CHAT_MODEL = "gpt-4.1-mini"
_SUPPORT_PHONE_DISPLAY = os.getenv("SUPPORT_PHONE_DISPLAY", "00 00000-0000")


def _periodo_do_dia() -> str:
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    return "Boa noite"


def _call_llm(system_instruction: str, user_input: str) -> str:
    llm = ChatOpenAI(model=CHAT_MODEL)

    prompt = f"""
{system_instruction}

Entrada do usuário:
{user_input}
""".strip()

    response = llm.invoke(prompt)
    return response.content.strip()


def generate_greeting(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Gere uma saudação curta, educada, natural e profissional.
Explique brevemente que pode ajudar com:
- problemas no equipamento
- dúvidas técnicas
- encaminhamento para atendente

A resposta deve parecer conversa natural de WhatsApp.
Não use listas.
Não invente informações técnicas.
"""
    return _call_llm(instruction, user_input)


def generate_loja_confirmation_ask(loja_id: int, returning: bool = False) -> str:
    saudacao = _periodo_do_dia()
    if returning:
        return (
            f"{saudacao}! Bem-vindo de volta! 👋\n\n"
            f"Da última vez você estava na unidade *{loja_id}*. Ainda é essa mesma?\n"
            "_(Responda *sim* ou envie o novo número)_"
        )
    return (
        f"{saudacao}! No seu último acesso identificamos a unidade *{loja_id}*. "
        f"Ainda é essa mesma? _(Responda *sim* ou envie o novo número)_"
    )


def generate_greeting_ask_loja(user_input: str) -> str:
    periodo = _periodo_do_dia()
    instruction = f"""
Você é um assistente de suporte técnico para sistemas de refrigeração.

Cumprimente o usuário com "{periodo}!" de forma curta e natural.
Em seguida, peça o número de identificação da unidade.

Exemplo: "{periodo}! Para te ajudar melhor, qual é o número da sua unidade?"

Máximo 2 linhas. Tom de WhatsApp. Não invente informações.
"""
    return _call_llm(instruction, user_input)


def generate_loja_confirmation_menu(loja_id: int) -> str:
    return (
        f"Perfeito! Unidade *{loja_id}* identificada. ✅\n\n"
        "Como posso te ajudar hoje?\n\n"
        "*1* — Verificar alarmes ativos\n"
        "*2* — Tirar uma dúvida técnica\n"
        "*3* — Falar com um técnico profissional\n"
        "*4* — Visualizar dashboard da unidade"
    )


def generate_problem_request(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Peça para o usuário descrever melhor o problema.
A resposta deve ser curta, natural, educada e conversacional.
Não use listas.
"""
    return _call_llm(instruction, user_input)


def generate_human_handoff(user_input: str, protocolo: str = "") -> str:
    protocolo_linha = f"*Protocolo:* #{protocolo}\n\n" if protocolo else ""
    return (
        "Vou acionar nossa equipe técnica agora! 🛠️\n\n"
        f"{protocolo_linha}"
        "Em breve um especialista vai entrar em contato com você.\n\n"
        f"Se preferir, você também pode chamar diretamente no WhatsApp:\n"
        f"👉 *{_SUPPORT_PHONE_DISPLAY}*"
    )


def generate_awaiting_human_response() -> str:
    return (
        "Você já está na fila de atendimento! Nossa equipe técnica vai entrar em contato em breve. 🛠️\n\n"
        f"Para contato direto: *{_SUPPORT_PHONE_DISPLAY}*"
    )


def generate_closing(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Gere uma resposta de encerramento curta, simpática, natural e profissional.
A resposta deve demonstrar disponibilidade para futuras dúvidas.
"""
    return _call_llm(instruction, user_input)


def generate_fallback(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Gere uma resposta curta e natural pedindo mais detalhes para entender melhor a necessidade do usuário.
Não use listas.
"""
    return _call_llm(instruction, user_input)