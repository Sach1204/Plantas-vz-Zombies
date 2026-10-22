import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hash_contrasena TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plantas (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    especie TEXT NOT NULL,
    propietario_id TEXT NOT NULL REFERENCES usuarios(id),
    dispositivo_id TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS referencias (
    especie TEXT PRIMARY KEY COLLATE NOCASE,
    humedad_min REAL NOT NULL,
    humedad_max REAL NOT NULL,
    luz_min REAL NOT NULL,
    luz_max REAL NOT NULL,
    temperatura_min REAL NOT NULL,
    temperatura_max REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planta_id TEXT NOT NULL REFERENCES plantas(id),
    dispositivo_id TEXT,
    marca_temporal TEXT NOT NULL,
    especie TEXT NOT NULL,
    humedad REAL NOT NULL,
    luz REAL NOT NULL,
    temperatura REAL NOT NULL,
    origen TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lecturas_planta_fecha
    ON lecturas(planta_id, marca_temporal DESC);
"""


class SQLiteDatabase:
    def __init__(self, ruta):
        self.ruta = str(ruta)
        if self.ruta != ":memory:":
            Path(self.ruta).parent.mkdir(parents=True, exist_ok=True)
        self.inicializar()

    def conectar(self):
        conexion = sqlite3.connect(self.ruta, timeout=10)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def inicializar(self):
        with self.conectar() as conexion:
            conexion.executescript(SCHEMA)
