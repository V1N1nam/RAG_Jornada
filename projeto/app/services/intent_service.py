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


def detect_confirmation(text: str) -> bool | None:
    """Retorna True para sim, False para não, None se não reconhecido."""
    t = normalize_text(text)
    if t in ("sim", "s", "yes", "isso", "correto", "certo", "é", "é essa", "é essa mesmo", "confirmo"):
        return True
    if t in ("não", "nao", "n", "no", "errado", "errada", "outro", "outra", "trocar", "mudar"):
        return False
    return None


def detect_meta_request(text: str) -> str | None:
    """Detecta pedidos de menu ou dashboard que funcionam em qualquer estado."""
    t = normalize_text(text)
    if "menu" in t or "opç" in t or "opc" in t or "voltar" in t or "opções" in t:
        return "menu"
    if "dashboard" in t or "dash" in t or "painel" in t:
        return "dash"
    return None


def detect_menu_choice(text: str) -> str | None:
    t = normalize_text(text)

    if t in ("1", "1️⃣") or "alarme" in t:
        return "alarmes"

    if t in ("2", "2️⃣") or "dúvida" in t or "duvida" in t or "pergunta" in t or "duvid" in t:
        return "duvida"

    if t in ("3", "3️⃣") or "técnico" in t or "tecnico" in t or "atendente" in t or "humano" in t or "pessoa" in t:
        return "tecnico"

    if t in ("4", "4️⃣") or "dashboard" in t or "dash" in t or "visualizar" in t or "painel" in t:
        return "dash"

    return None