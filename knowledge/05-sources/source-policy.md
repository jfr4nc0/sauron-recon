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

El relevamiento de portales adicionales del 2026-07-31 está documentado en [[portal-audit-2026-07-31]]. Los candidatos prioritarios fueron Inmuebles Clarín, Zeta Prop, Inmoup, PubliqueInmuebles, iCasas, Bullano, Servidos, InmoPro y BuscadorProp. Se separaron fuentes parciales, bloqueadas o dinámicas de las fuentes habilitables; ningún candidato queda configurado automáticamente por aparecer en el relevamiento.

## MercadoLibre oficial

La documentación oficial de autenticación y autorización ([MercadoLibre OAuth](https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion), observada 2026-07-28) indica que la aplicación entrega APP ID y Secret Key, y que el usuario autorizado entrega un `code` intercambiable por `access_token` y `refresh_token`. El `refresh_token` rota y es de uso único. La guía [Localizar Inmuebles](https://developers.mercadolibre.com.ar/es_ar/localizar-inmuebles) documenta `classified_locations` para resolver ubicaciones, no un buscador de publicaciones. El [MCP Server](https://developers.mercadolibre.com.ar/es_ar/mcp-server) expone herramientas de documentación (`search_documentation` y `get_documentation_page`), no un feed inmobiliario para Sauron.

La cobertura de MercadoLibre no se considera completa mediante Firecrawl. El adapter debe usar la API oficial de publicaciones con OAuth, paginación y resolución de ubicación; los secretos permanecen sólo en el entorno local del perfil Hermes.
