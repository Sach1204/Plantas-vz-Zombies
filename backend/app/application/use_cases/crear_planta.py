from uuid import uuid4

from app.domain.entities.especie import Especie
from app.domain.entities.planta import Planta
from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import EspecieNoSoportada


class CrearPlanta:
    def __init__(self, plantas, referencias, emisor_token):
        self.plantas = plantas
        self.referencias = referencias
        self.emisor_token = emisor_token

    def ejecutar(self, usuario_id: UsuarioId, nombre, especie):
        especie = Especie(especie)
        referencia = self.referencias.obtener_por_especie(especie.nombre)
        if referencia is None:
            raise EspecieNoSoportada("ESPECIE_NO_SOPORTADA")

        planta = Planta(
            id=str(uuid4()),
            nombre=nombre.strip(),
            especie=especie,
            propietario_id=usuario_id,
            dispositivo_id=str(uuid4()),
        )
        self.plantas.guardar(planta)
        return planta, self.emisor_token.emitir_dispositivo(
            planta.dispositivo_id,
            planta.id,
        )
