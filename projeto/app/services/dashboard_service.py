from itsdangerous import URLSafeTimedSerializer
from app.config import DASH_SECRET, DASH_BASE_URL

_serializer = URLSafeTimedSerializer(DASH_SECRET)
TOKEN_MAX_AGE = 3600  # 1 hora


def generate_dash_link(loja_id: int) -> str:
    token = _serializer.dumps({"loja_id": loja_id})
    return f"{DASH_BASE_URL}/dash?t={token}"
