def lectura_a_json(lectura):
    return {
        "especie": lectura.especie.nombre,
        "humedad": lectura.humedad,
        "luz": lectura.luz,
        "temperatura": lectura.temperatura,
        "marca_temporal": lectura.marca_temporal.isoformat(),
        "origen": lectura.origen.value,
    }


def diagnostico_a_json(diagnostico):
    return {
        "especie": diagnostico.especie,
        "estado": diagnostico.estado.value,
        "parametros": [
            {
                "nombre": parametro.nombre,
                "valor": parametro.valor,
                "unidad": parametro.unidad,
                "rango_min": parametro.rango_min,
                "rango_max": parametro.rango_max,
                "estado": parametro.estado.value,
            }
            for parametro in diagnostico.parametros
        ],
        "recomendaciones": list(diagnostico.recomendaciones),
    }
