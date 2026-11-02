from pathlib import Path
import re


PLANTILLA = """\
#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// CREDENCIALES DEL DISPOSITIVO
// Este archivo se actualiza automáticamente desde el backend al crear una
// planta o al consultar sus credenciales. No hace falta editar estas líneas.
// ============================================================================
#define DEVICE_ID    "{dispositivo_id}"
#define DEVICE_TOKEN "{token_dispositivo}"
#define ESPECIE      "{especie}" // Opciones: sansevieria, potos, suculenta, helecho, lavanda, manito

// ============================================================================
// CONFIGURACIÓN DE RED Y SERVIDOR
// ============================================================================
#define WIFI_SSID     "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// En el simulador Wokwi, "host.wokwi.internal" redirige al localhost de tu máquina.
#define BACKEND_BASE_URL "http://host.wokwi.internal:5000"

// Intervalo de reporte de lecturas (en segundos)
#define INTERVALO_SEGUNDOS 5

// Asignación de pines (coincide exactamente con diagram.json)
#define PIN_DHT        15
#define PIN_LDR        34
#define PIN_LED_OK     18
#define PIN_LED_ALERTA 19

#endif // CONFIG_H
"""


class EscritorConfiguracionDispositivo:
    def __init__(self, ruta):
        self.ruta = Path(ruta) if ruta else None

    def escribir(self, planta, token_dispositivo):
        if self.ruta is None:
            return
        try:
            contenido = self.ruta.read_text(encoding="utf-8")
        except FileNotFoundError:
            contenido = PLANTILLA
        except OSError:
            return

        contenido = _definir(contenido, "DEVICE_ID", planta.dispositivo_id)
        contenido = _definir(contenido, "DEVICE_TOKEN", token_dispositivo)
        contenido = _definir(contenido, "ESPECIE", planta.especie.nombre)

        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            self.ruta.write_text(contenido, encoding="utf-8")
        except OSError:
            return


def _definir(contenido, nombre, valor):
    patron = re.compile(r'(#define\s+' + re.escape(nombre) + r'\s+)"[^"]*"')
    nuevo, reemplazos = patron.subn(lambda coincidencia: f'{coincidencia.group(1)}"{valor}"', contenido)
    if reemplazos:
        return nuevo
    indice = contenido.rfind("#endif")
    if indice == -1:
        return contenido.rstrip() + f'\n#define {nombre} "{valor}"\n'
    return contenido[:indice] + f'#define {nombre} "{valor}"\n' + contenido[indice:]
