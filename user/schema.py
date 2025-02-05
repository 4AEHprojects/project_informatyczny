from marshmallow import fields, validate

from application.extension import ma
from user.models import User


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = fields.Int(dump_only=True)
    firstname = fields.Str(required=True, validate=validate.Length(min=3))
    lastname = fields.Str(required=True, validate=validate.Length(min=3))

    phone = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\+?[1-9]\d{1,14}$', error="Invalid phone number format.")
    )

    email = fields.Email(required=True, validate=validate.Email())
    password = fields.Str(
        load_only=True,
        validate=validate.Length(min=8),
        required=True
    )


class UserLoginSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = fields.Int(dump_only=True)

    email = fields.Email(required=True, validate=validate.Email())
    password = fields.Str(load_only=True, required=True, validate=validate.Length(min=8))

class WalletSchema(ma.SQLAlchemySchema):
    user_id = fields.Int(required=True)
    currency_code = fields.Str(required=True)
    balance = fields.Decimal(as_string=True, required=True)  # Отображаем Decimal как строку

class UserFavoriteCurrencySchema(ma.SQLAlchemySchema):
    user_id = fields.Int(required=True)
    currency_code = fields.Str(required=True)

