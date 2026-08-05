"""Runner local: mantiene actualizado el mensaje de Discord desde este PC.

Sustituye al cron de GitHub Actions, que daba una ejecucion cada 1-2 horas en
vez de cada 5 minutos. Aqui el intervalo se cumple de verdad.

Uso:
    python bot_local.py            actualiza en bucle hasta que se cierre
    python bot_local.py --una-vez  actualiza una sola vez y termina

La configuracion vive en config_local.json, que NO se sube a git porque
contiene el webhook.
"""

import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config_local.json"
LOG = BASE / "bot.log"

INTERVALO_MINIMO = 30  # segundos; por debajo no aporta nada y roza el rate limit


def configurar_log() -> logging.Logger:
    log = logging.getLogger("lazarus")
    log.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")

    # Un solo archivo de 1 MB con una rotacion: no crece sin control.
    archivo = RotatingFileHandler(LOG, maxBytes=1_000_000, backupCount=1, encoding="utf-8")
    archivo.setFormatter(formato)
    log.addHandler(archivo)

    # Si hay consola (no la hay bajo pythonw), tambien escribe ahi.
    if sys.stdout is not None:
        consola = logging.StreamHandler(sys.stdout)
        consola.setFormatter(formato)
        log.addHandler(consola)

    return log


def cargar_config(log: logging.Logger) -> dict:
    if not CONFIG.exists():
        log.error("No existe %s. Copia config_local.ejemplo.json y rellenalo.", CONFIG.name)
        return None

    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log.error("config_local.json tiene un error de formato: %s", e)
        return None

    faltan = [c for c in ("webhook_url", "message_id") if not cfg.get(c)]
    if faltan:
        log.error("Faltan campos en config_local.json: %s", ", ".join(faltan))
        return None

    cfg["intervalo_segundos"] = max(INTERVALO_MINIMO, int(cfg.get("intervalo_segundos", 60)))
    if cfg.get("logo_url"):
        os.environ["LAZARUS_LOGO_URL"] = cfg["logo_url"]
    if cfg.get("arma_host"):
        os.environ["ARMA_HOST"] = cfg["arma_host"]
    if cfg.get("arma_query_port"):
        os.environ["ARMA_QUERY_PORT"] = str(cfg["arma_query_port"])
    return cfg


def main() -> int:
    log = configurar_log()
    cfg = cargar_config(log)
    if not cfg:
        return 1

    # Se importa despues de fijar las variables de entorno de la config.
    import update

    una_vez = "--una-vez" in sys.argv
    intervalo = cfg["intervalo_segundos"]

    if una_vez:
        exito, resumen = update.actualizar(cfg["webhook_url"], cfg["message_id"])
        log.info("%s · %s", "OK" if exito else "FALLO", resumen)
        return 0 if exito else 1

    log.info("=" * 55)
    log.info("Bot de estado LAZARUS iniciado · cada %d segundos", intervalo)
    log.info("=" * 55)

    fallos_seguidos = 0
    while True:
        try:
            exito, resumen = update.actualizar(cfg["webhook_url"], cfg["message_id"])
            if exito:
                if fallos_seguidos:
                    log.info("Recuperado tras %d fallo(s)", fallos_seguidos)
                fallos_seguidos = 0
                log.info("OK · %s", resumen)
            else:
                fallos_seguidos += 1
                log.warning("Fallo %d · %s", fallos_seguidos, resumen)

        except KeyboardInterrupt:
            log.info("Detenido por el usuario.")
            return 0
        except Exception:
            # Un error inesperado no puede tumbar el bot: se anota y se sigue.
            fallos_seguidos += 1
            log.exception("Error inesperado (fallo %d)", fallos_seguidos)

        # Ante fallos seguidos se espacia el reintento, hasta 10 minutos.
        espera = intervalo
        if fallos_seguidos >= 3:
            espera = min(600, intervalo * min(fallos_seguidos, 10))
            log.info("Esperando %d s por fallos repetidos", espera)

        try:
            time.sleep(espera)
        except KeyboardInterrupt:
            log.info("Detenido por el usuario.")
            return 0


if __name__ == "__main__":
    sys.exit(main())
