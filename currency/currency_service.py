from sqlalchemy import func
from app.extension import db
from currency.models import CurrencyRate
from marshmallow import ValidationError
from flask import jsonify

from currency.schemas import CurrencySchema


def get_latest_currency_by_code(currency_code):
    """Получить курс валюты по коду с самой свежей датой, используя подзапрос"""

    # Создаем подзапрос для получения самой свежей даты для данной валюты
    subquery = db.session.query(
        CurrencyRate.code,
        func.max(CurrencyRate.effective_date).label('max_date')
    ).filter(CurrencyRate.code == currency_code) \
        .group_by(CurrencyRate.code) \
        .subquery()

    # Получаем валюту с самой свежей датой
    latest_currency = db.session.query(CurrencyRate) \
        .join(subquery, (CurrencyRate.code == subquery.c.code) & (CurrencyRate.effective_date == subquery.c.max_date)) \
        .first()  # Получаем только один самый последний результат

    if not latest_currency:
        raise ValidationError(f"Валюта с кодом {currency_code} не найдена.")

    # Возвращаем результат
    return latest_currency