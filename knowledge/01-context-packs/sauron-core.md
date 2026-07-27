# Context Pack — Sauron Core

## Misión

Sauron Recon descubre locales comerciales en alquiler o venta, combina fuentes permitidas, normaliza listings, detecta novedades y produce reportes trazables para Hermes/Telegram.

## Invariantes

- El dominio no depende de Hermes, Firecrawl, HTTP ni SQLite.
- Las fuentes están aisladas detrás de ports/adapters.
- Los errores de una fuente no cancelan las demás.
- No se inventan campos faltantes.
- Las ejecuciones y envíos son idempotentes.
- No se evaden controles anti-bot.

## Navegación

- Arquitectura: [[02-architecture/overview]]
- Contratos: [[03-contracts/domain-contracts]]
- Fuentes: [[05-sources/source-policy]]
- Operación: [[06-operations/runbook]]
- Roadmap: [[07-roadmap/phase-1-core]]

## Contexto de implementación

El núcleo actual es Python 3.11+ con dependencias runtime estándar. La primera integración usa fixtures/in-memory para validar el caso de uso antes de conectar Firecrawl real.
