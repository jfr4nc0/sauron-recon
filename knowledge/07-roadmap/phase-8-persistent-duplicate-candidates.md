# Phase 8 — persistent duplicate candidates

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- Normalización de direcciones con eliminación de acentos y sufijos geográficos comunes.
- Tabla SQLite `duplicate_candidates` ligada a cada corrida.
- Persistencia idempotente mediante una clave estable basada en las dos identidades.
- Razones guardadas como JSON: `same_address`, `same_area`, `title_overlap`.
- Contador de candidatos para verificaciones operativas.
- Sin fusión automática ni cambios de identidad primaria.

## Compatibilidad

La tabla se crea de forma aditiva con `CREATE TABLE IF NOT EXISTS`; no se borran listings, observaciones ni corridas anteriores.

## Tests

- 22 tests automatizados pasan.
- Verificador de distribución pasa.
- Compilación y `git diff --check` pasan.

## Próximo incremento

Añadir una vista/reporte histórico de candidatos repetidos, resolver revisiones explícitas y preparar delivery Telegram en preview. Los cronjobs productivos continuarán deshabilitados hasta confirmar destino y frecuencia.
