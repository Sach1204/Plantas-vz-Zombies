import os
import secrets
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from app.application.use_cases.consultar_estado import ConsultarEstado
from app.application.use_cases.consultar_historial import ConsultarHistorial
from app.application.use_cases.crear_planta import CrearPlanta
from app.application.use_cases.iniciar_sesion import IniciarSesion
from app.application.use_cases.listar_especies import ListarEspecies
from app.application.use_cases.listar_plantas import ListarPlantas
from app.application.use_cases.registrar_lectura import RegistrarLectura
from app.application.use_cases.registrar_usuario import RegistrarUsuario
from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.services.recomendador import Recomendador
from app.domain.services.validador_de_estado import ValidadorDeEstado
from app.infrastructure.database import SQLiteDatabase
from app.infrastructure.repositories.csv_referencia_plantas import CSVReferenciaPlantas
from app.infrastructure.repositories.sqlite_historial import SQLiteHistorialLecturas
from app.infrastructure.repositories.sqlite_plantas import SQLitePlantas
from app.infrastructure.repositories.sqlite_referencia import (
    SQLiteTablaReferencia,
    cargar_referencias_iniciales,
)
from app.infrastructure.repositories.sqlite_usuarios import SQLiteUsuarios
from app.infrastructure.security.jwt_tokens import JwtTokenService
from app.infrastructure.security.password_hasher import WerkzeugHashContrasenas
from app.presentation.controllers.api_front import api_front_bp
from app.presentation.errors import configurar_manejadores_errores


APP_DIR = Path(__file__).resolve().parent
CSV_PATH = APP_DIR / "infrastructure" / "data" / "plantas.csv"


def create_app(configuracion=None):
    app = Flask(__name__)
    CORS(app)

    app.config.from_mapping(
        DATABASE_PATH=os.environ.get(
            "MATERA_DATABASE_PATH",
            str(APP_DIR / "infrastructure" / "data" / "matera.sqlite3"),
        ),
        REFERENCE_ADAPTER=os.environ.get("MATERA_REFERENCE_ADAPTER", "csv"),
        JWT_SECRET=os.environ.get("MATERA_JWT_SECRET"),
    )
    if configuracion:
        app.config.update(configuracion)
    if not app.config["JWT_SECRET"]:
        app.config["JWT_SECRET"] = secrets.token_urlsafe(32)

    base_datos = SQLiteDatabase(app.config["DATABASE_PATH"])
    referencia_csv = CSVReferenciaPlantas(str(CSV_PATH))
    tipo_referencia = app.config["REFERENCE_ADAPTER"].lower()
    if tipo_referencia == "csv":
        referencias = referencia_csv
    elif tipo_referencia == "sqlite":
        cargar_referencias_iniciales(base_datos, referencia_csv)
        referencias = SQLiteTablaReferencia(base_datos)
    else:
        raise ValueError("MATERA_REFERENCE_ADAPTER debe ser csv o sqlite")

    plantas = SQLitePlantas(base_datos)
    historial = SQLiteHistorialLecturas(base_datos)
    usuarios = SQLiteUsuarios(base_datos)
    emisor_token = JwtTokenService(app.config["JWT_SECRET"])
    hash_contrasenas = WerkzeugHashContrasenas()
    validador = ValidadorDeEstado(EvaluadorPlanta(), Recomendador())

    app.extensions["jwt_tokens"] = emisor_token
    app.extensions["matera"] = {
        "referencias": referencias,
        "historial": historial,
        "listar_especies": ListarEspecies(referencias),
        "listar_plantas": ListarPlantas(plantas),
        "registrar_lectura": RegistrarLectura(
            plantas,
            referencias,
            historial,
            validador,
        ),
        "consultar_estado": ConsultarEstado(
            plantas,
            referencias,
            historial,
            validador,
        ),
        "consultar_historial": ConsultarHistorial(plantas, historial),
        "crear_planta": CrearPlanta(plantas, referencias, emisor_token),
        "registrar_usuario": RegistrarUsuario(
            usuarios,
            hash_contrasenas,
            emisor_token,
        ),
        "iniciar_sesion": IniciarSesion(
            usuarios,
            hash_contrasenas,
            emisor_token,
        ),
    }
    app.register_blueprint(api_front_bp)
    configurar_manejadores_errores(app)

    return app