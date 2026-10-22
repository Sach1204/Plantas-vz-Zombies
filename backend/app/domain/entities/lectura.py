from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite

from app.domain.entities.especie import Especie
from app.domain.exceptions import DatoInvalido


class OrigenLectura(Enum):
    SENSOR = "SENSOR"
    MANUAL = "MANUAL"


@dataclass(frozen=True)
class Lectura:
    especie: Especie
    humedad: float
    luz: float
    temperatura: float
    marca_temporal: datetime
    dispositivo_id: str | None = None
    planta_id: str | None = None
    origen: OrigenLectura = OrigenLectura.MANUAL

    def __post_init__(self):
        especie = self.especie
        if isinstance(especie, str):
            especie = Especie(especie)
            object.__setattr__(self, "especie", especie)
        elif not isinstance(especie, Especie):
            raise DatoInvalido("ESPECIE_INVALIDA")

        if not isinstance(self.marca_temporal, datetime):
            raise DatoInvalido("MARCA_TEMPORAL_INVALIDA")
        if self.marca_temporal.tzinfo is None:
            raise DatoInvalido("MARCA_TEMPORAL_INVALIDA")

        for nombre, minimo, maximo in (
            ("humedad", 0, 100),
            ("luz", 0, 200000),
            ("temperatura", -50, 80),
        ):
            valor = getattr(self, nombre)
            if isinstance(valor, bool):
                raise DatoInvalido("LECTURA_INVALIDA")
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                raise DatoInvalido("LECTURA_INVALIDA") from None
            if not isfinite(valor) or not minimo <= valor <= maximo:
                raise DatoInvalido("LECTURA_INVALIDA")
            object.__setattr__(self, nombre, valor)

        if self.origen == OrigenLectura.SENSOR and not self.dispositivo_id:
            raise DatoInvalido("DISPOSITIVO_INVALIDO")
