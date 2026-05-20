from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from src.models import SoundCloudTokens
from src.webapp.soundcloud_api import SoundCloudApiClient


class SoundCloudApiClientTests(unittest.TestCase):
    def test_create_playlist_best_effort_skips_single_rejected_track(self) -> None:
        client = SoundCloudApiClient(
            tokens=SoundCloudTokens(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_at=9999999999,
            ),
            refresh_tokens=lambda refresh_token: self.fail("refresh should not be called"),
            persist_tokens=lambda tokens: self.fail("tokens should not be persisted"),
        )

        def set_playlist_tracks(_playlist_id: str, track_ids: list[str]) -> dict[str, object]:
            if "bad" in track_ids:
                response = requests.Response()
                response.status_code = 422
                response._content = b'{"message":"Could not parse JSON request body."}'
                raise requests.exceptions.HTTPError(response=response)
            return {"id": 123}

        with (
            patch.object(client, "create_playlist", return_value={"id": 123}),
            patch.object(client, "set_playlist_tracks", side_effect=set_playlist_tracks),
            patch.object(client, "get_playlist", return_value={"id": 123, "permalink_url": "url"}),
        ):
            with self.assertLogs("src.webapp.soundcloud_api", level="WARNING") as logs:
                playlist, accepted_ids, skipped_ids = client.create_playlist_best_effort(
                    title="Livesets",
                    track_ids=["1", "2", "bad"],
                )

        self.assertEqual(playlist, {"id": 123, "permalink_url": "url"})
        self.assertEqual(accepted_ids, ["1", "2"])
        self.assertEqual(skipped_ids, ["bad"])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("Skipping SoundCloud track bad", logs.output[0])


if __name__ == "__main__":
    unittest.main()
