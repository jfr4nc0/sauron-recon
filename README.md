# Sauron-Recon

<p align="center">
  <img src="assets/logo.png" alt="Sauron Recon" width="400">
</p>

Profile Distribution de Hermes para descubrir locales comerciales en alquiler o venta, normalizar resultados de múltiples fuentes, detectar novedades y enviar reportes por Telegram. Es software libre, gratuito y self-hosted bajo licencia MIT.

Estado: implementación inicial. La arquitectura y el roadmap están en [PLAN.md](PLAN.md), y la capa de conocimiento está en [knowledge/00-index.md](knowledge/00-index.md).

## Distribution installable

Este repositorio sigue el formato oficial de Hermes Profile Distributions:

```bash
hermes profile install git@github.com:jfr4nc0/sauron-recon.git --alias
```

La distribución incluye `SOUL.md`, configuración, skill, ejemplos de cron y la vault Obsidian. Cada instalación conserva sus propias memorias, sesiones, credenciales y estado runtime.

## Desarrollo local

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
pytest
python scripts/verify_distribution.py
sauron-recon health
sauron-recon search --dry-run --criteria '{"operation":"rent","zones":["Palermo"],"max_price":1500,"min_area_m2":50}'
```

El núcleo actual es determinista y usa fixtures/in-memory para validar contratos, deduplicación, scoring, aislamiento de fallos e idempotencia SQLite antes de conectar fuentes externas. El adapter Firecrawl ya está conectado al daemon compartido existente de Hermes (`FIRECRAWL_API_URL`, por defecto `http://localhost:3002`):

```bash
sauron-recon search --live --dry-run --limit 10 \
  --criteria '{"operation":"rent","zones":["Palermo"]}'
```

En live, `--sources` permite elegir adapters explícitos:

```bash
sauron-recon search --live --sources zonaprop,argenprop,mercadolibre \\
  --criteria '{"operation":"rent","zones":["Palermo"]}'
```

También se pueden combinar búsquedas públicas con feeds autorizados locales:

```bash
sauron-recon search --feed ./runtime/inmobiliaria.csv \\
  --criteria '{"operation":"rent","zones":["Palermo"]}' --dry-run
```

Para una página pública autorizada que requiere renderizado JavaScript, puede
usarse Crawl4AI de forma opcional y local:

```bash
pip install -e '.[crawler]'
crawl4ai-setup
sauron-recon search \\
  --crawl4ai-url 'https://portal.example/busqueda/locales' \\
  --criteria '{"operation":"rent","zones":["Palermo"]}' --dry-run
```

El adapter valida allowlist de dominio y `robots.txt` antes de cada página,
falla cerrado si no puede verificar la autorización y no usa proxies,
cookies personales, stealth ni automatización de login. `undetected-chromedriver`
no está integrado: no se utiliza para evadir controles anti-bot, CAPTCHA,
autenticación ni restricciones del portal.

Desde Telegram, `/setup` inicia el wizard de conectores. Permite seleccionar
una instalación sólo local, ngrok, Cloudflare Tunnel, dominio HTTPS propio o
configuración manual. La selección se persiste sólo en el runtime local y no
solicita secretos por Telegram. MercadoLibre queda habilitado únicamente
después de completar su OAuth oficial y validar el callback HTTPS.

Cada portal tiene allowlist y query propia. Si Firecrawl responde `data: []`, se prueba como máximo un fallback específico, con rate limiting; una respuesta vacía no se interpreta como mercado vacío. `--scrape-details` habilita una segunda extracción sólo para URLs permitidas, descarta categorías como listings y expande un máximo controlado de avisos individuales; el parser extrae ID externo, expensas, disponibilidad y un indicador seguro de contacto público. Los posibles duplicados entre portales se reportan como candidatos explicables, sin fusionar automáticamente avisos, y se persisten por corrida para seguimiento histórico. El wizard Telegram `/start` normaliza operación, tipo de inmueble, ambientes, baños, superficie, trifásica, zona/localidad y rangos ARS/USD; tras confirmación puede alimentar un job horario. El PDF incluye enlaces y descripción pública limitada, y sólo recibe cambios nuevos/modificados para evitar repetir viviendas.


## Seguridad y cumplimiento

El proyecto no evade CAPTCHAs, autenticación ni controles anti-bot. Las fuentes deben consultarse respetando sus términos, robots.txt, límites de frecuencia y permisos de automatización.

El registro de capacidades de fuentes separa integraciones por API, feed autorizado, páginas públicas compatibles con Firecrawl, importación manual y fuentes deshabilitadas. Ver [LICENSE](LICENSE), [ADR-004](knowledge/04-decisions/adr-004-free-software-mit.md) y el [relevamiento de portales](knowledge/05-sources/portal-audit-2026-07-31.md).

En Telegram, `/sources` muestra el estado de cada fuente. `/setup` configura el conector OAuth HTTPS sin pedir secretos por el chat. El cliente OAuth oficial de MercadoLibre y el callback local one-shot están en `src/sauron_recon/adapters/mercadolibre_oauth.py`; requieren que el usuario configure su propia aplicación y `redirect_uri` HTTPS.
