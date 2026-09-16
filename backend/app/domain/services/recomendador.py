from app.domain.entities.estado_parametro import EstadoParametro


class Recomendador:

    def generar(self, resultado):
        if resultado.estado == EstadoParametro.OPTIMO:
            return None

        if resultado.nombre == "humedad":
            if resultado.estado == EstadoParametro.BAJO:
                return "La humedad del sustrato esta por debajo del rango recomendado: riegue moderadamente."
            return "La humedad del sustrato esta por encima del rango recomendado: reduzca el riego."

        if resultado.nombre == "luz":
            if resultado.estado == EstadoParametro.BAJO:
                return "La planta recibe poca luz: considere ubicarla en un lugar con mayor iluminacion."
            return "La planta recibe demasiada luz: considere reducir su exposicion directa."

        if resultado.nombre == "temperatura":
            if resultado.estado == EstadoParametro.BAJO:
                return "La temperatura esta por debajo del rango recomendado."
            return "La temperatura esta por encima del rango recomendado."

        return "El parametro esta fuera del rango recomendado."
