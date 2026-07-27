# Phase 4 — explicit portal adapters

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- `ZonapropSource` con allowlist y query específica.
- `ArgenpropSource` con allowlist y query específica.
- `MercadoLibreSource` con allowlist para `inmuebles.mercadolibre.com.ar`.
- `InmobiliariaSource` configurable para un dominio permitido explícito.
- CLI con selección mediante `--sources`.
- Fallback limitado por portal cuando Firecrawl devuelve cero resultados.
- Cada fallback conserva rate limiting y circuit breaker.
- Desconocidos rechazados por factory.

## Cobertura y límites

Los adapters comparten el parser conservador de `Listing` y aún no declaran snapshots completos. Las páginas devueltas por Firecrawl pueden ser páginas de categoría y no avisos individuales; por eso no se infieren precios, superficies ni disponibilidad.

El proveedor Firecrawl mostró variabilidad entre consultas: en algunas ejecuciones devolvió páginas de Zonaprop, Argenprop y Mercado Libre; en otras respondió `success: true` con `data: []`. El sistema trata esto como cero resultados, no como evidencia de que el mercado esté vacío, y no marca desapariciones.

## Evidencia

- 15 tests automatizados pasan.
- Verificador de distribución pasa.
- CLI live/dry-run probado con selección de portales.

## Próximo incremento

Agregar parsers contractuales para páginas de detalle, validación de URL individual versus página de categoría y fixtures reales anonimizados. Sólo después evaluar snapshots completos por portal y delivery Telegram.
