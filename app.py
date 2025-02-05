from application import create_app
from application.extension import db

app = create_app()

with app.app_context():
    db.create_all()  # Создаем таблицы в БД

app.run(debug=True)
