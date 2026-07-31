# Sauron Recon — plan de implementación

## 1. Objetivo

Construir un agente liviano para Hermes que descubra locales comerciales en alquiler o venta según requisitos expresados por el usuario, consulte múltiples fuentes públicas —Mercado Libre Inmuebles, Zonaprop, Argenprop, inmobiliarias y otras fuentes configurables—, normalice y deduplique resultados, y genere reportes periódicos enviados por Telegram mediante cronjobs del Hermes Gateway.

El sistema debe priorizar resiliencia, trazabilidad y bajo acoplamiento: una fuente caída no debe impedir el reporte de las demás, y el agente conversacional no debe ser responsable de ejecutar scraping frágil o mantener estado de forma implícita.

## 2. Principios y límites

- Clean Architecture / Ports and Adapters: dominio y casos de uso sin dependencias de Hermes, Firecrawl, HTTP o SQLite.
- Lightweight first: Python estándar + pocas dependencias; SQLite como persistencia inicial; sin servidor web ni cola propia en el MVP.
- Deterministic core: búsqueda, parsing, normalización, deduplicación, scoring e idempotencia en código determinista; Hermes se usa para interpretar requisitos y redactar el informe, no para extraer datos críticos.
- Source isolation: cada sitio se implementa detrás de un adapter independiente y reemplazable.
- Graceful degradation: errores por fuente se registran y se reportan, pero no abortan el job completo.
- Secure by default: secretos sólo por variables de entorno/secret manager; nunca en el repositorio ni en prompts.
- Compliance-aware: respetar robots.txt, términos de uso, límites de frecuencia y mecanismos anti-bot; no evadir CAPTCHAs, login walls ni controles de acceso. Si una fuente no permite acceso automatizado, se deshabilita o se usa su API/feed autorizado.
- Reproducible: cada corrida deja run_id, configuración efectiva no sensible, fuentes consultadas, timestamps, errores y hashes de resultados.

## 3. Arquitectura propuesta

```text
Hermes Gateway / Telegram
          |
          | requisitos y comandos; cronjob dispara CLI
          v
      Application
  SearchListingsUseCase
  BuildReportUseCase
          |
          +--> SourcePort <--- FirecrawlAdapter
          |                 <--- HTTP/API adapter
          |                 <--- source adapters futuros
          |
          +--> ListingRepositoryPort <--- SQLiteRepository
          +--> RunRepositoryPort     <--- SQLiteRepository
          +--> NotificationPort       <--- Hermes send / Telegram adapter
          |
      Domain
  SearchCriteria, Listing, SourceResult,
  MatchScore, SearchRun, Report
```

### Capas

- `domain/`: entidades, value objects, reglas de normalización y scoring; sin IO.
- `application/`: casos de uso, puertos, políticas de retry/idempotencia y orquestación.
- `adapters/`: Firecrawl, HTTP/API, SQLite, Telegram/Hermes, clock y filesystem.
- `entrypoints/`: CLI para búsqueda manual, reportes y health checks; integración de skills/prompts de Hermes.
- `config/`: schema y ejemplos sin secretos.
- `connectors/`: contratos y providers opcionales para OAuth HTTPS y servicios externos; no contienen secretos.

## 4. Modelo funcional

### Requisitos de búsqueda

Representar explícitamente, con schema validable:

- operación: alquiler, venta o ambas;
- tipo: local comercial/oficina/galpón si se amplía;
- zonas, barrios, radios y exclusiones;
- precio máximo/mínimo y moneda;
- superficie cubierta/total mínima y máxima;
- frente, esquina, baños, apto gastronómico, expensas, cochera y otros atributos opcionales;
- frecuencia de ejecución y ventana de novedades;
- fuentes habilitadas y límite por fuente;
- reglas de notificación y destinatario lógico, sin guardar IDs sensibles en el repo.

La interpretación de lenguaje natural se hará en Hermes hacia este contrato estructurado. Se validará antes de ejecutar y se conservará la consulta normalizada junto con el job.

### Pipeline de una corrida

