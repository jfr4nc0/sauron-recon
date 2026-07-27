# Phase 1 — deterministic core

## Estado

Completada la primera implementación y verificada localmente. El daemon Firecrawl existente responde en `http://localhost:3002` y Hermes tiene `web` habilitado mediante `FIRECRAWL_API_URL` en su configuración persistente.

## Alcance

- Package Python liviano.
- `SearchCriteria` y `Listing` como contratos.
- Canonicalización de URL.
- Score explicable.
- Orquestación de múltiples fuentes con aislamiento de fallos.
- Deduplicación por identidad.
- CLI `health` y `search --dry-run`.

## Aceptación

- Tests unitarios pasan.
- Una fuente fallida no cancela la corrida.
- Listings repetidos se deduplican.
- Rangos inválidos se rechazan.
- El CLI devuelve JSON machine-readable.

## Próximo incremento

Agregar adapters específicos por fuente, detección de listings desaparecidos, límites/rate limiting por dominio y delivery Telegram después de validar el destino.
