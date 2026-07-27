# Phase 7 — availability and cross-source duplicate candidates

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- Estados de disponibilidad: `available` y `unavailable` cuando la página lo respalda.
- JSON CLI expone `external_id`, `availability`, `expenses` y `contact`.
- Detección de candidatos cross-source con razones explicables.
- Evidencia usada: misma dirección, misma superficie y overlap fuerte de título.
- Nunca se fusionan automáticamente listings de portales distintos.
- Reporte informa cantidad de posibles duplicados.

## Seguridad de deduplicación

Un mismo inmueble puede tener avisos legítimos en distintos portales, con precio, operación o condiciones diferentes. Por eso la identidad primaria sigue siendo `source:url`; los candidatos sólo orientan revisión/scoring posterior.

No se considera suficiente compartir únicamente superficie, zona o un número externo de portal.

## Evidencia real

Corrida live con Mercado Libre y `--scrape-details --limit 1`:

- external_id: `3642907412`
- availability: `available`
- precio: `1400000`
- superficie: `80 m²`
- fallos: `0`

## Tests

- 21 tests automatizados pasan.
- Verificador de distribución pasa.
- Compilación y `git diff --check` pasan.

## Próximo incremento

Persistir candidatos de duplicado para seguimiento, mejorar matching de direcciones por portal y ajustar scoring/filtros de usuario. Luego comenzar integración de delivery Telegram en modo preview, sin cron productivo.
