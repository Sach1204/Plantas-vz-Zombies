from dataclasses import replace

from app.domain.entities.lectura import OrigenLectura
from app.domain.exceptions import (
    DatoInvalido,
    DispositivoNoAutorizado,
    RecursoNoEncontrado,
)
from app.domain.ports.entrada import RegistrarLecturaPort


class RegistrarLectura(RegistrarLecturaPort):
    def __init__(self, plantas, referencias, historial, validador):
        self.plantas = plantas
        self.referencias = referencias
        self.historial = historial
        self.validador = validador

    def ejecutar(self, lectura, usuario_id=None, dispositivo_id=None):
        if (usuario_id is None) == (dispositivo_id is None):
            raise DispositivoNoAutorizado("IDENTIDAD_REQUERIDA")

        if usuario_id is not None:
            planta = self.plantas.obtener(lectura.planta_id)
            if planta is None:
                raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
            planta.asegurar_propietario(usuario_id)
            lectura = replace(lectura, origen=OrigenLectura.MANUAL)
        else:
            if lectura.dispositivo_id != dispositivo_id:
                raise DispositivoNoAutorizado("DISPOSITIVO_NO_AUTORIZADO")
            planta = self.plantas.obtener_por_dispositivo(dispositivo_id)
            if planta is None:
                raise RecursoNoEncontrado("DISPOSITIVO_NO_ASOCIADO")
            lectura = replace(
                lectura,
                especie=planta.especie,
                planta_id=planta.id,
                origen=OrigenLectura.SENSOR,
            )

        if lectura.especie.nombre.lower() != planta.especie.nombre.lower():
            raise DatoInvalido("ESPECIE_NO_CORRESPONDE_A_PLANTA")

        referencia = self.referencias.obtener_por_especie(lectura.especie.nombre)
        diagnostico = self.validador.validar(lectura, referencia)
        self.historial.guardar(lectura)
        return diagnostico
