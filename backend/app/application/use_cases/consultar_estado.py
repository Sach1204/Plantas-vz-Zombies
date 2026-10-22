from app.domain.exceptions import RecursoNoEncontrado
from app.domain.entities.usuario_id import UsuarioId
from app.domain.ports.entrada import ConsultarEstadoPort


class ConsultarEstado(ConsultarEstadoPort):
    def __init__(self, plantas, referencias, historial, validador):
        self.plantas = plantas
        self.referencias = referencias
        self.historial = historial
        self.validador = validador

    def ejecutar(self, planta_id, usuario_id: UsuarioId):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)

        lectura = self.historial.ultima_por_planta(planta_id)
        if lectura is None:
            return None
        referencia = self.referencias.obtener_por_especie(planta.especie.nombre)
        return self.validador.validar(lectura, referencia)
