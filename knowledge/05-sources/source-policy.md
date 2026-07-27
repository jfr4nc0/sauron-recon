# Source Policy

## Permitido

- Consultar fuentes públicas sólo dentro de sus términos, robots.txt y límites de frecuencia.
- Usar API, feed o integración autorizada cuando exista.
- Registrar URL, timestamp y fuente para trazabilidad.

## No permitido

- Evadir CAPTCHA, login walls, paywalls o mecanismos anti-bot.
- Usar cookies/sesiones personales en la distribución.
- Hacer crawling ilimitado o paralelismo agresivo.
- Guardar PII innecesaria o payloads crudos sin retención definida.

## Estado inicial

Firecrawl es el adapter de extracción implementado en esta fase y usa el daemon compartido existente, no una instancia propia. El cliente usa `POST /v1/search`, timeout, retry con backoff y errores tipados; el source filtra por allowlist de dominios y mapea resultados a `Listing`. Una corrida real `dry-run` con `local comercial alquiler Palermo` devolvió dos resultados de Zonaprop sin fallos.

Mercado Libre, Zonaprop, Argenprop e inmobiliarias todavía deben habilitarse individualmente después de un spike que verifique términos, acceso y estabilidad. En esta fase Zonaprop apareció como resultado del endpoint general Firecrawl; aún no se considera un adapter específico de Zonaprop.
