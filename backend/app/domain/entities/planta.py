from dataclasses import dataclass

from app.domain.entities.especie import Especie
from app.domain.entities.usuario_id import UsuarioId
from app.domain.exceptions import AccesoDenegado, DatoInvalido


@dataclass(frozen=True)
class Planta:
    id: str
    nombre: str
    especie: Especie
    propietario_id: UsuarioId
    dispositivo_id: str

    def __post_init__(self):
        if (
            not isinstance(self.nombre, str)
            or not isinstance(self.id, str)
            or not isinstance(self.propietario_id, str)
            or not isinstance(self.dispositivo_id, str)
            or not all((self.id, self.nombre.strip(), self.propietario_id, self.dispositivo_id))
        ):
            raise DatoInvalido("PLANTA_INVALIDA")
        if isinstance(self.especie, str):
            object.__setattr__(self, "especie", Especie(self.especie))
        object.__setattr__(self, "propietario_id", UsuarioId(self.propietario_id))

    def asegurar_propietario(self, usuario_id):
        if usuario_id != self.propietario_id:
            raise AccesoDenegado("PLANTA_NO_PERTENECE_AL_USUARIO")
