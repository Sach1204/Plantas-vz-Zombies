from pathlib import Path

from flask import Blueprint, jsonify, request

from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.medicion import Medicion
from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.services.recomendador import Recomendador
from app.infrastructure.repositories.csv_referencia_plantas import CSVReferenciaPlantas

diagnostico_bp = Blueprint(
    "diagnosticos",
    __name__,
    url_prefix="/api/v1"
)

BASE_DIR = Path(__file__).resolve().parents[3]
CSV_PATH = BASE_DIR / "app" / "infrastructure" / "data" / "plantas.csv"


def _crear_diagnostico():
    referencia = CSVReferenciaPlantas(str(CSV_PATH))
    return DiagnosticarPlanta(
        referencia,
        EvaluadorPlanta(),
        Recomendador(),
    )


@diagnostico_bp.get("/especies")
def listar_especies():
    especies = _crear_diagnostico().referencia.listar_especies()
    return jsonify({
        "especies": [
            especie.especie for especie in especies
        ]
    })


def _procesar_diagnostico(data):
    try:
        medicion = Medicion(
            data.get("especie"),
            float(data.get("humedad")),
            float(data.get("luz")),
            float(data.get("temperatura")),
        )

        resultado = _crear_diagnostico().ejecutar(medicion)
        return jsonify(resultado), 200

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 404

    except (TypeError, ValueError):
        return jsonify({
            "error": "Datos de entrada invalidos"
        }), 400


@diagnostico_bp.get("/diagnosticos")
def diagnosticar_get():
    data = request.args.to_dict(flat=True)

    if not data:
        data = {
            "especie": "sansevieria",
            "humedad": 10,
            "luz": 500,
            "temperatura": 20,
        }

    return _procesar_diagnostico(data)


@diagnostico_bp.post("/diagnosticos")
def diagnosticar():
    data = request.get_json(silent=True) or {}
    return _procesar_diagnostico(data)

