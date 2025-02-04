# app/routes/transaction_routes.py
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.routing import ValidationError

from app.extension import db
from auth.jwt import token_required
from currency.currency_service import get_latest_currency_by_code
from transaction.models import Transaction
from user.models import Wallet
from user.wallet_service import WalletError

from scripts.trim_decimal import trim_decimal

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions(user_id):
    """Получить список всех транзакций пользователя"""

    transactions = Transaction.query.filter_by(user_id=user_id).all()
    transactions_list = [
        {
            "id": txn.id,
            "currency_code": txn.currency_code,
            "amount": str(txn.amount),  # Конвертируем Decimal в строку
            "transaction_type": txn.transaction_type,
            "timestamp": txn.timestamp,
            "final_pln_balance": str(txn.final_pln_balance),
            "final_currency_balance": str(txn.final_currency_balance)
        } for txn in transactions
    ]

    return jsonify(transactions_list), 200

@transaction_bp.route('/transaction/buy', methods=['POST'])
@token_required
def buy_currency(user_id):
    """Покупка валюты"""
    data = request.get_json()
    currency_code = data.get("currency_code")  # Валюта, которую покупаем
    amount = data.get("amount")  # Сумма для транзакции

    if not currency_code or not amount:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Получаем курс валюты
        latest_currency = get_latest_currency_by_code(currency_code)

        # Получаем кошелек в PLN (Польские злоты)
        pln_wallet = Wallet.query.filter_by(user_id=user_id, currency_code="PLN").first()
        if not pln_wallet:
            return jsonify({"error": "PLN wallet not found"}), 404

        # Получаем кошелек для выбранной валюты
        currency_wallet = Wallet.query.filter_by(user_id=user_id, currency_code=currency_code).first()
        if not currency_wallet:
            # Если кошелек не существует, создаем его для валюты
            currency_wallet = Wallet(user_id=user_id, currency_code=currency_code, balance=Decimal('0.00'))
            db.session.add(currency_wallet)

        print(latest_currency.ask)
        # Используем курс валюты для вычислений
        selling_price = Decimal(latest_currency.ask)  # Цена продажи валюты в PLN
        total_cost = Decimal(amount) * selling_price  # Считаем стоимость покупки (в PLN)

        if pln_wallet.balance < total_cost:
            return jsonify({"error": "Insufficient PLN balance"}), 400

        # Вычитаем PLN и увеличиваем валюту
        pln_wallet.balance -= total_cost
        currency_wallet.balance += Decimal(amount)

        # Создаем транзакцию
        transaction = Transaction(
            user_id=user_id,
            currency_code=currency_code,
            amount=Decimal(amount),
            transaction_type="buy",
            final_pln_balance=pln_wallet.balance,
            final_currency_balance=currency_wallet.balance
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            "message": f"Successfully bought {amount} {currency_code}",
            "final_pln_balance": str(pln_wallet.balance),
            "final_currency_balance": str(currency_wallet.balance),
            "selling_price": str(selling_price)
        }), 200

    except WalletError as e:
        return jsonify({"error": str(e)}), 400
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400


@transaction_bp.route('/transaction/sell', methods=['POST'])
@token_required
def sell_currency(user_id):
    """Продажа валюты"""
    data = request.get_json()
    currency_code = data.get("currency_code")  # Валюта, которую продаем
    amount = data.get("amount")  # Сумма для транзакции

    if not currency_code or not amount:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Получаем курс валюты
        latest_currency = get_latest_currency_by_code(currency_code)

        # Получаем кошелек в PLN (Польские злоты)
        pln_wallet = Wallet.query.filter_by(user_id=user_id, currency_code="PLN").first()
        if not pln_wallet:
            return jsonify({"error": "PLN wallet not found"}), 404

        # Получаем кошелек для выбранной валюты
        currency_wallet = Wallet.query.filter_by(user_id=user_id, currency_code=currency_code).first()
        if not currency_wallet:
            return jsonify({"error": f"{currency_code} wallet not found"}), 404

        # Используем курс валюты для вычислений
        buying_price = Decimal(latest_currency.bid)  # Цена покупки валюты в PLN
        total_income = Decimal(amount) * buying_price  # Считаем доход от продажи (в PLN)

        if currency_wallet.balance < Decimal(amount):
            return jsonify({"error": "Insufficient currency balance"}), 400

        # Уменьшаем валюту и добавляем PLN
        currency_wallet.balance -= Decimal(amount)
        pln_wallet.balance += total_income

        # Создаем транзакцию
        transaction = Transaction(
            user_id=user_id,
            currency_code=currency_code,
            amount=Decimal(amount),
            transaction_type="sell",
            final_pln_balance=pln_wallet.balance,
            final_currency_balance=currency_wallet.balance
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            "message": f"Successfully sold {amount} {currency_code}",
            "final_pln_balance": str(pln_wallet.balance),
            "final_currency_balance": str(currency_wallet.balance),
            "buying_price": str(buying_price)
        }), 200

    except WalletError as e:
        return jsonify({"error": str(e)}), 400
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400