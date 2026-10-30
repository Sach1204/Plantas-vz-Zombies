#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHTesp.h>
#include <time.h>
#include "config.h"

DHTesp dht;

unsigned long ultimaTransmision = 0;
const unsigned long intervaloTransmision = INTERVALO_SEGUNDOS * 1000UL;

void sincronizarHoraNTP() {
    Serial.print(F("[NTP] Sincronizando hora con pool.ntp.org..."));
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    time_t ahora = time(nullptr);
    int intentos = 0;
    while (ahora < 100000 && intentos < 20) {
        delay(300);
        Serial.print(F("."));
        ahora = time(nullptr);
        intentos++;
    }
    if (ahora >= 100000) {
        Serial.println(F(" OK!"));
    } else {
        Serial.println(F(" (Se usará marca temporal estimada)"));
    }
}

String obtenerMarcaTemporalISO() {
    time_t ahora = time(nullptr);
    struct tm infoTiempo;
    if (ahora >= 100000 && gmtime_r(&ahora, &infoTiempo)) {
        char buffer[32];
        strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &infoTiempo);
        return String(buffer);
    }
    // Si NTP tarda en sincronizar, calcular marca temporal coherente
    unsigned long seg = millis() / 1000;
    char buffer[32];
    snprintf(buffer, sizeof(buffer), "2026-10-30T12:%02lu:%02luZ", (seg / 60) % 60, seg % 60);
    return String(buffer);
}

float calcularLuxLDR(int pin) {
    int lecturaAnalogica = analogRead(pin);
    if (lecturaAnalogica <= 0) lecturaAnalogica = 1;
    if (lecturaAnalogica >= 4095) lecturaAnalogica = 4094;

    float voltaje = (float)lecturaAnalogica / 4095.0f * 3.3f;
    float resistencia = 2000.0f * voltaje / (1.0f - voltaje / 3.3f);
    const float GAMMA = 0.7f;
    const float RL10 = 50.0f;
    float lux = pow((RL10 * 1e3 * pow(10, GAMMA)) / resistencia, (1.0f / GAMMA));

    if (isnan(lux) || isinf(lux) || lux < 0) lux = 0;
    if (lux > 200000) lux = 200000;
    return round(lux * 10.0f) / 10.0f;
}

void conectarWiFi() {
    Serial.println();
    Serial.println(F("=================================================="));
    Serial.println(F("   🌱 Plantas vs Zombies · ESP32 Sensor Matera   "));
    Serial.println(F("=================================================="));
    Serial.printf("[WiFi] Conectando a red virtual Wokwi: %s", WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);

    int intentos = 0;
    while (WiFi.status() != WL_CONNECTED && intentos < 30) {
        delay(400);
        Serial.print(F("."));
        intentos++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F(" CONECTADO!"));
        Serial.print(F("[WiFi] Dirección IP asignada: "));
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(F(" [ERROR] No se pudo conectar al WiFi"));
    }
}

void actualizarLEDs(const String& estado) {
    if (estado == "SALUDABLE") {
        digitalWrite(PIN_LED_OK, HIGH);
        digitalWrite(PIN_LED_ALERTA, LOW);
    } else if (estado == "EN_RIESGO" || estado == "CRITICO") {
        digitalWrite(PIN_LED_OK, LOW);
        digitalWrite(PIN_LED_ALERTA, HIGH);
    } else {
        digitalWrite(PIN_LED_OK, LOW);
        digitalWrite(PIN_LED_ALERTA, LOW);
    }
}

