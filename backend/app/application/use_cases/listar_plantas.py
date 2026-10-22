from app.domain.ports.entrada import ListarPlantasPort
from app.domain.entities.usuario_id import UsuarioId


class ListarPlantas(ListarPlantasPort):
    def __init__(self, plantas):
        self.plantas = plantas

    def ejecutar(self, usuario_id: UsuarioId):
        return self.plantas.listar_por_usuario(usuario_id)
