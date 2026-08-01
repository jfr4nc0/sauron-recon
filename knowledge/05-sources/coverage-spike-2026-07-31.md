# Spike de cobertura real — 2026-07-31

- Observación: 2026-07-31 22:00 -03:00
- Método: probe HTTP honesto (urllib) + spike Firecrawl local (browser real) sobre 22 portales.
- Búsqueda de referencia: locales/depósitos en alquiler en Caballito, CABA.

## Matriz de cobertura verificada

### En producción (confiable vía Firecrawl search)

| Portal | Inventario observado | Método | Confiabilidad |
|---|---|---|---|
| zonaprop | 152 locales en Caballito | Firecrawl `/v1/search` site:query | Media — CloudFront puede devolver 403 intermitentemente |
| argenprop | 119 locales en Caballito | Firecrawl `/v1/search` site:query | Media — mismo patrón intermitente |

### Candidatos con inventario real pero no confiables para cron

| Portal | Inventario observado | Problema | Próximo paso |
|---|---|---|---|
| inmuebles-clarin | 56 listings de locales en Caballito con precios/áreas | CloudFront bloquea Firecrawl de forma intermitente (a veces 35K de markdown, a veces 403) | No habilitar en cron hasta resolver estabilidad; considerar feed autorizado |
| mercadolibre | Disponible vía API | Requiere OAuth oficial + redirect_uri HTTPS | Pendiente de credenciales del usuario |

### Candidatos JS-rendered (Firecrawl no extrae listings de HTML estático)

| Portal | Home responde | Listings extraíbles | Problema |
|---|---|---|---|
| remax | 200, 1.3K markdown | No — JS-heavy, sin contenido en scrape estático | Requiere Crawl4AI con renderizado completo |
| publiqueinmuebles | 200, 9.8K home | No — filtros devuelven "0 Propiedad" en HTML estático | Requiere JS rendering |
| bullano | 200, 24K home | No — propiedades cargadas vía JS | Requiere JS rendering |
| inmopro | 200, 70K home | No — /propiedades devuelve 404 | URLs de listing rotas o cambiadas |
| inmoup | 200, 3K home | No — JS-rendered | Requiere JS rendering |
| century21 | 200, 3K home | No — JS-rendered (sólo nav) | Requiere JS rendering |

### No usables

| Portal | Estado | Razón |
|---|---|---|
| servidos | 200 OK pero 0 anuncios | Sitio nuevo/vacío — estructura correcta pero sin inventario real |
| soloduenos | 500 en listing pages | Errores de servidor en URLs de locales/depósitos |
| mudafy | 404 en rutas de listing | URLs de alquiler devuelven 404 |
| properati | 403 | Bloqueado — robots.txt inaccesible |
| nestoria | 401 | Bloqueado — requiere autenticación |
| inmuebles24 | 403 | Bloqueado |
| facebook-marketplace | Login wall | Deshabilitado por autenticación y política |

## Resumen numérico

- En producción: 2 portales (zonaprop, argenprop)
- Candidatos con inventario: 2 (inmuebles-clarin intermitente, mercadolibre OAuth)
- Candidatos JS-rendered: 6 (remax, publiqueinmuebles, bullano, inmopro, inmoup, century21)
- No usables: 7 (servidos, soloduenos, mudafy, properati, nestoria, inmuebles24, facebook)

## Conclusión

La cobertura real hoy es zonaprop + argenprop vía Firecrawl search mode. Inmuebles Clarín tiene inventario parseable pero CloudFront lo hace intermitente. Los 6 portales JS-rendered no entregan listings en HTML estático; Crawl4AI con renderizado podría habilitarlos, sujeto a robots y términos. MercadoLibre queda pendiente de OAuth.

No se evadieron 403, login, CAPTCHA ni robots. Los portales bloqueados quedan como bloqueados.
