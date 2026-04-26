from __future__ import annotations

"""Server-side SoundCloud OAuth helpers for playlist creation features."""

import base64
import hashlib
import secrets
import time
from typing import Any
from urllib.parse import quote, urlencode

import requests

from src.models import SoundCloudTokens, WebAppConfig


class SoundCloudOAuthService:
    """Build SoundCloud OAuth URLs and exchange codes for usable user tokens."""

    AUTH_BASE_URL = "https://secure.soundcloud.com/authorize"
    TOKEN_URL = "https://secure.soundcloud.com/oauth/token"
    API_BASE_URL = "https://api.soundcloud.com"

    def __init__(self, config: WebAppConfig) -> None:
        """Store the web app configuration needed for the OAuth flow."""

        self.config = config

    def build_authorize_url(
        self,
        state: str,
        code_challenge: str,
    ) -> str:
        """Build the SoundCloud authorization URL for the current user session."""

        query = urlencode(
            {
                "client_id": self.config.soundcloud_client_id,
                "redirect_uri": self.config.soundcloud_redirect_uri,
                "response_type": "code",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": state,
            },
            quote_via=quote,
        )
        return f"{self.AUTH_BASE_URL}?{query}"

    def exchange_code(self, code: str, code_verifier: str) -> SoundCloudTokens:
        """Exchange a one-time SoundCloud authorization code for user tokens."""

        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": self.config.soundcloud_client_id,
                "client_secret": self.config.soundcloud_client_secret,
                "redirect_uri": self.config.soundcloud_redirect_uri,
                "code_verifier": code_verifier,
                "code": code,
            },
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        return self._build_tokens(response.json())

    def refresh_tokens(self, refresh_token: str) -> SoundCloudTokens:
        """Refresh a SoundCloud token set for a returning user session."""

        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "client_id": self.config.soundcloud_client_id,
                "client_secret": self.config.soundcloud_client_secret,
                "refresh_token": refresh_token,
            },
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if "refresh_token" not in payload:
            payload["refresh_token"] = refresh_token
        return self._build_tokens(payload)

    def get_current_user_profile(self, access_token: str) -> dict[str, Any]:
        """Fetch the authenticated SoundCloud user's profile."""

        response = requests.get(
            f"{self.API_BASE_URL}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        return response.json()

    def generate_state(self) -> str:
        """Generate a random state token to protect the OAuth redirect."""

        return secrets.token_urlsafe(32)

    def generate_code_verifier(self) -> str:
        """Generate a PKCE verifier for SoundCloud's OAuth 2.1 flow."""

        return secrets.token_urlsafe(64)

    @staticmethod
    def build_code_challenge(code_verifier: str) -> str:
        """Convert a PKCE verifier into the S256 challenge SoundCloud expects."""

        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    @staticmethod
    def _build_tokens(payload: dict[str, Any]) -> SoundCloudTokens:
        """Convert SoundCloud token JSON into the app's typed token model."""

        expires_in = int(payload.get("expires_in", 0))
        return SoundCloudTokens(
            access_token=str(payload["access_token"]),
            refresh_token=str(payload["refresh_token"]) if payload.get("refresh_token") else None,
            expires_at=int(time.time()) + expires_in,
        )
