# Plantas vs Zombies

API Flask y aplicación web estática para registrar y consultar lecturas de plantas. El
frontend se ejecuta por separado y consulta la API con `fetch`; no se renderiza desde
Flask.

## Requisitos

- Python 3.12 o superior
- Navegador web moderno
- PowerShell en Windows (o una terminal equivalente)

## Ejecutar el backend

En una terminal:

```powershell
cd .\backend
py -3.12 -m pip install -r .\requirements.txt
$env:MATERA_JWT_SECRET = "cambia-esto-por-un-secreto-largo"
py -3.12 .\run.py
```

La API queda disponible en `http://127.0.0.1:5000`. La base SQLite guarda usuarios,
plantas y lecturas en `backend/app/infrastructure/data/matera.sqlite3`. Define
`MATERA_DATABASE_PATH` para usar otra ubicación. Si no se define
`MATERA_JWT_SECRET`, se genera un secreto temporal al iniciar; configura uno estable
para conservar la validez de los tokens entre reinicios.

La tabla de referencia se selecciona por configuración:

```powershell
$env:MATERA_REFERENCE_ADAPTER = "csv"
```

Usa `"sqlite"` para leer la tabla de referencia desde SQLite. La primera ejecución en
ese modo importa las especies del CSV actual si la tabla está vacía. Ambos adaptadores
implementan el mismo puerto y la selección no cambia el dominio.

## Ejecutar el frontend

En otra terminal, desde la raíz del repositorio:

```powershell
cd .\frontend
py -3.12 -m http.server 8000
```

Abre `http://127.0.0.1:8000`. Regístrate o inicia sesión, agrega una planta y elige su
especie. El panel consulta automáticamente el estado y el historial cada cinco segundos.
También permite guardar una lectura manual.

Al agregar una planta, copia el identificador y token del dispositivo: el token se muestra
una sola vez y es independiente del token de usuario.

## Ejecutar el simulador ESP32

Con el backend encendido y una planta creada, abre una tercera terminal y proporciona las
credenciales de dispositivo mostradas por el frontend:

```powershell
cd .\backend
$env:MATERA_DEVICE_ID = "id-del-dispositivo"
$env:MATERA_DEVICE_TOKEN = "token-del-dispositivo"
py -3.12 .\simulador_esp32.py --interval 5 --especie sansevieria
```

También admite `--device-id`, `--token`, `--api-url` y `--interval`; el intervalo debe ser
mayor que cero. Cada quinto envío produce una humedad físicamente válida pero fuera del
rango de referencia; cada séptimo envía un dato no numérico para comprobar que la API lo
rechace con HTTP 400 sin guardarlo.

## Endpoints principales

- `POST /api/v1/auth/registro` y `POST /api/v1/auth/login`: autenticación de usuarios.
- `GET /api/v1/especies`, `GET /api/v1/plantas` y `POST /api/v1/plantas`: requieren JWT
  de usuario.
- `GET /api/v1/plantas/{id}/estado` y `GET /api/v1/plantas/{id}/lecturas`: solo el
  propietario puede consultar estado e historial.
- `POST /api/v1/plantas/{id}/lecturas`: registra una lectura manual y requiere JWT de
  usuario.
- `POST /api/dispositivos/{id}/lecturas`: recibe lecturas del sensor y requiere un JWT de
  dispositivo limitado a reportar para su planta.

Un valor inválido (por ejemplo, humedad no numérica o fuera de los límites físicos) produce
HTTP 400. Una lectura físicamente válida que queda fuera del rango recomendado de su
especie se guarda y produce un estado como `EN_RIESGO` o `CRITICO`.

## Pruebas

Desde `backend`:

```powershell
py -3.12 -m pytest -q tests/test_dominio.py
py -3.12 -m pytest -q
```

Las pruebas de dominio invocan los casos de uso directamente con dobles de los puertos;
no inician Flask ni requieren archivos o base de datos.
