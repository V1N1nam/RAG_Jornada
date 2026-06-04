import re

from app.database.repositories.conversation_repository import (
    get_or_create_conversation,
    update_conversation_loja,
)
from app.services.conversation_service import (
    register_user_message,
    register_assistant_message,
    set_conversation_state,
)
from app.services.intent_service import detect_intent, detect_menu_choice, detect_meta_request, detect_confirmation
from app.services.rag_service import ask_question
from app.services.eletrofio_service import buscar_contexto_loja
from app.services.dashboard_service import generate_dash_link

from app.services.natural_language_service import (
    generate_greeting_ask_loja,
    generate_loja_confirmation_ask,
    generate_loja_confirmation_menu,
    generate_problem_request,
    generate_human_handoff,
    generate_closing,
    generate_fallback,
)

_LOJA_RE = re.compile(r'(?:unidade|loja|id|cod(?:igo)?)[^\d]*(\d{2,6})', re.IGNORECASE)
_PLAIN_NUMBER_RE = re.compile(r'^\s*(\d{2,6})\s*$')

_ASK_LOJA_AGAIN = (
    "Não consegui identificar o número da unidade. "
    "Por favor, envie só o número (ex: *1234*)."
)


def _extrair_loja_id(text: str) -> int | None:
    m = _LOJA_RE.search(text)
    if m:
        return int(m.group(1))
    m = _PLAIN_NUMBER_RE.match(text)
    if m:
        return int(m.group(1))
    return None


