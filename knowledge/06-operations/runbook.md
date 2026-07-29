# Operations Runbook

## Dry-run

1. Copiar `.env.template` a la configuración del perfil Hermes fuera del repositorio y completar sólo las variables necesarias.
2. Ejecutar `sauron-recon health`.
3. Validar criterios JSON con `sauron-recon search --dry-run --criteria '{...}'`.
4. Revisar cobertura, errores y deduplicación antes de habilitar notificaciones.

## Incidentes

- Firecrawl caído: mantener la corrida parcial, registrar fuente fallida y no reintentar indefinidamente.
- Cambios de layout: detener sólo el adapter afectado, conservar evidencia de schema drift y actualizar fixture/parser.
- Telegram fallido: persistir delivery pendiente e impedir duplicados en el reintento.
- Estado corrupto: restaurar backup SQLite, ejecutar health y repetir desde un run_id nuevo.

## Verificación

No declarar un cron productivo hasta verificar manualmente el destino Telegram, el `workdir`, las variables requeridas y al menos una ejecución dry-run.
