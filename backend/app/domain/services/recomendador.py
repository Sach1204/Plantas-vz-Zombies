from app.domain.entities.estado_parametro import EstadoParametro


class EstrategiaRecomendacion:
    """Contrato que debe cumplir la recomendación de un parámetro.
    Nuevas reglas (pH, etc.) implementan esto sin tocar Recomendador."""

    def generar(self, estado):
        raise NotImplementedError


class RecomendacionHumedad(EstrategiaRecomendacion):
    def generar(self, estado):
        if estado == EstadoParametro.BAJO:
            return "La humedad del sustrato esta por debajo del rango recomendado: riegue moderadamente."
        return "La humedad del sustrato esta por encima del rango recomendado: reduzca el riego."


class RecomendacionLuz(EstrategiaRecomendacion):
    def generar(self, estado):
        if estado == EstadoParametro.BAJO:
            return "La planta recibe poca luz: considere ubicarla en un lugar con mayor iluminacion."
        return "La planta recibe demasiada luz: considere reducir su exposicion directa."


class RecomendacionTemperatura(EstrategiaRecomendacion):
    def generar(self, estado):
        if estado == EstadoParametro.BAJO:
            return "La temperatura esta por debajo del rango recomendado."
        return "La temperatura esta por encima del rango recomendado."


class RecomendacionGenerica(EstrategiaRecomendacion):
    def generar(self, estado):
        return "El parametro esta fuera del rango recomendado."


def estrategias_por_defecto():
    """Punto de registro: agregar un parámetro nuevo es agregar una línea
    aquí, no modificar la clase Recomendador."""
    return {
        "humedad": RecomendacionHumedad(),
        "luz": RecomendacionLuz(),
        "temperatura": RecomendacionTemperatura(),
    }


class Recomendador:

    def __init__(self, estrategias=None, estrategia_por_defecto=None):
        self.estrategias = estrategias or estrategias_por_defecto()
        self.estrategia_por_defecto = estrategia_por_defecto or RecomendacionGenerica()

    def generar(self, resultado):
        if resultado.estado == EstadoParametro.OPTIMO:
            return None

        estrategia = self.estrategias.get(resultado.nombre, self.estrategia_por_defecto)
        return estrategia.generar(resultado.estado)
