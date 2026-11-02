from app import create_app


def _cliente(tmp_path, config_extra=None):
    configuracion = {
        "TESTING": True,
        "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
        "JWT_SECRET": "config-test-secret",
    }
    if config_extra:
        configuracion.update(config_extra)
    return create_app(configuracion).test_client()


def _registrar_y_crear_planta(cliente, email="config@example.com"):
    usuario = cliente.post(
        "/api/v1/auth/registro",
        json={"email": email, "contrasena": "contrasena-segura"},
    ).get_json()
    planta = cliente.post(
        "/api/v1/plantas",
        headers={"Authorization": f"Bearer {usuario['token']}"},
        json={"nombre": "Config", "especie": "suculenta"},
    ).get_json()
    return usuario, planta


def test_crear_planta_actualiza_config_h_conservando_el_resto(tmp_path):
    ruta = tmp_path / "config.h"
    ruta.write_text(
        '#ifndef CONFIG_H\n'
        '#define CONFIG_H\n'
        '#define DEVICE_ID    "id-anterior"\n'
        '#define DEVICE_TOKEN "token-anterior"\n'
        '#define ESPECIE      "potos"\n'
        '#define INTERVALO_SEGUNDOS 7\n'
        '#endif // CONFIG_H\n',
        encoding="utf-8",
    )
    cliente = _cliente(tmp_path, {"DEVICE_CONFIG_PATH": str(ruta)})

    _, planta = _registrar_y_crear_planta(cliente)

    contenido = ruta.read_text(encoding="utf-8")
    assert f'#define DEVICE_ID    "{planta["dispositivo_id"]}"' in contenido
    assert f'#define DEVICE_TOKEN "{planta["token_dispositivo"]}"' in contenido
    assert '#define ESPECIE      "suculenta"' in contenido
    assert "#define INTERVALO_SEGUNDOS 7" in contenido
    assert "id-anterior" not in contenido
    assert "token-anterior" not in contenido


def test_consultar_credenciales_vuelve_a_actualizar_config_h(tmp_path):
    ruta = tmp_path / "config.h"
    cliente = _cliente(tmp_path, {"DEVICE_CONFIG_PATH": str(ruta)})
    usuario, planta = _registrar_y_crear_planta(cliente)

    ruta.write_text('#define DEVICE_ID "otra-cosa"\n', encoding="utf-8")

    respuesta = cliente.get(
        f"/api/v1/plantas/{planta['id']}/credenciales",
        headers={"Authorization": f"Bearer {usuario['token']}"},
    )
    assert respuesta.status_code == 200
    credenciales = respuesta.get_json()

    contenido = ruta.read_text(encoding="utf-8")
    assert credenciales["dispositivo_id"] in contenido
    assert credenciales["token_dispositivo"] in contenido
    assert "otra-cosa" not in contenido


def test_secreto_jwt_se_persiste_entre_arranques(tmp_path):
    ruta_secreto = tmp_path / "jwt_secret.key"
    configuracion = {
        "TESTING": True,
        "DATABASE_PATH": str(tmp_path / "matera.sqlite3"),
        "JWT_SECRET": None,
        "JWT_SECRET_PATH": str(ruta_secreto),
        "DEVICE_CONFIG_PATH": None,
    }
    primero = create_app(configuracion)
    segundo = create_app(configuracion)

    assert primero.config["JWT_SECRET"]
    assert primero.config["JWT_SECRET"] == segundo.config["JWT_SECRET"]
    assert ruta_secreto.read_text(encoding="utf-8").strip() == primero.config["JWT_SECRET"]
