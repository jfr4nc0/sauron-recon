from sauron_recon.application.connectors import ConnectorProvider, ConnectorRegistry, ConnectorSetupWizard


def test_registry_exposes_self_hosted_and_external_options_without_secrets():
    options = ConnectorRegistry.options()

    assert {option.provider for option in options} == {
        ConnectorProvider.LOCAL,
        ConnectorProvider.NGROK,
        ConnectorProvider.CLOUDFLARE,
        ConnectorProvider.CUSTOM_DOMAIN,
        ConnectorProvider.MANUAL,
    }
    assert all("token" not in option.description.lower() for option in options)


def test_setup_selects_ngrok_without_collecting_credentials():
    wizard = ConnectorSetupWizard()
    prompt = wizard.start()
    assert "ngrok local" in prompt

    message, completed, payload = wizard.receive("2")

    assert completed is True
    assert "OAuth" in message
    assert payload == {
        "target": "mercadolibre",
        "provider": "ngrok",
        "self_hosted": "false",
        "external_service": "true",
        "status": "selected",
    }


def test_setup_rejects_unknown_provider():
    wizard = ConnectorSetupWizard()
    wizard.start()

    message, completed, payload = wizard.receive("secret-token")

    assert completed is False
    assert payload is None
    assert "No reconocí" in message
