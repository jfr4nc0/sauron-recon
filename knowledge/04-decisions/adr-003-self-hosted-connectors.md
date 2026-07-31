# ADR-003 — Núcleo self-hosted con conectores externos opcionales

- Fecha: 2026-07-31
- Estado: aceptada
- Decisión: Sauron Recon mantiene su núcleo, persistencia, jobs y reportes en la instalación local del usuario. Hermes Gateway y su plugin Telegram son la interfaz principal. Las integraciones que requieren infraestructura externa se encapsulan en conectores explícitos y opcionales.
- Fuente: discusión de producto y revisión de Hermes/MercadoLibre, 2026-07-31.

## Alcance

Self-hosted por defecto:

- Sauron Recon y sus adapters.
- Hermes Gateway y Telegram bridge.
- SQLite, estado del wizard, jobs y reportes.
- Firecrawl local cuando el usuario lo instala localmente.
- Secretos y tokens en el entorno local del perfil Hermes.

Conectores externos opcionales:

- ngrok o Cloudflare Tunnel para callbacks OAuth HTTPS.
- dominio/reverse proxy propio del usuario.
- Firecrawl administrado.
- APIs de terceros, incluyendo MercadoLibre.

## Decisiones de integración

- El plugin de Hermes Gateway sigue siendo la superficie principal porque resuelve Telegram, allowlists, topics, home channel y cron.
- MCP queda como fachada opcional futura para que otros agentes consuman búsquedas y reportes; no reemplaza el bridge Telegram ni el núcleo determinista.
- No se compra ni se exige un dominio HTTPS central compartido: agregaría dependencia multi-tenant, costo y manejo centralizado de callbacks/tokens.
- MercadoLibre usa su OAuth oficial cuando el usuario configura un conector HTTPS. Sin callback válido, la fuente queda explícitamente `no configurada` y nunca se presenta como cubierta.

## Seguridad

- Cada conector declara capacidades, estado de configuración y si utiliza infraestructura externa.
- El setup wizard no solicita secretos por Telegram.
- `state`, PKCE y validación estricta de `redirect_uri` serán obligatorios para OAuth.
- Sólo se expone el endpoint de callback, nunca el panel ni el puerto completo de Sauron.
- Los tokens permanecen locales; no se persisten en `knowledge/`, Git ni mensajes.

## Plan de implementación

1. Registry y contrato de conectores.
2. `/setup` Telegram para seleccionar fuentes y conector OAuth.
3. Callback OAuth local detrás del conector elegido.
4. Adapter oficial paginado de MercadoLibre.
5. Health checks y cobertura por conector.
6. MCP facade opcional.
