from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify(error="Username and password are required"), 400

    # Здесь можно добавить логику регистрации (например, сохранение в базу данных)
    return jsonify(message="Пользователь зарегистрирован", username=username), 201
