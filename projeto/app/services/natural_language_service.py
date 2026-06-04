from langchain_openai import ChatOpenAI

CHAT_MODEL = "gpt-4.1-mini"


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


def generate_greeting_ask_loja(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Responda à saudação do usuário de forma curta, educada e natural (máximo 1 linha).
Em seguida, peça o número de identificação da unidade para poder consultar as informações.

Exemplo de tom: "Olá! Para te ajudar melhor, qual é o número da sua unidade?"

Responda em tom de WhatsApp, máximo 2 linhas. Não invente informações.
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


def generate_human_handoff(user_input: str) -> str:
    instruction = """
Você é um assistente de suporte técnico para sistemas de refrigeração.

Informe de forma natural e educada que o atendimento pode ser encaminhado para um atendente humano.
A resposta deve ser curta e profissional.
"""
    return _call_llm(instruction, user_input)


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