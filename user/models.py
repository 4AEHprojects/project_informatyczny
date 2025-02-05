from decimal import Decimal

from passlib.hash import bcrypt
from sqlalchemy import Numeric

from application.extension import db


class User(db.Model):
    """Модель пользователя"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    firstname = db.Column(db.String(64), unique=False, nullable=False)
    lastname = db.Column(db.String(64), unique=False, nullable=False)
    phone = db.Column(db.String(64), unique=False, nullable=False)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Дополнительные отношения (если понадобится)
    favorite_currencies = db.relationship('UserFavoriteCurrency', back_populates='user', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', back_populates='user')
    wallet = db.relationship('Wallet', back_populates='user', uselist=False)

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)

class UserFavoriteCurrency(db.Model):
    """Many-to-many relationship between users and currencies"""
    __tablename__ = "user_favorite_currencies"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    currency_code = db.Column(db.String(10), db.ForeignKey('currency_rates.code'), primary_key=True)

    # Relationships
    user = db.relationship('User', back_populates='favorite_currencies')
    currency = db.relationship('CurrencyRate', back_populates='favored_by')

class Wallet(db.Model):
    __tablename__ = "wallets"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    currency_code = db.Column(db.String(3), primary_key=True)
    balance = db.Column(Numeric(precision=20, scale=4), default=Decimal('0.00'))
    user = db.relationship('User', back_populates='wallet')

    def deposit(self, amount):
        """Пополнение кошелька"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += Decimal(amount)

    def withdraw(self, amount):
        """Снятие средств"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < Decimal(amount):
            raise ValueError("Insufficient balance")
        self.balance -= Decimal(amount)
