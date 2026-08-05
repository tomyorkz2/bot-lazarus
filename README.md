# Estado de LAZARUS OPS en Discord

Un mensaje fijo en Discord que se actualiza solo cada minuto con el estado
del servidor de Arma 3: misión en curso, cuántos hay dentro y quiénes son.

Corre en el PC del usuario mediante `bot_local.py` (~28 MB de RAM).

> **Nota sobre GitHub Actions:** el proyecto nació corriendo en Actions con un
> cron de 5 minutos, pero GitHub deprioriza los workflows programados y daba
> **una ejecución cada 1-2 horas**, inservible para saber quién está conectado.
> El cron quedó desactivado en `estado.yml`; el disparo manual sigue disponible
> como respaldo para refrescar el mensaje si el PC está apagado.

```
🟢  LAZARUS OPS                    ← verde: hay gente jugando
    Misión      LAZARUS - Liberacion Altis
    Mapa        Altis
    Jugadores   3 / 64

    EN COMBATE
      1h 12m   Slc. TomYork
         34m   Cbo. Ramirez
          8m   Sld. Vega

    Conexión    38.225.91.3:2332  🔒
    DISCIPLINA · PRECISIÓN · LEALTAD
```

El color comunica el estado de un vistazo:

| Color | Significa |
|---|---|
| 🟢 Verde | Hay jugadores dentro |
| 🔴 Rojo LAZARUS | En línea pero vacío |
| ⚫ Gris | El servidor no responde |

---

## Uso diario (ejecución local)

```
iniciar_bot.bat     arranca el bot en segundo plano, sin ventana
detener_bot.bat     lo detiene
bot.log             registro de actividad
```

Para que arranque solo con Windows, ver la sección *Arranque automático*.

Configuración en `config_local.json` (no se sube a git, contiene el webhook).
Se parte de `config_local.ejemplo.json`:

| Campo | Para qué |
|---|---|
| `webhook_url` | El webhook del canal de Discord |
| `message_id` | El mensaje que se edita, lo da `setup.py` |
| `intervalo_segundos` | Cada cuánto actualiza. Mínimo 30, por defecto 60 |
| `logo_url` | Thumbnail del embed |
| `arma_host` / `arma_query_port` | Servidor a consultar |

## Arranque automático

El bot no se instala solo en el arranque a propósito. Para activarlo:

1. `Win + R` → `shell:startup` → se abre la carpeta de Inicio
2. Crear ahí un acceso directo a `iniciar_bot.bat`

Para quitarlo, se borra ese acceso directo.

---

## Puesta en marcha desde cero

### 1. Crear el webhook en Discord

En el canal donde quieras el mensaje:

**Editar canal** → **Integraciones** → **Crear webhook** → ponle nombre
(por ejemplo *LAZARUS OPS*) → **Copiar URL del webhook**.

Guarda esa URL, la necesitas dos veces.

### 2. Crear el mensaje

Desde esta carpeta, en la terminal:

```bash
python setup.py "LA_URL_DEL_WEBHOOK_QUE_COPIASTE"
```

Aparecerá el mensaje en tu canal y la terminal imprimirá algo así:

```
DISCORD_MESSAGE_ID = 1234567890123456789
```

Apunta ese número.

### 3. Subir el proyecto a GitHub

Crea un repositorio **público** (los repos públicos tienen Actions ilimitado y
gratis; los privados solo dan 2.000 minutos al mes y no alcanzan).

Sube todos los archivos de esta carpeta. Si no usas git, en la web de GitHub:
**Add file** → **Upload files** y arrastra todo, incluida la carpeta `.github`.

### 4. Configurar los secretos

En el repositorio: **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Crea estos dos:

| Nombre | Valor |
|---|---|
| `DISCORD_WEBHOOK_URL` | La URL del paso 1 |
| `DISCORD_MESSAGE_ID` | El número del paso 2 |

### 5. Probarlo

Pestaña **Actions** → **Estado LAZARUS OPS** → **Run workflow**.

Si el mensaje de Discord se actualiza, está listo. A partir de ahí corre solo
cada 5 minutos.

---

## Detalles que conviene saber

**El cron se retrasa.** GitHub no garantiza puntualidad en los workflows
programados: si pides cada 5 minutos, en horas pico pueden ser 8 o 12. Es una
limitación de GitHub, no del código.

**Los repos inactivos se desactivan.** GitHub apaga los workflows programados
si el repositorio pasa 60 días sin commits. Por eso está `latido.yml`, que hace
un commit automático el día 1 de cada mes.

**Si Discord falla, no pasa nada.** El código reintenta 3 veces y, si aun así
falla, termina sin error. El mensaje conserva el último estado bueno y a los
5 minutos se vuelve a intentar.

**El mensaje nunca se borra**, solo se edita. Por eso queda anclado en el canal.

---

## Archivos

| Archivo | Para qué |
|---|---|
| `query.py` | Consulta el servidor por protocolo Steam A2S |
| `embed.py` | Construye el embed con la paleta de LAZARUS |
| `update.py` | Une los dos y edita el mensaje. Lo llama Actions |
| `setup.py` | Crea el mensaje inicial. Se usa una sola vez |
| `.github/workflows/estado.yml` | El cron de 5 minutos |
| `.github/workflows/latido.yml` | Commit mensual anti-desactivación |
| `logo_lazarus.png` | Thumbnail del embed |

## Configuración opcional

Se ajusta con variables de entorno, todas con valor por defecto:

| Variable | Por defecto |
|---|---|
| `ARMA_HOST` | `38.225.91.3` |
| `ARMA_QUERY_PORT` | `2333` (puerto del juego + 1) |
| `ARMA_CONEXION` | `38.225.91.3:2332` |
| `LAZARUS_LOGO_URL` | La rellena el workflow desde el propio repo |

## Probar en local

```bash
python query.py    # imprime el estado del servidor en la terminal
```
