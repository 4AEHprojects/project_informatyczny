# app/services/wallet_service.py

from app.extension import db
from user.models import Wallet
from decimal import Decimal


class WalletError(Exception):
    pass


def deposit_funds(user_id, currency_code, amount):
    """Функция пополнения средств на кошельке"""
    if not amount or amount <= 0:
        raise WalletError("Invalid amount")

    wallet = Wallet.query.filter_by(user_id=user_id, currency_code=currency_code).first()
    if not wallet:
        raise WalletError(f"Wallet with currency {currency_code} not found")

    wallet.balance += Decimal(amount)  # Пополнение баланса
    db.session.commit()


def withdraw_funds(user_id, currency_code, amount):
    """Функция снятия средств с кошелька"""
    if not amount or amount <= 0:
        raise WalletError("Invalid amount")

    wallet = Wallet.query.filter_by(user_id=user_id, currency_code=currency_code).first()
    if not wallet:
        raise WalletError(f"Wallet with currency {currency_code} not found")

    if wallet.balance < Decimal(amount):
        raise WalletError("Insufficient funds")

    wallet.balance -= Decimal(amount)  # Снятие средств
    db.session.commit()
