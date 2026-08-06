"""Consulta el estado de un servidor Arma 3 mediante el protocolo Steam A2S.

El servidor de Arma 3 expone el puerto de consulta en <puerto_juego> + 1.
Para LAZARUS OPS: juego en 2332, consulta en 2333.
"""

import math
import os
import socket
import struct
from dataclasses import dataclass, field

HOST = os.environ.get("ARMA_HOST", "38.225.91.3")
PORT = int(os.environ.get("ARMA_QUERY_PORT", "2333"))
TIMEOUT = 5

MAGIC = b"\xff\xff\xff\xff"
A2S_INFO = b"\x54Source Engine Query\x00"
A2S_PLAYER = b"\x55"


@dataclass
class Jugador:
    nombre: str
    segundos: float

    @property
    def tiempo(self) -> str:
        """Devuelve el tiempo de sesion como '1h 12m' o '34m'.

        Arma devuelve a veces -1 o NaN para jugadores que aun estan entrando,
        asi que hay que sanearlo: un NaN reventaba int() y dejaba el mensaje
        sin actualizar hasta que ese jugador se iba.
        """
        if not math.isfinite(self.segundos) or self.segundos < 0:
            return "nuevo"
        total = int(self.segundos)
        if total < 60:
            return "<1m"
        horas, minutos = total // 3600, (total % 3600) // 60
        return f"{horas}h {minutos:02d}m" if horas else f"{minutos}m"


@dataclass
class Estado:
    en_linea: bool
    nombre: str = ""
    mision: str = ""
    mapa: str = ""
    jugadores: int = 0
    maximo: int = 0
    con_clave: bool = False
    version: str = ""
    lista: list = field(default_factory=list)


def _leer_cadena(datos: bytes, i: int) -> tuple:
    """Lee una cadena terminada en nulo. Devuelve (texto, indice_siguiente)."""
    fin = datos.index(b"\x00", i)
    return datos[i:fin].decode("utf-8", "replace"), fin + 1


def _consultar(payload: bytes, sufijo_challenge: bool = False) -> bytes:
    """Envia una consulta A2S resolviendo el challenge si el servidor lo pide."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.sendto(MAGIC + payload, (HOST, PORT))
        datos, _ = sock.recvfrom(8192)
        if datos[4:5] == b"A":  # 0x41 = el servidor exige challenge
            challenge = datos[5:9]
            reintento = payload + challenge if sufijo_challenge else payload[:1] + challenge
            sock.sendto(MAGIC + reintento, (HOST, PORT))
            datos, _ = sock.recvfrom(8192)
        return datos
    finally:
        sock.close()


def _parsear_info(datos: bytes) -> Estado:
    # 0-3 cabecera magica, 4 el byte 'I', 5 la version de protocolo.
    # El nombre empieza en el 6: arrancar en el 5 colaba el byte de protocolo
    # (0x11) como primer caracter del nombre del servidor.
    i = 6
    nombre, i = _leer_cadena(datos, i)
    mapa, i = _leer_cadena(datos, i)
    _carpeta, i = _leer_cadena(datos, i)
    mision, i = _leer_cadena(datos, i)
    i += 2  # appid
    jugadores, maximo = datos[i], datos[i + 1]
    i += 3  # jugadores, maximo, bots
    con_clave = bool(datos[i + 2])
    i += 4  # tipo, entorno, visibilidad, vac
    version, i = _leer_cadena(datos, i)

    return Estado(
        en_linea=True,
        nombre=nombre,
        mision=mision,
        mapa=mapa,
        jugadores=jugadores,
        maximo=maximo,
        con_clave=con_clave,
        version=version,
    )


def _parsear_jugadores(datos: bytes) -> list:
    total = datos[5]
    jugadores, i = [], 6
    for _ in range(total):
        i += 1  # indice, que Arma deja en 0
        nombre, i = _leer_cadena(datos, i)
        i += 4  # score, que Arma no usa
        segundos = struct.unpack_from("<f", datos, i)[0]
        i += 4
        if nombre:
            jugadores.append(Jugador(nombre, segundos))
    return sorted(jugadores, key=lambda j: j.segundos, reverse=True)


def obtener_estado() -> Estado:
    """Consulta el servidor. Si no responde, devuelve un Estado marcado como caido."""
    try:
        estado = _parsear_info(_consultar(A2S_INFO, sufijo_challenge=True))
    except (socket.timeout, OSError, IndexError, ValueError):
        return Estado(en_linea=False)

    # La lista de jugadores es opcional: si falla, el resto del estado sigue siendo util.
    try:
        estado.lista = _parsear_jugadores(_consultar(A2S_PLAYER + b"\xff\xff\xff\xff"))
    except (socket.timeout, OSError, IndexError, ValueError, struct.error):
        estado.lista = []

    return estado


if __name__ == "__main__":
    e = obtener_estado()
    if not e.en_linea:
        print("Servidor sin respuesta")
    else:
        print(f"{e.nombre} | {e.mision} ({e.mapa}) | {e.jugadores}/{e.maximo}")
        for j in e.lista:
            print(f"  - {j.nombre}  {j.tiempo}")
