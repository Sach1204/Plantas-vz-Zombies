from pathlib import Path

from app import create_app
from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.medicion import Medicion
from app.domain.services.evaluador_planta import EvaluadorPlanta
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
