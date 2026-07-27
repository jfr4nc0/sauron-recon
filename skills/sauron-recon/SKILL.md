---
name: sauron-recon
description: "Reconocimiento resiliente de locales comerciales con fuentes configurables, conocimiento Obsidian y reportes Hermes."
version: 0.1.0
metadata:
  hermes:
    tags: [sauron, real-estate, recon, firecrawl, listings, telegram, knowledge]
---

# Sauron Recon

## Cuándo usar

Usar para convertir requisitos de alquiler/venta de locales en criterios estructurados, ejecutar búsquedas, revisar novedades o mantener la vault `knowledge/`.

## Flujo obligatorio

1. Leer `knowledge/00-index.md` y `knowledge/01-context-packs/sauron-core.md`.
2. Convertir el pedido a `SearchCriteria`; validar operación, zonas, moneda, precio y superficie.
3. Ejecutar primero en `dry-run` cuando cambie la consulta, una fuente o el destino.
4. Reportar resultados con URL, fuente, timestamp, campos no informados, score y razones.
5. Reportar también fuentes fallidas/omitidas y la cobertura real.
6. Actualizar conocimiento durable sólo con decisiones verificadas, incidentes reproducibles o cambios de contrato; enlazar la nota desde `00-index.md`.

## Comandos

Desde la raíz de la distribución:

```bash
python -m sauron_recon.entrypoints.cli health
python -m sauron_recon.entrypoints.cli search --dry-run \
  --criteria '{"operation":"rent","zones":["Palermo"],"max_price":1500,"min_area_m2":50}'
```

## Guardrails

- No inventar datos faltantes.
- No evadir CAPTCHA, login, robots.txt, paywalls o controles anti-bot.
- No guardar tokens, cookies, sesiones, PII innecesaria o bases runtime en `knowledge/`.
- No registrar cronjobs productivos ni enviar a Telegram sin destino confirmado y una prueba dry-run.
