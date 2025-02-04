import jwt
import datetime
from flask import request, jsonify

# Секретный ключ для подписи токенов (замени на свой)
SECRET_KEY = "your_secret_key_here"

# Функция создания JWT
def generate_jwt(user_id):
    payload = {
        "sub": str(user_id),  # ID пользователя
        "iat": datetime.datetime.utcnow(),  # Время создания
        "exp": datetime.datetime.utcnow() + datetime.timedelta(weeks=1)  # Срок действия (1 неделя)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# Функция декодирования JWT
def decode_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

# Декоратор для защиты маршрутов
def token_required(f):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token required"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"error": "Invalid token format"}), 401

        token = parts[1]
        payload = decode_jwt(token)

        if "error" in payload:
            return jsonify(payload), 401  # Возвращаем ошибку токена

        return f(payload["sub"], *args, **kwargs)  # Передаём user_id в защищённый маршрут

    wrapper.__name__ = f.__name__
    return wrapper
