from decimal import Decimal

from sauron_recon.application.wizard import RequirementsWizard, WizardStep


def test_wizard_normalizes_full_property_requirements():
    wizard = RequirementsWizard()
    wizard.start()
    answers = [
        "comprar o alquilar",
        "departamento",
        "3 ambientes",
        "2 baños",
        "80 a 150 m2",
        "sí, trifásica",
        "Palermo, Villa Crespo, CABA",
        "ARS 500000 a 900000; USD 400 a 800",
    ]
    reply = None
    for answer in answers:
        reply = wizard.receive(answer)
    assert reply is not None
    assert reply.step is WizardStep.CONFIRM
    assert reply.criteria.operation == "rent_or_sale"
    assert reply.criteria.property_type == "departamento"
    assert reply.criteria.rooms == 3
    assert reply.criteria.bathrooms == 2
    assert reply.criteria.min_area_m2 == Decimal("80")
    assert reply.criteria.max_area_m2 == Decimal("150")
    assert reply.criteria.needs_three_phase is True
    assert reply.criteria.zones == ("Palermo", "Villa Crespo", "CABA")
    assert reply.criteria.min_price_ars == Decimal("500000")
    assert reply.criteria.max_price_ars == Decimal("900000")
    assert reply.criteria.min_price_usd == Decimal("400")
    assert reply.criteria.max_price_usd == Decimal("800")
    assert "Búsqueda normalizada" in reply.text

    confirmed = wizard.receive("sí")
    assert confirmed.completed is True
    assert confirmed.step is WizardStep.COMPLETE
