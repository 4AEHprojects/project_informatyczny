from application.extension import db
from datetime import datetime
from decimal import Decimal

class Transaction(db.Model):
    """Записи финансовых транзакций"""
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    amount = db.Column(db.Numeric(20, 4), nullable=False)  # Используем Decimal
    transaction_type = db.Column(db.String(20))  # deposit, withdrawal, transfer
    price = db.Column(db.Numeric(12, 4), nullable=True)  # Сколько тратили злотых за 1 валюту
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    final_pln_balance = db.Column(db.Numeric(20, 4), nullable=False)  # Баланс PLN после транзакции
    final_currency_balance = db.Column(db.Numeric(20, 4), nullable=False)  # Баланс валюты после транзакции

    # Связи
    user = db.relationship('User', back_populates='transactions')
