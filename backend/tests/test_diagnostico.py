from pathlib import Path

import pytest

from app import create_app
from app.application.use_cases.diagnosticar_planta import DiagnosticarPlanta
from app.domain.entities.medicion import Medicion
from app.domain.services.evaluador_planta import EvaluadorPlanta
from app.domain.services.recomendador import Recomendador
from app.infrastructure.repositories.csv_referencia_plantas import CSVReferenciaPlantas


BACKEND_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BACKEND_DIR / "app" / "infrastructure" / "data" / "plantas.csv"


@pytest.fixture
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
            "JWT_SECRET": "test-secret",
        }
    )
    return app.test_client()


def registrar_usuario(client, email):
    response = client.post(
        "/api/v1/auth/registro",
        json={"email": email, "contrasena": "contrasena-segura"},
    )
    assert response.status_code == 201
    return response.get_json()


def crear_planta(client, token, especie="sansevieria"):
    return client.post(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {token}"},
        json={"nombre": "Mi planta", "especie": especie},
    )


def test_diagnostico_conserva_la_validacion_existente():
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


def test_api_registra_y_consulta_lecturas_solo_del_propietario(client):
    usuario = registrar_usuario(client, "dueño@example.com")
    token = usuario["token"]
    planta_response = crear_planta(client, token)
    assert planta_response.status_code == 201
    planta_id = planta_response.get_json()["id"]
    headers = {"Authorization": f"Bearer {token}"}

    sin_lecturas = client.get(
        f"/api/v1/plantas/{planta_id}/estado",
        headers=headers,
    )
    assert sin_lecturas.status_code == 200
    assert sin_lecturas.get_json()["estado"] == "SIN_LECTURAS"

    lectura = client.post(
        f"/api/v1/plantas/{planta_id}/lecturas",
        headers=headers,
        json={
            "especie": "sansevieria",
            "humedad": 10,
            "luz": 500,
            "temperatura": 20,
        },
    )
    assert lectura.status_code == 201
    assert lectura.get_json()["estado"] == "EN_RIESGO"

    estado = client.get(f"/api/v1/plantas/{planta_id}/estado", headers=headers)
    historial = client.get(f"/api/v1/plantas/{planta_id}/lecturas", headers=headers)
    assert estado.status_code == 200
    assert estado.get_json()["estado"] == "EN_RIESGO"
    assert historial.status_code == 200
    assert len(historial.get_json()["lecturas"]) == 1

    otro_usuario = registrar_usuario(client, "otra@example.com")
    headers_ajenos = {"Authorization": f"Bearer {otro_usuario['token']}"}
    estado_ajeno = client.get(
        f"/api/v1/plantas/{planta_id}/estado",
        headers=headers_ajenos,
    )
    historial_ajeno = client.get(
        f"/api/v1/plantas/{planta_id}/lecturas",
        headers=headers_ajenos,
    )
    assert estado_ajeno.status_code == 403
    assert historial_ajeno.status_code == 403


@pytest.mark.parametrize(
    ("lectura", "error"),
    [
        (
            {"especie": "sansevieria", "humedad": "abc", "luz": 500, "temperatura": 20},
            "LECTURA_INVALIDA",
        ),
        (
            {"especie": "sansevieria", "humedad": 101, "luz": 500, "temperatura": 20},
            "LECTURA_INVALIDA",
        ),
        (
            {"especie": "sansevieria", "humedad": 30, "luz": 500},
            "LECTURA_INVALIDA",
        ),
    ],
)
def test_api_distingue_lecturas_invalidas(client, lectura, error):
    usuario = registrar_usuario(client, "jardinero@example.com")
    planta = crear_planta(client, usuario["token"]).get_json()
    response = client.post(
        f"/api/v1/plantas/{planta['id']}/lecturas",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json=lectura,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == error


def test_api_exige_jwt_en_endpoints_del_front(client):
    assert client.get("/api/v1/plantas").status_code == 401
    assert client.get("/api/v1/especies").status_code == 401


def test_login_verifica_contrasena_hasheada(client):
    registrar_usuario(client, "login@example.com")

    correcto = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "contrasena": "contrasena-segura"},
    )
    incorrecto = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "contrasena": "incorrecta"},
    )

    assert correcto.status_code == 200
    assert correcto.get_json()["token"]
    assert incorrecto.status_code == 400


def test_tabla_referencia_sqlite_se_elige_por_configuracion(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
            "JWT_SECRET": "test-secret",
            "REFERENCE_ADAPTER": "sqlite",
        }
    )
    client = app.test_client()
    usuario = registrar_usuario(client, "sqlite@example.com")
    response = client.get(
        "/api/v1/especies",
        headers={"Authorization": f"Bearer {usuario['token']}"},
    )
    planta = crear_planta(client, usuario["token"]).get_json()
    lectura = client.post(
        f"/api/v1/plantas/{planta['id']}/lecturas",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json={
            "especie": "sansevieria",
            "humedad": 0,
            "luz": 700,
            "temperatura": 22,
        },
    )

    assert response.status_code == 200
    assert "sansevieria" in response.get_json()["especies"]
    assert lectura.status_code == 201
    assert lectura.get_json()["estado"] == "EN_RIESGO"
