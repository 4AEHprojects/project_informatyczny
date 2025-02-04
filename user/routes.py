from datetime import timedelta
from decimal import Decimal

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extension import db
from auth.jwt import generate_jwt, decode_jwt, token_required
from currency.models import CurrencyRate
from user.models import User, Wallet, UserFavoriteCurrency
from user.schema import UserSchema, UserLoginSchema

user_bp = Blueprint('user', __name__)
user_schema = UserSchema()  # Создаем экземпляр схемы

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Получаем JSON из запроса

    # Валидация данных
    errors = user_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    existing_user = User.query.filter(
        User.email == data['email']
    ).first()

    if existing_user:
        if existing_user.email == data['email']:
            return jsonify({"error": "Email already in use"}), 409  # Conflict

    # Создание пользователя
    new_user = User(
        email=data['email'],
        firstname=data['firstname'],
        lastname=data['lastname'],
        phone=data['phone'],
    )
    new_user.password = data['password']  # Используем setter для хеширования пароля

    db.session.add(new_user)
    db.session.commit()

    # Создание кошелька для нового пользователя
    new_wallet = Wallet(user_id=new_user.id, currency_code="PLN", balance=Decimal('0.00'))
    db.session.add(new_wallet)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_schema = UserLoginSchema()

    # Валидация входных данных
    errors = user_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    # Ищем пользователя по email
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.verify_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = generate_jwt(user_id=user.id)

    return jsonify({"message": "Login successful", "access_token": f'{access_token}'}), 200

@user_bp.route('/profile', methods=['GET'])
@token_required  # Используем декоратор для проверки токена
def get_user_profile(user_id):
    # Получаем пользователя по user_id
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Возвращаем данные пользователя
    return jsonify({
        "email": user.email,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "phone": user.phone
    }), 200

@user_bp.route('/deposit', methods=['POST'])
@token_required
def deposit(user_id):
    """Пополнение кошелька"""
    data = request.get_json()
    amount = data.get("amount")

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        # Только PLN
        wallet = Wallet.query.filter_by(user_id=user_id, currency_code="PLN").first()
        if not wallet:
            wallet = Wallet(user_id=user_id, currency_code="PLN", balance=Decimal('0.00'))
            db.session.add(wallet)

        wallet.deposit(amount)
        db.session.commit()

        return jsonify({"message": f"Successfully deposited {amount} PLN"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route('/withdraw', methods=['POST'])
@token_required
def withdraw(user_id):
    """Снятие средств"""
    data = request.get_json()
    amount = data.get("amount")

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        # Только PLN
        wallet = Wallet.query.filter_by(user_id=user_id, currency_code="PLN").first()
        if not wallet:
            return jsonify({"error": "Wallet not found"}), 404

        wallet.withdraw(amount)
        db.session.commit()

        return jsonify({"message": f"Successfully withdrew {amount} PLN"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/wallet', methods=['GET'])
@token_required
def get_wallet(user_id):
    """Получить информацию о кошельке пользователя (все валюты)"""

    wallets = Wallet.query.filter_by(user_id=user_id).all()
    if not wallets:
        return jsonify({"error": "Wallets not found"}), 404

    # Сериализуем данные о всех кошельках
    # wallet_data = [{
    #     "currency_code": wallet.currency_code,
    #     "balance": str(wallet.balance)  # Преобразуем Decimal в строку для точности
    # } for wallet in wallets]

    wallet_data = {str(wallet.currency_code): str(wallet.balance) for wallet in wallets}

    return jsonify(wallet_data), 200

@user_bp.route('/favorites', methods=['GET'])
@token_required
def get_favorite_currencies(user_id):
    user = User.query.get_or_404(user_id)
    favorites = [fav.currency_code for fav in user.favorite_currencies]
    return jsonify({'favorite_currencies': favorites})


# Добавить любимую валюту пользователю
@user_bp.route('/favorites', methods=['POST'])
@token_required
def add_favorite_currency(user_id):
    data = request.get_json()
    currency_code = data.get('currency_code')

    if not currency_code:
        return jsonify({'error': 'Currency code is required'}), 400

    user = User.query.get_or_404(user_id)
    currency = CurrencyRate.query.filter_by(code=currency_code).first()

    if not currency:
        return jsonify({'error': 'Currency not found'}), 404

    # Проверяем, что валюты еще нет в избранном
    if any(fav.currency_code == currency_code for fav in user.favorite_currencies):
        return jsonify({'message': 'Currency already in favorites'}), 400

    favorite = UserFavoriteCurrency(user_id=user_id, currency_code=currency_code)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'message': 'Currency added to favorites'}), 201


# Удалить любимую валюту пользователя
@user_bp.route('/favorites/<string:currency_code>', methods=['DELETE'])
@token_required
def remove_favorite_currency(user_id, currency_code):
    favorite = UserFavoriteCurrency.query.filter_by(user_id=user_id, currency_code=currency_code).first()

    if not favorite:
        return jsonify({'error': 'Favorite currency not found'}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'message': 'Currency removed from favorites'}), 200

@user_bp.route('/protected', methods=['GET'])
@token_required
def protected(user_id):
    return jsonify({"message": "Protected content", "user_id": user_id}), 200

