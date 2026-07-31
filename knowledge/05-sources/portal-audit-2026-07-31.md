# Relevamiento de portales adicionales — Argentina

- Observación: 2026-07-31 19:50:16 -03:00
- Método: navegación pública, lectura de `robots.txt` y `POST /v1/scrape` al Firecrawl local compartido.
- Alcance: portales con alquiler/venta de inmuebles, locales, departamentos u otras categorías en Argentina.
- Regla: un `robots.txt` permisivo no reemplaza los Términos de Uso; cada fuente requiere un spike limitado antes de habilitarla.

## Candidatos prioritarios

| Portal | Evidencia observada | Robots / acceso | Evaluación | Próximo paso |
|---|---|---|---|---|
| [Inmuebles Clarín](https://www.inmuebles.clarin.com/locales/alquiler/argentina) | Firecrawl `success=true`, 35.012 caracteres, 217 enlaces internos; se observaron fichas como `local-en-alquiler-en-caballito--16095209`. | `robots.txt` permite rutas públicas de locales y contiene reglas explícitas de paginación. | **Prioridad alta**. Tiene búsqueda nacional, categorías y detalle reproducible. | Spike de listado + detalle + paginación; revisar términos y duplicados con Zonaprop/Argenprop. |
| [iCasas](https://www.icasas.com.ar/) | Firecrawl `success=true`, 12.048 caracteres; se observaron rutas por operación, tipo y localidades de distintas provincias, por ejemplo Córdoba, Rosario y Mar del Plata. | No bloquea las rutas públicas de búsqueda; bloquea endpoints internos, login y feeds. | **Prioridad alta/media**. Agregador nacional; riesgo alto de duplicados. | Validar una búsqueda de local y departamento, identificar detalle canónico y deduplicar por URL/ID. |
| [Servidos](https://servidos.ar/clasificados/inmuebles) | Firecrawl `success=true`, 5.783 caracteres; expone categorías de departamento, casa, PH, local comercial, oficina, terreno y galpón/depósito. | `User-agent: *` permite `/`; bloquea cuentas, gestión y rutas privadas. | **Prioridad media**. Clasificados públicos con cobertura declarada de Buenos Aires y Argentina. | Confirmar volumen real, URLs de detalle y paginación; no asumir cobertura completa por la página inicial. |
| [Bullano](https://www.bullano.com.ar/) | Firecrawl `success=true`, 25.232 caracteres; portal con rutas públicas de casas, departamentos y terrenos. | `User-agent: *` permite `/`; otros bots específicos están bloqueados. | **Prioridad media**. Potencialmente útil y accesible, pero hay que confirmar locales y cobertura provincial. | Buscar rutas de locales/alquiler y validar detalle. Respetar rate limit conservador. |
| [InmoBusqueda](https://www.inmobusqueda.com.ar/) | Firecrawl `success=true`, 23.918 caracteres; portal inmobiliario argentino con categorías y enlaces públicos. | `robots.txt` contiene bloqueos para varios crawlers identificados; falta revisar de forma completa el bloque `User-agent: *`. | **Pendiente de validación**. No habilitar hasta confirmar que el adapter elegido está permitido. | Revisión manual de Términos/robots y spike de bajo volumen. |
| [Inmoup](https://inmoup.com.ar/) | Firecrawl `success=true`, 6.360 caracteres; rutas por venta/alquiler y provincias, observadas Capital Federal y Mendoza. | `User-agent: *` permite `/`; bloquea áreas privadas y algunos parámetros. | **Prioridad alta/media**. Buenas URLs semánticas y cobertura multi-provincia. | Validar locales, departamentos, fichas y paginación; revisar si el contenido es agregador. |
| [PubliqueInmuebles](https://www.publiqueinmuebles.com.ar/propiedades) | Firecrawl `success=true`, 9.877 caracteres; expone rutas nacionales para departamentos, casas, PH, terrenos, locales, oficinas, galpones, campos, hoteles y cocheras. | Permite `/propiedades` y rutas públicas; bloquea `/api/`, dashboard y búsquedas con `?q=`. | **Prioridad alta/media**. Categorías nacionales y URL limpia para extracción. | Usar rutas permitidas sin `?q=`; validar alquiler/venta, detalle y paginación. |
| [InmoPro](https://inmopro.com.ar/) | Firecrawl `success=true`, 70.482 caracteres; expone búsqueda, alquiler y publicación de propiedades. | `robots.txt` sólo bloquea una ruta de importación de WordPress en la respuesta observada. | **Prioridad media**. Mucho contenido público, pero debe comprobarse si la búsqueda devuelve avisos o sólo contenido editorial. | Spike de búsqueda y detalle; descartar páginas institucionales. |
| [Zeta Prop](https://zetaprop.com.ar/propiedades) | Firecrawl `success=true`, 43.948 caracteres; observadas rutas de búsqueda por tipo y fichas `/propiedades/<id>`, incluyendo local comercial. | Permite `/`; bloquea dashboard, admin, API, impresión y assets internos. | **Prioridad alta/media**. Tiene fichas canónicas y páginas de búsqueda públicas. | Validar filtros de operación/localidad, paginación y campos de precio/superficie. |
| [BuscadorProp](https://www.buscadorprop.com.ar/) | Firecrawl `success=true`, 58.748 caracteres; sitio de búsqueda de propiedades e inmobiliarias. | Bloquea AJAX, tracker, estadísticas y algunas rutas de impresión; las páginas públicas no están bloqueadas en la respuesta observada. | **Prioridad media**. Puede aportar inventario agregado; riesgo de duplicados y páginas institucionales. | Identificar URLs de detalle y limitar a páginas públicas, nunca endpoints AJAX. |
| [Inmuebles en Baires](https://www.inmueblesenbaires.com.ar/) | Firecrawl `success=true`, 6.181 caracteres; portal público de propiedades en Buenos Aires. | `robots.txt` observado como `User-agent: * / Disallow:` vacío. | **Prioridad baja/media**. Cobertura regional, no nacional confirmada. | Validar volumen, categorías y fichas antes de incorporarlo. |
| [IZR](https://www.izr.com.ar/) | Firecrawl `success=true`, 28.350 caracteres; expone `/comprar` y `/alquilar` y contenido inmobiliario público. | `robots.txt` observado con `Disallow:` vacío. | **Prioridad baja/media**. Inmobiliaria/portal con foco aparente en Buenos Aires. | Confirmar si es inventario propio y cobertura; evitar tratarlo como portal nacional. |

## Fuentes con acceso parcial o no recomendadas todavía

- [SoloDueños](https://www.soloduenos.com/): home pública y `robots.txt` permite rutas públicas; Firecrawl devolvió `HTTP 500` en la URL de locales en alquiler observada. Reintentar de forma aislada y revisar si la falla es estable antes de habilitar.
- [RE/MAX Argentina](https://www.remax.com.ar/): las páginas de comprar/alquilar responden a Firecrawl, pero entregaron sólo 969/970 caracteres y no se observó inventario suficiente en el HTML extraído. Parece depender de contenido dinámico. Pendiente de spike; no declarar cobertura.
- [Mudafy](https://mudafy.com.ar/): la home responde a Firecrawl, pero `robots.txt` bloquea `/ficha/`, `/api/` y URLs con query. No es apto para una cobertura completa de avisos con detalle bajo la política actual.
- [Century 21 Argentina](https://century21.com.ar/): la home respondió con contenido `Loading` de 7 caracteres y `robots.txt` bloquea `/busqueda` y rutas de fichas. No habilitar.
- [Properati](https://www.properati.com.ar/): `robots.txt` y home devolvieron HTTP 403 en la observación. No intentar evadir el bloqueo.
- [Nestoria Argentina](https://www.nestoria.com.ar/): devolvió HTTP 401 en `robots.txt` y home. No habilitar sin autorización explícita.
- [Inmuebles24](https://www.inmuebles24.com/): la respuesta observada fue HTTP 403 y el dominio no representa claramente un inventario argentino; no priorizar.

## Facebook Marketplace

[Facebook Marketplace](https://www.facebook.com/marketplace/) **no se agrega** como adapter Firecrawl.

Evidencia observada el 2026-07-31:

- La página pública redirige a una pantalla de login con campos de email/teléfono y contraseña.
- `https://www.facebook.com/robots.txt` declara que la recolección automatizada está prohibida salvo permiso escrito expreso de Facebook y para el propósito limitado autorizado.
- No se usarán sesiones personales, login automatizado, CAPTCHA ni evasión de controles.

Clasificación: **excluido por autenticación y política de recolección automatizada**, salvo futura integración oficial/autorizada.

## Priorización resultante

1. Inmuebles Clarín.
2. Zeta Prop.
3. Inmoup.
4. PubliqueInmuebles.
5. iCasas.
6. Bullano y Servidos.
7. InmoPro y BuscadorProp.
8. Inmuebles en Baires e IZR para cobertura regional.

La prioridad no implica habilitación automática. Cada portal debe superar un spike con: URL de búsqueda, URLs de detalle, paginación, normalización de campos, términos/robots, rate limit y comparación de duplicados. La cobertura debe reportarse por fuente y no puede declararse completa mientras una fuente configurada quede sin validar.
