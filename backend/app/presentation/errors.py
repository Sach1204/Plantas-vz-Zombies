import sqlite3

from flask import jsonify

from app.domain.exceptions import (
    AccesoDenegado,
    DatoInvalido,
    DispositivoNoAutorizado,
    DominioError,
    EspecieNoSoportada,
    RecursoNoEncontrado,
)


def configurar_manejadores_errores(app):
    @app.errorhandler(DatoInvalido)
    def manejar_dato_invalido(error):
        return jsonify({"error": str(error)}), 400

    def manejar_acceso_denegado(error):
        return jsonify({"error": str(error)}), 403

    @app.errorhandler(EspecieNoSoportada)
    def manejar_especie_no_soportada(error):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(RecursoNoEncontrado)
    def manejar_recurso_no_encontrado(error):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(DominioError)
    def manejar_error_dominio(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(sqlite3.IntegrityError)
    def manejar_conflicto_persistencia(error):
        return jsonify({"error": "CONFLICTO_DE_DATOS"}), 409

    app.register_error_handler(AccesoDenegado, manejar_acceso_denegado)
    app.register_error_handler(DispositivoNoAutorizado, manejar_acceso_denegado)
