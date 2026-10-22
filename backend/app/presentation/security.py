from functools import wraps

from flask import current_app, g, jsonify, request

from app.infrastructure.security.jwt_tokens import TokenInvalido


def requiere_usuario(vista):
    @wraps(vista)
    def protegida(*args, **kwargs):
        claims = _verificar_token("usuario")
        if not isinstance(claims, dict):
            return claims
        if "plantas:consultar" not in claims.get("scope", []):
            return jsonify({"error": "ALCANCE_INSUFICIENTE"}), 403
        g.usuario_id = claims["sub"]
        return vista(*args, **kwargs)

    return protegida


def requiere_dispositivo(vista):
    @wraps(vista)
    def protegida(*args, **kwargs):
        claims = _verificar_token("dispositivo")
        if not isinstance(claims, dict):
            return claims
        dispositivo_id = kwargs.get("dispositivo_id")
        if (
            "lecturas:reportar" not in claims.get("scope", [])
            or claims["sub"] != dispositivo_id
        ):
            return jsonify({"error": "DISPOSITIVO_NO_AUTORIZADO"}), 403
        g.dispositivo_id = claims["sub"]
        g.planta_id = claims["planta_id"]
        return vista(*args, **kwargs)

    return protegida


def _verificar_token(tipo):
    autorizacion = request.headers.get("Authorization", "")
    esquema, separador, token = autorizacion.partition(" ")
    if esquema.lower() != "bearer" or not separador or not token.strip():
        return jsonify({"error": "TOKEN_REQUERIDO"}), 401

    servicio = current_app.extensions["jwt_tokens"]
    try:
        return servicio.verificar(token.strip(), tipo)
    except TokenInvalido:
        return jsonify({"error": "TOKEN_INVALIDO"}), 401
