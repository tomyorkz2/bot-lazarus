"""Construye el embed de Discord con la identidad visual de LAZARUS.

Paleta tomada del logo del clan:
  negro #0D0D0D · rojo carmesi #B01E28 · hueso #EDE8DF · gris #55554F
"""

import os
from datetime import datetime, timezone

# El color de la barra lateral comunica el estado de un vistazo.
VERDE = 0x3BA55D   # hay gente jugando
ROJO = 0xB01E28    # en linea pero vacio (rojo LAZARUS)
GRIS = 0x55554F    # el servidor no responde

LEMA = "DISCIPLINA · PRECISIÓN · LEALTAD"

MAX_CAMPO = 1024   # limite de Discord por valor de campo
ANCHO_NOMBRE = 22  # se recorta a esto para que la tabla quede cuadrada

# Codigos ANSI que Discord interpreta dentro de un bloque ```ansi.
RESET = "[0m"
GRIS_ANSI = "[0;30m"
VERDE_ANSI = "[0;32m"
AMARILLO_ANSI = "[0;33m"
BLANCO_ANSI = "[0;37m"

VETERANO = 3600  # a partir de 1 hora de sesion
ASENTADO = 900   # a partir de 15 minutos


def _color_por_sesion(segundos: float) -> str:
    """Verde para los veteranos de la sesion, amarillo para los que acaban de entrar."""
    try:
        if segundos >= VETERANO:
            return VERDE_ANSI
        if segundos >= ASENTADO:
            return BLANCO_ANSI
    except TypeError:
        pass
    return AMARILLO_ANSI


def _limpiar(nombre: str) -> str:
    """Neutraliza lo que podria romper el bloque ANSI.

    Dentro de un bloque de codigo el markdown no se interpreta, pero un
    backtick cerraria el bloque y un escape ANSI dejaria al jugador elegir
    los colores del mensaje.
    """
    limpio = nombre.replace("`", "'").replace("", "")
    limpio = "".join(c for c in limpio if c.isprintable())
    if len(limpio) > ANCHO_NOMBRE:
        limpio = limpio[: ANCHO_NOMBRE - 1] + "…"
    return limpio or "?"


def _tabla_jugadores(jugadores: list) -> str:
    """Tabla monoespaciada con cabecera y color segun tiempo de sesion."""
    cabecera = f"{GRIS_ANSI} TIEMPO   JUGADOR{RESET}"
    separador = f"{GRIS_ANSI} {'─' * 30}{RESET}"
    envoltura = len("```ansi\n") + len("\n```")

    lineas = [cabecera, separador]
    usados = len(cabecera) + len(separador) + 2
    omitidos = 0

    for j in jugadores:
        color = _color_por_sesion(j.segundos)
        linea = f"{color} {j.tiempo:>7}   {_limpiar(j.nombre)}{RESET}"
        # Se reservan 40 caracteres para el aviso de omitidos y su color.
        if usados + len(linea) + 1 > MAX_CAMPO - envoltura - 40:
            omitidos += 1
            continue
        lineas.append(linea)
        usados += len(linea) + 1

    if omitidos:
        lineas.append(f"{GRIS_ANSI} …y {omitidos} más{RESET}")

    return "```ansi\n" + "\n".join(lineas) + "\n```"


def construir(estado, visto_por_ultima_vez: str = None) -> dict:
    """Devuelve el embed listo para enviar a Discord.

    visto_por_ultima_vez: timestamp ISO del ultimo sondeo con exito. Solo se
    usa cuando el servidor esta caido, para no perder ese dato.
    """
    ahora = datetime.now(timezone.utc).isoformat()
    # Se leen en cada llamada para que el runner local pueda fijarlas al vuelo.
    logo_url = os.environ.get("LAZARUS_LOGO_URL", "")
    conexion = os.environ.get("ARMA_CONEXION", "38.225.91.3:2332")

    if not estado.en_linea:
        embed = {
            "title": "⚫  LAZARUS OPS",
            "description": "**SIN RESPUESTA**\nEl servidor no contesta a la consulta.",
            "color": GRIS,
            "footer": {"text": f"{LEMA}  ·  última vez en línea"},
            "timestamp": visto_por_ultima_vez or ahora,
        }
        if logo_url:
            embed["thumbnail"] = {"url": logo_url}
        return embed

    hay_gente = estado.jugadores > 0
    nombre = estado.nombre.strip() or "LAZARUS OPS"

    embed = {
        "title": f"{'🟢' if hay_gente else '🔴'}  {nombre}",
        "color": VERDE if hay_gente else ROJO,
        "fields": [
            {"name": "Misión", "value": estado.mision or "—", "inline": False},
            {"name": "Mapa", "value": estado.mapa or "—", "inline": True},
            {"name": "Jugadores", "value": f"## {estado.jugadores} / {estado.maximo}", "inline": True},
        ],
        "footer": {"text": LEMA},
        "timestamp": ahora,
    }

    if estado.lista:
        embed["fields"].append(
            {"name": "EN COMBATE", "value": _tabla_jugadores(estado.lista), "inline": False}
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
        {"name": "Conexión", "value": f"`{conexion}`{candado}", "inline": False}
    )

    if logo_url:
        embed["thumbnail"] = {"url": logo_url}

    return embed
