import os
from datetime import datetime

import requests as _requests
from flask import Flask, request, jsonify, render_template
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv

from app.services.chat_flow_service import handle_chat_message
from app.services.whatsapp_service import send_message
from app.services.eletrofio_service import buscar_alarmes_loja, buscar_dashboard_loja
from app.config import DASH_SECRET, ML_API_BASE_URL

load_dotenv(override=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
_token_serializer = URLSafeTimedSerializer(DASH_SECRET)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API RAG online"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    question = data.get("question", "").strip()
    loja_id_raw = data.get("loja_id")

    if not phone:
        return jsonify({"error": "Campo 'phone' é obrigatório"}), 400

    if not question:
        return jsonify({"error": "Campo 'question' é obrigatório"}), 400

    loja_id = int(loja_id_raw) if loja_id_raw is not None else None

    result = handle_chat_message(phone, question, loja_id=loja_id)
    return jsonify(result)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    event = data.get("event", "")
    if event != "messages.upsert":
        return jsonify({"status": "ignored"}), 200

    msg_data = data.get("data", {})
    key = msg_data.get("key", {})

    if key.get("fromMe"):
        return jsonify({"status": "ignored"}), 200

    remote_jid = key.get("remoteJid", "")
    if remote_jid.endswith("@g.us"):
        return jsonify({"status": "ignored"}), 200

    if remote_jid.endswith("@lid"):
        sender_pn = msg_data.get("senderPn") or msg_data.get("SenderPn") or ""
        send_to = sender_pn if sender_pn else remote_jid
    else:
        send_to = remote_jid

    phone = send_to.replace("@s.whatsapp.net", "").replace("@c.us", "").replace("@lid", "")
    if not phone:
        return jsonify({"status": "ignored"}), 200

    message_obj = msg_data.get("message", {})
    text = (
        message_obj.get("conversation")
        or message_obj.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return jsonify({"status": "ignored"}), 200

    result = handle_chat_message(phone, text)
    answer = result.get("answer", "")

    print(f"[webhook] phone={phone} state={result.get('state')} intent={result.get('intent')} answer={repr(answer[:80]) if answer else 'EMPTY'}", flush=True)

    if answer:
        ok = send_message(send_to, answer)
        print(f"[webhook] send_message to={send_to} -> {ok}", flush=True)
    else:
        print("[webhook] answer vazio, nada enviado", flush=True)

    return jsonify({"status": "ok"}), 200


@app.route("/dash")
def dash_loja():
    token = request.args.get("t", "")
    try:
        data = _token_serializer.loads(token, max_age=3600)
        loja_id = int(data["loja_id"])
    except SignatureExpired:
        return "<h2>Link expirado. Solicite um novo link pelo chat.</h2>", 403
    except (BadSignature, KeyError, Exception):
        return "<h2>Link inválido.</h2>", 403

    # Ping rápido na ML API (2 s) para saber se está acordada
    ml_api_ok = False
    try:
        _ping = _requests.get(f"{ML_API_BASE_URL}/api/health", timeout=2)
        ml_api_ok = _ping.status_code == 200
    except Exception:
        pass

    dashboard = buscar_dashboard_loja(loja_id)
    alarmes   = buscar_alarmes_loja(loja_id)

    return render_template(
        "loja_dash.html",
        loja_id=dashboard["loja_id"],
        loja_nome=dashboard["loja_nome"],
        risco=dashboard["risco"],
        financeiro=dashboard["financeiro"],
        saude=dashboard["saude"],
        modelo=dashboard["modelo"],
        stats=alarmes["stats"],
        alarmes=alarmes["alarmes"],
        atualizado=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        support_phone=os.getenv("SUPPORT_PHONE_DISPLAY", ""),
        ml_api_ok=ml_api_ok,
    )


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "api": True})


