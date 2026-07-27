# Phase 6 — listing enrichment and change contract

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- `external_id` derivado de URLs de Zonaprop, Argenprop y Mercado Libre.
- Parseo de expensas cuando la página publica el valor.
- Indicador `contact` seguro: guarda sólo que existe contacto público, no el teléfono/email.
- Campo `availability` preparado para estados posteriores.
- Fingerprint y changed-fields ampliados con los nuevos atributos.
- Migración SQLite aditiva para instalaciones existentes.
- Reporte Markdown muestra expensas y `contacto publicado`.
- Parser de títulos evita headings auxiliares como “Características adicionales”.

## Evidencia real

Una corrida live con `--scrape-details` obtuvo avisos individuales de Zonaprop y Mercado Libre con precio y superficie. El parsing quedó limitado a contenido publicado; no se persisten credenciales ni números de contacto.

## Tests

- 19 tests automatizados pasan.
- Verificador de distribución pasa.
- Compilación y `git diff --check` pasan.

## Próximo incremento

Agregar disponibilidad/estado real por fuente, identificar expensas y moneda por separado, y mejorar deduplicación cross-source mediante `external_id` sin conflar avisos distintos.
