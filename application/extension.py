from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

ma = Marshmallow()
db = SQLAlchemy()  # Создаем экземпляр SQLAlchemy без привязки к `application`
