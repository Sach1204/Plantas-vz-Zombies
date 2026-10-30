from app.domain.entities.especie import Especie
from app.domain.entities.planta import Planta
from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import DatoInvalido, EspecieNoSoportada, RecursoNoEncontrado


class EditarPlanta:
    def __init__(self, plantas, referencias):
        self.plantas = plantas
        self.referencias = referencias

    def ejecutar(self, planta_id, usuario_id: UsuarioId, nombre, especie=None):
        planta = self.plantas.obtener(planta_id)
        if planta is None:
            raise RecursoNoEncontrado("PLANTA_NO_ENCONTRADA")
        planta.asegurar_propietario(usuario_id)

        nueva_especie = planta.especie
        if especie:
            nueva_especie = Especie(especie)
            if self.referencias.obtener_por_especie(nueva_especie.nombre) is None:
                raise EspecieNoSoportada("ESPECIE_NO_SOPORTADA")

        nuevo_nombre = nombre.strip() if nombre else planta.nombre
        if not nuevo_nombre:
            raise DatoInvalido("NOMBRE_INVALIDO")

        planta_actualizada = Planta(
            id=planta.id,
            nombre=nuevo_nombre,
            especie=nueva_especie,
            propietario_id=planta.propietario_id,
            dispositivo_id=planta.dispositivo_id,
        )
        self.plantas.actualizar(planta_actualizada)
        return planta_actualizada

