from __future__ import annotations

from collections.abc import Iterable

from sauron_recon.application.ports import SearchResult
from sauron_recon.domain.changes import ListingChange


def render_report(result: SearchResult, changes: Iterable[ListingChange] = ()) -> str:
    changes = tuple(changes)
    actionable = tuple(change for change in changes if change.is_actionable)
    lines = [f"# Sauron Recon — corrida `{result.run_id}`", "", f"Novedades: **{len(actionable)}**", ""]
    if actionable:
        lines.append("## Listings nuevos o modificados")
        lines.append("")
        for change in actionable:
            listing = change.listing
            marker = {"new": "Nuevo", "changed": "Modificado", "disappeared": "Desaparecido"}[change.kind]
            details = []
            if listing.price is not None:
                details.append(f"precio {listing.price} {listing.currency or ''}".strip())
            if listing.area_m2 is not None:
                details.append(f"{listing.area_m2} m²")
            if listing.expenses is not None:
                details.append(f"expensas {listing.expenses}")
            if listing.contact:
                details.append("contacto publicado")
            suffix = f" — {', '.join(details)}" if details else ""
            fields = f" ({', '.join(change.changed_fields)})" if change.changed_fields else ""
            lines.extend([f"- **{marker}**{fields}: [{listing.title}]({listing.url}){suffix}"])
        lines.append("")
    else:
        lines.extend(["No hay listings nuevos o modificados.", ""])
    lines.append("## Cobertura")
    lines.append("")
    lines.append(f"- Listings observados: {len(result.listings)}")
    lines.append(f"- Fuentes con error: {len(result.failures)}")
    lines.append(f"- Posibles duplicados cross-source: {len(result.duplicate_candidates)}")
    for failure in result.failures:
        lines.append(f"- ⚠️ `{failure.source}`: {failure.error_type} — {failure.message}")
    lines.append("")
    lines.append("_Los campos no publicados por la fuente no se infieren._")
    return "\n".join(lines)
