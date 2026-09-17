class DiagnosticarPlanta:

    def __init__(self, referencia, evaluador, recomendador):
        self.referencia = referencia
        self.evaluador = evaluador
        self.recomendador = recomendador

    def ejecutar(self, medicion):

        referencia = self.referencia.obtener_por_especie(
            medicion.especie
        )

        if referencia is None:
            raise ValueError("ESPECIE_NO_SOPORTADA")

        humedad = self.evaluador.evaluar_parametro(
            "humedad",
            medicion.humedad,
            referencia.humedad_min,
            referencia.humedad_max,
            "%"
        )

        luz = self.evaluador.evaluar_parametro(
            "luz",
            medicion.luz,
            referencia.luz_min,
            referencia.luz_max,
            "lux"
        )

        temperatura = self.evaluador.evaluar_parametro(
            "temperatura",
            medicion.temperatura,
            referencia.temperatura_min,
            referencia.temperatura_max,
            "C"
        )

        parametros = [
            humedad,
            luz,
            temperatura
        ]

        estado = self.evaluador.calcular_indice(parametros)

        recomendaciones = []

        for parametro in parametros:
            recomendacion = self.recomendador.generar(parametro)

            if recomendacion:
                recomendaciones.append(recomendacion)

        return {
            "especie": medicion.especie,
            "estado": estado.value,
            "parametros": parametros,
            "recomendaciones": recomendaciones
        }
