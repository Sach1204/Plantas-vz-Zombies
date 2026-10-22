from app.domain.exceptions import RecursoNoEncontrado
from app.domain.ports.entrada import ConsultarHistorialPort


class ConsultarHistorial(ConsultarHistorialPort):
    def __init__(self, plantas, historial):
        self.plantas = plantas
        self.historial = historial

    def ejecutar(self, planta_id, usuario_id):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)
        return self.historial.listar_por_planta(planta_id)
