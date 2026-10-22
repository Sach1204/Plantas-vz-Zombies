from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from app.domain.ports.salida import EmisorTokenPort


class TokenInvalido(Exception):
    pass


class JwtTokenService(EmisorTokenPort):
    def __init__(self, secreto, duracion_minutos=60):
        self.secreto = secreto
        self.duracion = timedelta(minutes=duracion_minutos)

    def emitir_usuario(self, usuario_id):
        return self._emitir(
            {
                "sub": usuario_id,
                "tipo": "usuario",
                "scope": ["plantas:consultar", "lecturas:registrar"],
            }
        )

    def emitir_dispositivo(self, dispositivo_id, planta_id):
        return self._emitir(
            {
                "sub": dispositivo_id,
                "tipo": "dispositivo",
                "scope": ["lecturas:reportar"],
                "planta_id": planta_id,
            }
        )

    def verificar(self, token, tipo):
        try:
            claims = jwt.decode(
                token,
                self.secreto,
                algorithms=["HS256"],
                options={"require": ["sub", "tipo", "exp"]},
            )
        except InvalidTokenError as error:
            raise TokenInvalido("TOKEN_INVALIDO") from error
        if claims.get("tipo") != tipo:
            raise TokenInvalido("TIPO_DE_TOKEN_INVALIDO")
        return claims

    def _emitir(self, claims):
        ahora = datetime.now(timezone.utc)
        payload = {
            **claims,
            "iat": ahora,
            "exp": ahora + self.duracion,
        }
        return jwt.encode(payload, self.secreto, algorithm="HS256")
