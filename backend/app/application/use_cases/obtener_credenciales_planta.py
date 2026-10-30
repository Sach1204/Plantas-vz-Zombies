from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import RecursoNoEncontrado


class ObtenerCredencialesPlanta:
    def __init__(self, plantas, emisor_token):
        self.plantas = plantas
        self.emisor_token = emisor_token

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)

        token = self.emisor_token.emitir_dispositivo(
            planta.dispositivo_id,
            planta.id,
        )
        return {
            "planta_id": planta.id,
            "nombre": planta.nombre,
            "especie": planta.especie.nombre,
            "dispositivo_id": planta.dispositivo_id,
            "token_dispositivo": token,
        }

