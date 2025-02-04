from datetime import datetime, timedelta

from flask import jsonify, Blueprint, request
from sqlalchemy import func
from sqlalchemy.orm import aliased
from werkzeug.exceptions import BadRequest

from currency.models import CurrencyRate
from app import db
from marshmallow import ValidationError

from currency.schemas import CurrencySchema

currency_bp = Blueprint('currency', __name__)
user_schema = CurrencySchema()  # Создаем экземпляр схемы

@currency_bp.route('/currency-rates', methods=['GET'])
def get_all_currency_rates():
    # Создаем алиас для валютных курсов, чтобы получить последние значения для каждой валюты
    subquery = db.session.query(
        CurrencyRate.code,
        func.max(CurrencyRate.effective_date).label('max_date')
    ).group_by(CurrencyRate.code).subquery()

    # Основной запрос для получения данных с последними датами для каждой валюты
    latest_rates = db.session.query(CurrencyRate).join(
        subquery,
        (CurrencyRate.code == subquery.c.code) &
        (CurrencyRate.effective_date == subquery.c.max_date)
    ).all()

    # Сериализуем данные
    schema = CurrencySchema(many=True)
    result = schema.dump(latest_rates)

    # Преобразуем список в словарь с кодами валют в качестве ключей
    result_dict = {rate['code']: rate for rate in result}

    return jsonify(result_dict), 200


@currency_bp.route('/delete-old-currency-rates', methods=['DELETE'])
def delete_old_currency_rates():
    target_date = datetime(2025, 2, 4)
    try:
        # Создаем алиас для модели CurrencyRate
        CurrencyRateAlias = aliased(CurrencyRate)

        # Подзапрос для проверки существования записи с target_date для каждого code
        subquery = db.session.query(CurrencyRateAlias.code).filter(
            CurrencyRateAlias.code == CurrencyRate.code,
            CurrencyRateAlias.effective_date == target_date
        )

        # Удаляем все записи, где нет соответствующей записи с target_date
        deleted_count = CurrencyRate.query.filter(~subquery.exists()).delete(
            synchronize_session=False
        )
        db.session.commit()

        return jsonify({
            "message": f"Удалено {deleted_count} старых курсов валют без записи на {target_date.date()}"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка при удалении: {str(e)}"}), 500


@currency_bp.route('/currency-rates/<string:currency_code>', methods=['GET'])
def get_currency_by_code(currency_code):
    # Получаем параметры запроса (дата начала и дата конца)
    start_date = request.args.get('start_date')  # Начальная дата (например, '2025-01-01')
    end_date = request.args.get('end_date')  # Конечная дата (например, '2025-01-07')

    # Проверка на корректность даты
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise BadRequest(f"Некорректная дата: {date_str}. Ожидаемый формат: yyyy-mm-dd.")

    query = CurrencyRate.query.filter(CurrencyRate.code == currency_code)

    if start_date:
        start_date = parse_date(start_date)
        query = query.filter(CurrencyRate.effective_date >= start_date)

    if end_date:
        end_date = parse_date(end_date)
        query = query.filter(CurrencyRate.effective_date <= end_date)

    # Если нет start_date и end_date, то возвращаем данные за неделю
    if not start_date and not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        query = query.filter(CurrencyRate.effective_date >= start_date, CurrencyRate.effective_date <= end_date)

    # Получаем результат
    currencies = query.order_by(CurrencyRate.effective_date.asc()).all()

    # Сериализуем данные
    schema = CurrencySchema(many=True)
    result = schema.dump(currencies)

    return jsonify(result), 200
