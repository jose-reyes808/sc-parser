from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from src.models import SpotifyTrackMatch


class SpotifyTrackMatcher:
    def match(
        self,
        artist: str,
        song: str,
        candidates: list[dict[str, Any]],
        search_query: str,
    ) -> SpotifyTrackMatch | None:
        best_match: SpotifyTrackMatch | None = None

        for candidate in candidates:
            score = self._score_candidate(artist, song, candidate)
            if best_match is not None and score <= best_match.match_score:
                continue

            candidate_artists = ", ".join(
                artist_item.get("name", "")
                for artist_item in candidate.get("artists", [])
                if artist_item.get("name")
            )

            best_match = SpotifyTrackMatch(
                spotify_track_id=str(candidate.get("id", "")),
                spotify_uri=str(candidate.get("uri", "")),
                matched_artist=candidate_artists,
                matched_song=str(candidate.get("name", "")),
                match_score=round(score, 4),
                search_query=search_query,
                album_name=self._optional_string(candidate.get("album", {}).get("name")),
                external_url=self._optional_string(
                    candidate.get("external_urls", {}).get("spotify")
                ),
            )

        if best_match is None or best_match.match_score < 0.55:
            return None

        return best_match

    def build_search_query(self, artist: str, song: str) -> str:
        artist_query = artist.strip()
        song_query = song.strip()

        if artist_query and song_query:
            return f'track:"{song_query}" artist:"{artist_query}"'

        return f"{artist_query} {song_query}".strip()

    def _score_candidate(
        self,
        source_artist: str,
        source_song: str,
        candidate: dict[str, Any],
    ) -> float:
        candidate_song = self._normalize_text(str(candidate.get("name", "")))
        candidate_artists = self._normalize_text(
            " ".join(
                artist_item.get("name", "")
                for artist_item in candidate.get("artists", [])
                if artist_item.get("name")
            )
        )

        normalized_source_song = self._normalize_text(source_song)
        normalized_source_artist = self._normalize_text(source_artist)

        song_score = SequenceMatcher(
            None,
            normalized_source_song,
            candidate_song,
        ).ratio()
        artist_score = SequenceMatcher(
            None,
            normalized_source_artist,
            candidate_artists,
        ).ratio()

        return (song_score * 0.65) + (artist_score * 0.35)

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized_value = value.lower().strip()
        normalized_value = re.sub(r"[^\w\s]", " ", normalized_value)
        normalized_value = re.sub(r"\s+", " ", normalized_value)
        return normalized_value

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
