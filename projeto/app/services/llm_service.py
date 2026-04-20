from langchain_openai import ChatOpenAI

CHAT_MODEL = "gpt-4.1-mini"


def build_prompt(context: str, question: str) -> str:
    return f"""
Você é um assistente técnico especializado em refrigeração.

Seu objetivo é responder de forma:
- técnica
- clara
- natural
- profissional
- fácil de entender em uma conversa de WhatsApp

Regras:
- Use apenas o contexto fornecido.
- Não invente informações.
- Se o contexto não for suficiente, diga isso claramente.
- Não responda em formato de lista, a menos que seja realmente necessário.
- Prefira linguagem fluida e natural.

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