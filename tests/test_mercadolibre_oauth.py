import json
from urllib.parse import parse_qs, urlsplit

import pytest

from sauron_recon.adapters.mercadolibre_oauth import (
    MercadoLibreOAuthClient,
    MercadoLibreOAuthConfig,
    MercadoLibreOAuthError,
    OAuthTokenStore,
    OAuthStateStore,
)


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_oauth_requires_https_redirect_and_keeps_secret_out_of_authorization_url():
    with pytest.raises(ValueError):
        MercadoLibreOAuthConfig("app", "secret", "http://localhost/callback")

    client = MercadoLibreOAuthClient(MercadoLibreOAuthConfig("app", "secret", "https://example.org/callback"))
    url, state = client.authorization_url("state-1")
    query = parse_qs(urlsplit(url).query)

    assert query["client_id"] == ["app"]
    assert query["redirect_uri"] == ["https://example.org/callback"]
    assert query["state"] == ["state-1"]
    assert "secret" not in url


def test_oauth_exchange_validates_state_and_returns_token():
    def opener(request, timeout):
        assert request.full_url.endswith("/token")
        body = request.data.decode()
        assert "client_secret=secret" in body
        return Response({"access_token": "access", "refresh_token": "refresh"})

    client = MercadoLibreOAuthClient(
        MercadoLibreOAuthConfig("app", "secret", "https://example.org/callback"),
        opener=opener,
    )
    result = client.exchange_code("code", "state", "state")

    assert result["access_token"] == "access"

    with pytest.raises(MercadoLibreOAuthError):
        client.exchange_code("code", "wrong", "state")


def test_oauth_state_is_single_use():
    store = OAuthStateStore()
    state = store.issue()

    assert store.consume(state) is True
    assert store.consume(state) is False


def test_token_store_writes_local_file_with_restricted_permissions(tmp_path):
    path = tmp_path / "mercadolibre-token.json"

    OAuthTokenStore(path).save({"access_token": "[REDACTED]"})

    assert path.exists()
    assert path.stat().st_mode & 0o077 == 0
