from app.domain.ports.entrada import ListarPlantasPort


class ListarPlantas(ListarPlantasPort):
    def __init__(self, plantas):
        self.plantas = plantas

    def ejecutar(self, usuario_id):
        return self.plantas.listar_por_usuario(usuario_id)