def handle_chat_message(phone: str, text: str, loja_id: int | None = None) -> dict:
    conversation = register_user_message(phone, text)
    current_state = conversation["current_state"]
    intent = detect_intent(text)

    # loja_id da conversa salva (pode ser sobrescrito abaixo)
    if loja_id is None:
        loja_id = conversation.get("loja_id")

    # ── Intents globais (qualquer estado) ────────────────────────────────────

    if intent == "closing":
        answer = generate_closing(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "closed", "closing")
        return {"phone": phone, "state": "closed", "intent": "closing", "answer": answer}

    if intent == "human":
        answer = generate_human_handoff(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_human", "human")
        return {"phone": phone, "state": "awaiting_human", "intent": "human", "answer": answer}

    # Meta-requests: menu ou dash funcionam em qualquer estado de suporte
    if current_state not in ("new", "closed", "awaiting_loja_id", "awaiting_loja_confirmation"):
        meta = detect_meta_request(text)
        if meta == "menu":
            answer = (
                generate_loja_confirmation_menu(loja_id)
                if loja_id
                else "Por favor, informe o número da sua unidade primeiro."
            )
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_menu_choice", "menu_requested")
            return {"phone": phone, "state": "awaiting_menu_choice", "intent": "menu_requested", "answer": answer, "loja_id": loja_id}

        if meta == "dash":
            if loja_id:
                link = generate_dash_link(loja_id)
                answer = f"Aqui está o dashboard da unidade *{loja_id}*:\n{link}\n\n_Válido por 1 hora._"
            else:
                answer = "Não encontrei a unidade vinculada. Informe o número da unidade primeiro."
            register_assistant_message(conversation["id"], answer)
            return {"phone": phone, "state": current_state, "intent": "dash", "answer": answer, "loja_id": loja_id}

    # ── Onboarding ───────────────────────────────────────────────────────────

    if current_state in ("new", "closed"):
        if loja_id:
            # Já tem loja salva — pede confirmação
            answer = generate_loja_confirmation_ask(loja_id)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_loja_confirmation", "greeting")
            return {"phone": phone, "state": "awaiting_loja_confirmation", "intent": "greeting", "answer": answer, "loja_id": loja_id}
        # Sem loja salva — pede o ID
        answer = generate_greeting_ask_loja(text)
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "awaiting_loja_id", "greeting")
        return {"phone": phone, "state": "awaiting_loja_id", "intent": "greeting", "answer": answer}

    if current_state == "awaiting_loja_confirmation":
        confirmed = detect_confirmation(text)
        loja_id_extraido = _extrair_loja_id(text)

        if loja_id_extraido:
            # Mandou um número novo direto
            loja_id = loja_id_extraido
            update_conversation_loja(phone, loja_id)
            answer = generate_loja_confirmation_menu(loja_id)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_menu_choice", "loja_confirmed")
            return {"phone": phone, "state": "awaiting_menu_choice", "intent": "loja_confirmed", "answer": answer, "loja_id": loja_id}

        if confirmed is True:
            answer = generate_loja_confirmation_menu(loja_id)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_menu_choice", "loja_confirmed")
            return {"phone": phone, "state": "awaiting_menu_choice", "intent": "loja_confirmed", "answer": answer, "loja_id": loja_id}

        if confirmed is False:
            answer = "Tudo bem! Qual é o número correto da sua unidade?"
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_loja_id", "loja_change")
            return {"phone": phone, "state": "awaiting_loja_id", "intent": "loja_change", "answer": answer}

        # Resposta não reconhecida — repete a pergunta
        answer = generate_loja_confirmation_ask(loja_id)
        register_assistant_message(conversation["id"], answer)
        return {"phone": phone, "state": "awaiting_loja_confirmation", "intent": "confirmation_retry", "answer": answer, "loja_id": loja_id}

    if current_state == "awaiting_loja_id":
        loja_id_extraido = _extrair_loja_id(text)
        if loja_id_extraido:
            loja_id = loja_id_extraido
            update_conversation_loja(phone, loja_id)
            answer = generate_loja_confirmation_menu(loja_id)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_menu_choice", "loja_confirmed")
            return {
                "phone": phone,
                "state": "awaiting_menu_choice",
                "intent": "loja_confirmed",
                "answer": answer,
                "loja_id": loja_id,
            }
        # Não encontrou loja_id — pede novamente
        register_assistant_message(conversation["id"], _ASK_LOJA_AGAIN)
        return {
            "phone": phone,
            "state": "awaiting_loja_id",
            "intent": "loja_not_found",
            "answer": _ASK_LOJA_AGAIN,
        }

    if current_state == "awaiting_menu_choice":
        choice = detect_menu_choice(text)

        if choice == "alarmes":
            eletrofio_ctx = buscar_contexto_loja(loja_id) if loja_id else ""
            rag_result = ask_question("quais alarmes estão ativos", k=3, extra_context=eletrofio_ctx, mode="alarmes")
            answer = rag_result["answer"]
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "in_support", "alarmes")
            return {
                "phone": phone,
                "state": "in_support",
                "intent": "alarmes",
                "answer": answer,
                "sources": rag_result["sources"],
                "loja_id": loja_id,
            }

        if choice == "duvida":
            answer = generate_problem_request(text)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_problem_description", "duvida")
            return {
                "phone": phone,
                "state": "awaiting_problem_description",
                "intent": "duvida",
                "answer": answer,
            }

        if choice == "tecnico":
            answer = generate_human_handoff(text)
            register_assistant_message(conversation["id"], answer)
            set_conversation_state(phone, "awaiting_human", "human")
            return {"phone": phone, "state": "awaiting_human", "intent": "human", "answer": answer}

        if choice == "dash":
            if loja_id:
                link = generate_dash_link(loja_id)
                answer = (
                    f"Aqui está o link do dashboard da unidade *{loja_id}*:\n{link}\n\n"
                    "_O link é válido por 1 hora._"
                )
            else:
                answer = "Não encontrei o ID da unidade. Por favor, informe o número da unidade novamente."
            register_assistant_message(conversation["id"], answer)
            return {
                "phone": phone,
                "state": "awaiting_menu_choice",
                "intent": "dash",
                "answer": answer,
                "loja_id": loja_id,
            }

        # Opção não reconhecida — reexibe o menu
        answer = (
            generate_loja_confirmation_menu(loja_id)
            if loja_id
            else "Por favor, escolha uma opção: *1* Alarmes, *2* Dúvida, *3* Técnico."
        )
        register_assistant_message(conversation["id"], answer)
        return {
            "phone": phone,
            "state": "awaiting_menu_choice",
            "intent": "menu_repeat",
            "answer": answer,
        }

    # ── Suporte ativo ────────────────────────────────────────────────────────

    eletrofio_ctx = buscar_contexto_loja(loja_id) if loja_id else ""

    if current_state == "awaiting_problem_description":
        rag_result = ask_question(text, k=3, extra_context=eletrofio_ctx)
        answer = rag_result["answer"]
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "in_support", "problem_description")
        return {
            "phone": phone,
            "state": "in_support",
            "intent": "problem_description",
            "answer": answer,
            "sources": rag_result["sources"],
            "context": rag_result["context"],
            "loja_id": loja_id,
        }

    if intent in ("question", "problem") or current_state == "in_support":
        rag_result = ask_question(text, k=3, extra_context=eletrofio_ctx)
        answer = rag_result["answer"]
        register_assistant_message(conversation["id"], answer)
        set_conversation_state(phone, "in_support", intent)
        return {
            "phone": phone,
            "state": "in_support",
            "intent": intent,
            "answer": answer,
            "sources": rag_result["sources"],
            "context": rag_result["context"],
            "loja_id": loja_id,
        }

    answer = generate_fallback(text)
    register_assistant_message(conversation["id"], answer)
    set_conversation_state(phone, "awaiting_menu_choice", "fallback")
    return {"phone": phone, "state": "awaiting_menu_choice", "intent": "fallback", "answer": answer}