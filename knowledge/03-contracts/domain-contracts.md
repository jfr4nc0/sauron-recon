# Domain Contracts

## SearchCriteria

Campos actuales:

- `operation`: `rent`, `sale`, `rent_or_sale`.
- `zones`: lista de zonas o barrios.
- `min_price`, `max_price`, `currency`.
- `min_area_m2`, `max_area_m2`.
- `property_type`.

El constructor rechaza rangos invertidos y operaciones desconocidas.

## Listing

Campos mínimos:

- `source`
- `url` canónica
- `title`
- `operation`, `zone`, `price`, `currency`, `area_m2`, `address` opcionales
- `observed_at`
- `raw` acotado y no sensible

La identidad inicial es `source + canonical_url`. Los parámetros tracking se eliminan; el fragmento URL se descarta.

## Score

El score es explicable y devuelve razones. Un listing puede quedar como `hard_match=false` si la fuente no confirma un criterio; nunca se presenta como coincidencia completa sin evidencia.
