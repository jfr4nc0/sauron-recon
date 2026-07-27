# Phase 2 — extraction, history and reports

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- Cliente Firecrawl estándar contra el daemon compartido.
- Retry/backoff y errores tipados.
- Allowlist de dominios.
- Extracción detallada opcional con `--scrape-details`.
- Tabla `observations` con histórico por corrida.
- Detección `new`, `changed`, `unchanged`.
- Reporte Markdown con novedades, cobertura y errores.
- CLI `--report`.

## Evidencia

- Búsqueda live sin detalle: dos resultados reales de Zonaprop.
- Búsqueda live con detalle y límite 1: precio `4900000` y superficie `250` extraídos de la respuesta Firecrawl.
- Tests automatizados: 9 passed.
- Verificador de distribución: passed.

## Pendiente

- Parseo específico por fuente.
- Rate limiting/circuit breaker por dominio.
- Detección de listings desaparecidos.
- Delivery a Telegram y cronjobs productivos.
