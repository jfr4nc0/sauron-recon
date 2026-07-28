from __future__ import annotations

from pathlib import Path
from typing import Iterable

from sauron_recon.application.ports import SearchResult
from sauron_recon.domain.changes import ListingChange


def render_pdf(result: SearchResult, changes: Iterable[ListingChange], output: str | Path) -> Path:
    """Render a deduplicated report PDF; import reportlab only when PDF is requested."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF reports require the 'pdf' optional dependency (reportlab)") from exc

    unique: dict[str, ListingChange] = {}
    for change in changes:
        unique.setdefault(change.listing.identity, change)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    story = [Paragraph(f"Sauron Recon — corrida {result.run_id}", styles["Title"]), Spacer(1, 8)]
    story.append(Paragraph(f"Listings nuevos o modificados: {len(unique)}", normal))
    story.append(Paragraph(f"Candidatos de duplicado cross-source: {len(result.duplicate_candidates)}", normal))
    story.append(Spacer(1, 10))
    rows = [["Estado", "Fuente", "Aviso", "Descripción", "Precio", "Superficie", "Enlace"]]
    for change in unique.values():
        listing = change.listing
        description = " ".join(str(listing.raw.get("markdown", "")).split())
        description = description[:240] + ("…" if len(description) > 240 else "")
        price = f"{listing.price} {listing.currency or ''}".strip() if listing.price is not None else "—"
        area = f"{listing.area_m2} m²" if listing.area_m2 is not None else "—"
        rows.append([change.kind, listing.source, listing.title[:90], description or "—", price, area, listing.url])
    table = Table(rows, colWidths=[18 * mm, 20 * mm, 42 * mm, 55 * mm, 25 * mm, 22 * mm, 28 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f7")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))
    for failure in result.failures:
        story.append(Paragraph(f"Advertencia {failure.source}: {failure.message}", normal))
    SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm).build(story)
    return output_path
