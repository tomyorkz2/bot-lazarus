"""Consulta el servidor y edita el mensaje fijo de Discord.

Lo ejecuta GitHub Actions cada 5 minutos. Nunca publica mensajes nuevos:
siempre edita el mismo, por eso queda anclado en el canal.

Variables de entorno necesarias (se configuran como Secrets del repo):
  DISCORD_WEBHOOK_URL  el webhook del canal
  DISCORD_MESSAGE_ID   el id del mensaje creado por setup.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

import embed
import query

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "").rstrip("/")
MENSAJE_ID = os.environ.get("DISCORD_MESSAGE_ID", "")
REINTENTOS = 3


def _peticion(url: str, metodo: str, cuerpo: dict = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "LazarusStatusBot/1.0")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read() or b"{}")


def _timestamp_anterior(url: str):
    """Recupera el timestamp del embed actual para no perder cuando se vio vivo.

    Si el embed anterior ya estaba gris, su timestamp ya era el de la ultima
    vez en linea, asi que arrastrarlo es correcto en ambos casos.
    """
    try:
        actual = _peticion(url, "GET")
        embeds = actual.get("embeds") or []
        return embeds[0].get("timestamp") if embeds else None
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError):
        return None


def main() -> int:
    if not WEBHOOK or not MENSAJE_ID:
        print("ERROR: faltan DISCORD_WEBHOOK_URL o DISCORD_MESSAGE_ID.", file=sys.stderr)
        return 1

    url = f"{WEBHOOK}/messages/{MENSAJE_ID}"
    estado = query.obtener_estado()

    visto = _timestamp_anterior(url) if not estado.en_linea else None
    cuerpo = {"embeds": [embed.construir(estado, visto)]}

    for intento in range(1, REINTENTOS + 1):
        try:
            _peticion(url, "PATCH", cuerpo)
            if estado.en_linea:
                print(f"OK · {estado.jugadores}/{estado.maximo} · {estado.mision}")
            else:
                print("OK · servidor sin respuesta, embed en gris")
            return 0
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", "replace")[:200]
            print(f"Intento {intento}: HTTP {e.code} · {detalle}", file=sys.stderr)
            if e.code in (401, 403, 404):
                return 1  # credenciales o id mal: reintentar no arregla nada
        except urllib.error.URLError as e:
            print(f"Intento {intento}: red · {e.reason}", file=sys.stderr)
        if intento < REINTENTOS:
            time.sleep(3)

    # Que falle Discord no debe romper el workflow: a los 5 min se reintenta solo.
    print("No se pudo actualizar. Se reintentara en la proxima ronda.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
