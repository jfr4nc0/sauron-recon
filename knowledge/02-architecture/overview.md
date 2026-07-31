# Architecture Overview

## Boundaries

```text
Hermes profile / cron
        |
        v
CLI and application use cases
        |
        +--> SourcePort --> Firecrawl/API/feed/manual adapters
        +--> ConnectorPort --> local/tunnel/domain OAuth connectors
        +--> ListingRepositoryPort --> SQLite adapter
        +--> NotificationPort --> Hermes/Telegram adapter
        |
        v
Domain: criteria, listing, scoring, identity
```

## Decisions

- El agente conversacional interpreta requisitos y redacta reportes, pero el pipeline crítico es determinista.
- SQLite es suficiente para el MVP y evita operar una base externa.
- `knowledge/` es fuente de contexto durable y versionable; `runtime/` es estado mutable y está excluido de Git.
- La distribución Hermes se publica desde la raíz del repositorio y se instala con `hermes profile install`.

## Evolución prevista

1. Núcleo offline con fixtures.
2. Persistencia SQLite y migraciones.
3. Firecrawl adapter con timeouts, retry, rate limit y circuit breaker.
4. Adapters por fuente y report renderer.
5. Cronjobs y delivery Telegram después de dry-run.
6. Setup wizard y registry de conectores opcionales.
7. Registry de capacidades por fuente: API, feed autorizado, Firecrawl público, importación manual o deshabilitada.
