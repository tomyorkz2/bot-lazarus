"""Consulta el servidor y edita el mensaje fijo de Discord.

Expone `actualizar()` para que lo usen tanto GitHub Actions (via este mismo
archivo) como el runner local (`bot_local.py`). Nunca publica mensajes nuevos:
siempre edita el mismo, por eso queda anclado en el canal.

Variables de entorno al ejecutarlo directamente:
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


def actualizar(webhook: str, mensaje_id: str, reintentos: int = REINTENTOS) -> tuple:
    """Consulta el servidor y edita el mensaje.

    Devuelve (exito, resumen). `resumen` es un texto corto para el log.
    Los errores de red no se propagan: se informan en el resumen.
    """
    url = f"{webhook.rstrip('/')}/messages/{mensaje_id}"
    estado = query.obtener_estado()

    visto = _timestamp_anterior(url) if not estado.en_linea else None
    cuerpo = {"embeds": [embed.construir(estado, visto)]}

    if estado.en_linea:
        resumen = f"{estado.jugadores}/{estado.maximo} · {estado.mision}"
    else:
        resumen = "servidor sin respuesta"

    ultimo_error = ""
    for intento in range(1, reintentos + 1):
        try:
            _peticion(url, "PATCH", cuerpo)
            return True, resumen
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", "replace")[:150]
            ultimo_error = f"HTTP {e.code}: {detalle}"
            if e.code in (401, 403, 404):
                return False, ultimo_error  # credenciales o id mal: no insistir
        except urllib.error.URLError as e:
            ultimo_error = f"red: {e.reason}"
        if intento < reintentos:
            time.sleep(3)

    return False, ultimo_error


def main() -> int:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
    mensaje_id = os.environ.get("DISCORD_MESSAGE_ID", "")

    faltan = [
        nombre
        for nombre, valor in (("DISCORD_WEBHOOK_URL", webhook), ("DISCORD_MESSAGE_ID", mensaje_id))
        if not valor
    ]
    if faltan:
        print(f"ERROR: no llega el secret {' ni '.join(faltan)}", file=sys.stderr)
        print("Revisa en Settings > Secrets and variables > Actions:", file=sys.stderr)
        print("  - que esten en 'Repository secrets', NO en 'Environment secrets'", file=sys.stderr)
        print("  - que el nombre no lleve espacios ni minusculas", file=sys.stderr)
        return 1

    exito, resumen = actualizar(webhook, mensaje_id)
    if exito:
        print(f"OK · {resumen}")
        return 0

    # Que falle Discord no debe romper el workflow: se reintenta en la proxima ronda.
    print(f"No se pudo actualizar ({resumen}).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
