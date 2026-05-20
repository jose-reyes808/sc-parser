from __future__ import annotations

import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.models import WebAppConfig
from src.webapp.soundcloud_oauth import SoundCloudOAuthService


class SoundCloudOAuthServiceTests(unittest.TestCase):
    def test_authorize_url_uses_popup_display_mode(self) -> None:
        service = SoundCloudOAuthService(
            WebAppConfig(
                project_root=Path("."),
                database_url="sqlite:///webapp.sqlite3",
                redis_url="redis://localhost:6379/0",
                session_secret="secret",
                soundcloud_client_id="public-client",
                soundcloud_api_client_id="oauth-client",
                soundcloud_client_secret="client-secret",
                soundcloud_redirect_uri="http://127.0.0.1:8000/auth/soundcloud/callback",
                spotify_client_id="spotify-client",
                spotify_client_secret="spotify-secret",
                spotify_redirect_uri="http://127.0.0.1:8000/auth/spotify/callback",
                spotify_scopes=[],
                app_base_url="http://127.0.0.1:8000",
            )
        )

        query = parse_qs(urlparse(service.build_authorize_url("state", "challenge")).query)

        self.assertEqual(query["client_id"], ["oauth-client"])
        self.assertEqual(query["redirect_uri"], ["http://127.0.0.1:8000/auth/soundcloud/callback"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["code_challenge"], ["challenge"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["display"], ["popup"])
        self.assertEqual(query["state"], ["state"])


if __name__ == "__main__":
    unittest.main()
