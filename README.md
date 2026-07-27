# sauron-recon

Agente liviano para Hermes orientado a descubrir locales comerciales en alquiler o venta, normalizar resultados de múltiples fuentes, detectar novedades y enviar reportes por Telegram.

Estado: planificación. La arquitectura y el roadmap están en [PLAN.md](PLAN.md).

El proyecto no evade CAPTCHAs, autenticación ni controles anti-bot. Las fuentes deben ser consultadas respetando sus términos, robots.txt, límites de frecuencia y permisos de automatización.

## Próximo paso

Revisar y aprobar `PLAN.md`, especialmente el alcance del MVP, las fuentes permitidas, los criterios de búsqueda y el destino de Telegram. Luego se implementará el núcleo determinista antes de conectar scraping real y cronjobs productivos.
