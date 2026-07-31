# Sauron Recon Knowledge Vault

Esta vault es la capa de conocimiento durable del proyecto y la referencia para context engineering de los perfiles Sauron.

## Cómo usarla

1. Empezar por [[01-context-packs/sauron-core]].
2. Consultar [[02-architecture/overview]] para límites y dependencias.
3. Consultar [[03-contracts/domain-contracts]] antes de cambiar schemas.
4. Registrar decisiones nuevas en [[04-decisions/decision-log]].
5. Mantener fuentes, incidentes y runbooks enlazados.

## Reglas

- La vault contiene conocimiento reusable, no sesiones, secretos, tokens, cookies ni bases runtime.
- Cada afirmación externa importante incluye fuente y fecha.
- Los agentes actualizan notas sólo después de verificar evidencia.
- Las notas nuevas deben enlazarse desde este índice o desde un context pack.
- Los resultados de scraping crudos viven fuera de Git y tienen retención limitada.

## Mapa

- [[01-context-packs/sauron-core]] — contexto mínimo que todo perfil debe cargar.
- [[02-architecture/overview]] — arquitectura y flujo de datos.
- [[03-contracts/domain-contracts]] — contratos del núcleo.
- [[04-decisions/decision-log]] — decisiones arquitectónicas.
- [[04-decisions/adr-003-self-hosted-connectors]] — arquitectura self-hosted con conectores externos opcionales.
- [[04-decisions/adr-004-free-software-mit]] — software libre, gratuito y self-hosted bajo MIT.
- [[05-sources/portal-audit-2026-07-31]] — relevamiento de portales argentinos adicionales y validación inicial con Firecrawl.
- [[05-sources/source-policy]] — política de fuentes y cumplimiento.
- [[06-operations/runbook]] — operación, dry-run y recuperación.
- [[07-roadmap/phase-1-core]] — estado y aceptación de la primera fase.
- [[07-roadmap/phase-2-extraction-history]] — extracción real, histórico y reportes.
- [[07-roadmap/phase-3-resilience]] — rate limiting, circuit breaker y desapariciones seguras.
- [[07-roadmap/phase-4-portal-adapters]] — adapters explícitos y fallback por portal.
- [[07-roadmap/phase-5-contractual-detail-parsing]] — clasificación y extracción de avisos individuales.
- [[07-roadmap/phase-6-listing-enrichment]] — IDs, expensas, contacto público y fingerprint ampliado.
- [[07-roadmap/phase-7-availability-dedup]] — disponibilidad y candidatos de duplicado cross-source.
- [[07-roadmap/phase-8-persistent-duplicate-candidates]] — persistencia histórica y normalización de direcciones.
- [[07-roadmap/phase-9-telegram-wizard-pdf]] — wizard `/start`, criterios extendidos y PDF horario.
