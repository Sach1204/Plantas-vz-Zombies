from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app)

    from app.presentation.controllers.diagnostico_controller import diagnostico_bp

    app.register_blueprint(diagnostico_bp)

    return app