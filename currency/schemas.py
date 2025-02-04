from marshmallow import Schema, fields
from app.extension import ma
from currency.models import CurrencyRate


class CurrencySchema(ma.SQLAlchemySchema):
    class Meta:
        model = CurrencyRate
        fields = ("code", "effective_date", "bid", "ask")

    code = fields.Str(attribute="code", required=True)
    bid = fields.Decimal(attribute="bid", required=True)
    ask = fields.Decimal(attribute="ask", required=True)

    def format_output(self, data, many, **kwargs):
        result = super().format_output(data, many, **kwargs)
        if isinstance(result, list):
            return [
                {
                    "Currency Code": item["code"],
                    "Selling Price": item["ask"],
                    "Buying Price": item["bid"]
                }
                for item in result
            ]
        else:
            return {
                "Currency Code": result["code"],
                "Selling Price": result["ask"],
                "Buying Price": result["bid"]
            }

class FavoriteCurrencySchema(Schema):
    currency_code = fields.Str(required=True)