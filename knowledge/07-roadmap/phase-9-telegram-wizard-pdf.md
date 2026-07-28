# Phase 9 — Telegram requirements wizard and hourly PDF delivery

## Estado

Núcleo implementado y verificado el 2026-07-27. Telegram y cron productivo todavía no están activados.

## Wizard `/start`

`src/sauron_recon/application/wizard.py` mantiene una máquina de estados por chat/topic:

1. Operación: compra, alquiler o ambas.
2. Tipo: departamento, casa, local, depósito, fábrica, terreno u otro.
3. Ambientes.
4. Baños.
5. Superficie mínima/máxima.
6. Trifásica y requisitos libres.
7. Zona, barrio y localidad.
8. Rangos separados en ARS y USD.
9. Resumen normalizado y confirmación.

Cada respuesta se normaliza antes de avanzar. El usuario recibe el resumen normalizado y puede confirmar o reiniciar el flujo. Cancelar no crea ningún job.

## Criterios

`SearchCriteria` agrega:

- rooms
- bathrooms
- min/max price ARS
- min/max price USD
- needs_three_phase
- locality
- requirements

Los criterios son datos estructurados; nunca se ejecutan directamente desde texto sin pasar por validación.

## PDF

`src/sauron_recon/application/pdf_reporting.py` genera un PDF deduplicado por identidad con:

- estado del cambio
- fuente
- título
- descripción pública limitada
- precio
- superficie
- URL
- cantidad de candidatos cross-source
- advertencias de cobertura

Uso:

```bash
sauron-recon search --criteria '<json>' --pdf reports/hourly.pdf
```

El reporte horario debe recibir sólo `ListingChange` nuevos/modificados/desaparecidos provenientes de SQLite; así no repite viviendas en informes posteriores.

## Activación pendiente

No se registra cron productivo hasta confirmar:

- chat/topic Telegram destino
- zona horaria
- hora de inicio
- fuentes habilitadas
- criterios finales persistidos
- si el primer informe debe incluir el histórico existente o sólo novedades desde la confirmación
- política ante errores: entregar PDF parcial o no entregar

El ejemplo `cron/hourly-search-pdf.json` es deliberadamente `deliver: local` y no está instalado.
