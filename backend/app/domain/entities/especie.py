from dataclasses import dataclass

from app.domain.exceptions import DatoInvalido


@dataclass(frozen=True)
class Especie:
    nombre: str

    def __post_init__(self):
        nombre = self.nombre.strip() if isinstance(self.nombre, str) else ""
        if not nombre:
            raise DatoInvalido("ESPECIE_INVALIDA")
        object.__setattr__(self, "nombre", nombre)
