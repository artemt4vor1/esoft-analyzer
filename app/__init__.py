import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PLOTS_FOLDER"], exist_ok=True)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ресурс не найден"}), 404

    @app.errorhandler(405)
    def wrong_method(_):
        return jsonify({"error": "Метод не поддерживается для этого адреса"}), 405

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "Файл больше 50 МБ"}), 413

    @app.errorhandler(500)
    def internal(_):
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

    @app.route("/")
    def index():
        return jsonify({
            "service": "E-soft Data Analyzer API",
            "endpoints": {
                "POST /upload": "загрузка CSV/Excel",
                "GET /data/stats?file_id=N": "среднее, медиана, корреляция",
                "GET /data/clean?file_id=N&strategy=median": "очистка данных",
                "GET /data/plot?file_id=N&type=histogram&columns=salary": "график (PNG)",
            },
        })

    return app
