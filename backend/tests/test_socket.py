from datetime import datetime, timezone

import pytest

from app import create_app
from app.presentation.controllers.socket_controller import socketio


@pytest.fixture
def entorno(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
            "JWT_SECRET": "socket-test-secret",
            "DEVICE_CONFIG_PATH": None,
        }
    )
    cliente = app.test_client()
    usuario = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "socket@example.com", "contrasena": "contrasena-segura"},
    ).get_json()
    planta = cliente.post(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json={"nombre": "Potos en vivo", "especie": "sansevieria"},
    ).get_json()
    return app, cliente, usuario, planta


def conectar(app, cliente, usuario):
    ws = socketio.test_client(
        app,
        auth={"token": usuario["token"]},
        flask_test_client=cliente,
    )
    assert ws.is_connected()
    return ws


def test_socket_rechaza_conexion_sin_token(entorno):
    app, cliente, _, _ = entorno

    ws = socketio.test_client(app, flask_test_client=cliente)

    assert not ws.is_connected()


def test_socket_emite_lectura_del_sensor_a_suscritos(entorno):
    app, cliente, usuario, planta = entorno
    ws = conectar(app, cliente, usuario)

    respuesta = ws.emit(
        "suscribir_planta",
        {"planta_id": planta["id"]},
        callback=True,
    )
    assert respuesta["ok"] is True

    lectura = cliente.post(
        f"/api/dispositivos/{planta['dispositivo_id']}/lecturas",
        headers={"Authorization": f"Bearer {planta['token_dispositivo']}"},
        json={
            "dispositivo_id": planta["dispositivo_id"],
            "especie": planta["especie"],
            "marca_temporal": datetime.now(timezone.utc).isoformat(),
            "humedad": 0,
            "luz": 700,
            "temperatura": 22,
        },
    )
    assert lectura.status_code == 201

    eventos = [
        evento
        for evento in ws.get_received()
        if evento["name"] == "lectura_registrada"
    ]
    assert len(eventos) == 1
    payload = eventos[0]["args"][0]
    assert payload["planta_id"] == planta["id"]
    assert payload["lectura"]["origen"] == "SENSOR"
    assert payload["diagnostico"]["estado"] == "EN_RIESGO"


def test_socket_permite_suscribirse_a_colaboradores(entorno):
    app, cliente, usuario, planta = entorno
    colaborador = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "colaborador@example.com", "contrasena": "contrasena-segura"},
    ).get_json()
    cliente.post(
        f"/api/v1/plantas/{planta['id']}/colaboradores",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json={"email": "colaborador@example.com"},
    )
    ws = conectar(app, cliente, colaborador)

    respuesta = ws.emit(
        "suscribir_planta",
        {"planta_id": planta["id"]},
        callback=True,
    )

    assert respuesta["ok"] is True


def test_socket_no_suscribe_plantas_de_otros_usuarios(entorno):
    app, cliente, usuario, planta = entorno
    otro = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "ajeno@example.com", "contrasena": "contrasena-segura"},
    ).get_json()
    ws = conectar(app, cliente, otro)

    respuesta = ws.emit(
        "suscribir_planta",
        {"planta_id": planta["id"]},
        callback=True,
    )

    assert respuesta["ok"] is False
    assert respuesta["error"] == "ACCESO_DENEGADO"
