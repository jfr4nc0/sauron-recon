# sauron-recon

Profile Distribution de Hermes para descubrir locales comerciales en alquiler o venta, normalizar resultados de múltiples fuentes, detectar novedades y enviar reportes por Telegram.

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

`--scrape-details` habilita una segunda extracción sólo para URLs permitidas por la allowlist y permite completar precio/superficie cuando la página los publica. La persistencia histórica detecta listings `new`, `changed` y `unchanged`, y `--report` genera Markdown con novedades y cobertura. El rate limiter y circuit breaker protegen el daemon; las desapariciones sólo se marcan para fuentes declaradas como snapshots completos.

## Seguridad y cumplimiento

El proyecto no evade CAPTCHAs, autenticación ni controles anti-bot. Las fuentes deben consultarse respetando sus términos, robots.txt, límites de frecuencia y permisos de automatización.
