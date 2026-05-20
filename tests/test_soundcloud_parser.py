from __future__ import annotations

import unittest

from src.config import DEFAULT_LIVESET_KEYWORDS, DEFAULT_PAREN_KEYWORDS, DEFAULT_REMOVE_PATTERNS
from src.models import ParserSettings
from src.soundcloud.parser import SoundCloudTitleParser


class SoundCloudTitleParserTests(unittest.TestCase):
    def test_rebirth_parenthetical_is_preserved_as_version_identity(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=[],
            )
        )

        artist, song, source = parser.parse_title(
            "Dillon Francis - Drunk All The Time (The Rebirth) [feat. Simon Lord]",
            "Dillon Francis",
        )

        self.assertEqual(artist, "Dillon Francis")
        self.assertEqual(song, "Drunk All The Time (The Rebirth)")
        self.assertEqual(source, "Parsed from Title")

    def test_unspaced_trailing_version_suffix_is_preserved(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=[],
            )
        )

        artist, song, source = parser.parse_title(
            "Save the world-zedd remix-",
            "alemirri",
        )

        self.assertEqual(artist, "alemirri")
        self.assertEqual(song, "Save the world (zedd remix)")
        self.assertEqual(source, "Uploader Fallback")

    def test_unspaced_trailing_feature_artist_is_parsed_title_first(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=[],
            )
        )

        artist, song, source = parser.parse_title(
            "Melbourne Sound- Matty Lincoln ft.Mandas",
            "MELBOURNE BANGERS",
        )

        self.assertEqual(artist, "Matty Lincoln ft.Mandas")
        self.assertEqual(song, "Melbourne Sound")
        self.assertEqual(source, "Parsed from Title")

    def test_full_mix_hd_and_html_entities_are_cleaned(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Bombs Away &amp; Dan Absent - Samurai Bounce (Full Mix) HD",
            "Bombs Away, Dan Absent",
        )

        self.assertEqual(artist, "Bombs Away & Dan Absent")
        self.assertEqual(song, "Samurai Bounce")
        self.assertEqual(source, "Parsed from Title")

    def test_spaced_tilde_separator_is_parsed_like_artist_title_split(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Drake ~ Back To Back Freestyle",
            "octobersveryown",
        )

        self.assertEqual(artist, "Drake")
        self.assertEqual(song, "Back To Back Freestyle")
        self.assertEqual(source, "Parsed from Title")

    def test_bare_flip_after_artist_title_separator_is_kept_as_song_title(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Bro Safari X Boombox Cartel - Flip [Free Download]",
            "BRO SAFARI",
        )

        self.assertEqual(artist, "Bro Safari X Boombox Cartel")
        self.assertEqual(song, "Flip")
        self.assertEqual(source, "Parsed from Title")

    def test_matching_uploader_artist_keeps_vip_suffix_as_song_title(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "SNAILS - King is Back VIP (Snails & Ghastly) [Free Download]",
            "SNAILS",
        )

        self.assertEqual(artist, "SNAILS")
        self.assertEqual(song, "King is Back VIP")
        self.assertEqual(source, "Parsed from Title")

    def test_malformed_recordings_bracket_is_removed_from_parsed_title(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Chardy & Kronic - S.W.A.T. Team (Reece Low Remix) [Hussle Recordings)",
            "uploader",
        )

        self.assertEqual(artist, "Chardy & Kronic")
        self.assertEqual(song, "S.W.A.T. Team (Reece Low Remix)")
        self.assertEqual(source, "Parsed from Title")

    def test_tight_artist_title_dash_is_parsed_when_title_starts_after_space(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Firebeatz & KSHMR- No Heroes (feat. Luciana) (Original Mix)",
            "Spinnin'",
        )

        self.assertEqual(artist, "Firebeatz & KSHMR")
        self.assertEqual(song, "No Heroes (feat. Luciana)")
        self.assertEqual(source, "Parsed from Title")

    def test_free_dl_marketing_text_is_removed_from_title(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Showtek - Booyah (Party Favor Remix) **FREE DL**",
            "Showtek",
        )

        self.assertEqual(artist, "Showtek")
        self.assertEqual(song, "Booyah (Party Favor Remix)")
        self.assertEqual(source, "Parsed from Title")

    def test_title_by_artist_pattern_is_parsed_title_first(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "Dum Dee Dum by Keys N Krates",
            "Pantheon: Anarchy",
        )

        self.assertEqual(artist, "Keys N Krates")
        self.assertEqual(song, "Dum Dee Dum")
        self.assertEqual(source, "Parsed from Title")

    def test_leading_index_marker_is_removed_from_parsed_artist(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=[],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        artist, song, source = parser.parse_title(
            "7. GETTER - I WANT MORE",
            "uploader",
        )

        self.assertEqual(artist, "GETTER")
        self.assertEqual(song, "I WANT MORE")
        self.assertEqual(source, "Parsed from Title")

    def test_live_at_title_is_detected_as_liveset(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=["live at"],
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        self.assertTrue(
            parser.is_liveset(
                "Deorro Live At SCMF In El Paso 2014",
                "Deorro",
                "Deorro Live At SCMF In El Paso 2014",
            )
        )

    def test_default_liveset_keywords_detect_mix_and_radio_titles(self) -> None:
        parser = SoundCloudTitleParser(
            ParserSettings(
                paren_keywords=DEFAULT_PAREN_KEYWORDS,
                liveset_keywords=DEFAULT_LIVESET_KEYWORDS,
                cutoff_patterns=[],
                remove_patterns=DEFAULT_REMOVE_PATTERNS,
            )
        )

        liveset_titles = [
            "Night Owl Radio 007 ft. MK and JAUZ",
            "Metronome Mix #50 [www.insomniac.com]",
            "Diplo N Friends Guest Mix - Jauz",
            "500k Melbourne Tribute",
            "Menji Mix",
            "Excision - Shambhala 2014 Mix",
            "Tchami - Essential Mix",
            "Impact: REZZ | Mixmag",
            "Kennedy Jones - Nocturnal Wonderland 2014 Mix",
            "Aylen - Day Set at Envy'd Lounge 5/21/17",
            "Drezo - Triple J (JJJ) Mixup (12/16/17)",
            "Dzeko & Torres - 2014 In 10 Minutes",
        ]

        for title in liveset_titles:
            with self.subTest(title=title):
                self.assertTrue(parser.is_liveset(title, original_title=title))


if __name__ == "__main__":
    unittest.main()
