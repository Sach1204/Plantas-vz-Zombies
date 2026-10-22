from dataclasses import dataclass

from app.domain.entities.estado import Estado
from app.domain.entities.resultado_parametro import ResultadoParametro


@dataclass(frozen=True)
class Diagnostico:
    especie: str
    estado: Estado
    parametros: tuple[ResultadoParametro, ...]
    recomendaciones: tuple[str, ...]
