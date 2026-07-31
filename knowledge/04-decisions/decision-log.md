# Decision Log

## ADR-001 — distribución Hermes en la raíz

- Fecha: 2026-07-27
- Estado: aceptada
- Decisión: el repositorio es directamente una Profile Distribution, con `distribution.yaml`, `SOUL.md`, `config.yaml`, `skills/`, `cron/` y `knowledge/`.
- Motivo: permite instalar y actualizar el agente completo en VPS sin compartir memorias, sesiones, claves ni estado.
- Fuente: documentación oficial de Hermes, https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions (consultada 2026-07-27).

## ADR-002 — núcleo determinista antes de scraping real

- Fecha: 2026-07-27
- Estado: aceptada
- Decisión: validar dominio, normalización, deduplicación, aislamiento de errores y scoring con fixtures antes de integrar fuentes reales.
- Motivo: reduce acoplamiento y permite probar resiliencia sin depender de layouts o disponibilidad externa.

## ADR-003 — núcleo self-hosted con conectores externos opcionales

- Fecha: 2026-07-31
- Estado: aceptada
- Decisión: mantener Sauron y Hermes Gateway locales; encapsular OAuth HTTPS, Firecrawl administrado y otros servicios en conectores opcionales. MCP queda como fachada futura, no como reemplazo de Telegram/Gateway.
- Detalle: [[adr-003-self-hosted-connectors]].

## ADR-004 — software libre con licencia MIT

- Fecha: 2026-07-31
- Estado: aceptada
- Decisión: mantener Sauron como proyecto gratuito, comunitario y self-hosted bajo MIT; cada usuario configura sus propias fuentes y conectores.
- Límite: la licencia del código no autoriza evadir términos, robots, login, CAPTCHA o controles anti-bot de las fuentes.
- Detalle: [[adr-004-free-software-mit]].
