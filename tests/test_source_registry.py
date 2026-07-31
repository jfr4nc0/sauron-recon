from sauron_recon.application.source_registry import SourceCapabilityRegistry, SourceMode, SourceStatus


def test_source_registry_separates_enabled_candidates_and_blocked_sources():
    enabled = {item.name for item in SourceCapabilityRegistry.enabled()}
    candidates = {item.name for item in SourceCapabilityRegistry.selectable()}
    blocked = SourceCapabilityRegistry.get("facebook-marketplace")

    assert enabled == {"zonaprop"}
    assert "inmuebles-clarin" in candidates
    assert blocked is not None
    assert blocked.status is SourceStatus.BLOCKED
    assert blocked.modes == (SourceMode.DISABLED,)


def test_source_registry_normalizes_lookup_and_keeps_capabilities_without_secrets():
    item = SourceCapabilityRegistry.get("inmuebles_clarin")

    assert item is not None
    assert SourceMode.PUBLIC_FIRECRAWL in item.modes
    assert "token" not in item.reason.lower()
    assert "secret" not in item.reason.lower()
