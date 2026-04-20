from langchain_openai import ChatOpenAI

CHAT_MODEL = "gpt-4.1-mini"


def build_prompt(context: str, question: str) -> str:
    return f"""
Você é um assistente técnico de refrigeração.

Regras:
- Responda apenas com base no contexto fornecido.
- Não invente informações.
- Se o contexto não for suficiente, diga que são necessárias mais informações.
- Responda de forma objetiva e técnica.

Contexto:
{context}

Pergunta do usuário:
{question}
""".strip()


def ask_llm(context: str, question: str) -> str:
    llm = ChatOpenAI(model=CHAT_MODEL)
    prompt = build_prompt(context, question)
    response = llm.invoke(prompt)
    return response.content