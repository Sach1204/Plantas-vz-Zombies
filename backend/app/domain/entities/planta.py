from dataclasses import dataclass

from app.domain.entities.especie import Especie
from app.domain.exceptions import AccesoDenegado, DatoInvalido


@dataclass(frozen=True)
class Planta:
    id: str
    nombre: str
    especie: Especie
    propietario_id: str
    dispositivo_id: str

    def __post_init__(self):
        if not all((self.id, self.nombre.strip(), self.propietario_id, self.dispositivo_id)):
            raise DatoInvalido("PLANTA_INVALIDA")
        if isinstance(self.especie, str):
            object.__setattr__(self, "especie", Especie(self.especie))

    def asegurar_propietario(self, usuario_id):
        if usuario_id != self.propietario_id:
            raise AccesoDenegado("PLANTA_NO_PERTENECE_AL_USUARIO")