1. Cargar y validar `SearchCriteria`.
2. Crear `SearchRun` con `run_id` e idempotency key.
3. Expandir criterios a consultas por fuente.
4. Ejecutar adapters con concurrencia acotada y timeout por fuente.
5. Parsear a `Listing` canónico, conservando URL y campos originales.
6. Normalizar moneda, superficie, teléfono, dirección y texto; marcar valores inferidos como tales.
7. Deduplicar por URL canónica y fingerprint conservador —nunca fusionar sólo por título—.
8. Aplicar filtros duros y score explicable; cada match debe mostrar por qué califica.
9. Comparar contra el histórico para detectar nuevos, modificados, vistos y desaparecidos.
10. Persistir resultados y métricas de la corrida de forma transaccional.
11. Renderizar reporte Markdown/HTML corto y, si corresponde, dividirlo en mensajes Telegram respetando límites.
12. Emitir resumen de cobertura y errores por fuente.

## 5. Fuentes y estrategia de extracción

### MVP

- Firecrawl como proveedor principal de búsqueda/extracción cuando esté disponible.
- Adapters por fuente para construir queries, seleccionar URLs y mapear campos.
- Fallback HTTP sólo para fuentes donde sea legítimo y estable; no convertir el fallback en un scraper genérico sin límites.
- Configuración de fuentes mediante registry, de modo que agregar una inmobiliaria no requiera modificar el caso de uso.

### Robustez por fuente

Cada adapter debe declarar: nombre, capacidades, rate limit, timeout, estrategia de paginación, parser, health check y política de fallback. Errores tipados: timeout, rate limit, bloqueo, schema inválido, parse error y fuente no disponible.

Usar retry con exponential backoff + jitter sólo para errores transitorios, circuit breaker por fuente, cache de URLs/resultados, límites de páginas y concurrencia. Los parsers deben tolerar cambios de layout sin inventar datos: campos no encontrados quedan `null` y se registra una alerta de schema drift.

## 6. Persistencia e idempotencia

SQLite en modo WAL para el MVP, con migraciones versionadas y tablas mínimas:

- `searches`: criterios normalizados, estado y metadata no sensible;
- `runs`: estado, timestamps, cobertura, error summary y duración;
- `listings`: identidad canónica, datos normalizados, raw metadata acotada y source;
- `observations`: precio/estado/hash por corrida;
- `deliveries`: reporte, destino lógico, estado y deduplication key.

Políticas:

- Una misma corrida no puede duplicar listings ni enviar dos veces el mismo reporte.
- Retener raw payloads sólo de forma acotada/configurable; preferir hashes y campos normalizados.
- Backups opcionales del archivo SQLite; no incluir la base en Git.

## 7. Integración Hermes y cronjobs

No acoplar la lógica al proceso del Gateway. Entregar una skill/procedimiento de Sauron Recon y comandos CLI invocables desde cron:

- `sauron-recon search --criteria ...`
- `sauron-recon report --search-id ... --since ...`
- `sauron-recon health`

El cronjob sólo debe disparar una ejecución idempotente con `workdir`, skill, límites y destinatario configurados. El reporte puede encadenarse mediante `context_from` o enviarse usando el mecanismo de mensajería de Hermes; evitar que el LLM sea el canal de datos estructurados.

Cronjobs iniciales, después de validar manualmente:

1. descubrimiento periódico por búsqueda guardada;
2. generación de reporte de novedades;
3. health/alerta de fuentes fallidas.

Cada job tendrá timeout, reintento controlado, ventana de novedades, quiet hours opcionales y fallback de error. Nunca registrar un cron productivo sin confirmar el chat/Telegram destino y las credenciales disponibles.

## 8. Observabilidad y operación

- Logs estructurados en stderr con `run_id`, `source`, `request_id` y duración; URLs sin secretos.
- Métricas básicas: fuentes consultadas, éxito/error, listings extraídos, parse rate, deduplicación, nuevos y notificación.
- `health` verifica configuración, SQLite, Firecrawl y conectividad de notificación sin ejecutar scraping masivo.
- Reportes incluyen cobertura real, timestamp, fuentes omitidas y advertencias.
- Feature flags para habilitar fuentes individualmente y modo dry-run para no notificar.

## 9. Seguridad y privacidad

- `.env.template` documenta variables; `.env`, tokens Telegram, cookies, bases y reportes locales quedan ignorados.
- Allowlist de dominios para evitar SSRF y navegación accidental a destinos internos.
- Sanitizar HTML/Markdown antes de enviarlo a Telegram.
- No persistir datos personales innecesarios; teléfonos y nombres de contacto se tratan como PII y se pueden omitir por configuración.
- Validar URLs y redirecciones; límites de tamaño de respuesta y de memoria.
- Tests de secretos accidentales, path traversal, SSRF, contenido malicioso y Telegram message splitting.

