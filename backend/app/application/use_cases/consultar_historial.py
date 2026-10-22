from app.domain.exceptions import RecursoNoEncontrado
from app.domain.entities.usuario_id import UsuarioId
from app.domain.ports.entrada import ConsultarHistorialPort


class ConsultarHistorial(ConsultarHistorialPort):
    def __init__(self, plantas, historial):
        self.plantas = plantas
        self.historial = historial

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)
        return self.historial.listar_por_planta(planta_id)
