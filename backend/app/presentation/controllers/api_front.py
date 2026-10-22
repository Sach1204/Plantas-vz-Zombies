from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

from app.domain.entities.especie import Especie
from app.domain.entities.lectura import Lectura, OrigenLectura
from app.domain.exceptions import DatoInvalido, RecursoNoEncontrado
from app.presentation.security import requiere_usuario

api_front_bp = Blueprint("api_front", __name__, url_prefix="/api/v1")


def _servicios():
    return current_app.extensions["matera"]


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise DatoInvalido("DATOS_DE_ENTRADA_INVALIDOS")
    return data


def _a_json_lectura(lectura):
    return {
        "especie": lectura.especie.nombre,
        "humedad": lectura.humedad,
        "luz": lectura.luz,
        "temperatura": lectura.temperatura,
        "marca_temporal": lectura.marca_temporal.isoformat(),
        "origen": lectura.origen.value,
    }


def _a_json_diagnostico(diagnostico):
    return {
        "especie": diagnostico.especie,
        "estado": diagnostico.estado.value,
        "parametros": [
            {
                "nombre": parametro.nombre,
                "valor": parametro.valor,
                "unidad": parametro.unidad,
                "rango_min": parametro.rango_min,
                "rango_max": parametro.rango_max,
                "estado": parametro.estado.value,
            }
            for parametro in diagnostico.parametros
        ],
        "recomendaciones": list(diagnostico.recomendaciones),
    }


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
        raise RecursoNoEncontrado("LECTURAS_NO_ENCONTRADAS")
    return jsonify(_a_json_diagnostico(diagnostico))


@api_front_bp.get("/plantas/<planta_id>/lecturas")
@requiere_usuario
def consultar_historial(planta_id):
    lecturas = _servicios()["consultar_historial"].ejecutar(
        planta_id,
        g.usuario_id,
    )
    return jsonify({"lecturas": [_a_json_lectura(item) for item in lecturas]})


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
    return jsonify(_a_json_diagnostico(diagnostico)), 201
