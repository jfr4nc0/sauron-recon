# Phase 1 — deterministic core

## Estado

En implementación inicial.

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

Agregar repositorio SQLite, migraciones y fixtures contractuales; después implementar el adapter Firecrawl con límites y observabilidad.
