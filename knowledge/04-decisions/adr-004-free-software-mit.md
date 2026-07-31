# ADR-004 — Sauron como software libre con licencia MIT

- Fecha: 2026-07-31
- Estado: aceptada
- Decisión: mantener Sauron Recon como software libre, gratuito y self-hosted bajo MIT.
- Alcance: cualquier persona puede instalar, usar, modificar y redistribuir el proyecto. Cada instalación conserva sus datos, credenciales, sesiones y runtime local.
- Motivo: el objetivo es resolver búsquedas inmobiliarias de uso personal/comunitario, no operar un SaaS centralizado ni vender el acceso.
- Límite: la licencia del código no concede permiso para automatizar portales que prohíban la recolección. Cada source adapter debe respetar API, feed autorizado, términos, `robots.txt`, autenticación y límites de la fuente.
- Implementación: [[../05-sources/source-policy]] y [[../05-sources/portal-audit-2026-07-31]] definen los modos permitidos; `src/sauron_recon/application/source_registry.py` registra capacidades y estados sin habilitar fuentes bloqueadas.
- Licencia: el texto completo está en `LICENSE`; `pyproject.toml` declara `MIT`.
