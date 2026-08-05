"""Crea el mensaje inicial en Discord. Se ejecuta UNA SOLA VEZ.

Uso:
    python setup.py https://discord.com/api/webhooks/XXXX/YYYY

Imprime el ID del mensaje creado. Ese ID es el que hay que guardar como
secret DISCORD_MESSAGE_ID en GitHub para que el workflow lo edite siempre.
"""

import json
import sys
import urllib.error
import urllib.request

import embed
import query


def main() -> int:
    if len(sys.argv) != 2 or "discord.com/api/webhooks/" not in sys.argv[1]:
        print(__doc__)
        return 1

    webhook = sys.argv[1].rstrip("/")

    print("Consultando el servidor de Arma...")
    estado = query.obtener_estado()
    if estado.en_linea:
        print(f"  {estado.nombre} · {estado.jugadores}/{estado.maximo} · {estado.mision}")
    else:
        print("  sin respuesta (se creara el mensaje igualmente, en gris)")

    cuerpo = {"embeds": [embed.construir(estado)]}
    datos = json.dumps(cuerpo).encode()
    req = urllib.request.Request(f"{webhook}?wait=true", data=datos, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "LazarusStatusBot/1.0")

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            mensaje = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"\nERROR HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        print("Revisa que la URL del webhook sea correcta y siga activa.")
        return 1
    except urllib.error.URLError as e:
        print(f"\nERROR de red: {e.reason}")
        return 1

    print("\n" + "=" * 58)
    print("  MENSAJE CREADO. Guarda este ID como secret en GitHub:")
    print()
    print(f"     DISCORD_MESSAGE_ID = {mensaje['id']}")
    print()
    print("=" * 58)
    return 0


if __name__ == "__main__":
    sys.exit(main())
