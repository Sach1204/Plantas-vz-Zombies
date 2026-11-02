from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

from app.domain.entities.especie import Especie
from app.domain.entities.lectura import Lectura, OrigenLectura
from app.domain.exceptions import DatoInvalido
from app.presentation.controllers.socket_controller import (
    emitir_actividad,
    emitir_lectura,
)
from app.presentation.security import requiere_usuario
from app.presentation.serializers import diagnostico_a_json, lectura_a_json

api_front_bp = Blueprint("api_front", __name__, url_prefix="/api/v1")


def _servicios():
    return current_app.extensions["matera"]


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise DatoInvalido("DATOS_DE_ENTRADA_INVALIDOS")
    return data


@api_front_bp.get("/especies")
@requiere_usuario
def listar_especies():
    referencias = _servicios()["listar_especies"].ejecutar()
    return jsonify({"especies": [rango.especie for rango in referencias]})


@api_front_bp.post("/auth/registro")
def registrar_usuario():
    data = _payload()
    usuario, token = _servicios()["registrar_usuario"].ejecutar(
        data.get("email"),
        data.get("contrasena"),
    )
    return jsonify(
        {
            "usuario": {"id": usuario.id, "email": usuario.email},
            "token": token,
        }
    ), 201


@api_front_bp.post("/auth/recuperar-contrasena")
def recuperar_contrasena():
    data = _payload()
    _servicios()["recuperar_contrasena"].ejecutar(
        data.get("email"),
        data.get("nueva_contrasena"),
    )
    return jsonify({"mensaje": "CONTRASENA_ACTUALIZADA"})


@api_front_bp.post("/auth/login")
def iniciar_sesion():
    data = _payload()
    usuario, token = _servicios()["iniciar_sesion"].ejecutar(
        data.get("email"),
        data.get("contrasena"),
    )
    return jsonify(
        {
            "usuario": {"id": usuario.id, "email": usuario.email},
            "token": token,
        }
    )


@api_front_bp.post("/plantas")
@requiere_usuario
def crear_planta():
    data = _payload()
    nombre = data.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        raise DatoInvalido("NOMBRE_DE_PLANTA_INVALIDO")
    planta, token_dispositivo = _servicios()["crear_planta"].ejecutar(
        g.usuario_id,
        nombre,
        data.get("especie", ""),
    )
    return jsonify(
        {
            "id": planta.id,
            "nombre": planta.nombre,
            "especie": planta.especie.nombre,
            "dispositivo_id": planta.dispositivo_id,
            "token_dispositivo": token_dispositivo,
        }
    ), 201


@api_front_bp.get("/plantas")
@requiere_usuario
def listar_plantas():
    plantas = _servicios()["listar_plantas"].ejecutar(g.usuario_id)
    return jsonify(
        {
            "plantas": [
                {
                    "id": planta.id,
                    "nombre": planta.nombre,
                    "especie": planta.especie.nombre,
                    "dispositivo_id": planta.dispositivo_id,
                }
                for planta in plantas
            ]
        }
    )


@api_front_bp.get("/plantas/<planta_id>/estado")
@requiere_usuario
def consultar_estado(planta_id):
    diagnostico = _servicios()["consultar_estado"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    if diagnostico is None:
        return jsonify(
            {
                "estado": "SIN_LECTURAS",
                "parametros": [],
                "recomendaciones": [],
            }
        )
    return jsonify(diagnostico_a_json(diagnostico))


@api_front_bp.get("/plantas/<planta_id>/lecturas")
@requiere_usuario
def consultar_historial(planta_id):
    lecturas = _servicios()["consultar_historial"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify({"lecturas": [lectura_a_json(item) for item in lecturas]})


@api_front_bp.post("/plantas/<planta_id>/lecturas")
@requiere_usuario
def registrar_lectura_manual(planta_id):
    data = _payload()
    lectura = Lectura(
        especie=Especie(data.get("especie")),
        humedad=data.get("humedad"),
        luz=data.get("luz"),
        temperatura=data.get("temperatura"),
        marca_temporal=datetime.now(timezone.utc),
        planta_id=planta_id,
        origen=OrigenLectura.MANUAL,
    )
    diagnostico = _servicios()["registrar_lectura"].ejecutar(
        lectura,
        usuario_id=g.usuario_id,
    )
    emitir_lectura(planta_id, lectura, diagnostico)
    return jsonify(diagnostico_a_json(diagnostico)), 201


@api_front_bp.get("/plantas/<planta_id>/credenciales")
@requiere_usuario
def consultar_credenciales_planta(planta_id):
    credenciales = _servicios()["obtener_credenciales_planta"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify(credenciales)


@api_front_bp.put("/plantas/<planta_id>")
@requiere_usuario
def editar_planta(planta_id):
    data = _payload()
    planta = _servicios()["editar_planta"].ejecutar(
        planta_id,
        g.usuario_id,
        nombre=data.get("nombre"),
        especie=data.get("especie"),
    )
    return jsonify(
        {
            "id": planta.id,
            "nombre": planta.nombre,
            "especie": planta.especie.nombre,
            "dispositivo_id": planta.dispositivo_id,
        }
    )


@api_front_bp.delete("/plantas/<planta_id>")
@requiere_usuario
def eliminar_planta(planta_id):
    _servicios()["eliminar_planta"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify({"eliminada": True})


@api_front_bp.get("/plantas/<planta_id>/colaboradores")
@requiere_usuario
def listar_colaboradores(planta_id):
    equipo = _servicios()["listar_equipo_cuidado"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify({"colaboradores": equipo})


@api_front_bp.post("/plantas/<planta_id>/colaboradores")
@requiere_usuario
def invitar_colaborador(planta_id):
    data = _payload()
    email = data.get("email")
    if not isinstance(email, str) or not email.strip():
        raise DatoInvalido("EMAIL_INVALIDO")
    colab = _servicios()["invitar_colaborador"].ejecutar(
        planta_id,
        g.usuario_id,
        email,
    )
    return jsonify(colab), 201


@api_front_bp.get("/plantas/<planta_id>/actividades")
@requiere_usuario
def listar_actividades(planta_id):
    actividades = _servicios()["listar_actividades"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify({"actividades": actividades})


@api_front_bp.post("/plantas/<planta_id>/actividades")
@requiere_usuario
def registrar_actividad(planta_id):
    data = _payload()
    accion = data.get("accion")
    if not isinstance(accion, str) or not accion.strip():
        raise DatoInvalido("ACCION_INVALIDA")
    resultado = _servicios()["registrar_actividad"].ejecutar(
        planta_id,
        g.usuario_id,
        accion,
    )
    emitir_actividad(planta_id, resultado)
    return jsonify(resultado), 201
