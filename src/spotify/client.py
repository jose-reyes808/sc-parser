from __future__ import annotations

import base64
import json
import time
import webbrowser
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse

import requests

from src.models import SpotifyConfig


class SpotifyClient:
    AUTH_BASE_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, config: SpotifyConfig) -> None:
        self.config = config
        self._token_payload: dict[str, Any] | None = None

    def search_tracks(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/search",
            params={
                "q": query,
                "type": "track",
                "limit": limit,
            },
        )
        return response.json().get("tracks", {}).get("items", [])

    def create_playlist(
        self,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/me/playlists",
            json={
                "name": name,
                "description": description,
                "public": public,
            },
        )
        return response.json()

    def add_items_to_playlist(self, playlist_id: str, uris: list[str]) -> None:
        for start_index in range(0, len(uris), 100):
            chunk = uris[start_index : start_index + 100]
            self._request(
                "POST",
                f"/playlists/{playlist_id}/tracks",
                json={"uris": chunk},
            )

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        token = self._get_access_token()
        response = requests.request(
            method=method,
            url=f"{self.API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            json=json,
            timeout=self.config.request_timeout,
        )

        if response.status_code == 401:
            self._token_payload = None
            token = self._get_access_token(force_refresh=True)
            response = requests.request(
                method=method,
                url=f"{self.API_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=json,
                timeout=self.config.request_timeout,
            )

        response.raise_for_status()
        return response

    def _get_access_token(self, force_refresh: bool = False) -> str:
        token_payload = self._load_token_payload()

        if force_refresh and token_payload and token_payload.get("refresh_token"):
            token_payload = self._refresh_access_token(token_payload["refresh_token"])
        elif token_payload and not self._is_token_expired(token_payload):
            self._token_payload = token_payload
        elif token_payload and token_payload.get("refresh_token"):
            token_payload = self._refresh_access_token(token_payload["refresh_token"])
        else:
            token_payload = self._run_authorization_code_flow()

        return str(token_payload["access_token"])

    def _load_token_payload(self) -> dict[str, Any] | None:
        if self._token_payload is not None:
            return self._token_payload

        if not self.config.token_file.exists():
            return None

        with self.config.token_file.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise ValueError(f"{self.config.token_file.name} must contain a JSON object.")

        self._token_payload = payload
        return payload

    def _run_authorization_code_flow(self) -> dict[str, Any]:
        authorize_url = self._build_authorize_url()
        print("\nOpen this URL and authorize the app with Spotify:")
        print(authorize_url)

        try:
            webbrowser.open(authorize_url)
        except Exception:
            pass

        redirected_url = input(
            "\nPaste the full redirected URL from your browser after approval: "
        ).strip()

        code = parse_qs(urlparse(redirected_url).query).get("code", [None])[0]
        if not code:
            raise ValueError("Authorization code not found in redirected URL.")

        response = requests.post(
            self.TOKEN_URL,
            headers=self._build_token_headers(),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri,
            },
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        payload = self._finalize_token_payload(response.json())
        self._save_token_payload(payload)
        return payload

    def _refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        response = requests.post(
            self.TOKEN_URL,
            headers=self._build_token_headers(),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        refreshed_payload = response.json()
        current_payload = self._load_token_payload() or {}

        if "refresh_token" not in refreshed_payload:
            refreshed_payload["refresh_token"] = refresh_token or current_payload.get("refresh_token")

        payload = self._finalize_token_payload(refreshed_payload)
        self._save_token_payload(payload)
        return payload

    def _save_token_payload(self, payload: dict[str, Any]) -> None:
        with self.config.token_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        self._token_payload = payload

    @staticmethod
    def _is_token_expired(payload: dict[str, Any]) -> bool:
        expires_at = payload.get("expires_at")
        if not isinstance(expires_at, (int, float)):
            return True
        return time.time() >= float(expires_at) - 60

    def _build_authorize_url(self) -> str:
        query = urlencode(
            {
                "client_id": self.config.client_id,
                "response_type": "code",
                "redirect_uri": self.config.redirect_uri,
                "scope": " ".join(self.config.scopes),
                "show_dialog": "false",
            },
            quote_via=quote,
        )
        return f"{self.AUTH_BASE_URL}?{query}"

    def _build_token_headers(self) -> dict[str, str]:
        raw_credentials = f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
        encoded_credentials = base64.b64encode(raw_credentials).decode("utf-8")
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    @staticmethod
    def _finalize_token_payload(payload: dict[str, Any]) -> dict[str, Any]:
        expires_in = int(payload.get("expires_in", 0))
        payload["expires_at"] = int(time.time()) + expires_in
        return payload
