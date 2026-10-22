import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def argumentos():
    parser = argparse.ArgumentParser(description="Simula lecturas de un ESP32.")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("MATERA_API_URL", "http://127.0.0.1:5000"),
    )
    parser.add_argument(
        "--device-id",
        default=os.environ.get("MATERA_DEVICE_ID"),
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("MATERA_DEVICE_TOKEN"),
    )
    parser.add_argument(
        "--especie",
        default=os.environ.get("MATERA_ESPECIE", "sansevieria"),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.environ.get("MATERA_INTERVALO", "5")),
        help="Intervalo entre reportes en segundos.",
    )
    opciones = parser.parse_args()
    if not opciones.device_id or not opciones.token:
        parser.error("indica --device-id y --token o configura sus variables MATERA_*")
    if opciones.interval <= 0:
        parser.error("--interval debe ser mayor que cero")
    return opciones


def generar_lectura(numero, dispositivo_id, especie):
    if numero % 7 == 0:
        humedad = "dato-invalido"
        luz = 700
        temperatura = 22
    elif numero % 5 == 0:
        humedad = 0
        luz = 700
        temperatura = 22
    else:
        humedad = round(random.uniform(20, 60), 1)
        luz = round(random.uniform(400, 1200), 1)
        temperatura = round(random.uniform(18, 28), 1)

    marca_temporal = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "dispositivo_id": dispositivo_id,
        "especie": especie,
        "marca_temporal": marca_temporal,
        "humedad": humedad,
        "luz": luz,
        "temperatura": temperatura,
    }


def enviar_lectura(api_url, dispositivo_id, token, lectura):
    url = (
        f"{api_url.rstrip('/')}/api/dispositivos/"
        f"{quote(dispositivo_id, safe='')}/lecturas"
    )
    solicitud = Request(
        url,
        data=json.dumps(lectura).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            contenido = respuesta.read().decode("utf-8")
            print(f"{respuesta.status}: {contenido}", flush=True)
    except HTTPError as error:
        contenido = error.read().decode("utf-8")
        print(f"HTTP {error.code}: {contenido}", flush=True)
    except URLError as error:
        print(f"No se pudo conectar con la API: {error.reason}", flush=True)


def main():
    opciones = argumentos()
    numero = 0
    print(f"Simulando {opciones.device_id} cada {opciones.interval:g} s.")
    while True:
        numero += 1
        lectura = generar_lectura(numero, opciones.device_id, opciones.especie)
        enviar_lectura(
            opciones.api_url,
            opciones.device_id,
            opciones.token,
            lectura,
        )
        time.sleep(opciones.interval)


if __name__ == "__main__":
    main()
