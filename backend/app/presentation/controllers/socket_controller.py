from flask import current_app, request
from flask_socketio import SocketIO, disconnect, join_room, leave_room

from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import AccesoDenegado, RecursoNoEncontrado
from app.infrastructure.security.jwt_tokens import TokenInvalido
from app.presentation.serializers import diagnostico_a_json, lectura_a_json

socketio = SocketIO()
_sesiones = {}


def sala_de_planta(planta_id):
    return f"planta:{planta_id}"


def inicializar_socketio(app):
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
    )
    return socketio


def _usuario_del_socket(auth):
    token = auth.get("token") if isinstance(auth, dict) else None
    if not token:
        token = request.args.get("token")
    if not isinstance(token, str) or not token.strip():
        return None
    try:
        claims = current_app.extensions["jwt_tokens"].verificar(
            token.strip(),
            "usuario",
        )
    except TokenInvalido:
        return None
    if "plantas:consultar" not in claims.get("scope", []):
        return None
    return claims.get("sub")


@socketio.on("connect")
def al_conectar(auth):
    usuario_id = _usuario_del_socket(auth)
    if not usuario_id:
        raise ConnectionRefusedError("TOKEN_REQUERIDO")
    _sesiones[request.sid] = usuario_id


@socketio.on("disconnect")
def al_desconectar():
    _sesiones.pop(request.sid, None)


@socketio.on("suscribir_planta")
def suscribir_planta(data):
    usuario_id = _sesiones.get(request.sid)
    if not usuario_id:
        disconnect()
        return {"ok": False, "error": "NO_AUTORIZADO"}
    planta_id = data.get("planta_id") if isinstance(data, dict) else None
    if not isinstance(planta_id, str) or not planta_id.strip():
        return {"ok": False, "error": "PLANTA_INVALIDA"}

    try:
        current_app.extensions["matera"]["listar_equipo_cuidado"].ejecutar(
            planta_id,
            UsuarioId(usuario_id),
        )
    except (AccesoDenegado, RecursoNoEncontrado):
        return {"ok": False, "error": "ACCESO_DENEGADO"}

    join_room(sala_de_planta(planta_id))
    return {"ok": True, "planta_id": planta_id}


@socketio.on("desuscribir_planta")
def desuscribir_planta(data):
    planta_id = data.get("planta_id") if isinstance(data, dict) else None
    if isinstance(planta_id, str) and planta_id.strip():
        leave_room(sala_de_planta(planta_id))
        return {"ok": True, "planta_id": planta_id}
    return {"ok": False, "error": "PLANTA_INVALIDA"}


def emitir_lectura(planta_id, lectura, diagnostico):
    socketio.emit(
        "lectura_registrada",
        {
            "planta_id": planta_id,
            "lectura": lectura_a_json(lectura),
            "diagnostico": diagnostico_a_json(diagnostico),
        },
        to=sala_de_planta(planta_id),
    )


def emitir_actividad(planta_id, actividad):
    socketio.emit(
        "actividad_registrada",
        {"planta_id": planta_id, "actividad": actividad},
        to=sala_de_planta(planta_id),
    )
