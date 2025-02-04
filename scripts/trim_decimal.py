from decimal import Decimal, ROUND_DOWN

def trim_decimal(value: Decimal) -> Decimal:
    return value.normalize() if value % 1 != 0 else value.quantize(Decimal("1"), rounding=ROUND_DOWN)