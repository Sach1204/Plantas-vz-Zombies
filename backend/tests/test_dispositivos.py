from datetime import datetime, timezone

import jwt
import pytest

from app import create_app
from simulador_esp32 import generar_lectura


@pytest.fixture
def entorno(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
            "JWT_SECRET": "device-test-secret",
            "DEVICE_CONFIG_PATH": None,
        }
    )
    cliente = app.test_client()
    usuario = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "sensor@example.com", "contrasena": "contrasena-segura"},
    ).get_json()
    planta = cliente.post(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json={"nombre": "Potos", "especie": "sansevieria"},
    ).get_json()
    return cliente, usuario["token"], planta


def enviar_lectura(cliente, planta, valores=None, dispositivo_id=None, token=None):
    payload = {
        "dispositivo_id": planta["dispositivo_id"],
        "especie": planta["especie"],
        "marca_temporal": datetime.now(timezone.utc).isoformat(),
        "humedad": 0,
        "luz": 700,
        "temperatura": 22,
    }
    payload.update(valores or {})
    return cliente.post(
        f"/api/dispositivos/{dispositivo_id or planta['dispositivo_id']}/lecturas",
        headers={"Authorization": f"Bearer {token or planta['token_dispositivo']}"},
        json=payload,
    )


def test_dispositivo_reporta_lectura_fuera_de_rango_y_persiste_historial(entorno):
    cliente, token_usuario, planta = entorno

    response = enviar_lectura(cliente, planta)

    assert response.status_code == 201
    assert response.get_json()["estado"] == "EN_RIESGO"
    historial = cliente.get(
        f"/api/v1/plantas/{planta['id']}/lecturas",
        headers={"Authorization": f"Bearer {token_usuario}"},
    )
    assert historial.status_code == 200
    lectura = historial.get_json()["lecturas"][0]
    assert lectura["origen"] == "SENSOR"
    assert lectura["humedad"] == 0


def test_dispositivo_no_puede_usar_token_para_otro_dispositivo(entorno):
    cliente, _, planta = entorno

    response = enviar_lectura(
        cliente,
        planta,
        dispositivo_id="otro-dispositivo",
    )
    front = cliente.get(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {planta['token_dispositivo']}"},
    )

    assert response.status_code == 403
    assert front.status_code == 401


def test_token_dispositivo_tiene_solo_alcance_de_reportar_y_dura_30_dias(entorno):
    _, _, planta = entorno
    claims = jwt.decode(
        planta["token_dispositivo"],
        options={"verify_signature": False},
    )
    tiempo_restante = claims["exp"] - int(datetime.now(timezone.utc).timestamp())

    assert claims["tipo"] == "dispositivo"
    assert claims["scope"] == ["lecturas:reportar"]
    assert 29 * 24 * 60 * 60 < tiempo_restante <= 30 * 24 * 60 * 60


@pytest.mark.parametrize(
    "valores",
    [
        {"humedad": "dato-invalido"},
        {"marca_temporal": "no-es-una-fecha"},
        {"temperatura": 200},
    ],
)
def test_adaptador_dispositivo_rechaza_lectura_invalida(entorno, valores):
    cliente, token_usuario, planta = entorno

    response = enviar_lectura(cliente, planta, valores=valores)

    assert response.status_code == 400
    historial = cliente.get(
        f"/api/v1/plantas/{planta['id']}/lecturas",
        headers={"Authorization": f"Bearer {token_usuario}"},
    )
    assert historial.get_json()["lecturas"] == []


def test_simulador_genera_caso_fuera_de_rango_y_dato_invalido():
    fuera_de_rango = generar_lectura(5, "esp32-1", "sansevieria")
    invalida = generar_lectura(7, "esp32-1", "sansevieria")

    assert fuera_de_rango["humedad"] == 0
    assert invalida["humedad"] == "dato-invalido"