void enviarLectura(float humedad, float luz, float temperatura) {
    if (String(DEVICE_ID) == "id-del-dispositivo" || String(DEVICE_TOKEN) == "token-del-dispositivo") {
        Serial.println(F("--------------------------------------------------"));
        Serial.println(F("⚠️  ATENCIÓN: Credenciales de dispositivo sin configurar."));
        Serial.println(F("Abre esp32/include/config.h y coloca el DEVICE_ID y DEVICE_TOKEN"));
        Serial.println(F("que te da el Frontend web al agregar una planta."));
        Serial.println(F("--------------------------------------------------"));
        return;
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println(F("[HTTP] WiFi desconectado. Reintentando conexión..."));
        WiFi.reconnect();
        return;
    }

    HTTPClient http;
    String url = String(BACKEND_BASE_URL) + "/api/dispositivos/" + String(DEVICE_ID) + "/lecturas";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer " + String(DEVICE_TOKEN));

    String timestamp = obtenerMarcaTemporalISO();

    StaticJsonDocument<256> doc;
    doc["dispositivo_id"] = DEVICE_ID;
    doc["especie"] = ESPECIE;
    doc["marca_temporal"] = timestamp;
    doc["humedad"] = humedad;
    doc["luz"] = luz;
    doc["temperatura"] = temperatura;

    String payload;
    serializeJson(doc, payload);

    Serial.println(F("--------------------------------------------------"));
    Serial.printf("[SENSOR] Humedad: %.1f %% | Luz: %.1f lux | Temp: %.1f °C\n", humedad, luz, temperatura);
    Serial.printf("[HTTP POST] Enviando a: %s\n", url.c_str());
    Serial.printf("[PAYLOAD] %s\n", payload.c_str());

    int codigoHttp = http.POST(payload);

    if (codigoHttp > 0) {
        String respuesta = http.getString();
        Serial.printf("[HTTP] Código respuesta: %d\n", codigoHttp);
        Serial.printf("[RESPUESTA] %s\n", respuesta.c_str());

        if (codigoHttp == 201) {
            StaticJsonDocument<256> respDoc;
            DeserializationError err = deserializeJson(respDoc, respuesta);
            if (!err) {
                const char* estado = respDoc["estado"] | "DESCONOCIDO";
                Serial.printf(">>> ESTADO PLANTA EN BACKEND: [%s] <<<\n", estado);
                actualizarLEDs(estado);
            }
        } else {
            Serial.println(F("[HTTP] Error en reporte de lectura. Verifica credenciales y especie."));
            digitalWrite(PIN_LED_OK, LOW);
            digitalWrite(PIN_LED_ALERTA, HIGH);
        }
    } else {
        Serial.printf("[HTTP] Falló la petición. Error: %s\n", http.errorToString(codigoHttp).c_str());
        Serial.println(F("[TIP] Asegúrate de que el backend Flask esté corriendo en tu PC (run.py con host='0.0.0.0')."));
        digitalWrite(PIN_LED_OK, LOW);
        digitalWrite(PIN_LED_ALERTA, HIGH);
    }

    http.end();
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(PIN_LED_OK, OUTPUT);
    pinMode(PIN_LED_ALERTA, OUTPUT);
    pinMode(PIN_LDR, INPUT);

    digitalWrite(PIN_LED_OK, LOW);
    digitalWrite(PIN_LED_ALERTA, LOW);

    // Inicializar sensor DHT22
    dht.setup(PIN_DHT, DHTesp::DHT22);
    Serial.println(F("[DHT22] Sensor inicializado en GPIO 15"));

    // Conectar WiFi
    conectarWiFi();

    // Sincronizar NTP
    sincronizarHoraNTP();

    Serial.println(F("[SISTEMA] Inicialización completa. Iniciando ciclo de lecturas."));
}

void loop() {
    unsigned long ahora = millis();
    if (ahora - ultimaTransmision >= intervaloTransmision) {
        ultimaTransmision = ahora;

        // Leer DHT22
        TempAndHumidity lecturaDHT = dht.getTempAndHumidity();
        float temperatura = lecturaDHT.temperature;
        float humedad = lecturaDHT.humidity;

        // Manejar fallas de lectura en simulación
        if (isnan(temperatura) || isnan(humedad)) {
            temperatura = 22.0f;
            humedad = 45.0f;
        }

        // Leer LDR (Luz en Lux)
        float luz = calcularLuxLDR(PIN_LDR);

        // Enviar al backend Flask
        enviarLectura(humedad, luz, temperatura);
    }

    delay(50);
}

