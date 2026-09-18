class RangoReferencia:
    def __init__(
        self,
        especie,
        humedad_min,
        humedad_max,
        luz_min,
        luz_max,
        temperatura_min,
        temperatura_max
    ):
        self.especie = especie
        self.humedad_min = humedad_min
        self.humedad_max = humedad_max
        self.luz_min = luz_min
        self.luz_max = luz_max
        self.temperatura_min = temperatura_min
        self.temperatura_max = temperatura_max

    def obtener_parametros(self, medicion):
        return [
            {
                "nombre": "humedad",
                "valor": medicion.humedad,
                "minimo": self.humedad_min,
                "maximo": self.humedad_max,
                "unidad": "%",
            },
            {
                "nombre": "luz",
                "valor": medicion.luz,
                "minimo": self.luz_min,
                "maximo": self.luz_max,
                "unidad": "lux",
            },
            {
                "nombre": "temperatura",
                "valor": medicion.temperatura,
                "minimo": self.temperatura_min,
                "maximo": self.temperatura_max,
                "unidad": "C",
            },
        ]
