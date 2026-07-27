# Phase 5 — contractual detail parsing

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- Clasificación de URLs: `detail`, `category`, `unknown`.
- Parser contractual de precio, moneda, operación, superficie y título.
- Identificación de páginas individuales de Zonaprop, Argenprop y Mercado Libre.
- Extracción de enlaces individuales desde páginas de categoría.
- Expansión acotada con `--scrape-details` y `max_detail_pages`.
- Las categorías se omiten sin `--scrape-details`; no se almacenan como listings falsos.
- URLs desconocidas se rechazan y generan warning de cobertura.
- Precios ARS/USD y superficies se conservan sólo si aparecen en el contenido.

## Evidencia real

Una corrida live contra el daemon Firecrawl con Zonaprop y `--scrape-details --limit 1` produjo un aviso individual:

- título: `Serrano al 1300, Palermo, Capital Federal`
- precio: `3800000`
- superficie: `180 m²`
- página clasificada como `detail`
- fallos: `0`

## Guardrails

- `--limit` controla tanto resultados de búsqueda como cantidad máxima de detalles por categoría.
- No se infieren datos ausentes.
- No se consideran snapshots completos.
- Las páginas de categoría no generan una identidad de listing.

## Tests

- 18 tests automatizados pasan.
- Verificador de distribución pasa.
- Compilación de `src` y `tests` pasa.

## Próximo incremento

Agregar parseo contractual de expensas, dirección/contacto y campos específicos por portal; después ajustar scoring y filtros sobre listings individuales antes de configurar Telegram.
