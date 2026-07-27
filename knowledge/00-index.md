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
- [[05-sources/source-policy]] — política de fuentes y cumplimiento.
- [[06-operations/runbook]] — operación, dry-run y recuperación.
- [[07-roadmap/phase-1-core]] — estado y aceptación de la primera fase.
- [[07-roadmap/phase-2-extraction-history]] — extracción real, histórico y reportes.
- [[07-roadmap/phase-3-resilience]] — rate limiting, circuit breaker y desapariciones seguras.
