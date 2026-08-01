# ADR-005 — `sauron` como TUI principal

- Fecha: 2026-08-01
- Estado: aceptada

## Decisión

El comando de usuario principal es `sauron`, una TUI basada en la biblioteca
estándar `curses`. `sauron-recon` se conserva como CLI técnico para scripts,
cron, integraciones y compatibilidad.

## Alcance inicial

La TUI reutiliza `sauron_recon.entrypoints.cli` y los mismos casos de uso y
adapters del núcleo. Permite cargar operación, tipo, zonas, superficies,
fuentes, modo live/offline y extracción de detalle. No duplica la lógica de
búsqueda ni modifica las reglas de fuentes.

## Fuentes y fecha

Decisión del proyecto registrada el 2026-08-01. Contexto: [[01-context-packs/sauron-core]]
y contrato de búsqueda existente en `src/sauron_recon/application/use_cases.py`.
