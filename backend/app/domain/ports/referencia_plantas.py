from abc import ABC, abstractmethod


class ReferenciaPlantas(ABC):

    @abstractmethod
    def obtener_por_especie(self, especie):
        pass

    @abstractmethod
    def listar_especies(self):
        pass
