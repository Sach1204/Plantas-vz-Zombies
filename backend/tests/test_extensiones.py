import pytest
from app import create_app


@pytest.fixture
def entorno(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
            "JWT_SECRET": "extension-test-secret",
        }
    )
    cliente = app.test_client()
    usr1 = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "dueno@example.com", "contrasena": "contrasena-123"},
    ).get_json()
    usr2 = cliente.post(
        "/api/v1/auth/registro",
        json={"email": "amigo@example.com", "contrasena": "contrasena-456"},
    ).get_json()
    planta = cliente.post(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {usr1['token']}"},
        json={"nombre": "Mi Potos", "especie": "potos"},
    ).get_json()
    return cliente, usr1, usr2, planta


def test_consultar_credenciales_planta_propietario(entorno):
    cliente, usr1, usr2, planta = entorno
    # Propietario consulta sus credenciales
    res = cliente.get(
        f"/api/v1/plantas/{planta['id']}/credenciales",
        headers={"Authorization": f"Bearer {usr1['token']}"},
    )
    assert res.status_code == 200
    datos = res.get_json()
    assert datos["dispositivo_id"] == planta["dispositivo_id"]
    assert "token_dispositivo" in datos

    # Usuario ajeno no puede consultarlas
    res_ajena = cliente.get(
        f"/api/v1/plantas/{planta['id']}/credenciales",
        headers={"Authorization": f"Bearer {usr2['token']}"},
    )
    assert res_ajena.status_code == 403


def test_editar_y_eliminar_planta(entorno):
    cliente, usr1, usr2, planta = entorno

    # Usuario ajeno no puede editar
    res_ajeno = cliente.put(
        f"/api/v1/plantas/{planta['id']}",
        headers={"Authorization": f"Bearer {usr2['token']}"},
        json={"nombre": "Hackeada"},
    )
    assert res_ajeno.status_code == 403

    # Propietario edita nombre y especie
    res_edit = cliente.put(
        f"/api/v1/plantas/{planta['id']}",
        headers={"Authorization": f"Bearer {usr1['token']}"},
        json={"nombre": "Potos Renombrado", "especie": "sansevieria"},
    )
    assert res_edit.status_code == 200
    assert res_edit.get_json()["nombre"] == "Potos Renombrado"
    assert res_edit.get_json()["especie"] == "sansevieria"

    # Propietario elimina la planta
    res_del = cliente.delete(
        f"/api/v1/plantas/{planta['id']}",
        headers={"Authorization": f"Bearer {usr1['token']}"},
    )
    assert res_del.status_code == 200

    # Ya no existe
    res_check = cliente.get(
        f"/api/v1/plantas/{planta['id']}/estado",
        headers={"Authorization": f"Bearer {usr1['token']}"},
    )
    assert res_check.status_code == 404


def test_cuidado_compartido_y_actividades(entorno):
    cliente, usr1, usr2, planta = entorno

    # Invitar amigo
    res_inv = cliente.post(
        f"/api/v1/plantas/{planta['id']}/colaboradores",
        headers={"Authorization": f"Bearer {usr1['token']}"},
        json={"email": "amigo@example.com"},
    )
    assert res_inv.status_code == 201

    # Listar equipo
    res_eq = cliente.get(
        f"/api/v1/plantas/{planta['id']}/colaboradores",
        headers={"Authorization": f"Bearer {usr1['token']}"},
    )
    assert res_eq.status_code == 200
    colaboradores = res_eq.get_json()["colaboradores"]
    assert len(colaboradores) == 2

    # Amigo registra actividad
    res_act = cliente.post(
        f"/api/v1/plantas/{planta['id']}/actividades",
        headers={"Authorization": f"Bearer {usr2['token']}"},
        json={"accion": "REGADA"},
    )
    assert res_act.status_code == 201

    # Consultar actividades
    res_list = cliente.get(
        f"/api/v1/plantas/{planta['id']}/actividades",
        headers={"Authorization": f"Bearer {usr1['token']}"},
    )
    assert res_list.status_code == 200
    actividades = res_list.get_json()["actividades"]
    assert len(actividades) == 1
    assert actividades[0]["accion"] == "REGADA"


def test_recuperar_contrasena(entorno):
    cliente, usr1, _, _ = entorno

    # Cambiar contraseña
    res = cliente.post(
        "/api/v1/auth/recuperar-contrasena",
        json={"email": "dueno@example.com", "nueva_contrasena": "nueva-clave-segura"},
    )
    assert res.status_code == 200

    # Iniciar sesión con la nueva contraseña
    login = cliente.post(
        "/api/v1/auth/login",
        json={"email": "dueno@example.com", "contrasena": "nueva-clave-segura"},
    )
    assert login.status_code == 200

