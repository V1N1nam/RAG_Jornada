def normalize_text(text: str) -> str:
    return text.strip().lower()


def detect_intent(text: str) -> str:
    text = normalize_text(text)

    greetings = ["oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"]
    thanks = ["obrigado", "obrigada", "valeu", "fechou", "ta bom", "tá bom", "ok"]
    human = ["atendente", "humano", "pessoa", "suporte humano"]

    if any(word in text for word in greetings):
        return "greeting"

    if any(word in text for word in thanks):
        return "closing"

    if any(word in text for word in human):
        return "human"

    if "problema" in text or "falha" in text or "erro" in text:
        return "problem"

    return "question"