from app.domain.ports.entrada import ListarEspeciesPort


class ListarEspecies(ListarEspeciesPort):
    def __init__(self, referencias):
        self.referencias = referencias

    def ejecutar(self):
        return self.referencias.listar_especies()