## 10. Plan por fases

### Fase 0 — contrato y spike

- Confirmar versión/runtime de Hermes Gateway y mecanismo de entrega Telegram.
- Verificar Firecrawl real y probar una búsqueda pequeña por cada fuente candidata.
- Definir schema de `SearchCriteria` y `Listing` con fixtures anonimizados.
- Documentar límites legales/operativos por fuente.

Salida: ADR-001, schemas, fixtures y decisión de fuentes MVP.

### Fase 1 — núcleo determinista

- Crear package Python liviano y CLI.
- Implementar dominio, validación, normalización, deduplicación y scoring.
- Implementar SQLite repositories y migraciones.
- Tests unitarios y contract tests con respuestas fixture.

Salida: búsqueda offline reproducible con datos fixture y `pytest` verde.

### Fase 2 — extracción y resiliencia

- Implementar Firecrawl adapter y primer adapter de fuente.
- Agregar retry/backoff, timeout, circuit breaker, cache, rate limiting y métricas.
- Agregar adapters restantes sólo tras validar acceso permitido y estabilidad.
- Tests de fallos parciales, schema drift, rate limit y reanudación.

Salida: corrida real pequeña en dry-run, con evidencia por fuente.

### Fase 3 — reportes y Hermes

- Implementar report renderer, resumen de cobertura y Telegram delivery port.
- Crear skill Hermes, comandos documentados y configuración de ejemplo.
- Probar entrega manual a un chat de prueba, luego dry-run de cron.

Salida: reporte legible, deduplicado e idempotente.

### Fase 4 — operación programada

- Registrar cronjobs del Gateway con `workdir`, skill, timeout y horario aprobados.
- Agregar health job y alertas de degradación.
- Documentar backup, rotación, recuperación y rollback.
- Ejecutar corrida de aceptación durante varios ciclos antes de habilitar notificaciones completas.

Salida: operación estable y observable; runbook de incidentes.

## 11. Estructura de repositorio propuesta

```text
sauron-recon/
├── README.md
├── PLAN.md
├── pyproject.toml
├── .env.template
├── .gitignore
├── src/sauron_recon/
│   ├── domain/
│   ├── application/
│   ├── adapters/
│   ├── config/
│   └── entrypoints/
├── tests/
│   ├── unit/
│   ├── contract/
│   └── fixtures/
├── docs/
│   ├── adr/
│   ├── runbook.md
│   └── hermes-cron.example.md
└── skills/sauron-recon/SKILL.md
```

## 12. Criterios de aceptación del MVP

- Una búsqueda estructurada produce resultados canónicos desde al menos dos fuentes habilitadas.
- Una fuente que falla no cancela las otras y queda visible en el reporte.
- Repetir la misma corrida no duplica listings ni envíos.
- Los resultados incluyen URL fuente, timestamp, precio/superficie cuando están disponibles y explicación del score.
- Parsers no inventan valores ante cambios o campos ausentes.
- Se puede ejecutar en dry-run sin Telegram ni secretos productivos.
- `pytest`, lint/type checks y `health` pasan en un entorno limpio.
- No se almacenan secretos, cookies ni la base runtime en el repositorio.
- El cronjob de prueba puede ejecutar el CLI y entregar un reporte acotado a Telegram.

## 13. Decisiones pendientes antes de implementar

1. ¿Qué ciudades/barrios y moneda deben ser el primer caso real?
2. ¿Qué campos son obligatorios para considerar un local válido?
3. ¿Qué frecuencia y ventana de novedades se necesita?
4. ¿Qué chat/topic de Telegram recibirá los reportes?
5. ¿Qué fuentes tienen acceso autorizado/aceptable para automatización en el entorno?
6. ¿Se requiere historial largo o sólo novedades de los últimos N días?
7. ¿La primera versión debe ser una skill + CLI independiente o un plugin Hermes formal?

La recomendación inicial es skill + CLI independiente: reduce el acoplamiento, facilita pruebas y permite cambiar Hermes sin reescribir el núcleo.