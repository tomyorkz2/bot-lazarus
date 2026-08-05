"""Construye el embed de Discord con la identidad visual de LAZARUS.

Paleta tomada del logo del clan:
  negro #0D0D0D · rojo carmesi #B01E28 · hueso #EDE8DF · gris #55554F
"""

import os
from datetime import datetime, timezone

# El color comunica el estado de un vistazo.
VERDE = 0x3BA55D   # hay gente jugando
ROJO = 0xB01E28    # en linea pero vacio (rojo LAZARUS)
GRIS = 0x55554F    # el servidor no responde

LEMA = "DISCIPLINA · PRECISIÓN · LEALTAD"
CONEXION = os.environ.get("ARMA_CONEXION", "38.225.91.3:2332")
LOGO_URL = os.environ.get("LAZARUS_LOGO_URL", "")

MAX_CAMPO = 1024  # limite de Discord por valor de campo


def _lista_jugadores(jugadores: list) -> str:
    """Formatea la lista respetando el limite de caracteres de Discord."""
    lineas, usados, omitidos = [], 0, 0
    for j in jugadores:
        linea = f"`{j.tiempo:>7}`  {j.nombre}"
        # Se reservan 30 caracteres para el aviso de omitidos.
        if usados + len(linea) + 1 > MAX_CAMPO - 30:
            omitidos += 1
            continue
        lineas.append(linea)
        usados += len(linea) + 1
    if omitidos:
        lineas.append(f"*…y {omitidos} más*")
    return "\n".join(lineas)


def construir(estado, visto_por_ultima_vez: str = None) -> dict:
    """Devuelve el embed listo para enviar a Discord.

    visto_por_ultima_vez: timestamp ISO del ultimo sondeo con exito. Solo se
    usa cuando el servidor esta caido, para no perder ese dato.
    """
    ahora = datetime.now(timezone.utc).isoformat()

    if not estado.en_linea:
        embed = {
            "title": "⚫  LAZARUS OPS",
            "description": "**SIN RESPUESTA**\nEl servidor no contesta a la consulta.",
            "color": GRIS,
            "footer": {"text": f"{LEMA}  ·  última vez en línea"},
            "timestamp": visto_por_ultima_vez or ahora,
        }
        if LOGO_URL:
            embed["thumbnail"] = {"url": LOGO_URL}
        return embed

    hay_gente = estado.jugadores > 0
    embed = {
        "title": f"{'🟢' if hay_gente else '🔴'}  {estado.nombre}",
        "color": VERDE if hay_gente else ROJO,
        "fields": [
            {"name": "Misión", "value": estado.mision or "—", "inline": False},
            {"name": "Mapa", "value": estado.mapa or "—", "inline": True},
            {"name": "Jugadores", "value": f"**{estado.jugadores}** / {estado.maximo}", "inline": True},
        ],
        "footer": {"text": LEMA},
        "timestamp": ahora,
    }

    if estado.lista:
        embed["fields"].append(
            {"name": "EN COMBATE", "value": _lista_jugadores(estado.lista), "inline": False}
        )
    elif hay_gente:
        # El contador dice que hay gente pero A2S_PLAYER no devolvio nombres.
        embed["fields"].append(
            {"name": "EN COMBATE", "value": "*nombres no disponibles*", "inline": False}
        )
    else:
        embed["description"] = "*Nadie conectado ahora mismo.*"

    candado = "  🔒" if estado.con_clave else ""
    embed["fields"].append(
        {"name": "Conexión", "value": f"`{CONEXION}`{candado}", "inline": False}
    )

    if LOGO_URL:
        embed["thumbnail"] = {"url": LOGO_URL}

    return embed
