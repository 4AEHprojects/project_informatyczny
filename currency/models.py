from app.extension import db

class CurrencyRate(db.Model):
    """Store currency exchange rates"""
    __tablename__ = "currency_rates"

    code = db.Column(db.String(9), primary_key=True)  # ISO 4217 код (USD, EUR)
    effective_date = db.Column(db.Date, primary_key=True)
    bid = db.Column(db.Numeric(precision=20, scale=4))
    ask = db.Column(db.Numeric(precision=20, scale=4))

    # Relationship for favorite currencies
    favored_by = db.relationship('UserFavoriteCurrency', back_populates='currency')