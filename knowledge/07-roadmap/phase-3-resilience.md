# Phase 3 — source resilience and disappearance safety

## Estado

Implementada y verificada el 2026-07-27.

## Entregado

- Rate limiter in-process configurable por source.
- Circuit breaker con threshold y ventana de recuperación.
- Detail scrape degradable: una URL fallida no descarta las demás.
- Warnings de extracción parcial visibles como fallos de cobertura.
- Detección de listings desaparecidos opt-in mediante `complete_sources`.
- Migración compatible de SQLite para el estado de observaciones.
- Reporte con estado `Desaparecido`.

## Guardrail contra falsos positivos

Las búsquedas generales de Firecrawl no se consideran snapshots completos porque pueden devolver páginas de categoría, resultados parciales o variar entre ejecuciones. `mark_disappeared` exige que el caller declare explícitamente una fuente completa.

## Evidencia

- 13 tests automatizados pasan.
- Verificador de distribución pasa.
- Corrida live contra el daemon Firecrawl: un resultado detallado de Zonaprop, sin errores.
- Stack Firecrawl: 5 servicios en estado running.

## Próximo incremento

Implementar adapters específicos por fuente y definir para cada uno si puede producir snapshots completos. Después conectar Telegram y cronjobs con destino confirmado.
