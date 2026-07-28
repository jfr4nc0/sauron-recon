from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from sauron_recon.domain.models import SearchCriteria


class WizardStep(StrEnum):
    OPERATION = "operation"
    PROPERTY_TYPE = "property_type"
    ROOMS = "rooms"
    BATHROOMS = "bathrooms"
    AREA = "area"
    UTILITIES = "utilities"
    LOCATION = "location"
    BUDGET = "budget"
    CONFIRM = "confirm"
    COMPLETE = "complete"


@dataclass(frozen=True)
class WizardReply:
    text: str
    criteria: SearchCriteria | None
    step: WizardStep
    completed: bool = False


def _clean(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower().strip()


def _number(value: str) -> Decimal | None:
    match = re.search(r"\d[\d.\s]*(?:,\d+)?", value)
    if not match:
        return None
    try:
        return Decimal(match.group(0).replace(" ", "").replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


class RequirementsWizard:
    """Deterministic Telegram-friendly requirements wizard.

    The gateway can keep one instance per chat/thread. It never activates jobs;
    callers must persist the confirmed criteria and explicitly provision a job.
    """

    def __init__(self) -> None:
        self.criteria = SearchCriteria(operation="rent", property_type="local")
        self.step = WizardStep.OPERATION

    def start(self) -> WizardReply:
        self.criteria = SearchCriteria(operation="rent", property_type="local")
        self.step = WizardStep.OPERATION
        return WizardReply("¿Buscás comprar, alquilar o ambas opciones?", self.criteria, self.step)

    def receive(self, answer: str) -> WizardReply:
        value = _clean(answer)
        if value in {"cancelar", "cancel", "/cancel"}:
            self.step = WizardStep.COMPLETE
            return WizardReply("Cancelé la configuración de búsqueda.", None, self.step, completed=True)
        if self.step is WizardStep.OPERATION:
            operation = "rent_or_sale" if ("amb" in value or ("compr" in value and ("alquil" in value or "rent" in value))) else "sale" if any(x in value for x in ("compr", "venta", "vender")) else "rent"
            self.criteria = replace(self.criteria, operation=operation)
            self.step = WizardStep.PROPERTY_TYPE
            return WizardReply("¿Qué querés buscar? departamento, casa, local, depósito, fábrica u otro tipo.", self.criteria, self.step)
        if self.step is WizardStep.PROPERTY_TYPE:
            property_type = next((item for item in ("departamento", "casa", "local", "deposito", "fabrica", "terreno") if item in value), value or "local")
            self.criteria = replace(self.criteria, property_type=property_type)
            self.step = WizardStep.ROOMS
            return WizardReply("¿Cuántos ambientes necesitás? Podés responder ‘cualquiera’.", self.criteria, self.step)
        if self.step is WizardStep.ROOMS:
            self.criteria = replace(self.criteria, rooms=None if "cual" in value or "indist" in value else int(_number(value) or 0))
            self.step = WizardStep.BATHROOMS
            return WizardReply("¿Cuántos baños como mínimo? Podés responder ‘cualquiera’.", self.criteria, self.step)
        if self.step is WizardStep.BATHROOMS:
            self.criteria = replace(self.criteria, bathrooms=None if "cual" in value or "indist" in value else int(_number(value) or 0))
            self.step = WizardStep.AREA
            return WizardReply("¿Qué superficie necesitás? Indicá mínimo y máximo en m², por ejemplo ‘80 a 150’. ", self.criteria, self.step)
        if self.step is WizardStep.AREA:
            numbers = re.findall(r"\d[\d.\s]*(?:,\d+)?", value)
            parsed = [_number(item) for item in numbers]
            parsed = [item for item in parsed if item is not None]
            self.criteria = replace(self.criteria, min_area_m2=parsed[0] if parsed else None, max_area_m2=parsed[1] if len(parsed) > 1 else None)
            self.step = WizardStep.UTILITIES
            return WizardReply("¿Necesitás trifásica u otra condición? Respondé sí/no y podés agregar texto libre.", self.criteria, self.step)
        if self.step is WizardStep.UTILITIES:
            needs = None if "no" in value or "cual" in value else True if "trif" in value or "si" in value or "sí" in answer.lower() else None
            requirements = tuple(part.strip() for part in re.split(r",| y ", answer, flags=re.IGNORECASE) if part.strip())
            self.criteria = replace(self.criteria, needs_three_phase=needs, requirements=requirements)
            self.step = WizardStep.LOCATION
            return WizardReply("¿En qué localidad, barrio o zona querés buscar? Podés indicar varias separadas por coma.", self.criteria, self.step)
        if self.step is WizardStep.LOCATION:
            zones = tuple(item.strip() for item in re.split(r",| y ", answer, flags=re.IGNORECASE) if item.strip())
            self.criteria = replace(self.criteria, zones=zones, locality=zones[0] if zones else None)
            self.step = WizardStep.BUDGET
            return WizardReply("¿Cuál es tu rango de precio? Indicá ARS y/o USD, por ejemplo ‘ARS 500000 a 900000; USD 400 a 800’, o ‘sin límite’.", self.criteria, self.step)
        if self.step is WizardStep.BUDGET:
            self.criteria = replace(self.criteria, **self._parse_budget(answer))
            self.step = WizardStep.CONFIRM
            return WizardReply(self.normalized_summary() + "\n\n¿Confirmás esta búsqueda? Respondé sí para continuar o no para corregirla.", self.criteria, self.step)
        if self.step is WizardStep.CONFIRM:
            if value in {"si", "sí", "s", "confirmo", "confirmar", "ok", "dale"}:
                self.step = WizardStep.COMPLETE
                return WizardReply("Búsqueda confirmada. El sistema puede provisionar ahora el job horario, sujeto a la configuración del destino Telegram.", self.criteria, self.step, completed=True)
            self.step = WizardStep.OPERATION
            return self.start()
        return WizardReply("Esta búsqueda ya está completa. Usá /start para comenzar otra.", self.criteria, self.step, completed=True)

    def normalized_summary(self) -> str:
        c = self.criteria
        prices = []
        if c.min_price_ars is not None or c.max_price_ars is not None:
            prices.append(f"ARS {c.min_price_ars or 0}–{c.max_price_ars or 'sin límite'}")
        if c.min_price_usd is not None or c.max_price_usd is not None:
            prices.append(f"USD {c.min_price_usd or 0}–{c.max_price_usd or 'sin límite'}")
        return "Búsqueda normalizada:\n" + "\n".join((
            f"- Operación: {c.operation}", f"- Tipo: {c.property_type}",
            f"- Ambientes: {c.rooms or 'cualquiera'}", f"- Baños: {c.bathrooms or 'cualquiera'}",
            f"- Superficie: {c.min_area_m2 or 0}–{c.max_area_m2 or 'sin límite'} m²",
            f"- Trifásica: {'sí' if c.needs_three_phase else 'no especificado'}",
            f"- Zona/localidad: {', '.join(c.zones) or 'sin especificar'}",
            f"- Precio: {'; '.join(prices) or 'sin especificar'}",
            f"- Requisitos: {', '.join(c.requirements) or 'ninguno'}",
        ))

    @staticmethod
    def _parse_budget(answer: str) -> dict[str, Decimal | None]:
        result: dict[str, Decimal | None] = {"min_price_ars": None, "max_price_ars": None, "min_price_usd": None, "max_price_usd": None}
        for currency, marker in (("ars", "ars"), ("usd", "usd"), ("usd", "u$s"), ("usd", "us$"), ("ars", "$")):
            for match in re.finditer(rf"{re.escape(marker)}\s*([\d.]+(?:,\d+)?)\s*(?:a|-|hasta)\s*([\d.]+(?:,\d+)?)?", _clean(answer)):
                result[f"min_price_{currency}"] = _number(match.group(1))
                result[f"max_price_{currency}"] = _number(match.group(2)) if match.group(2) else None
        return result
