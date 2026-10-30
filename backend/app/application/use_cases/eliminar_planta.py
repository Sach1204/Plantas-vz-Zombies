from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import RecursoNoEncontrado


class EliminarPlanta:
    def __init__(self, plantas):
        self.plantas = plantas

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)
        self.plantas.eliminar(planta_id)
        return True

