from __future__ import annotations

"""Heuristics for selecting the most likely Spotify track match."""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from src.models import SpotifyTrackMatch

# The matcher is intentionally decoupled from API access. Search quality tends
# to evolve independently of transport concerns, and this keeps that iteration
# loop local to one place.
class SpotifyTrackMatcher:
    """Score Spotify search results against a parsed artist and song pair."""

    MINIMUM_MATCH_SCORE = 0.55
    SWAPPED_ORIENTATION_MINIMUM_MATCH_SCORE = 0.75
    VERSION_BASE_TITLE_OVERLAP_THRESHOLD = 0.65
    SHORT_TITLE_COMMON_TOKENS = {
        "a",
        "an",
        "and",
        "for",
        "i",
        "in",
        "me",
        "my",
        "of",
        "on",
        "or",
        "the",
        "to",
        "u",
        "we",
        "you",
    }

    FEATURE_PATTERN = re.compile(r"\b(?:feat|ft|featuring)\.?\b", re.IGNORECASE)
    FEATURE_BLOCK_PATTERN = re.compile(
        r"[\(\[]\s*(?:feat|ft|featuring)\.?\s+[^\)\]]+[\)\]]",
        re.IGNORECASE,
    )
    COLLABORATOR_BLOCK_PATTERN = re.compile(
        r"[\(\[]\s*(?:with|w/)\s+[^\)\]]+[\)\]]",
        re.IGNORECASE,
    )
    INLINE_FEATURE_PATTERN = re.compile(
        r"\s+\b(?:feat|ft|featuring)\.?\s+.+$",
        re.IGNORECASE,
    )
    TRAILING_COLLABORATOR_TITLE_PATTERN = re.compile(
        r"\s+\b(?:with|w/)\b\s+.+$",
        re.IGNORECASE,
    )
    LIVESET_TITLE_PATTERN = re.compile(
        r"\b(?:live\s+(?:at|set)|full set|festival set|mixtape|diplo\s+(?:&|and)\s+friends)\b",
        re.IGNORECASE,
    )
    TITLE_DECORATION_PATTERN = re.compile(
        r"\b(?:teaser|preview|forthcoming|official|out soon|out now|album version|original mix|full mix|radio edit|radio mix|explicit edit|explicit|clean|freestyle|hd)\b",
        re.IGNORECASE,
    )
    PRODUCTION_CREDIT_PATTERN = re.compile(
        r"\b(?:prod\.?|prod\s+by|produced\s+by)\b.*$",
        re.IGNORECASE,
    )
    PART_MARKER_PATTERN = re.compile(
        r"\b(?:pt|part)\.?\s*(\d+|[ivx]+)\b",
        re.IGNORECASE,
    )
    TITLE_FORM_MARKER_PATTERN = re.compile(
        r"\b(?:commentary|intro|outro)\b",
        re.IGNORECASE,
    )
    TITLE_SUFFIX_SEPARATOR_PATTERN = re.compile(r"\s+-\s+")
    MIX_DESCRIPTOR_PATTERN = re.compile(
        r"[\(\[]\s*([^\)\]]*\b(?:original mix|extended mix|club mix|mix|edit|remix|re[\s-]*remix|flip|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|re[\s-]*work|re[\s-]*crank|club|version)\b[^\)\]]*)\s*[\)\]]",
        re.IGNORECASE,
    )
    VERSION_SUFFIX_PATTERN = re.compile(
        r"\s+-\s+(.*\b(?:mix|edit|remix|re[\s-]*remix|flip|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|re[\s-]*work|re[\s-]*crank)\b.*)$",
        re.IGNORECASE,
    )
    DUPLICATED_VERSION_TITLE_PATTERN = re.compile(
        r"^\s*(?P<version>.+\b(?:mix|edit|remix|re[\s-]*remix|flip|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|re[\s-]*work|re[\s-]*crank)\b.*)\s+-\s+(?P=version)\s*$",
        re.IGNORECASE,
    )
    TRAILING_GENERIC_VERSION_PATTERN = re.compile(
        r"\s+\b(?:original radio mix|original mix|extended mix|club mix|full mix|radio edit|radio mix|explicit edit|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|re[\s-]*remix|re[\s-]*work|re[\s-]*crank)\b$",
        re.IGNORECASE,
    )
    VERSION_MARKER_PATTERN = re.compile(
        r"\b(?:original radio mix|original mix|extended mix|club mix|full mix|radio edit|radio mix|explicit edit|mix|edit|remix|re[\s-]*remix|flip|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|clean|re[\s-]*work|re[\s-]*crank|club|version)\b",
        re.IGNORECASE,
    )
    STRICT_VERSION_MARKER_PATTERN = re.compile(
        r"\b(?:club mix|remix|re[\s-]*remix|flip|vip|bootleg|rebirth|unreleased(?:\s+verses?)?|re[\s-]*work|re[\s-]*crank|club)\b",
        re.IGNORECASE,
    )
    GENERIC_VERSION_WORDS = {
        "bootleg",
        "club",
        "clean",
        "edit",
        "extended",
        "festival",
        "explicit",
        "full",
        "flip",
        "mix",
        "original",
        "radio",
        "remix",
        "rework",
        "version",
        "vip",
    }
    LABEL_DESCRIPTOR_WORDS = {
        "label",
        "record",
        "recording",
        "recordings",
        "records",
    }
    ARTIST_DECORATION_SUFFIX_PATTERN = re.compile(
        r"\b(?:official)\b$",
        re.IGNORECASE,
    )
    ARTIST_CATALOG_PREFIX_PATTERN = re.compile(
        r"^\s*[a-z]{2,}\d+\s*:\s*",
        re.IGNORECASE,
    )
    ARTIST_VS_SEPARATOR_PATTERN = re.compile(
        r"(?:\b(?:vs|versus|x)\b|[×✕✖]|\s+\?\s+)",
        re.IGNORECASE,
    )
    ARTIST_SPLIT_PATTERN = re.compile(
        r"\s*(?:,|&|[×✕✖]|\s+\?\s+|\band\b|\bvs\b|\bversus\b|/|;|\bwith\b|\bx\b|\baka\b|\bfeat\b\.?|\bft\b\.?|\bfeaturing\b)\s*",
        re.IGNORECASE,
    )
    ARTIST_ALIASES = {
        "deorro": {"ton c"},
        "deadmau5": {"fuckmylife"},
        "dj mercer": {"mercer"},
        "dillon francis": {"dillonfrancis"},
        "dillonfrancis": {"dillon francis"},
        "diskord": {"diskorduk gmail com"},
        "diskorduk gmail com": {"diskord"},
        "fetty wap": {"fettywap1738"},
        "fettywap1738": {"fetty wap"},
        "funtcase": {"funtcaseuk"},
        "funtcaseuk": {"funtcase"},
        "carnage": {"gordo"},
        "clammyclams": {"clams casino"},
        "clams casino": {"clammyclams"},
        "cookie monsta": {"cookiemonstatc"},
        "cookiemonstatc": {"cookie monsta"},
        "fuckmylife": {"deadmau5"},
        "good times ahead": {"gta"},
        "gordo": {"carnage"},
        "gta": {"good times ahead"},
        "j boog": {"jboogmusic"},
        "jboogmusic": {"j boog"},
        "justin blau": {"3lau"},
        "mercer": {"dj mercer"},
        "mgmt": {"whoismgmt"},
        "rich brian": {"rich chigga"},
        "rich chigga": {"rich brian"},
        "spag": {"spag heddy"},
        "spag heddy": {"spag"},
        "totally enormous extinct dinosaurs": {"teed"},
        "ton c": {"deorro"},
        "3lau": {"justin blau"},
        "teed": {"totally enormous extinct dinosaurs"},
        "whoismgmt": {"mgmt"},
    }
    BLOCKED_SPOTIFY_TRACK_IDS: set[str] = set()
    BLOCKED_MATCHES = (
        {
            "source_artists": {"fuckmylife", "deadmau5"},
            "source_title": "beneath with me",
            "candidate_title": "beneath with me",
            "candidate_artists": {"kaskade", "deadmau5", "skylar grey"},
        },
    )

    # The system is biased toward false negatives over false positives here.
    # It is better to leave a track unmatched than to quietly add the wrong song
    # to a user's playlist and erode trust in the import.
    def match(
        self,
        artist: str,
        song: str,
        candidates: list[dict[str, Any]],
        search_query: str,
        *,
        artist_source: str = "",
        original_title: str = "",
    ) -> SpotifyTrackMatch | None:
        """Return the strongest candidate above the minimum confidence threshold."""

        best_match = self.find_best_candidate(
            artist,
            song,
            candidates,
            search_query,
            artist_source=artist_source,
            original_title=original_title,
        )
        if best_match is None or best_match.match_score < self.MINIMUM_MATCH_SCORE:
            return None
        return best_match

    def find_best_candidate(
        self,
        artist: str,
        song: str,
        candidates: list[dict[str, Any]],
        search_query: str,
        *,
        artist_source: str = "",
        original_title: str = "",
    ) -> SpotifyTrackMatch | None:
        """Return the strongest Spotify candidate even if it is below threshold.

        Review tooling benefits from seeing the best near-miss for unmatched
        rows. The acceptance threshold remains a separate policy decision so we
        can expose debugging data without silently broadening what gets added to
        playlists.
        """

        best_match: SpotifyTrackMatch | None = None

        for candidate in candidates:
            score = self._score_candidate(
                artist,
                song,
                candidate,
                artist_source=artist_source,
                original_title=original_title,
            )
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

        return best_match

    # When both artist and song are available, we spend that structure in the
    # query itself. It narrows candidate quality before heuristic scoring begins.
    def build_search_query(self, artist: str, song: str) -> str:
        """Build a focused Spotify search query from the parsed row values."""

        artist_query = artist.strip()
        song_query = song.strip()

        if artist_query and song_query:
            return f'track:"{song_query}" artist:"{artist_query}"'

        return f"{artist_query} {song_query}".strip()

    def build_search_queries(
        self,
        artist: str,
        song: str,
        *,
        original_title: str = "",
        artist_source: str = "",
    ) -> list[str]:
        """Build a small set of progressively looser Spotify search queries.

        The first query stays strict. Additional queries are reserved for
        uploader-fallback rows, where the parsed artist is known to be weaker
        and we can justify spending a couple of targeted recovery attempts.
        """

        queries: list[str] = [self.build_search_query(artist, song)]

        canonical_song = self._canonicalize_song_title(song)
        if canonical_song and canonical_song != self._normalize_text(song):
            queries.append(f'track:"{canonical_song}" artist:"{artist.strip()}"')

        indexed_canonical_song = self._strip_leading_title_index_marker(canonical_song, song)
        if indexed_canonical_song and indexed_canonical_song != canonical_song:
            queries.append(f'track:"{indexed_canonical_song}" artist:"{artist.strip()}"')

        compact_title_query = self._compact_short_token_title(canonical_song)
        if compact_title_query:
            queries.append(f'track:"{compact_title_query}" artist:"{artist.strip()}"')

        compact_initialism_artist = self._compact_stylized_initialism_artist(artist)
        if canonical_song and compact_initialism_artist:
            queries.append(f'track:"{canonical_song}" artist:"{compact_initialism_artist}"')

        contributor_names = list(self._extract_contributors(artist, song))
        if canonical_song and contributor_names:
            primary_contributor = max(contributor_names, key=len)
            queries.append(f'track:"{canonical_song}" artist:"{primary_contributor}"')

        if canonical_song:
            queries.append(f'track:"{canonical_song}"')
        if indexed_canonical_song and indexed_canonical_song != canonical_song:
            queries.append(f'track:"{indexed_canonical_song}"')
        queries.append(song.strip())

        if artist_source != "Uploader Fallback":
            return self._dedupe_queries(queries)

        inferred_artist, inferred_song = self._infer_artist_from_trailing_mix_title(original_title)
        if inferred_artist and inferred_song:
            queries.append(self.build_search_query(inferred_artist, inferred_song))

        if canonical_song:
            queries.append(f'track:"{canonical_song}"')

        return self._dedupe_queries(queries)

    def build_swapped_orientation_search_queries(self, artist: str, song: str) -> list[str]:
        """Build fallback searches for rows that may be parsed title-first."""

        return self.build_search_queries(song, artist)

    def match_swapped_orientation(
        self,
        artist: str,
        song: str,
        candidates: list[dict[str, Any]],
        search_query: str,
        *,
        original_title: str = "",
    ) -> SpotifyTrackMatch | None:
        """Try matching with parsed artist and song reversed.

        This is intentionally stricter than normal matching because it is a
        recovery path for unusual SoundCloud titles like `Freaks - Timmy
        Trumpet`, where the upload appears to be `title - artist`.
        """

        best_match = self.find_best_candidate(
            song,
            artist,
            candidates,
            search_query,
            original_title=original_title,
        )
        if (
            best_match is None
            or best_match.match_score < self.SWAPPED_ORIENTATION_MINIMUM_MATCH_SCORE
        ):
            return None
        return best_match

    # Song title gets more weight than artist because SoundCloud artist metadata
    # is often inferred or uploader-driven, while the title usually carries the
    # strongest identity signal.
    WEAK_ARTIST_EVIDENCE_CAP = 0.49
    MINIMUM_ARTIST_EVIDENCE = 0.5

    def _score_candidate(
        self,
        source_artist: str,
        source_song: str,
        candidate: dict[str, Any],
        *,
        artist_source: str = "",
        original_title: str = "",
    ) -> float:
        """Combine artist and title similarity into a single match score."""

        if self._looks_like_liveset_title(source_artist, source_song):
            return 0.0
        if self._has_clean_marker(str(candidate.get("name", ""))):
            return 0.0

        candidate_song = self._normalize_text(str(candidate.get("name", "")))
        candidate_artist_names = self._candidate_artist_names(candidate)
        candidate_artists = self._normalize_artist_text(
            " ".join(candidate_artist_names)
        )

        if self._is_blocked_match(source_artist, source_song, candidate, candidate_artist_names):
            return 0.0

        normalized_source_artist = self._normalize_artist_text(source_artist)
        source_artist_names = list(self._split_artist_names(source_artist))
        source_context_artist_names = source_artist_names + candidate_artist_names
        source_title_prefix_contributors = self._extract_leading_artist_title_segment_contributors(
            source_song,
            source_context_artist_names,
        )
        source_song_for_matching = self._strip_leading_artist_title_segment(
            source_song,
            source_context_artist_names,
        )
        source_title_prefix_contributors.update(
            self._extract_leading_artist_title_prefix_contributors(
                source_song_for_matching,
                source_context_artist_names,
            )
        )
        source_song_for_matching = self._strip_leading_artist_title_prefix(
            source_song_for_matching,
            source_context_artist_names,
        )
        source_title_prefix_contributors.update(
            self._extract_trailing_artist_title_segment_contributors(
                source_song_for_matching,
                source_context_artist_names,
            )
        )
        source_song_for_matching = self._strip_trailing_artist_title_segment(
            source_song_for_matching,
            source_context_artist_names,
        )
        normalized_source_song = self._normalize_text(source_song_for_matching)
        canonical_source_song = self._canonicalize_song_title(source_song_for_matching)
        canonical_candidate_song = self._canonicalize_song_title(str(candidate.get("name", "")))
        source_version_base_title = self._canonicalize_version_base_title(
            source_song_for_matching,
            source_context_artist_names,
        )
        candidate_version_base_title = self._canonicalize_version_base_title(
            str(candidate.get("name", "")),
            candidate_artist_names,
        )
        source_version_tokens = self._extract_version_identity_tokens(source_song_for_matching)
        source_version_token_groups = self._extract_version_identity_token_groups(source_song_for_matching)
        if not source_version_tokens:
            source_version_tokens = self._extract_original_title_version_tokens(
                original_title,
                canonical_source_song,
            )
            if source_version_tokens:
                source_version_token_groups = [source_version_tokens]
        candidate_version_tokens = self._extract_version_identity_tokens(
            str(candidate.get("name", "")),
            candidate_artist_names,
        )
        source_has_version_marker = self._has_version_marker(source_song_for_matching) or bool(
            source_version_tokens
        )
        candidate_has_version_marker = self._has_version_marker(str(candidate.get("name", "")))
        source_artist_has_version_marker = bool(self._extract_version_identity_tokens(source_artist))
        source_contributors = self._extract_contributors(source_artist, source_song_for_matching)
        if artist_source == "Uploader Fallback" and source_title_prefix_contributors:
            source_contributors = set(source_title_prefix_contributors)
        else:
            source_contributors.update(source_title_prefix_contributors)
        source_artist_contributors = self._extract_contributors(source_artist, "")
        candidate_contributors = self._extract_contributors(
            ", ".join(candidate_artist_names),
            str(candidate.get("name", "")),
        )
        source_named_version_matches_plain_candidate = (
            self._named_source_version_matches_plain_candidate(
                source_version_base_title,
                candidate_version_base_title,
                source_version_token_groups,
                candidate_contributors,
            )
        )

        if source_artist_has_version_marker and self._has_feature_marker(source_song_for_matching):
            title_side_score = self._score_title_side_version_candidate(
                source_artist,
                source_song_for_matching,
                str(candidate.get("name", "")),
                candidate_version_tokens,
                candidate_artist_names,
            )
            if title_side_score is not None:
                return title_side_score

        direct_song_score = SequenceMatcher(None, normalized_source_song, candidate_song).ratio()
        canonical_song_score = SequenceMatcher(
            None,
            canonical_source_song,
            canonical_candidate_song,
        ).ratio()
        title_token_overlap_score = self._score_title_token_overlap(
            canonical_source_song,
            canonical_candidate_song,
        )
        original_title_expanded_match = self._original_title_expanded_title_matches(
            original_title,
            canonical_source_song,
            canonical_candidate_song,
        )
        original_title_candidate_expansion_match = (
            original_title_expanded_match
            and canonical_source_song
            and canonical_candidate_song
            and not self._titles_equivalent(canonical_source_song, canonical_candidate_song)
        )
        song_score = max(direct_song_score, canonical_song_score, title_token_overlap_score)

        direct_artist_score = SequenceMatcher(
            None,
            normalized_source_artist,
            candidate_artists,
        ).ratio()
        contributor_overlap_score = self._score_contributor_overlap(
            source_contributors,
            candidate_contributors,
        )
        individual_artist_score = self._score_individual_artist_similarity(
            source_contributors,
            candidate_artist_names,
        )
        artist_score = max(direct_artist_score, contributor_overlap_score, individual_artist_score)

        if canonical_source_song and canonical_source_song == canonical_candidate_song:
            song_score = max(song_score, 0.98)
        if original_title_expanded_match:
            song_score = max(song_score, 1.0)
        if source_named_version_matches_plain_candidate:
            song_score = max(song_score, 1.0)
        if (
            candidate_has_version_marker
            and self._titles_equivalent(canonical_source_song, candidate_version_base_title)
            and self._has_required_version_overlap(source_contributors, candidate_version_tokens)
        ):
            song_score = max(song_score, 1.0)
        if source_contributors and source_contributors.issubset(candidate_contributors):
            artist_score = max(artist_score, 0.98)

        duplicate_version_score = self._score_duplicate_version_title_candidate(
            source_version_tokens,
            candidate_version_tokens,
            source_contributors,
            candidate_contributors,
            str(candidate.get("name", "")),
        )
        if duplicate_version_score is not None:
            return duplicate_version_score

        version_only_title_score = self._score_version_only_title_candidate(
            source_version_tokens,
            candidate_version_tokens,
            source_contributors,
            candidate_contributors,
            str(candidate.get("name", "")),
            candidate_artist_names,
        )
        if version_only_title_score is not None:
            return version_only_title_score

        # Search broadening is useful for recall, but we still need a guardrail
        # against "same vibe, wrong record" matches. If the title is only
        # loosely similar and the artist evidence is weak, this candidate should
        # not survive on title fuzziness alone.
        if artist_score < 0.5 and contributor_overlap_score == 0.0:
            if canonical_source_song != canonical_candidate_song and title_token_overlap_score < 1.0:
                return 0.0

        score = (song_score * 0.65) + (artist_score * 0.35)

        production_credit_score = self._score_production_credit_candidate(
            source_song_for_matching,
            original_title,
            canonical_source_song,
            canonical_candidate_song,
            str(candidate.get("name", "")),
            candidate_artist_names,
        )
        if production_credit_score is not None:
            return max(score, production_credit_score)

        source_part_markers = self._extract_part_markers(source_song_for_matching)
        candidate_part_markers = self._extract_part_markers(str(candidate.get("name", "")))
        original_title_part_markers = self._extract_part_markers(original_title)
        if (
            source_part_markers != candidate_part_markers
            and not (
                original_title_expanded_match
                and original_title_part_markers == candidate_part_markers
                and original_title_candidate_expansion_match
            )
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if self._extract_title_form_markers(source_song_for_matching) != self._extract_title_form_markers(
            str(candidate.get("name", ""))
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            not source_has_version_marker
            and self._has_strict_version_marker(str(candidate.get("name", "")))
            and not self._has_required_version_overlap(source_artist_contributors, candidate_version_tokens)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            self._has_strict_version_marker(source_song_for_matching)
            and not candidate_has_version_marker
            and not (
                self._titles_equivalent(canonical_source_song, canonical_candidate_song)
                and not self._extract_version_descriptors(
                    source_song_for_matching,
                    source_context_artist_names,
                )
            )
            and not source_named_version_matches_plain_candidate
            and not self._generic_unnamed_remix_source_matches_plain_candidate(
                source_song_for_matching,
                str(candidate.get("name", "")),
                source_contributors,
                candidate_contributors,
                source_context_artist_names,
                candidate_artist_names,
            )
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if self._is_short_title_expansion_mismatch(
            canonical_source_song,
            canonical_candidate_song,
            source_contributors,
            candidate_contributors,
        ) and not original_title_expanded_match and not (
            candidate_has_version_marker
            and self._titles_equivalent(canonical_source_song, candidate_version_base_title)
            and self._has_required_version_overlap(source_contributors, candidate_version_tokens)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            normalized_source_artist
            and source_contributors
            and canonical_source_song != canonical_candidate_song
            and not self._titles_equivalent(canonical_source_song, canonical_candidate_song)
            and title_token_overlap_score == 0.0
            and not original_title_expanded_match
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            normalized_source_artist
            and source_contributors
            and canonical_source_song != canonical_candidate_song
            and title_token_overlap_score < self.VERSION_BASE_TITLE_OVERLAP_THRESHOLD
            and contributor_overlap_score == 0.0
            and individual_artist_score == 0.0
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            normalized_source_artist
            and source_contributors
            and canonical_source_song == canonical_candidate_song
            and contributor_overlap_score == 0.0
            and individual_artist_score == 0.0
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        # An exact title match is common across unrelated catalogs. When the
        # parsed SoundCloud artist does not resemble the Spotify artist at all,
        # cap the score below the acceptance threshold instead of letting title
        # similarity alone create a confident false positive.
        if (
            normalized_source_artist
            and artist_score < self.MINIMUM_ARTIST_EVIDENCE
            and contributor_overlap_score == 0.0
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            source_has_version_marker
            and source_version_base_title
            and candidate_version_base_title
            and not self._titles_equivalent(source_version_base_title, candidate_version_base_title)
            and not original_title_candidate_expansion_match
            and self._score_title_token_overlap(
                source_version_base_title,
                candidate_version_base_title,
            )
            < self.VERSION_BASE_TITLE_OVERLAP_THRESHOLD
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            source_has_version_marker
            and candidate_has_version_marker
            and source_version_tokens
            and candidate_version_tokens
            and not self._has_required_version_overlap(source_version_tokens, candidate_version_tokens)
            and not original_title_candidate_expansion_match
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            source_version_tokens
            and not self._has_required_version_overlap(
                source_version_tokens,
                candidate_version_tokens,
            )
            and not original_title_candidate_expansion_match
            and not source_named_version_matches_plain_candidate
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            source_version_token_groups
            and not self._has_required_version_group_overlap(
                source_version_token_groups,
                candidate_version_tokens,
            )
            and not original_title_candidate_expansion_match
            and not source_named_version_matches_plain_candidate
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            source_has_version_marker
            and not source_version_tokens
            and candidate_version_tokens
            and not self._has_required_version_overlap(source_contributors, candidate_version_tokens)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            not source_has_version_marker
            and candidate_version_tokens
            and not self._has_required_version_overlap(source_contributors, candidate_version_tokens)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            self._has_vs_artist_separator(source_artist)
            and source_contributors
            and not source_contributors.issubset(candidate_contributors)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        if (
            artist_source == "Uploader Fallback"
            and self._has_feature_marker(source_song)
            and not source_has_version_marker
            and source_artist_contributors
            and not source_artist_contributors.issubset(candidate_contributors)
        ):
            return min(score, self.WEAK_ARTIST_EVIDENCE_CAP)

        return score

    @classmethod
    def _score_title_side_version_candidate(
        cls,
        source_title_with_version: str,
        source_performer_text: str,
        candidate_song: str,
        candidate_version_tokens: set[str],
        candidate_artist_names: list[str],
    ) -> float | None:
        """Handle rows parsed as title/version on the artist side and artist text on the song side."""

        source_base_title = cls._canonicalize_version_base_title(source_title_with_version)
        candidate_base_title = cls._canonicalize_version_base_title(candidate_song)
        title_overlap_score = cls._score_title_token_overlap(source_base_title, candidate_base_title)
        if source_base_title != candidate_base_title and title_overlap_score < 1.0:
            return 0.0

        source_version_tokens = cls._extract_version_identity_tokens(source_title_with_version)
        if source_version_tokens and not cls._has_required_version_overlap(
            source_version_tokens,
            candidate_version_tokens,
        ):
            return cls.WEAK_ARTIST_EVIDENCE_CAP

        source_performers = cls._extract_performers_from_title_side_song(source_performer_text)
        performer_score = cls._score_individual_artist_similarity(
            source_performers,
            candidate_artist_names,
        )
        return (0.65 * 1.0) + (0.35 * performer_score)

    @classmethod
    def _canonicalize_song_title(cls, value: str) -> str:
        """Reduce a song title to its identity-bearing core for comparison.

        SoundCloud titles often omit metadata that Spotify adds for catalog
        hygiene, such as featured artists or "Radio Edit" suffixes. Matching
        should reward shared song identity, not penalize the richer storefront
        representation.
        """

        normalized_value = value.strip()
        normalized_value = cls.FEATURE_BLOCK_PATTERN.sub("", normalized_value)
        normalized_value = cls.COLLABORATOR_BLOCK_PATTERN.sub("", normalized_value)
        normalized_value = cls.INLINE_FEATURE_PATTERN.sub("", normalized_value)
        normalized_value = cls.TRAILING_COLLABORATOR_TITLE_PATTERN.sub("", normalized_value)
        normalized_value = cls.PRODUCTION_CREDIT_PATTERN.sub("", normalized_value)
        normalized_value = cls.TITLE_DECORATION_PATTERN.sub("", normalized_value)

        segments = cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(normalized_value)
        if len(segments) > 1:
            kept_segments = [segments[0]]
            for segment in segments[1:]:
                if (
                    not cls.TITLE_DECORATION_PATTERN.search(segment)
                    and not cls._is_generic_version_suffix_segment(segment)
                ):
                    kept_segments.append(segment)
            normalized_value = " - ".join(kept_segments)

        normalized_value = re.sub(r"[\(\[]([^\)\]]+)[\)\]]", cls._strip_decorative_brackets, normalized_value)
        return cls._normalize_text(normalized_value)

    @classmethod
    def _is_generic_version_suffix_segment(cls, value: str) -> bool:
        """Return whether a dash suffix is only generic version text."""

        normalized_value = cls._normalize_text(value)
        return normalized_value in {
            "original",
            "original version",
        }

    @classmethod
    def _canonicalize_version_base_title(
        cls,
        value: str,
        artist_names: list[str] | None = None,
    ) -> str:
        """Canonicalize the base title while removing remix/version descriptors."""

        without_bracketed_versions = cls.MIX_DESCRIPTOR_PATTERN.sub("", value)
        without_suffix_versions = cls.VERSION_SUFFIX_PATTERN.sub("", without_bracketed_versions)
        without_bare_artist_version = cls._strip_bare_artist_version_suffix(
            without_suffix_versions,
            artist_names or [],
        )
        without_leading_artist = cls._strip_leading_artist_title_prefix(
            without_bare_artist_version,
            artist_names or [],
        )
        without_parenthetical_subtitle = re.sub(
            r"[\(\[]([^\)\]]+)[\)\]]",
            "",
            without_leading_artist,
        )
        without_trailing_generic_version = cls.TRAILING_GENERIC_VERSION_PATTERN.sub(
            "",
            without_parenthetical_subtitle,
        )
        return cls._canonicalize_song_title(without_trailing_generic_version)

    @classmethod
    def _strip_decorative_brackets(cls, match: re.Match[str]) -> str:
        """Remove bracketed title text when it is descriptive rather than identifying."""

        content = match.group(1)
        if (
            cls.FEATURE_PATTERN.search(content)
            or cls.TITLE_DECORATION_PATTERN.search(content)
            or cls.ARTIST_VS_SEPARATOR_PATTERN.search(content)
        ):
            return ""
        return f" {content} "

    @classmethod
    def _extract_contributors(cls, artist: str, song: str) -> set[str]:
        """Extract likely contributor names from artist and featured-title text.

        Contributor overlap is a more stable signal than raw artist-string
        similarity because Spotify and SoundCloud express collaborations with
        different punctuation, ordering, and placement of featured artists.
        """

        contributor_names = cls._split_artist_names(artist)
        feature_match = re.search(
            r"\b(?:feat|ft|featuring)\.?\s+(.+?)(?:$|\)|\]|\s-\s)",
            song,
            re.IGNORECASE,
        )
        if feature_match:
            contributor_names.update(cls._split_artist_names(feature_match.group(1)))
        for collaborator_block in cls.COLLABORATOR_BLOCK_PATTERN.finditer(song):
            collaborator_match = re.search(
                r"[\(\[]\s*(?:with|w/)\s+([^\)\]]+)[\)\]]",
                collaborator_block.group(0),
                re.IGNORECASE,
            )
            if collaborator_match:
                contributor_names.update(cls._split_artist_names(collaborator_match.group(1)))
        contributor_names.update(cls._extract_version_contributors(song))
        return cls._expand_artist_aliases(contributor_names)

    @classmethod
    def _has_vs_artist_separator(cls, value: str) -> bool:
        """Return whether source artist text uses a `vs`/`versus` identity split."""

        return bool(cls.ARTIST_VS_SEPARATOR_PATTERN.search(value))

    @classmethod
    def _has_feature_marker(cls, value: str) -> bool:
        """Return whether title text explicitly names a featured artist."""

        return bool(cls.FEATURE_PATTERN.search(value))

    @staticmethod
    def _has_clean_marker(value: str) -> bool:
        """Return whether a Spotify candidate is explicitly a clean version."""

        return bool(re.search(r"\bclean\b", value, re.IGNORECASE))

    @classmethod
    def _is_blocked_match(
        cls,
        source_artist: str,
        source_song: str,
        candidate: dict[str, Any],
        candidate_artist_names: list[str],
    ) -> bool:
        """Return whether a known catalog exception should stay unmatched."""

        candidate_id = str(candidate.get("id") or "")
        if candidate_id and candidate_id in cls.BLOCKED_SPOTIFY_TRACK_IDS:
            return True

        source_artists = cls._extract_contributors(source_artist, source_song)
        candidate_artists = cls._extract_contributors(
            ", ".join(candidate_artist_names),
            str(candidate.get("name", "")),
        )
        source_title = cls._normalize_text(source_song)
        candidate_title = cls._normalize_text(str(candidate.get("name", "")))

        for blocked_match in cls.BLOCKED_MATCHES:
            if not blocked_match["source_artists"].intersection(source_artists):
                continue
            if source_title != blocked_match["source_title"]:
                continue
            if not cls._blocked_title_matches(candidate_title, blocked_match["candidate_title"]):
                continue
            if not blocked_match["candidate_artists"].issubset(candidate_artists):
                continue
            return True

        return False

    @staticmethod
    def _blocked_title_matches(candidate_title: str, blocked_title: str) -> bool:
        """Match a blocked title while allowing feature text after it."""

        return candidate_title == blocked_title or candidate_title.startswith(
            f"{blocked_title} feat "
        )

    @classmethod
    def _score_production_credit_candidate(
        cls,
        source_song: str,
        original_title: str,
        canonical_source_song: str,
        canonical_candidate_song: str,
        candidate_song: str,
        candidate_artist_names: list[str],
    ) -> float | None:
        """Allow producer-credit rows to match on a distinctive exact title."""

        source_has_production_credit = bool(cls.PRODUCTION_CREDIT_PATTERN.search(source_song))
        original_title_has_production_credit = bool(
            cls.PRODUCTION_CREDIT_PATTERN.search(original_title)
        )
        if not source_has_production_credit and not original_title_has_production_credit:
            return None
        if not canonical_source_song or canonical_source_song != canonical_candidate_song:
            return None
        if len(canonical_source_song.split()) < 2:
            return None

        if original_title_has_production_credit and not source_has_production_credit:
            if not cls._has_feature_marker(candidate_song):
                return None
            if len(candidate_artist_names) < 2:
                return None

        return 0.65

    @classmethod
    def _extract_part_markers(cls, value: str) -> set[str]:
        """Extract `Pt. 2` / `Part II` title identity markers."""

        markers: set[str] = set()
        normalized_value = cls._normalize_text(value)
        for match in cls.PART_MARKER_PATTERN.finditer(normalized_value):
            marker = match.group(1)
            markers.add(cls._normalize_part_marker(marker))
        return markers

    @classmethod
    def _extract_title_form_markers(cls, value: str) -> set[str]:
        """Extract title-form markers that distinguish adjacent catalog tracks."""

        normalized_value = cls._normalize_text(value)
        return {match.group(0) for match in cls.TITLE_FORM_MARKER_PATTERN.finditer(normalized_value)}

    @staticmethod
    def _normalize_part_marker(value: str) -> str:
        """Normalize simple roman part numbers to decimal strings."""

        normalized_value = value.lower()
        roman_values = {
            "i": "1",
            "ii": "2",
            "iii": "3",
            "iv": "4",
            "v": "5",
            "vi": "6",
            "vii": "7",
            "viii": "8",
            "ix": "9",
            "x": "10",
        }
        return roman_values.get(normalized_value, normalized_value)

    @staticmethod
    def _is_short_title_expansion_mismatch(
        source_title: str,
        candidate_title: str,
        source_contributors: set[str] | None = None,
        candidate_contributors: set[str] | None = None,
    ) -> bool:
        """Reject weak short titles matching longer title expansions."""

        source_tokens = source_title.split()
        candidate_tokens = candidate_title.split()
        if not source_tokens or len(candidate_tokens) <= len(source_tokens):
            return False
        if SpotifyTrackMatcher._titles_equivalent(source_title, candidate_title):
            return False

        if len(source_tokens) == 1:
            source_token = source_tokens[0]
            if source_token not in candidate_tokens:
                return False
            if len(source_token) <= 2:
                return True

            extra_candidate_tokens = set(candidate_tokens) - {source_token}
            contributor_tokens = {
                token
                for contributor in (source_contributors or set()) | (candidate_contributors or set())
                for token in contributor.split()
            }
            if extra_candidate_tokens and extra_candidate_tokens.issubset(contributor_tokens):
                return False
            return True

        if len(source_tokens) > 2:
            return False

        weak_source_tokens = {
            token
            for token in source_tokens
            if len(token) <= 2 or token in SpotifyTrackMatcher.SHORT_TITLE_COMMON_TOKENS
        }
        if weak_source_tokens != set(source_tokens):
            return False

        return set(source_tokens).issubset(set(candidate_tokens))

    @classmethod
    def _looks_like_liveset_title(cls, artist: str, song: str) -> bool:
        """Return whether source text looks like a DJ set rather than a track."""

        return bool(cls.LIVESET_TITLE_PATTERN.search(f"{artist} {song}"))

    @classmethod
    def _extract_performers_from_title_side_song(cls, value: str) -> set[str]:
        """Extract artist contributors from rows where song text actually contains performer text."""

        leading_artist_text = cls.FEATURE_PATTERN.split(value, maxsplit=1)[0]
        leading_artist_text = leading_artist_text.strip(" ([{")
        contributors = cls._split_artist_names(leading_artist_text)
        contributors.update(cls._extract_contributors("", value))
        return cls._expand_artist_aliases(contributors)

    @classmethod
    def _split_artist_names(cls, value: str) -> set[str]:
        """Split a composite artist string into normalized contributor tokens."""

        contributors = {
            cls._normalize_artist_text(token)
            for token in cls.ARTIST_SPLIT_PATTERN.split(value)
            if cls._normalize_artist_text(token)
        }
        contributors = {token for token in contributors if len(token) > 1}

        normalized_value = cls._normalize_artist_text(value)
        if cls._looks_like_stylized_initialism_artist(value, normalized_value):
            contributors.add(normalized_value)

        return contributors

    @staticmethod
    def _looks_like_stylized_initialism_artist(raw_value: str, normalized_value: str) -> bool:
        if not normalized_value:
            return False

        compact_normalized_value = normalized_value.replace(" ", "")
        if len(compact_normalized_value) < 2:
            return False

        return bool(re.fullmatch(r"\s*[A-Za-z](?:[.&][A-Za-z])+\s*", raw_value.strip()))

    @classmethod
    def _compact_stylized_initialism_artist(cls, value: str) -> str:
        normalized_value = cls._normalize_artist_text(value)
        if not cls._looks_like_stylized_initialism_artist(value, normalized_value):
            return ""
        return normalized_value.replace(" ", "")

    @staticmethod
    def _compact_short_token_title(value: str) -> str:
        tokens = value.split()
        if len(tokens) != 2:
            return ""
        if all(len(token) > 2 for token in tokens):
            return ""

        compact_value = "".join(tokens)
        if len(compact_value) < 4:
            return ""
        return compact_value

    @classmethod
    def _strip_leading_title_index_marker(cls, canonical_title: str, raw_title: str) -> str:
        if not canonical_title:
            return ""
        if not re.match(r"^\s*\d+[\s.]+[A-Za-z]", raw_title):
            return ""
        if not cls._has_feature_marker(raw_title):
            return ""

        stripped_title = re.sub(r"^\d+\s+", "", canonical_title).strip()
        return stripped_title if stripped_title != canonical_title else ""

    @classmethod
    def _expand_artist_aliases(cls, contributors: set[str]) -> set[str]:
        """Add known artist aliases for local matching without extra API calls."""

        expanded_contributors = set(contributors)
        for contributor in contributors:
            expanded_contributors.update(cls.ARTIST_ALIASES.get(contributor, set()))
        return expanded_contributors

    @classmethod
    def _extract_version_identity_tokens(
        cls,
        value: str,
        artist_names: list[str] | None = None,
    ) -> set[str]:
        """Extract identity-bearing words from remix or mix descriptors."""

        tokens: set[str] = set()
        for descriptor_tokens in cls._extract_version_identity_token_groups(value, artist_names):
            tokens.update(descriptor_tokens)
        return tokens

    @classmethod
    def _extract_version_identity_token_groups(
        cls,
        value: str,
        artist_names: list[str] | None = None,
    ) -> list[set[str]]:
        """Extract identity-bearing tokens grouped by each version descriptor."""

        token_groups: list[set[str]] = []
        for descriptor in cls._extract_version_descriptors(value, artist_names):
            descriptor_tokens = cls._extract_version_descriptor_identity_tokens(descriptor)
            if descriptor_tokens:
                token_groups.append(descriptor_tokens)
        return token_groups

    @classmethod
    def _extract_version_descriptor_identity_tokens(cls, descriptor: str) -> set[str]:
        """Extract identity-bearing words from one remix or mix descriptor."""

        tokens: set[str] = set()
        identity_descriptor = cls.FEATURE_PATTERN.split(descriptor, maxsplit=1)[0]
        normalized_descriptor = cls._normalize_text(identity_descriptor)
        descriptor_words = set(normalized_descriptor.split())
        if descriptor_words.intersection(cls.LABEL_DESCRIPTOR_WORDS):
            return set()
        tokens.update(
            token
            for token in descriptor_words
            if len(token) > 1 and token not in cls.GENERIC_VERSION_WORDS
        )
        contributor_text = cls.VERSION_MARKER_PATTERN.sub("", identity_descriptor)
        tokens.update(cls._expand_artist_aliases(cls._split_artist_names(contributor_text)))
        return tokens

    @classmethod
    def _extract_version_contributors(cls, value: str) -> set[str]:
        """Extract named remix/version contributors from title descriptors."""

        contributors: set[str] = set()
        for descriptor in cls._extract_version_descriptors(value):
            contributor_text = cls.VERSION_MARKER_PATTERN.sub("", descriptor)
            contributors.update(cls._split_artist_names(contributor_text))
        return contributors

    @classmethod
    def _extract_original_title_version_tokens(
        cls,
        original_title: str,
        canonical_source_song: str,
    ) -> set[str]:
        """Recover version identity from the raw SoundCloud title when parsing stripped it."""

        if not original_title or not canonical_source_song:
            return set()

        split_title = cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(original_title, maxsplit=1)
        if len(split_title) == 2 and split_title[0].strip() and split_title[1].strip():
            original_title_candidates = [split_title[1].strip(), split_title[0].strip()]
        else:
            original_title_candidates = [original_title]

        source_tokens = {token for token in canonical_source_song.split() if token}
        for title_candidate in original_title_candidates:
            version_tokens = cls._extract_version_identity_tokens(title_candidate)
            if not version_tokens:
                continue

            original_base_title = cls._canonicalize_version_base_title(title_candidate)
            if cls._titles_equivalent(canonical_source_song, original_base_title):
                return version_tokens

            original_base_tokens = {token for token in original_base_title.split() if token}
            if source_tokens and source_tokens.issubset(original_base_tokens):
                return version_tokens

        return set()

    @classmethod
    def _extract_version_descriptors(
        cls,
        value: str,
        artist_names: list[str] | None = None,
    ) -> list[str]:
        """Return raw remix/version descriptor text from brackets or suffixes."""

        descriptors = [
            match.group(1)
            for match in cls.MIX_DESCRIPTOR_PATTERN.finditer(value)
        ]
        suffix_match = cls.VERSION_SUFFIX_PATTERN.search(value)
        if suffix_match:
            descriptors.append(suffix_match.group(1))
        bare_artist_version = cls._extract_bare_artist_version_suffix(
            value,
            artist_names or [],
        )
        if bare_artist_version:
            descriptors.append(bare_artist_version)
        return descriptors

    @classmethod
    def _strip_bare_artist_version_suffix(cls, value: str, artist_names: list[str]) -> str:
        """Remove candidate suffixes like `Moody Good Remix` when Moody Good is an artist."""

        suffix_length = cls._bare_artist_version_suffix_length(value, artist_names)
        if suffix_length == 0:
            return value

        words = value.strip().split()
        return " ".join(words[:-suffix_length])

    @classmethod
    def _strip_leading_artist_title_prefix(cls, value: str, artist_names: list[str]) -> str:
        """Remove accidental leading artist text from a title base."""

        prefix_length = cls._leading_artist_title_prefix_length(value, artist_names)
        if prefix_length == 0:
            return value

        raw_words = value.strip().split()
        return " ".join(raw_words[prefix_length:])

    @classmethod
    def _extract_leading_artist_title_prefix_contributors(
        cls,
        value: str,
        artist_names: list[str],
    ) -> set[str]:
        """Return leading title-prefix artists when Spotify confirms them."""

        prefix_length = cls._leading_artist_title_prefix_length(value, artist_names)
        if prefix_length == 0:
            return set()

        raw_words = value.strip().split()
        return cls._expand_artist_aliases(
            cls._split_artist_names(" ".join(raw_words[:prefix_length]))
        )

    @classmethod
    def _leading_artist_title_prefix_length(cls, value: str, artist_names: list[str]) -> int:
        """Find leading artist words in parsed song text."""

        normalized_value_words = cls._normalize_text(value).split()
        if not normalized_value_words:
            return 0

        raw_words = value.strip().split()
        if len(raw_words) != len(normalized_value_words):
            return 0

        for artist_name in sorted(artist_names, key=len, reverse=True):
            artist_words = cls._normalize_artist_text(artist_name).split()
            if not artist_words:
                continue
            if len(normalized_value_words) <= len(artist_words):
                continue
            if normalized_value_words[:len(artist_words)] == artist_words:
                return len(artist_words)

        return 0

    @classmethod
    def _strip_leading_artist_title_segment(cls, value: str, artist_names: list[str]) -> str:
        """Remove accidental `artist - title` prefixes from parsed song text."""

        prefix_contributors = cls._extract_leading_artist_title_segment_contributors(
            value,
            artist_names,
        )
        if not prefix_contributors:
            return value

        segments = cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(value, maxsplit=1)
        return segments[1].strip() if len(segments) == 2 and segments[1].strip() else value

    @classmethod
    def _extract_leading_artist_title_segment_contributors(
        cls,
        value: str,
        artist_names: list[str],
    ) -> set[str]:
        """Return leading title-segment artists when Spotify confirms them."""

        segments = cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(value, maxsplit=1)
        if len(segments) != 2:
            return set()

        prefix_contributors = cls._expand_artist_aliases(cls._split_artist_names(segments[0]))
        known_contributors = cls._expand_artist_aliases(
            cls._split_artist_names(", ".join(artist_names))
        )
        if not prefix_contributors or not known_contributors:
            return set()
        if not prefix_contributors.issubset(known_contributors):
            return set()

        return prefix_contributors

    @classmethod
    def _strip_trailing_artist_title_segment(cls, value: str, artist_names: list[str]) -> str:
        """Remove accidental `title - artist` suffixes from parsed song text."""

        suffix_contributors = cls._extract_trailing_artist_title_segment_contributors(
            value,
            artist_names,
        )
        if not suffix_contributors:
            return value

        title, _separator, _suffix = value.rpartition("-")
        return title.strip() if title.strip() else value

    @classmethod
    def _extract_trailing_artist_title_segment_contributors(
        cls,
        value: str,
        artist_names: list[str],
    ) -> set[str]:
        """Return trailing title-segment artists when Spotify confirms them."""

        title, separator, suffix = value.rpartition("-")
        if not separator or not title.strip() or not suffix.strip():
            return set()

        suffix_contributors = cls._expand_artist_aliases(cls._split_artist_names(suffix))
        known_contributors = cls._expand_artist_aliases(
            cls._split_artist_names(", ".join(artist_names))
        )
        if not suffix_contributors or not known_contributors:
            return set()
        if not suffix_contributors.issubset(known_contributors):
            return set()

        return suffix_contributors

    @classmethod
    def _extract_bare_artist_version_suffix(
        cls,
        value: str,
        artist_names: list[str],
    ) -> str | None:
        """Return a bare artist/version suffix when it matches a structured artist."""

        suffix_length = cls._bare_artist_version_suffix_length(value, artist_names)
        if suffix_length == 0:
            return None

        words = value.strip().split()
        return " ".join(words[-suffix_length:])

    @classmethod
    def _bare_artist_version_suffix_length(cls, value: str, artist_names: list[str]) -> int:
        """Find trailing `artist + version marker` word counts in unpunctuated titles."""

        raw_words = value.strip().split()
        normalized_words = cls._normalize_text(value).split()
        if len(raw_words) != len(normalized_words):
            return 0

        marker_word_groups = (
            ("remix",),
            ("flip",),
            ("edit",),
            ("mix",),
            ("vip",),
            ("bootleg",),
            ("rebirth",),
            ("rework",),
        )
        for artist_name in sorted(artist_names, key=len, reverse=True):
            artist_words = tuple(cls._normalize_artist_text(artist_name).split())
            if not artist_words:
                continue

            for marker_words in marker_word_groups:
                suffix_words = artist_words + marker_words
                if len(normalized_words) <= len(suffix_words):
                    continue
                if tuple(normalized_words[-len(suffix_words):]) == suffix_words:
                    return len(suffix_words)

        return 0

    @classmethod
    def _score_duplicate_version_title_candidate(
        cls,
        source_version_tokens: set[str],
        candidate_version_tokens: set[str],
        source_contributors: set[str],
        candidate_contributors: set[str],
        candidate_song: str,
    ) -> float | None:
        """Rescue storefront rows where the title is duplicated remix metadata."""

        if not cls.DUPLICATED_VERSION_TITLE_PATTERN.fullmatch(candidate_song):
            return None
        if not source_version_tokens or not candidate_version_tokens:
            return None
        if not cls._has_required_version_overlap(source_version_tokens, candidate_version_tokens):
            return None
        if not source_contributors or not source_contributors.issubset(candidate_contributors):
            return None

        return 1.0

    @classmethod
    def _score_version_only_title_candidate(
        cls,
        source_version_tokens: set[str],
        candidate_version_tokens: set[str],
        source_contributors: set[str],
        candidate_contributors: set[str],
        candidate_song: str,
        candidate_artist_names: list[str],
    ) -> float | None:
        """Rescue malformed Spotify rows whose title is only version metadata."""

        if not source_version_tokens or not candidate_version_tokens:
            return None
        if not cls._has_required_version_overlap(source_version_tokens, candidate_version_tokens):
            return None
        if not source_contributors or not source_contributors.issubset(candidate_contributors):
            return None
        if not cls._is_version_only_title(candidate_song, candidate_artist_names):
            return None

        return 1.0

    @classmethod
    def _generic_unnamed_remix_source_matches_plain_candidate(
        cls,
        source_song: str,
        candidate_song: str,
        source_contributors: set[str],
        candidate_contributors: set[str],
        source_artist_names: list[str],
        candidate_artist_names: list[str],
    ) -> bool:
        """Allow generic `(Remix)` source labels when the catalog title is plain."""

        if not cls._has_generic_unnamed_remix_descriptor(source_song):
            return False
        if cls._extract_version_identity_tokens(source_song):
            return False
        if not source_contributors or not source_contributors.issubset(candidate_contributors):
            return False

        source_base_title = cls._canonicalize_version_base_title(source_song, source_artist_names)
        candidate_base_title = cls._canonicalize_version_base_title(
            candidate_song,
            candidate_artist_names,
        )
        return bool(source_base_title and cls._titles_equivalent(source_base_title, candidate_base_title))

    @classmethod
    def _named_source_version_matches_plain_candidate(
        cls,
        source_base_title: str,
        candidate_base_title: str,
        source_version_token_groups: list[set[str]],
        candidate_contributors: set[str],
    ) -> bool:
        """Allow named source remix text when Spotify carries that name as an artist."""

        if not source_version_token_groups or not candidate_contributors:
            return False
        if not source_base_title or not cls._titles_equivalent(source_base_title, candidate_base_title):
            return False
        return cls._has_required_version_group_overlap(
            source_version_token_groups,
            candidate_contributors,
        )

    @classmethod
    def _has_generic_unnamed_remix_descriptor(cls, value: str) -> bool:
        for descriptor in cls._extract_version_descriptors(value):
            descriptor_without_features = cls.FEATURE_PATTERN.split(descriptor, maxsplit=1)[0]
            normalized_descriptor = cls._normalize_text(descriptor_without_features)
            descriptor_tokens = set(normalized_descriptor.split())
            if descriptor_tokens == {"remix"}:
                return True
        return False

    @classmethod
    def _is_version_only_title(cls, value: str, artist_names: list[str]) -> bool:
        """Return whether every title segment is artist/version metadata."""

        segments = [
            segment.strip()
            for segment in cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(value)
            if segment.strip()
        ]
        if not segments:
            return False

        known_contributors = cls._expand_artist_aliases(cls._split_artist_names(", ".join(artist_names)))
        if not known_contributors:
            return False

        for segment in segments:
            if not cls._has_version_marker(segment):
                return False

            contributor_text = cls.VERSION_MARKER_PATTERN.sub("", segment).strip()
            segment_contributors = cls._expand_artist_aliases(
                cls._split_artist_names(contributor_text)
            )
            if not segment_contributors:
                return False
            if not segment_contributors.issubset(known_contributors):
                return False

        return True

    @classmethod
    def _has_version_marker(cls, value: str) -> bool:
        """Return whether a title mentions remix, edit, rework, or similar version text."""

        return bool(cls.VERSION_MARKER_PATTERN.search(value))

    @classmethod
    def _has_strict_version_marker(cls, value: str) -> bool:
        """Return whether a candidate has a version marker that should not match a plain source."""

        return bool(cls.STRICT_VERSION_MARKER_PATTERN.search(value))

    @staticmethod
    def _has_required_version_overlap(source: set[str], candidate: set[str]) -> bool:
        """Return whether the candidate carries the same remix/version identity."""

        if not candidate:
            return False

        for source_token in source:
            best_similarity = max(
                (
                    SequenceMatcher(None, source_token, candidate_token).ratio()
                    for candidate_token in candidate
                ),
                default=0.0,
            )
            if best_similarity >= 0.84:
                return True

        return False

    @classmethod
    def _has_required_version_group_overlap(
        cls,
        source_groups: list[set[str]],
        candidate: set[str],
    ) -> bool:
        """Return whether every named source version descriptor is represented."""

        if not candidate:
            return False

        for source_group in source_groups:
            if not cls._has_required_version_overlap(source_group, candidate):
                return False

        return True

    @classmethod
    def _score_individual_artist_similarity(
        cls,
        source: set[str],
        candidate_artist_names: list[str],
    ) -> float:
        """Score source contributors against each structured Spotify artist."""

        candidate_names = {
            cls._normalize_artist_text(candidate_name)
            for candidate_name in candidate_artist_names
            if cls._normalize_artist_text(candidate_name)
        }
        if not source or not candidate_names:
            return 0.0

        matched_source_contributors = 0
        for source_name in source:
            best_similarity = max(
                (
                    cls._artist_name_similarity(source_name, candidate_name)
                    for candidate_name in candidate_names
                ),
                default=0.0,
            )
            if best_similarity >= 0.84:
                matched_source_contributors += 1

        return matched_source_contributors / len(source)

    @staticmethod
    def _score_contributor_overlap(source: set[str], candidate: set[str]) -> float:
        """Score how completely the candidate covers the source contributors.

        Artist credits across platforms are messy in predictable ways: `vs`
        separators, featured-artist placement, punctuation differences, and the
        occasional one-character spelling drift. The goal here is not to demand
        byte-for-byte equality, but to answer the more useful question: "does
        this Spotify result appear to contain the same collaborating artists?"
        """

        if not source or not candidate:
            return 0.0

        matched_source_contributors = 0
        for source_name in source:
            best_similarity = max(
                (SpotifyTrackMatcher._artist_name_similarity(source_name, candidate_name) for candidate_name in candidate),
                default=0.0,
            )
            if best_similarity >= 0.84:
                matched_source_contributors += 1

        return matched_source_contributors / len(source)

    @staticmethod
    def _artist_name_similarity(source_name: str, candidate_name: str) -> float:
        if source_name == candidate_name:
            return 1.0

        compact_source = source_name.replace(" ", "")
        compact_candidate = candidate_name.replace(" ", "")
        if compact_source == compact_candidate:
            return 1.0

        shorter, longer = sorted((compact_source, compact_candidate), key=len)
        if len(shorter) >= 5 and longer.startswith(shorter):
            return 0.0

        return SequenceMatcher(None, source_name, candidate_name).ratio()

    @staticmethod
    def _score_title_token_overlap(source_title: str, candidate_title: str) -> float:
        """Measure title agreement using exact normalized tokens.

        Sequence similarity is good at spotting close spellings, but it can
        over-credit pairs like `danger` and `dangerous`. Token overlap is a
        better guardrail for deciding whether two titles refer to the same
        underlying song identity.
        """

        source_tokens = {token for token in source_title.split() if token}
        candidate_tokens = {token for token in candidate_title.split() if token}
        if not source_tokens or not candidate_tokens:
            return 0.0

        if source_tokens == candidate_tokens:
            return 1.0

        overlap = source_tokens.intersection(candidate_tokens)
        if not overlap:
            return 0.0

        return len(overlap) / max(len(source_tokens), len(candidate_tokens))

    @classmethod
    def _titles_equivalent(cls, source_title: str, candidate_title: str) -> bool:
        """Return whether normalized titles are equal, allowing tight variants."""

        normalized_source = cls._normalize_text(source_title)
        normalized_candidate = cls._normalize_text(candidate_title)
        if normalized_source == normalized_candidate:
            return True
        if normalized_source.replace(" ", "") == normalized_candidate.replace(" ", ""):
            return True
        if cls._strip_leading_title_article(normalized_source) == cls._strip_leading_title_article(
            normalized_candidate
        ):
            return True
        if cls._has_single_letter_subtitle_expansion(normalized_source, normalized_candidate):
            return True
        return cls._has_acronym_expansion_match(normalized_source, normalized_candidate)

    @classmethod
    def _original_title_expanded_title_matches(
        cls,
        original_title: str,
        canonical_source_song: str,
        canonical_candidate_song: str,
    ) -> bool:
        """Return whether raw SoundCloud title confirms a candidate subtitle."""

        if not original_title or not canonical_source_song or not canonical_candidate_song:
            return False
        if cls._titles_equivalent(canonical_source_song, canonical_candidate_song):
            return True

        title_candidates = [original_title]
        split_title = cls.TITLE_SUFFIX_SEPARATOR_PATTERN.split(original_title, maxsplit=1)
        if len(split_title) == 2 and split_title[1].strip():
            title_candidates.insert(0, split_title[1].strip())

        source_tokens = set(canonical_source_song.split())
        for title_candidate in title_candidates:
            canonical_original_title = cls._canonicalize_song_title(title_candidate)
            if not canonical_original_title:
                continue
            if not source_tokens.issubset(set(canonical_original_title.split())):
                continue
            if cls._titles_equivalent(canonical_original_title, canonical_candidate_song):
                return True

        return False

    @staticmethod
    def _strip_leading_title_article(value: str) -> str:
        return re.sub(r"^(?:a|an|the)\s+", "", value).strip()

    @staticmethod
    def _has_single_letter_subtitle_expansion(source_title: str, candidate_title: str) -> bool:
        """Allow official subtitles like `Runaway (U & I)` to match `Runaway`."""

        def matches(short_title: str, long_title: str) -> bool:
            short_tokens = short_title.split()
            long_tokens = long_title.split()
            if not short_tokens or len(long_tokens) <= len(short_tokens):
                return False
            if long_tokens[:len(short_tokens)] != short_tokens:
                return False

            extra_tokens = long_tokens[len(short_tokens):]
            return len(extra_tokens) <= 3 and all(
                len(token) == 1 and token.isalpha()
                for token in extra_tokens
            )

        return matches(source_title, candidate_title) or matches(candidate_title, source_title)

    @staticmethod
    def _has_acronym_expansion_match(source_title: str, candidate_title: str) -> bool:
        """Allow `TTU` to match `TTU Too Turnt Up` without broad substring matching."""

        def matches(short_title: str, long_title: str) -> bool:
            short_tokens = short_title.split()
            long_tokens = long_title.split()
            if len(short_tokens) != 1 or len(long_tokens) < 3:
                return False

            acronym = short_tokens[0]
            if not (3 <= len(acronym) <= 6):
                return False

            if long_tokens[0] == acronym:
                expansion_tokens = long_tokens[1:]
            else:
                expansion_tokens = long_tokens

            if len(expansion_tokens) < 2:
                return False

            expansion_acronym = "".join(token[0] for token in expansion_tokens if token)
            return acronym == expansion_acronym

        return matches(source_title, candidate_title) or matches(candidate_title, source_title)

    @classmethod
    def _infer_artist_from_trailing_mix_title(cls, original_title: str) -> tuple[str | None, str | None]:
        """Recover `artist` and `song` from uploader-fallback titles when possible.

        Some uploads append the actual artist after a mix descriptor instead of
        placing it before a dash, e.g. `Burner (Original Mix) Leik`. This is
        too specialized to bake into the primary parser, but it is useful as a
        second-pass search hint once we already know the row came from uploader
        fallback.
        """

        normalized_title = " ".join(original_title.strip().split())
        mix_match = cls.MIX_DESCRIPTOR_PATTERN.search(normalized_title)
        if mix_match is None:
            return None, None

        trailing_text = normalized_title[mix_match.end():].strip(" -")
        if not trailing_text:
            return None, None
        if len(trailing_text.split()) > 4:
            return None, None

        leading_text = normalized_title[:mix_match.start()].strip(" -")
        mix_text = mix_match.group(1).strip()
        if not leading_text or not mix_text:
            return None, None

        inferred_song = f"{leading_text} ({mix_text})"
        return trailing_text, inferred_song

    @staticmethod
    def _dedupe_queries(queries: list[str]) -> list[str]:
        """Preserve query order while removing duplicate search attempts."""

        seen_queries: set[str] = set()
        unique_queries: list[str] = []
        for query in queries:
            normalized_query = query.strip()
            if not normalized_query or normalized_query in seen_queries:
                continue
            seen_queries.add(normalized_query)
            unique_queries.append(normalized_query)
        return unique_queries

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize punctuation and spacing before fuzzy comparison."""

        normalized_value = unicodedata.normalize("NFKD", value.lower().strip())
        normalized_value = "".join(
            character for character in normalized_value if not unicodedata.combining(character)
        )
        normalized_value = re.sub(r"\bf[\W_]*ck\b", "fuck", normalized_value)
        normalized_value = re.sub(r"[^\w\s]", " ", normalized_value)
        normalized_value = re.sub(r"\s+", " ", normalized_value)
        return normalized_value

    @classmethod
    def _normalize_artist_text(cls, value: str) -> str:
        """Normalize artist names while dropping storefront profile decorations."""

        value = cls.ARTIST_CATALOG_PREFIX_PATTERN.sub("", value)
        normalized_value = cls._normalize_text(value)
        normalized_value = re.sub(r"^\d+\s+", "", normalized_value)
        normalized_value = cls.ARTIST_DECORATION_SUFFIX_PATTERN.sub("", normalized_value)
        normalized_value = re.sub(r"\s+", " ", normalized_value)
        return normalized_value.strip()

    @staticmethod
    def _candidate_artist_names(candidate: dict[str, Any]) -> list[str]:
        """Return Spotify artist names without flattening away their boundaries."""

        return [
            str(artist_item.get("name", "")).strip()
            for artist_item in candidate.get("artists", [])
            if artist_item.get("name")
        ]

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        """Convert a possibly-missing API field into a nullable string."""

        if value is None:
            return None
        return str(value)
