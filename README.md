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
`MATERA_DATABASE_PATH` para usar otra ubicación.

Si no se define `MATERA_JWT_SECRET`, el backend genera un secreto una sola vez y lo
guarda en `backend/app/infrastructure/data/jwt_secret.key`; en los siguientes arranques
lo reutiliza, así que los tokens de los dispositivos siguen siendo válidos. Puedes
sobrescribirlo con `MATERA_JWT_SECRET` o cambiar la ruta con `MATERA_JWT_SECRET_PATH`.

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
especie. La interfaz responsive incluye panel del jardín, colección con filtros, detalle
por planta, gráficas e historial exportable, diagnóstico manual, notificaciones locales y
configuración. El panel mantiene una consulta de respaldo cada cinco segundos y recibe las
lecturas nuevas por WebSocket sin refrescar la página.

El alta de planta usa un flujo de tres pasos. Al crear la planta, el backend escribe
automáticamente su identificador, token y especie en `esp32/include/config.h`; no hace
falta copiar nada a mano. Para cambiar de planta activa en Wokwi, abre el detalle de la
planta y consulta sus credenciales: el archivo se vuelve a escribir con esa planta. El
token del dispositivo es independiente del token de usuario.

El mockup también muestra invitaciones y cuidado compartido. La API de esta fase no
implementa colaboradores ni invitaciones; esa pantalla informa la limitación y no simula
un permiso que el backend no puede comprobar. Las alertas visibles se generan en este
navegador cuando cambia el estado observado de una planta; no son notificaciones push del
servidor.

## Actualizaciones en tiempo real

El backend publica eventos con Flask-SocketIO en el mismo puerto que la API. El cliente de
Socket.IO se sirve desde `frontend/js/vendor/socket.io.min.js`, así que no hace falta
conexión a internet para usarlo.

- Al iniciar sesión, el navegador abre la conexión con su JWT y se suscribe a cada planta
  que puede consultar (propietario o colaborador).
- Cuando llega una lectura por `POST /api/dispositivos/{id}/lecturas` o por
  `POST /api/v1/plantas/{id}/lecturas`, el backend calcula el diagnóstico y emite
  `lectura_registrada` a la sala de esa planta.
- El frontend actualiza el estado, las gráficas y las alertas con el evento recibido.
- Los cambios de actividad compartida emiten `actividad_registrada`.

La conexión se autentica con el mismo JWT de usuario; el servidor comprueba el permiso de
cada planta antes de permitir la suscripción. Los dispositivos ESP32 siguen reportando por
HTTP, de modo que el backend puede guardar lecturas aunque no haya ningún navegador
conectado.

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
