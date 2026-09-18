from pathlib import Path

from app import create_app
from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.indice_vitalidad import IndiceVitalidad
from app.domain.entities.medicion import Medicion
from app.domain.services.evaluador_planta import AgregadorVitalidad, EvaluadorPlanta
from app.domain.services.recomendador import Recomendador
from app.infrastructure.repositories.csv_referencia_plantas import CSVReferenciaPlantas


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "app" / "infrastructure" / "data" / "plantas.csv"


def test_diagnostico_planta_ejecuta():
    referencia = CSVReferenciaPlantas(str(CSV_PATH))
    diagnostico = DiagnosticarPlanta(
        referencia,
        EvaluadorPlanta(),
        Recomendador(),
    )

    resultado = diagnostico.ejecutar(
        Medicion("sansevieria", 10, 500, 20)
    )

    assert resultado["especie"] == "sansevieria"
    assert resultado["estado"] == "EN_RIESGO"
    assert any(parametro["nombre"] == "humedad" for parametro in resultado["parametros"])


def test_api_diagnostica_plantas():
    app = create_app()

    response = app.test_client().post(
        "/api/v1/diagnosticos",
        json={
            "especie": "sansevieria",
            "humedad": 10,
            "luz": 500,
            "temperatura": 20,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["especie"] == "sansevieria"
    assert data["estado"] == "EN_RIESGO"
    assert len(data["recomendaciones"]) >= 1


def test_api_diagnostica_plantas_con_get():
    app = create_app()

    response = app.test_client().get(
        "/api/v1/diagnosticos?especie=sansevieria&humedad=10&luz=500&temperatura=20"
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["especie"] == "sansevieria"
    assert data["estado"] == "EN_RIESGO"


def test_api_rechaza_especie_desconocida():
    app = create_app()

    response = app.test_client().post(
        "/api/v1/diagnosticos",
        json={
            "especie": "planta_inventada",
            "humedad": 30,
            "luz": 500,
            "temperatura": 22,
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "ESPECIE_NO_SOPORTADA"


def test_api_rechaza_parametro_faltante():
    app = create_app()

    response = app.test_client().post(
        "/api/v1/diagnosticos",
        json={
            "especie": "sansevieria",
            "humedad": 30,
            "luz": 500,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "DATOS_DE_ENTRADA_INVALIDOS"


def test_api_rechaza_valor_no_numerico():
    app = create_app()

    response = app.test_client().post(
        "/api/v1/diagnosticos",
        json={
            "especie": "sansevieria",
            "humedad": "abc",
            "luz": 500,
            "temperatura": 22,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "DATOS_DE_ENTRADA_INVALIDOS"


def test_api_rechaza_valor_fuera_de_rango_fisico():
    app = create_app()

    response = app.test_client().post(
        "/api/v1/diagnosticos",
        json={
            "especie": "sansevieria",
            "humedad": 30,
            "luz": 500,
            "temperatura": 200,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "VALOR_FUERA_DE_RANGO_FISICO"


def test_evaluador_acepta_estrategia_de_agregacion_customizada():
    class AgregadorPersonalizado:
        def calcular(self, resultados):
            return IndiceVitalidad.SALUDABLE

    evaluador = EvaluadorPlanta(agregador=AgregadorPersonalizado())
    resultados = [
        evaluador.evaluar_parametro("humedad", 40, 30, 60, "%"),
        evaluador.evaluar_parametro("luz", 500, 400, 800, "lux"),
    ]

    assert evaluador.calcular_indice(resultados) == IndiceVitalidad.SALUDABLE
    assert isinstance(evaluador.agregador, AgregadorPersonalizado)
