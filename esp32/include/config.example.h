#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// CREDENCIALES DEL DISPOSITIVO
// El backend crea y actualiza config.h automáticamente al agregar una planta
// o al consultar sus credenciales. Usa este archivo solo como referencia.
// config.h está ignorado por git para no subir credenciales reales.
// ============================================================================
#define DEVICE_ID    "id-del-dispositivo"
#define DEVICE_TOKEN "token-del-dispositivo"
#define ESPECIE      "suculenta" // Opciones: sansevieria, potos, suculenta, helecho, lavanda, manito

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