@app.route("/api/debug/loja/<int:loja_id>")
def debug_loja(loja_id):
    """Diagnóstico: mostra o que a ML API retorna e se os filtros batem."""
    result = {}

    # Alarmes
    try:
        r = _requests.get(f"{ML_API_BASE_URL}/api/alarmes", timeout=10)
        raw = r.json()
        todos = raw.get("dados", [])
        sample = todos[:3] if todos else []
        # detecta campo de loja no primeiro item
        primeiro = todos[0] if todos else {}
        campo_loja = next((k for k in ("lojaId", "loja_id", "loja", "lojaID") if k in primeiro), None)
        batem = [a for a in todos if str(a.get(campo_loja, "")) == str(loja_id)] if campo_loja else []
        result["alarmes"] = {
            "total_na_api": len(todos),
            "campo_loja_detectado": campo_loja,
            "loja_id_buscado": loja_id,
            "tipo_loja_id_buscado": type(loja_id).__name__,
            "valor_campo_no_primeiro": primeiro.get(campo_loja) if campo_loja else None,
            "tipo_valor_campo": type(primeiro.get(campo_loja)).__name__ if campo_loja else None,
            "batem_com_loja_id": len(batem),
            "sample_primeiros_3": sample,
        }
    except Exception as e:
        result["alarmes"] = {"erro": str(e)}

    # Risco
    try:
        r = _requests.get(f"{ML_API_BASE_URL}/api/dashboard/risco", timeout=10)
        raw = r.json()
        todos = raw.get("dados", [])
        primeiro = todos[0] if todos else {}
        campo_loja = next((k for k in ("loja_id", "lojaId", "loja", "lojaID") if k in primeiro), None)
        batem = [d for d in todos if str(d.get(campo_loja, "")) == str(loja_id)] if campo_loja else []
        result["risco"] = {
            "total_na_api": len(todos),
            "campo_loja_detectado": campo_loja,
            "batem_com_loja_id": len(batem),
            "valor_campo_no_primeiro": primeiro.get(campo_loja) if campo_loja else None,
            "tipo_valor_campo": type(primeiro.get(campo_loja)).__name__ if campo_loja else None,
            "sample_primeiro": {k: v for k, v in list(primeiro.items())[:12]} if primeiro else None,
        }
    except Exception as e:
        result["risco"] = {"erro": str(e)}

    return jsonify(result)


@app.route("/api/telemetria/<int:dispositivo_id>")
def proxy_telemetria(dispositivo_id):
    try:
        r = _requests.get(f"{ML_API_BASE_URL}/api/telemetria/{dispositivo_id}", timeout=8)
        return r.content, r.status_code, {"Content-Type": "application/json"}
    except Exception:
        return jsonify({"status": "ok", "dispositivo_id": dispositivo_id, "features": {}}), 200


@app.route("/api/predict/<int:dispositivo_id>")
def proxy_predict(dispositivo_id):
    try:
        r = _requests.get(f"{ML_API_BASE_URL}/api/predict/{dispositivo_id}", timeout=8)
        if r.status_code == 200:
            return r.content, 200, {"Content-Type": "application/json"}
    except Exception:
        pass
    return jsonify({"status": "ok", "risk_score": None, "anomaly": False, "anomaly_reason": None}), 200


@app.route("/api/abrir-chamado", methods=["POST"])
def proxy_abrir_chamado():
    try:
        r = _requests.post(f"{ML_API_BASE_URL}/api/abrir-chamado",
                          json=request.get_json(silent=True),
                          timeout=15)
        return r.content, r.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# ── Helpers de proxy ─────────────────────────────────────────────────────────

def _proxy_get(path: str, timeout: int = 15):
    try:
        r = _requests.get(f"{ML_API_BASE_URL}{path}", timeout=timeout)
        return r.content, r.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 502


def _proxy_post(path: str, timeout: int = 30):
    try:
        r = _requests.post(f"{ML_API_BASE_URL}{path}",
                           json=request.get_json(silent=True),
                           timeout=timeout)
        return r.content, r.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 502


def _proxy_patch(path: str, timeout: int = 15):
    try:
        r = _requests.patch(f"{ML_API_BASE_URL}{path}",
                            json=request.get_json(silent=True),
                            timeout=timeout)
        return r.content, r.status_code, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 502


# ── Admin / Pipeline ─────────────────────────────────────────────────────────

@app.route("/api/admin/coletar", methods=["POST"])
def admin_coletar():
    return _proxy_post("/api/admin/coletar", timeout=60)


@app.route("/api/admin/treinar", methods=["POST"])
def admin_treinar():
    return _proxy_post("/api/admin/treinar", timeout=60)


@app.route("/api/pipeline/status")
def pipeline_status():
    return _proxy_get("/api/pipeline/status")


# ── Feedback loop ─────────────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def feedback():
    return _proxy_post("/api/feedback")


# ── Chamados ──────────────────────────────────────────────────────────────────

@app.route("/api/chamados/<int:chamado_id>/resolver", methods=["PATCH"])
def chamados_resolver(chamado_id):
    return _proxy_patch(f"/api/chamados/{chamado_id}/resolver")


# ── Monitoramento ─────────────────────────────────────────────────────────────

@app.route("/api/monitoramento/scores/<int:dispositivo_id>")
def monitoramento_scores(dispositivo_id):
    return _proxy_get(f"/api/monitoramento/scores/{dispositivo_id}")


@app.route("/api/monitoramento/reincidencia")
def monitoramento_reincidencia():
    return _proxy_get("/api/monitoramento/reincidencia")


if __name__ == "__main__":
    app.run(debug=True, port=5000)