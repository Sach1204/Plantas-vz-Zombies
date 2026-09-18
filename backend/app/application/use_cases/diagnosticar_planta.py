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

        configuracion_parametros = referencia.obtener_parametros(medicion)
        parametros = self.evaluador.evaluar_parametros(configuracion_parametros)
        estado = self.evaluador.calcular_indice(parametros)

        recomendaciones = []

        for parametro in parametros:
            recomendacion = self.recomendador.generar(parametro)

            if recomendacion:
                recomendaciones.append(recomendacion)

        return {
            "especie": medicion.especie,
            "estado": estado.value,
            "parametros": [
                {
                    "nombre": parametro.nombre,
                    "valor": parametro.valor,
                    "unidad": parametro.unidad,
                    "rango_min": parametro.rango_min,
                    "rango_max": parametro.rango_max,
                    "estado": parametro.estado.value,
                }
                for parametro in parametros
            ],
            "recomendaciones": recomendaciones
        }
