from datetime import timedelta
from locale import currency

import flask_migrate
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from app.extension import db
from currency.routes import currency_bp
from transaction.routes import transaction_bp
from user.routes import user_bp  # Импортируем Blueprint

def create_app():
    app = Flask(__name__)

    # Конфигурация базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config["JWT_SECRET_KEY"] = "SECRET_KEY"  # Задай свой секретный ключ
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(weeks=1)

    jwt = JWTManager(app)

    # Инициализация базы данных
    db.init_app(app)

    from user.models import User
    from currency.models import CurrencyRate
    from transaction.models import Transaction

    from user.models import Wallet
    from user.models import UserFavoriteCurrency

    # Регистрация Blueprint
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(currency_bp, url_prefix='/currency')
    app.register_blueprint(transaction_bp, url_prefix='/transactions')

    return app
