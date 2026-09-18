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
RANGOS_FISICOS = {
    "humedad": (0, 100),
    "luz": (0, 200000),
    "temperatura": (-50, 80),
}


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


def _parsear_medicion(data):
    campos_requeridos = ["especie", "humedad", "luz", "temperatura"]

    for campo in campos_requeridos:
        valor = data.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ValueError("DATOS_DE_ENTRADA_INVALIDOS")

    try:
        especie = str(data["especie"]).strip()
        humedad = float(data["humedad"])
        luz = float(data["luz"])
        temperatura = float(data["temperatura"])
    except (TypeError, ValueError):
        raise ValueError("DATOS_DE_ENTRADA_INVALIDOS")

    if not especie:
        raise ValueError("DATOS_DE_ENTRADA_INVALIDOS")

    for nombre, valor in {
        "humedad": humedad,
        "luz": luz,
        "temperatura": temperatura,
    }.items():
        minimo, maximo = RANGOS_FISICOS[nombre]
        if valor < minimo or valor > maximo:
            raise ValueError("VALOR_FUERA_DE_RANGO_FISICO")

    return Medicion(
        especie,
        humedad,
        luz,
        temperatura,
    )


def _procesar_diagnostico(data):
    try:
        medicion = _parsear_medicion(data)
        resultado = _crear_diagnostico().ejecutar(medicion)
        return jsonify(resultado), 200

    except ValueError as exc:
        codigo_error = str(exc)
        if codigo_error == "ESPECIE_NO_SOPORTADA":
            return jsonify({"error": codigo_error}), 404
        if codigo_error in {"DATOS_DE_ENTRADA_INVALIDOS", "VALOR_FUERA_DE_RANGO_FISICO"}:
            return jsonify({"error": codigo_error}), 400
        return jsonify({"error": codigo_error}), 400


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

