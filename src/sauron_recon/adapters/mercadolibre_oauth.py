from __future__ import annotations

import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class MercadoLibreOAuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class MercadoLibreOAuthConfig:
    app_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str = "https://auth.mercadolibre.com.ar/authorization"
    token_url: str = "https://api.mercadolibre.com/oauth/token"

    def __post_init__(self) -> None:
        if not self.app_id or not self.client_secret:
            raise ValueError("MercadoLibre app_id and client_secret are required")
        if not self.redirect_uri.startswith("https://"):
            raise ValueError("MercadoLibre redirect_uri must use HTTPS")


class MercadoLibreOAuthClient:
    """Official MercadoLibre OAuth code exchange; credentials never enter URLs."""

    def __init__(self, config: MercadoLibreOAuthConfig, opener=urlopen) -> None:
        self.config = config
        self.opener = opener

    def authorization_url(self, state: str | None = None) -> tuple[str, str]:
        state = state or secrets.token_urlsafe(32)
        query = urlencode({
            "response_type": "code",
            "client_id": self.config.app_id,
            "redirect_uri": self.config.redirect_uri,
            "state": state,
        })
        return f"{self.config.authorization_url}?{query}", state

    def exchange_code(self, code: str, state: str, expected_state: str) -> dict:
        if not code or not secrets.compare_digest(state, expected_state):
            raise MercadoLibreOAuthError("invalid OAuth state or code")
        return self._token_request({
            "grant_type": "authorization_code",
            "client_id": self.config.app_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        })

    def refresh_token(self, refresh_token: str) -> dict:
        if not refresh_token:
            raise MercadoLibreOAuthError("refresh_token is required")
        return self._token_request({
            "grant_type": "refresh_token",
            "client_id": self.config.app_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        })

    def _token_request(self, payload: dict[str, str]) -> dict:
        request = Request(
            self.config.token_url,
            data=urlencode(payload).encode(),
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with self.opener(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MercadoLibreOAuthError(f"MercadoLibre OAuth request failed: {type(exc).__name__}") from exc
        if not isinstance(result, dict) or "access_token" not in result:
            raise MercadoLibreOAuthError("MercadoLibre OAuth response did not contain access_token")
        return result


class OAuthStateStore:
    """In-memory state store suitable for one local setup flow; stores no tokens."""

    def __init__(self) -> None:
        self._states: set[str] = set()

    def issue(self) -> str:
        state = secrets.token_urlsafe(32)
        self._states.add(state)
        return state

    def consume(self, state: str) -> bool:
        if state not in self._states:
            return False
        self._states.remove(state)
        return True


@dataclass
class OAuthTokenStore:
    path: str | Path

    def save(self, token_payload: dict) -> None:
        path = Path(self.path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(token_payload, ensure_ascii=False), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(path)
        path.chmod(0o600)


class LocalOAuthCallbackServer:
    """One-shot loopback callback; a tunnel may forward its public HTTPS URI here."""

    def __init__(self, client: MercadoLibreOAuthClient, expected_state: str, token_store: OAuthTokenStore, callback_path: str):
        self.client = client
        self.expected_state = expected_state
        self.token_store = token_store
        self.callback_path = callback_path if callback_path.startswith("/") else f"/{callback_path}"

    def serve_once(self, host: str = "127.0.0.1", port: int = 8787, timeout: int = 600) -> dict:
        result: dict = {}
        callback = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                parsed = urlsplit(self.path)
                if parsed.path != callback.callback_path:
                    self.send_error(404)
                    return
                params = parse_qs(parsed.query)
                try:
                    if params.get("error"):
                        raise MercadoLibreOAuthError("MercadoLibre authorization returned an error")
                    code = params.get("code", [""])[0]
                    state = params.get("state", [""])[0]
                    result.update(callback.client.exchange_code(code, state, callback.expected_state))
                    callback.token_store.save(result)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"<h1>Autorizacion completada</h1><p>Podes cerrar esta ventana.</p>")
                except MercadoLibreOAuthError:
                    self.send_error(400, "OAuth authorization failed")

            def log_message(self, format: str, *args) -> None:
                return

        server = HTTPServer((host, port), Handler)
        server.timeout = timeout
        try:
            server.handle_request()
        finally:
            server.server_close()
        if not result:
            raise MercadoLibreOAuthError("OAuth callback timed out or was invalid")
        return result
