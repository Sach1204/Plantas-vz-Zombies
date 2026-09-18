# Plantas-vz-Zombies

Proyecto de diagnóstico de plantas con arquitectura en capas, API REST en Flask y frontend estático en HTML/CSS/JS.

## Requisitos

- Python 3.12+
- Pip para instalar dependencias
```powershell
cd .\backend
C:\Users\DANGUU\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r requirements.txt
```
- Navegador web moderno
- PowerShell o WSL

## Estructura principal

- backend/: API Flask y lógica del dominio
- frontend/: aplicación web estática
- backend/tests/: pruebas unitarias del dominio y de integración

## Ejecutar el backend

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
cd .\backend
C:\Users\DANGUU\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r requirements.txt
C:\Users\DANGUU\AppData\Local\Programs\Python\Python312\python.exe run.py
```

Esto levanta la API en:

- http://127.0.0.1:5000

Endpoints principales:

- GET /api/v1/especies
- GET /api/v1/diagnosticos
- POST /api/v1/diagnosticos

## Ejecutar el frontend

Abre otra terminal y sirve la carpeta frontend con un servidor estático, por ejemplo:

```powershell
cd .\frontend
python -m http.server 8000
```

Luego abre en el navegador:

- http://127.0.0.1:8000

El frontend consume la API del backend mediante fetch, sin recargar la página.

## Ejecutar pruebas unitarias del dominio

Desde la carpeta backend:

```powershell
cd .\backend
C:\Users\DANGUU\AppData\Local\Programs\Python\Python312\python.exe -m pytest -q tests/test_dominio.py
```

Resultado esperado:

- 7 pruebas pasando

## Pruebas completas del backend

```powershell
cd .\backend
C:\Users\DANGUU\AppData\Local\Programs\Python\Python312\python.exe -m pytest -q
```

## Observaciones

- El backend responde exclusivamente JSON.
- El frontend es cliente estático y separado.
- Las pruebas del dominio no levantan el servidor web ni leen la fuente real de datos.
- La validación de negocio usa una abstracción de referencia y dobles de prueba para aislar el dominio.