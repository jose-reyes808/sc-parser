from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

from src.models import SpotifyTokens
from src.webapp.spotify_api import SpotifyApiClient


class SpotifyApiClientTests(unittest.TestCase):
    def test_search_tracks_returns_empty_candidates_for_transient_spotify_failure(self) -> None:
        response = requests.Response()
        response.status_code = 502
        response.url = "https://api.spotify.com/v1/search"

        client = SpotifyApiClient(
            tokens=SpotifyTokens(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_at=9999999999,
            ),
            refresh_tokens=lambda refresh_token: self.fail("refresh should not be called"),
            persist_tokens=lambda tokens: self.fail("tokens should not be persisted"),
        )

        with patch("src.webapp.spotify_api.requests.request", return_value=response):
            self.assertEqual(client.search_tracks('track:"Facts"'), [])

    def test_search_tracks_still_raises_non_transient_spotify_errors(self) -> None:
        response = requests.Response()
        response.status_code = 400
        response.url = "https://api.spotify.com/v1/search"

        client = SpotifyApiClient(
            tokens=SpotifyTokens(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_at=9999999999,
            ),
            refresh_tokens=lambda refresh_token: self.fail("refresh should not be called"),
            persist_tokens=lambda tokens: self.fail("tokens should not be persisted"),
        )

        with patch("src.webapp.spotify_api.requests.request", return_value=response):
            with self.assertRaises(requests.exceptions.HTTPError):
                client.search_tracks('track:"Facts"')


if __name__ == "__main__":
    unittest.main()
