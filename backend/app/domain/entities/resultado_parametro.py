class ResultadoParametro:
    def __init__(
        self,
        nombre,
        valor,
        unidad,
        rango_min,
        rango_max,
        estado
    ):
        self.nombre = nombre
        self.valor = valor
        self.unidad = unidad
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.estado = estado
