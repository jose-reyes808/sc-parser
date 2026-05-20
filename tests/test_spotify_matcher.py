from __future__ import annotations

import unittest

from src.spotify.matcher import SpotifyTrackMatcher


class SpotifyTrackMatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matcher = SpotifyTrackMatcher()

    def test_exact_title_with_unrelated_artist_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("Danger", ["BTS"])

        best_candidate = self.matcher.find_best_candidate(
            "Bro Safari & Sazon Booya",
            "Danger",
            [candidate],
            'track:"Danger"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Bro Safari & Sazon Booya",
                "Danger",
                [candidate],
                'track:"Danger"',
                )
        )

    def test_near_prefix_artist_and_partial_title_overlap_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("Getting Away With It", ["Loudery"])

        best_candidate = self.matcher.find_best_candidate(
            "Louder",
            "Get Away",
            [candidate],
            'track:"Get Away" artist:"Louder"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Louder",
                "Get Away",
                [candidate],
                'track:"Get Away" artist:"Louder"',
                )
        )

    def test_same_artist_zero_title_token_overlap_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("Fricken Dope", ["Getter"])

        best_candidate = self.matcher.find_best_candidate(
            "Getter",
            "Wat The Frick",
            [candidate],
            'track:"Wat The Frick" artist:"Getter"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Getter",
                "Wat The Frick",
                [candidate],
                'track:"Wat The Frick" artist:"Getter"',
                )
        )

    def test_intro_title_form_mismatch_rejects_wrong_song_and_aliases_real_bonus_track(self) -> None:
        wrong_candidate = self._candidate("No Pressure Intro", ["Logic"])
        real_candidate = self._candidate(
            "No Pressure (feat. Snoop Dogg) - Bonus Track",
            ["J Boog", "Snoop Dogg"],
        )

        wrong_best_candidate = self.matcher.find_best_candidate(
            "JBoogMusic",
            "No Pressure (feat. Snoop Dogg)",
            [wrong_candidate],
            'track:"No Pressure" artist:"JBoogMusic"',
        )
        match = self.matcher.match(
            "JBoogMusic",
            "No Pressure (feat. Snoop Dogg)",
            [wrong_candidate, real_candidate],
            'track:"No Pressure" artist:"JBoogMusic"',
        )

        self.assertIsNotNone(wrong_best_candidate)
        self.assertLess(wrong_best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "J Boog, Snoop Dogg")
        self.assertEqual(match.matched_song, "No Pressure (feat. Snoop Dogg) - Bonus Track")
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_exact_title_with_unrelated_collaborators_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("Throw Ya Hands Up", ["Mr. Green", "DJ Kool Herc"])

        best_candidate = self.matcher.find_best_candidate(
            "Joel Fletcher feat. Cris Gamble, Madeleine Jayne",
            "Throw Ya Hands Up !",
            [candidate],
            'track:"Throw Ya Hands Up"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Joel Fletcher feat. Cris Gamble, Madeleine Jayne",
                "Throw Ya Hands Up !",
                [candidate],
                'track:"Throw Ya Hands Up"',
            )
        )

    def test_exact_title_with_matching_artist_still_matches(self) -> None:
        candidate = self._candidate("Danger", ["Bro Safari", "Sazon Booya"])

        match = self.matcher.match(
            "Bro Safari & Sazon Booya",
            "Danger",
            [candidate],
            'track:"Danger" artist:"Bro Safari & Sazon Booya"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_exact_repeated_title_with_unrelated_artist_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("Dump Dump", ["$krrt Cobain"])

        best_candidate = self.matcher.find_best_candidate(
            "Ryan Collins",
            "Dump Dump",
            [candidate],
            'track:"Dump Dump" artist:"Ryan Collins"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Ryan Collins",
                "Dump Dump",
                [candidate],
                'track:"Dump Dump" artist:"Ryan Collins"',
            )
        )

    def test_exact_title_with_with_phrase_does_not_create_fake_artist_overlap(self) -> None:
        candidate = self._candidate(
            "Music Sounds Better With You",
            ["Stardust", "Benjamin Diamond", "Alan Braxe", "Thomas Bangalter"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Malaa & Noizu",
            "Music Sounds Better With You",
            [candidate],
            'track:"Music Sounds Better With You" artist:"Malaa & Noizu"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Malaa & Noizu",
                "Music Sounds Better With You",
                [candidate],
                'track:"Music Sounds Better With You" artist:"Malaa & Noizu"',
            )
        )

    def test_production_credit_title_can_match_exact_multiword_spotify_title(self) -> None:
        candidate = self._candidate("DJ Khaled", ["Azizi Gibson"])

        match = self.matcher.match(
            "Millz Douglas",
            "Dj Khaled prod.",
            [candidate],
            'track:"Dj Khaled prod." artist:"Millz Douglas"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_production_credit_one_word_title_still_needs_artist_evidence(self) -> None:
        candidate = self._candidate("Danger", ["BTS"])

        best_candidate = self.matcher.find_best_candidate(
            "Producer Name",
            "Danger prod.",
            [candidate],
            'track:"Danger prod." artist:"Producer Name"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Producer Name",
                "Danger prod.",
                [candidate],
                'track:"Danger prod." artist:"Producer Name"',
            )
        )

    def test_original_title_production_credit_can_match_featured_spotify_performers(self) -> None:
        wrong_candidate = self._candidate("Look At Me Now", ["Deckside Diplomats"])
        real_candidate = self._candidate(
            "Look At Me Now (Feat. Lil'Wayne & Busta Rhymes)",
            ["Chris Brown", "Lil Wayne", "Busta Rhymes"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Diplo",
            "Look At Me Now",
            [wrong_candidate, real_candidate],
            'track:"Look At Me Now"',
            original_title="Look At Me Now (Produced By Diplo)",
        )
        wrong_best_candidate = self.matcher.find_best_candidate(
            "Diplo",
            "Look At Me Now",
            [wrong_candidate],
            'track:"Look At Me Now" artist:"Diplo"',
            original_title="Look At Me Now (Produced By Diplo)",
        )
        match = self.matcher.match(
            "Diplo",
            "Look At Me Now",
            [wrong_candidate, real_candidate],
            'track:"Look At Me Now"',
            original_title="Look At Me Now (Produced By Diplo)",
        )

        self.assertIsNotNone(wrong_best_candidate)
        self.assertLess(wrong_best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNotNone(best_candidate)
        self.assertEqual(best_candidate.matched_artist, "Chris Brown, Lil Wayne, Busta Rhymes")
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "Chris Brown, Lil Wayne, Busta Rhymes")
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_dotted_artist_initials_match_same_spotify_artist(self) -> None:
        candidate = self._candidate("Honey", ["D.O.D"])

        match = self.matcher.match(
            "D.O.D",
            "Honey",
            [candidate],
            'track:"Honey" artist:"D.O.D"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_dotted_artist_initials_do_not_match_same_title_wrong_artist(self) -> None:
        candidate = self._candidate("Honey", ["Vacations"])

        best_candidate = self.matcher.find_best_candidate(
            "D.O.D",
            "Honey",
            [candidate],
            'track:"Honey" artist:"D.O.D"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "D.O.D",
                "Honey",
                [candidate],
                'track:"Honey" artist:"D.O.D"',
                )
        )

    def test_dotted_artist_initials_retry_with_compact_search_query(self) -> None:
        wrong_candidate = self._candidate("Honey", ["Vacations"])
        real_candidate = self._candidate("Honey", ["D.O.D"])
        responses = {
            'track:"Honey" artist:"D.O.D"': [wrong_candidate],
            'track:"honey" artist:"dod"': [real_candidate],
        }

        match = None
        matched_query = ""
        search_queries = self.matcher.build_search_queries("D.O.D", "Honey")
        for search_query in search_queries:
            candidate_match = self.matcher.match(
                "D.O.D",
                "Honey",
                responses.get(search_query, []),
                search_query,
            )
            if candidate_match is not None:
                match = candidate_match
                matched_query = search_query
                break

        self.assertIn('track:"honey" artist:"dod"', search_queries)
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "D.O.D")
        self.assertEqual(match.match_score, 1.0)
        self.assertEqual(matched_query, 'track:"honey" artist:"dod"')

    def test_ampersand_initialism_artist_matches_extended_mix(self) -> None:
        candidate = self._candidate("Live The Night - Extended Mix", ["W&W", "Hardwell", "Lil Jon"])

        match = self.matcher.match(
            "W&W",
            "Live the Night (Extended Mix)",
            [candidate],
            'track:"Live the Night" artist:"W&W"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_leading_article_title_variant_matches_same_artist(self) -> None:
        candidate = self._candidate("The Suburbs", ["Mr Little Jeans"])

        match = self.matcher.match(
            "Mr Little Jeans",
            "Suburbs",
            [candidate],
            'track:"Suburbs" artist:"Mr Little Jeans"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_single_letter_parenthetical_subtitle_matches_same_artist_without_original_title(self) -> None:
        candidate = self._candidate("Runaway (U & I)", ["Galantis"])

        match = self.matcher.match(
            "Galantis",
            "Runaway",
            [candidate],
            'track:"Runaway" artist:"Galantis"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_numeric_subtitle_does_not_match_plain_title_with_same_artist_and_feature(self) -> None:
        candidate = self._candidate("Collapse 2.0 (feat. Memorecks)", ["Zeds Dead", "Memorecks"])

        best_candidate = self.matcher.find_best_candidate(
            "Zeds Dead",
            "Collapse (feat. Memorecks)",
            [candidate],
            'track:"Collapse (feat. Memorecks)" artist:"Zeds Dead"',
            original_title="Zeds Dead - Collapse (feat. Memorecks)",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Zeds Dead",
                "Collapse (feat. Memorecks)",
                [candidate],
                'track:"Collapse (feat. Memorecks)" artist:"Zeds Dead"',
                original_title="Zeds Dead - Collapse (feat. Memorecks)",
            )
        )

    def test_plain_title_prefers_real_track_over_numeric_subtitle_variant(self) -> None:
        numeric_variant = self._candidate(
            "Collapse 2.0 (feat. Memorecks)",
            ["Zeds Dead", "Memorecks"],
        )
        real_track = self._candidate("Collapse", ["Zeds Dead", "Memorecks"])

        match = self.matcher.match(
            "Zeds Dead",
            "Collapse (feat. Memorecks)",
            [numeric_variant, real_track],
            'track:"Collapse (feat. Memorecks)" artist:"Zeds Dead"',
            original_title="Zeds Dead - Collapse (feat. Memorecks)",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, real_track["id"])
        self.assertEqual(match.match_score, 1.0)

    def test_inline_feature_title_with_accented_featured_artist_matches(self) -> None:
        candidate = self._candidate(
            "Smoke And Retribution feat. Vince Staples & Ku\u010dka",
            ["Flume", "Vince Staples", "Ku\u010dka"],
        )

        match = self.matcher.match(
            "Flume",
            "Smoke And Retribution feat. Vince Staples & Ku\u010dka",
            [candidate],
            'track:"Smoke And Retribution feat. Vince Staples & Ku\u010dka" artist:"Flume"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_name_with_club_does_not_trigger_title_side_version_recovery(self) -> None:
        candidate = self._candidate(
            "Wonder (feat. The Kite String Tangle)",
            ["Adventure Club", "The Kite String Tangle"],
        )

        match = self.matcher.match(
            "Adventure Club",
            "Wonder Feat. The Kite String Tangle",
            [candidate],
            'track:"Wonder Feat. The Kite String Tangle" artist:"Adventure Club"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_inline_feature_title_does_not_match_different_song_with_same_feature(self) -> None:
        candidate = self._candidate(
            "The Dark Room (feat. Vince Staples)",
            ["Dilated Peoples", "Vince Staples"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Flume",
            "Smoke And Retribution feat. Vince Staples & Ku\u010dka",
            [candidate],
            'track:"Smoke And Retribution feat. Vince Staples & Ku\u010dka" artist:"Flume"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Flume",
                "Smoke And Retribution feat. Vince Staples & Ku\u010dka",
                [candidate],
                'track:"Smoke And Retribution feat. Vince Staples & Ku\u010dka" artist:"Flume"',
            )
        )

    def test_x_collaboration_exact_title_matches_structured_spotify_artists(self) -> None:
        candidate = self._candidate("Flip", ["Bro Safari", "Boombox Cartel"])

        match = self.matcher.match(
            "Bro Safari X Boombox Cartel",
            "Flip",
            [candidate],
            'track:"Flip" artist:"Bro Safari X Boombox Cartel"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_multiply_symbol_collaboration_matches_structured_spotify_artists(self) -> None:
        candidate = self._candidate("Og Purp", ["Tha Trickaz", "Creaky Jackals"])

        match = self.matcher.match(
            "Tha Trickaz \u2716 Creaky Jackals",
            "OG Purp",
            [candidate],
            'track:"OG Purp" artist:"Tha Trickaz \u2716 Creaky Jackals"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_vip_title_with_apostrophe_matches_compact_spotify_title(self) -> None:
        candidate = self._candidate("VIPs", ["Skrillex", "MUST DIE!"])

        match = self.matcher.match(
            "Skrillex & MUST DIE!",
            "VIP's",
            [candidate],
            'track:"VIPs" artist:"Skrillex & MUST DIE!"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_mangled_multiply_symbol_collaboration_matches_structured_spotify_artists(self) -> None:
        candidate = self._candidate("Og Purp", ["Tha Trickaz", "Creaky Jackals"])

        match = self.matcher.match(
            "Tha Trickaz ? Creaky Jackals",
            "OG Purp",
            [candidate],
            'track:"OG Purp" artist:"Tha Trickaz ? Creaky Jackals"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_compact_spotify_title_matches_spaced_source_title_with_same_artists(self) -> None:
        candidate = self._candidate("Pushup", ["Enschway", "O5CAR"])

        match = self.matcher.match(
            "Enschway & O5CAR",
            "Push Up",
            [candidate],
            'track:"Push Up" artist:"Enschway & O5CAR"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_short_token_title_retries_with_compact_spotify_spelling(self) -> None:
        wrong_candidate = self._candidate("Push Up - Original Mix", ["Creeds"])
        real_candidate = self._candidate("Pushup", ["Enschway", "O5CAR"])
        responses = {
            'track:"Push Up" artist:"Enschway & O5CAR"': [wrong_candidate],
            'track:"pushup" artist:"Enschway & O5CAR"': [real_candidate],
        }

        match = None
        matched_query = ""
        search_queries = self.matcher.build_search_queries("Enschway & O5CAR", "Push Up")
        for search_query in search_queries:
            candidate_match = self.matcher.match(
                "Enschway & O5CAR",
                "Push Up",
                responses.get(search_query, []),
                search_query,
            )
            if candidate_match is not None:
                match = candidate_match
                matched_query = search_query
                break

        self.assertIn('track:"pushup" artist:"Enschway & O5CAR"', search_queries)
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "Enschway, O5CAR")
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertEqual(matched_query, 'track:"pushup" artist:"Enschway & O5CAR"')

    def test_title_by_artist_parse_matches_structured_spotify_artist(self) -> None:
        candidate = self._candidate("Dum Dee Dum", ["Keys N Krates"])

        match = self.matcher.match(
            "Keys N Krates",
            "Dum Dee Dum",
            [candidate],
            'track:"Dum Dee Dum" artist:"Keys N Krates"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_tight_dash_artist_title_parse_matches_featured_spotify_artist(self) -> None:
        candidate = self._candidate("No Heroes (feat. Luciana)", ["Firebeatz", "KSHMR", "Luciana"])

        match = self.matcher.match(
            "Firebeatz & KSHMR",
            "No Heroes (feat. Luciana)",
            [candidate],
            'track:"No Heroes (feat. Luciana)" artist:"Firebeatz & KSHMR"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_original_radio_mix_source_matches_real_title_and_rejects_shared_feature_wrong_title(self) -> None:
        wrong_candidate = self._candidate(
            "Perdoname (feat. DyCy & Adrian Delgado)",
            ["Deorro", "DyCy", "Adrian Delgado"],
        )
        real_candidate = self._candidate("Let Me Love You", ["Deorro", "Adrian Delgado"])
        original_title = (
            "Deorro Feat. Adrian Delgado - Let Me Love You "
            "(Original Radio Mix) Out May 20th"
        )

        wrong_best_candidate = self.matcher.find_best_candidate(
            "Deorro Feat. Adrian Delgado",
            "Let Me Love You",
            [wrong_candidate],
            'track:"Let Me Love You" artist:"Deorro Feat. Adrian Delgado"',
            original_title=original_title,
        )
        match = self.matcher.match(
            "Deorro Feat. Adrian Delgado",
            "Let Me Love You",
            [wrong_candidate, real_candidate],
            'track:"Let Me Love You" artist:"Deorro Feat. Adrian Delgado"',
            original_title=original_title,
        )

        self.assertIsNotNone(wrong_best_candidate)
        self.assertLess(wrong_best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "Deorro, Adrian Delgado")
        self.assertEqual(match.matched_song, "Let Me Love You")
        self.assertEqual(match.match_score, 1.0)

    def test_original_title_subtitle_can_match_spotify_dash_subtitle(self) -> None:
        candidate = self._candidate(
            "Tremor - Sensation 2014 Anthem",
            ["Dimitri Vegas & Like Mike", "Martin Garrix", "Dimitri Vegas"],
        )

        match = self.matcher.match(
            "Dimitri Vegas, Martin Garrix, Like Mike",
            "Tremor",
            [candidate],
            'track:"Tremor" artist:"Dimitri Vegas, Martin Garrix, Like Mike"',
            original_title=(
                "Dimitri Vegas, Martin Garrix, Like Mike - "
                "Tremor (Sensation 2014 Anthem) OUT NOW"
            ),
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_original_title_part_subtitle_can_match_spotify_dash_subtitle(self) -> None:
        candidate = self._candidate(
            "Red Light Green Light - For Club Play Only, Pt. 6",
            ["Duke Dumont", "Shaun Ross"],
        )

        match = self.matcher.match(
            "Duke Dumont",
            "Red Light Green Light",
            [candidate],
            'track:"Red Light Green Light" artist:"Duke Dumont"',
            original_title="Red Light Green Light (For Club Play Only, Pt. 6)",
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_leading_artist_index_marker_does_not_block_exact_match(self) -> None:
        candidate = self._candidate("I Want More", ["Getter"])

        match = self.matcher.match(
            "7. GETTER",
            "I WANT MORE",
            [candidate],
            'track:"I WANT MORE" artist:"7. GETTER"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_catalog_code_prefix_does_not_block_exact_match(self) -> None:
        candidate = self._candidate("Nigga Who", ["The Beatangers"])

        match = self.matcher.match(
            "CUFF008: The Beatangers",
            "Nigga Who",
            [candidate],
            'track:"Nigga Who" artist:"CUFF008: The Beatangers"',
            original_title="CUFF008: The Beatangers - Nigga Who (Original Mix) [CUFF]",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_liveset_title_does_not_match_same_artist_spotify_track(self) -> None:
        candidate = self._candidate(
            "Bailar (feat. Pitbull & Elvis Crespo)",
            ["Deorro", "Pitbull", "Elvis Crespo"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Deorro",
            "Deorro Live At SCMF In El Paso 2014",
            [candidate],
            'track:"Deorro Live At SCMF In El Paso 2014" artist:"Deorro"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertEqual(best_candidate.match_score, 0.0)
        self.assertIsNone(
            self.matcher.match(
                "Deorro",
                "Deorro Live At SCMF In El Paso 2014",
                [candidate],
                'track:"Deorro Live At SCMF In El Paso 2014" artist:"Deorro"',
            )
        )

    def test_plain_source_does_not_match_unrelated_same_artist_vip_track(self) -> None:
        candidate = self._candidate("Ripple VIP", ["Liquid Stranger"])

        best_candidate = self.matcher.find_best_candidate(
            "Liquid Stranger",
            "Party Like Us",
            [candidate],
            'track:"Party Like Us" artist:"Liquid Stranger"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Liquid Stranger",
                "Party Like Us",
                [candidate],
                'track:"Party Like Us" artist:"Liquid Stranger"',
            )
        )

    def test_wrong_remix_version_stays_below_match_threshold(self) -> None:
        candidate = self._candidate("A Bit Patchy - Eric Prydz Remix", ["Switch"])

        best_candidate = self.matcher.find_best_candidate(
            "Switch",
            "A Bit Patchy (Will Sparks Mix)",
            [candidate],
            'track:"A Bit Patchy (Will Sparks Mix)" artist:"Switch"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Switch",
                "A Bit Patchy (Will Sparks Mix)",
                [candidate],
                'track:"A Bit Patchy (Will Sparks Mix)" artist:"Switch"',
            )
        )

    def test_matching_remix_version_can_match(self) -> None:
        candidate = self._candidate("A Bit Patchy - Will Sparks Mix", ["Switch"])

        match = self.matcher.match(
            "Switch",
            "A Bit Patchy (Will Sparks Mix)",
            [candidate],
            'track:"A Bit Patchy (Will Sparks Mix)" artist:"Switch"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_festival_edit_source_matches_plain_artist_edit_candidate(self) -> None:
        candidate = self._candidate(
            "Jumpoff (Carnage Edit)",
            ["BL3R", "Andres Fresko", "Carnage"],
        )

        match = self.matcher.match(
            "Bl3r & Andres Fresko",
            "Jumpoff (Carnage Festival Edit)",
            [candidate],
            'track:"Jumpoff (Carnage Festival Edit)" artist:"Bl3r & Andres Fresko"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_festival_edit_selects_real_jumpoff_over_unrelated_jump_out(self) -> None:
        wrong_candidate = self._candidate("JUMP OUT", ["Excision", "Juelz"])
        real_candidate = self._candidate(
            "Jumpoff - Carnage Edit",
            ["BL3R", "Andres Fresko", "Carnage"],
        )

        wrong_best_candidate = self.matcher.find_best_candidate(
            "0 Bl3r & Andres Fresko",
            "Jumpoff (Carnage Festival Edit)",
            [wrong_candidate],
            'track:"Jumpoff (Carnage Festival Edit)" artist:"0 Bl3r & Andres Fresko"',
            original_title=(
                "Bl3r & Andres Fresko - Jumpoff (Carnage Festival Edit)"
                "[DROPS ON JAN 19TH. VIA SMASH THE HOUSE]"
            ),
        )
        match = self.matcher.match(
            "0 Bl3r & Andres Fresko",
            "Jumpoff (Carnage Festival Edit)",
            [wrong_candidate, real_candidate],
            'track:"Jumpoff (Carnage Festival Edit)" artist:"0 Bl3r & Andres Fresko"',
            original_title=(
                "Bl3r & Andres Fresko - Jumpoff (Carnage Festival Edit)"
                "[DROPS ON JAN 19TH. VIA SMASH THE HOUSE]"
            ),
        )

        self.assertIsNotNone(wrong_best_candidate)
        self.assertLess(wrong_best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNotNone(match)
        self.assertEqual(match.matched_artist, "BL3R, Andres Fresko, Carnage")
        self.assertEqual(match.matched_song, "Jumpoff - Carnage Edit")
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_clean_version_source_matches_regular_edit_candidate(self) -> None:
        candidate = self._candidate("BTSTU - Edit", ["Jai Paul"])

        match = self.matcher.match(
            "Jai Paul",
            "BTSTU (Edit Clean)",
            [candidate],
            'track:"BTSTU (Edit Clean)" artist:"Jai Paul"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_clean_spotify_candidate_is_not_selected_for_clean_source(self) -> None:
        clean_candidate = self._candidate("BTSTU - Edit Clean", ["Jai Paul"])
        regular_candidate = self._candidate("BTSTU - Edit", ["Jai Paul"])

        clean_best = self.matcher.find_best_candidate(
            "Jai Paul",
            "BTSTU (Edit Clean)",
            [clean_candidate],
            'track:"BTSTU (Edit Clean)" artist:"Jai Paul"',
        )
        match = self.matcher.match(
            "Jai Paul",
            "BTSTU (Edit Clean)",
            [clean_candidate, regular_candidate],
            'track:"BTSTU (Edit Clean)" artist:"Jai Paul"',
        )

        self.assertIsNotNone(clean_best)
        self.assertLess(clean_best.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, regular_candidate["id"])

    def test_hyphenated_remixer_suffix_can_match_same_remix(self) -> None:
        candidate = self._candidate("The Night Out - A-Trak Remix", ["Martin Solveig"])

        match = self.matcher.match(
            "Martin Solveig",
            "The Night Out (A-Trak Remix)",
            [candidate],
            'track:"The Night Out (A-Trak Remix)" artist:"Martin Solveig"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_spaced_hyphen_remixer_and_missing_subtitle_can_match_remix_edit(self) -> None:
        candidate = self._candidate(
            "Cry (Just a Little) - A-Trak and Phantoms Remix Edit",
            ["Bingo Players", "A-Trak", "Phantoms"],
        )

        match = self.matcher.match(
            "Bingo Players",
            "Cry (A - Trak And Phantoms Remix)",
            [candidate],
            'track:"Cry (A - Trak And Phantoms Remix)" artist:"Bingo Players"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_acronym_title_can_match_spotify_expanded_subtitle_remix(self) -> None:
        candidate = self._candidate(
            "TTU (Too Turnt Up) (feat. Waka Flocka Flame) - TroyBoi Remix",
            ["Flosstradamus", "Waka Flocka Flame", "TroyBoi"],
        )

        match = self.matcher.match(
            "Flosstradamus feat. Waka Flocka",
            "TTU (TroyBoi Remix)",
            [candidate],
            'track:"TTU (TroyBoi Remix)" artist:"Flosstradamus feat. Waka Flocka"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_with_collaborator_block_and_accented_artist_remix_matches(self) -> None:
        candidate = self._candidate(
            "Where Are Ü Now (with Justin Bieber) - Marshmello Remix",
            ["Jack Ü", "Skrillex", "Diplo", "Justin Bieber", "Marshmello"],
        )

        match = self.matcher.match(
            "Jack Ü",
            "Where Are Ü Now [Marshmello Remix]",
            [candidate],
            'track:"Where Are Ü Now [Marshmello Remix]" artist:"Jack Ü"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_source_artist_can_confirm_named_spotify_remix_when_source_title_is_plain(self) -> None:
        candidate = self._candidate(
            "Where Are \u00dc Now (with Justin Bieber) - Ember Island Remix",
            ["Jack \u00dc", "Skrillex", "Diplo", "Justin Bieber", "Ember Island"],
        )

        match = self.matcher.match(
            "ember island",
            "where are \u00fc now",
            [candidate],
            'track:"where are \u00fc now" artist:"ember island"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_bare_artist_remix_suffix_can_match_when_artist_is_structured_remixer(self) -> None:
        candidate = self._candidate("Fall in Love Moody Good Remix", ["Moody Good"])

        match = self.matcher.match(
            "Slum Village",
            "Fall In Love [Moody Good Remix]",
            [candidate],
            'track:"Fall In Love [Moody Good Remix]" artist:"Slum Village"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_version_base_can_ignore_parenthetical_subtitle_when_remix_matches(self) -> None:
        candidate = self._candidate(
            "Exostomp (Jump Up High) - DISKORD Remix",
            ["Flux Pavilion", "Diskord"],
        )

        match = self.matcher.match(
            "Flux Pavilion",
            "Exostomp [DISKORD Remix]",
            [candidate],
            'track:"Exostomp [DISKORD Remix]" artist:"Flux Pavilion"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_version_base_strips_accidental_leading_artist_prefix(self) -> None:
        candidate = self._candidate(
            "Going Gorillas - Doctor P's Bananas Remix",
            ["Doctor P"],
        )

        match = self.matcher.match(
            "Doctor P",
            "Doctor P 'Going Gorillas' (Doctor P's Bananas Remix)",
            [candidate],
            'track:"Doctor P Going Gorillas" artist:"Doctor P"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_version_base_strips_leading_spotify_artist_prefix_from_source_title(self) -> None:
        candidate = self._candidate(
            "Levels - Skrillex Remix",
            ["Avicii", "Skrillex"],
        )

        match = self.matcher.match(
            "Skrillex",
            "Avicii 'Levels' Skrillex Remix",
            [candidate],
            'track:"Avicii Levels Skrillex Remix" artist:"Skrillex"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_short_title_does_not_match_longer_title_with_same_remix_artist(self) -> None:
        candidate = self._candidate("Go Deep - TroyBoi Remix", ["Flosstradamus", "TroyBoi"])

        best_candidate = self.matcher.find_best_candidate(
            "Flosstradamus",
            "Go (TroyBoi Remix)",
            [candidate],
            'track:"Go (TroyBoi Remix)" artist:"Flosstradamus"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_one_word_title_does_not_match_longer_unrelated_title_with_partial_artist_overlap(self) -> None:
        candidate = self._candidate("Jack Me", ["Shear Gen1us", "G-Buck"])

        best_candidate = self.matcher.find_best_candidate(
            "G-Buck & Twine",
            "JACK",
            [candidate],
            'track:"JACK" artist:"G-Buck & Twine"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "G-Buck & Twine",
                "JACK",
                [candidate],
                'track:"JACK" artist:"G-Buck & Twine"',
            )
        )

    def test_dotted_title_and_matching_remix_suffix_can_match(self) -> None:
        candidate = self._candidate(
            "S.W.A.T Team - Reece Low Remix",
            ["Chardy", "Kronic", "Reece Low"],
        )

        match = self.matcher.match(
            "Chardy & Kronic",
            "S.W.A.T. Team (Reece Low Remix)",
            [candidate],
            'track:"S.W.A.T. Team (Reece Low Remix)" artist:"Chardy & Kronic"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_trailing_vip_source_title_matches_named_vip_spotify_suffix(self) -> None:
        candidate = self._candidate(
            "King is Back - Snails & Ghastly VIP",
            ["SNAILS", "Big Ali", "Snails & Ghastly"],
        )

        match = self.matcher.match(
            "SNAILS",
            "King is Back VIP",
            [candidate],
            'track:"King is Back VIP" artist:"SNAILS"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_plain_source_title_does_not_match_candidate_vip_version(self) -> None:
        candidate = self._candidate("Lavender Town VIP", ["G Jones"])

        best_candidate = self.matcher.find_best_candidate(
            "G JONES",
            "Lavender Town",
            [candidate],
            'track:"Lavender Town" artist:"G JONES"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "G JONES",
                "Lavender Town",
                [candidate],
                'track:"Lavender Town" artist:"G JONES"',
            )
        )

    def test_original_title_recrank_context_blocks_plain_spotify_original(self) -> None:
        candidate = self._candidate("Weekends!!! (feat. Sirah)", ["Skrillex", "Sirah"])
        original_title = "Skrillex ft. Sirah - Weekends (Crankdat Re-Crank) \u2699"

        best_candidate = self.matcher.find_best_candidate(
            "Skrillex ft. Sirah",
            "Weekends \u2699",
            [candidate],
            'track:"Weekends" artist:"Skrillex ft. Sirah"',
            original_title=original_title,
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Skrillex ft. Sirah",
                "Weekends \u2699",
                [candidate],
                'track:"Weekends" artist:"Skrillex ft. Sirah"',
                original_title=original_title,
            )
        )

    def test_source_vip_version_does_not_match_plain_candidate_original(self) -> None:
        candidate = self._candidate("Deep Down Low", ["Valentino Kha"])

        best_candidate = self.matcher.find_best_candidate(
            "Valentino Khan",
            "Deep Down Low (VIP)",
            [candidate],
            'track:"Deep Down Low (VIP)" artist:"Valentino Khan"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Valentino Khan",
                "Deep Down Low (VIP)",
                [candidate],
                'track:"Deep Down Low (VIP)" artist:"Valentino Khan"',
            )
        )

    def test_source_vip_with_feature_does_not_match_plain_candidate_original(self) -> None:
        candidate = self._candidate("Just Us", ["Ephwurd", "Liinks"])

        best_candidate = self.matcher.find_best_candidate(
            "Ephwurd",
            "Just Us Feat. Liinks (VIP)",
            [candidate],
            'track:"Just Us Feat. Liinks (VIP)" artist:"Ephwurd"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Ephwurd",
                "Just Us Feat. Liinks (VIP)",
                [candidate],
                'track:"Just Us Feat. Liinks (VIP)" artist:"Ephwurd"',
            )
        )

    def test_extra_source_vip_layer_does_not_match_base_spotify_remix(self) -> None:
        candidate = self._candidate(
            "The End - Carnage & Breaux Remix",
            ["Eptic", "Carnage", "Breaux"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Eptic",
            "The End (Carnage & Breaux Remix) [Crankdat VIP]",
            [candidate],
            'track:"The End (Carnage & Breaux Remix) [Crankdat VIP]" artist:"Eptic"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Eptic",
                "The End (Carnage & Breaux Remix) [Crankdat VIP]",
                [candidate],
                'track:"The End (Carnage & Breaux Remix) [Crankdat VIP]" artist:"Eptic"',
            )
        )

    def test_extra_source_flip_layer_does_not_match_base_spotify_remix(self) -> None:
        candidate = self._candidate(
            "The Dopest - Cesqeaux Remix",
            ["Moksi", "Cesqeaux"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Moksi",
            "The Dopest (Cesqeaux Remix) [Boombox Cartel Flip]",
            [candidate],
            'track:"The Dopest (Cesqeaux Remix) [Boombox Cartel Flip]" artist:"Moksi"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Moksi",
                "The Dopest (Cesqeaux Remix) [Boombox Cartel Flip]",
                [candidate],
                'track:"The Dopest (Cesqeaux Remix) [Boombox Cartel Flip]" artist:"Moksi"',
            )
        )

    def test_reremix_source_does_not_match_different_base_spotify_remix(self) -> None:
        candidate = self._candidate(
            "Some Chords - Dillon Francis Remix",
            ["deadmau5", "Dillon Francis"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Deadmau5 X Dillon Francis",
            "Some Chords (Jauz ReRemix)",
            [candidate],
            'track:"Some Chords" artist:"Deadmau5 X Dillon Francis"',
            original_title="Deadmau5 X Dillon Francis - Some Chords (Jauz ReRemix)",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Deadmau5 X Dillon Francis",
                "Some Chords (Jauz ReRemix)",
                [candidate],
                'track:"Some Chords" artist:"Deadmau5 X Dillon Francis"',
                original_title="Deadmau5 X Dillon Francis - Some Chords (Jauz ReRemix)",
            )
        )

    def test_leading_artist_prefix_with_weak_uploader_can_match_vip_title(self) -> None:
        candidate = self._candidate("Warm Ups - VIP", ["Virtual Riot"])

        match = self.matcher.match(
            "Vh",
            "Virtual Riot Warm Ups VIP",
            [candidate],
            'track:"Virtual Riot Warm Ups VIP" artist:"Vh"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_leading_artist_segment_with_weak_uploader_can_match_vip_mix_title(self) -> None:
        candidate = self._candidate("Snake Bite - VIP Mix", ["Eliminate"])

        match = self.matcher.match(
            "Pantheon: Anarchy",
            "Eliminate - Snake Bite VIP",
            [candidate],
            'track:"Eliminate - Snake Bite VIP" artist:"Pantheon: Anarchy"',
            artist_source="Uploader Fallback",
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_source_title_artist_prefix_can_match_named_vip_spotify_suffix(self) -> None:
        candidate = self._candidate(
            "The Blastaz - Barely Alive VIP",
            ["BARELY ALIVE", "Datsik"],
        )

        match = self.matcher.match(
            "BARELY ALIVE",
            "Datsik & Barely Alive - The Blastaz VIP",
            [candidate],
            'track:"Datsik & Barely Alive - The Blastaz VIP" artist:"BARELY ALIVE"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_named_flip_source_does_not_match_plain_original(self) -> None:
        candidate = self._candidate("Dat $tick", ["Rich Brian"])

        best_candidate = self.matcher.find_best_candidate(
            "Rich Chigga",
            "Dat $tick (FAWKS FLIP)",
            [candidate],
            'track:"Dat $tick (FAWKS FLIP)" artist:"Rich Chigga"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Rich Chigga",
                "Dat $tick (FAWKS FLIP)",
                [candidate],
                'track:"Dat $tick (FAWKS FLIP)" artist:"Rich Chigga"',
            )
        )

    def test_generic_source_remix_does_not_match_different_named_spotify_remix(self) -> None:
        candidate = self._candidate(
            "Go Deep - Timbaland/Missy Remix",
            ["Janet Jackson", "Missy Elliott", "Timbaland"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Tchami x Janet Jackson",
            "Go Deep (remix)",
            [candidate],
            'track:"Go Deep (remix)" artist:"Tchami x Janet Jackson"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Tchami x Janet Jackson",
                "Go Deep (remix)",
                [candidate],
                'track:"Go Deep (remix)" artist:"Tchami x Janet Jackson"',
            )
        )

    def test_matching_named_spotify_remix_can_match_generic_source_remix_artist(self) -> None:
        candidate = self._candidate("Go Deep - Tchami Remix", ["Janet Jackson", "Tchami"])

        match = self.matcher.match(
            "Tchami x Janet Jackson",
            "Go Deep (remix)",
            [candidate],
            'track:"Go Deep (remix)" artist:"Tchami x Janet Jackson"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_matching_remixer_does_not_override_different_base_title(self) -> None:
        candidate = self._candidate(
            "Animal - Louis The Child Remix",
            ["Louis The Child", "Goose"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Oh Wonder",
            "Body Gold (Louis The Child Remix)",
            [candidate],
            'track:"Body Gold (Louis The Child Remix)" artist:"Oh Wonder"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Oh Wonder",
                "Body Gold (Louis The Child Remix)",
                [candidate],
                'track:"Body Gold (Louis The Child Remix)" artist:"Oh Wonder"',
            )
        )

    def test_matching_remixer_can_match_same_base_title(self) -> None:
        candidate = self._candidate(
            "Body Gold - Louis The Child Remix",
            ["Oh Wonder", "Louis The Child"],
        )

        match = self.matcher.match(
            "Oh Wonder",
            "Body Gold (Louis The Child Remix)",
            [candidate],
            'track:"Body Gold (Louis The Child Remix)" artist:"Oh Wonder"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_remixer_artist_and_title_alone_cannot_match_different_base_title(self) -> None:
        candidate = self._candidate("Animal House", ["Animal House"])

        best_candidate = self.matcher.find_best_candidate(
            "Animal H\u00d6use",
            "Crush On You (Animal H\u00d6use Remix)",
            [candidate],
            'track:"Crush On You (Animal H\u00d6use Remix)" artist:"Animal H\u00d6use"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Animal H\u00d6use",
                "Crush On You (Animal H\u00d6use Remix)",
                [candidate],
                'track:"Crush On You (Animal H\u00d6use Remix)" artist:"Animal H\u00d6use"',
            )
        )

    def test_duplicated_remixer_title_can_match_when_source_remix_identity_matches(self) -> None:
        candidate = self._candidate(
            "Nom De Strip Remix - Nom De Strip Remix",
            ["deadmau5", "Nom De Strip"],
        )

        match = self.matcher.match(
            "deadmau5",
            "Reward Is Cheese (Nom De Strip Remix)",
            [candidate],
            'track:"Reward Is Cheese (Nom De Strip Remix)" artist:"deadmau5"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_version_only_storefront_title_can_match_when_artists_and_version_agree(self) -> None:
        candidate = self._candidate(
            "Nom De Strip Edit - Nom De Strip Remix",
            ["Nom De Strip", "Bart B More"],
        )

        match = self.matcher.match(
            "Bart B More",
            "Cowbell (Nom De Strip Edit)",
            [candidate],
            'track:"Cowbell (Nom De Strip Edit)" artist:"Bart B More"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_duplicated_remixer_title_still_rejects_different_remixer_identity(self) -> None:
        candidate = self._candidate(
            "Nom De Strip Remix - Nom De Strip Remix",
            ["deadmau5", "Nom De Strip"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "deadmau5",
            "Reward Is Cheese (Madeon Remix)",
            [candidate],
            'track:"Reward Is Cheese (Madeon Remix)" artist:"deadmau5"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "deadmau5",
                "Reward Is Cheese (Madeon Remix)",
                [candidate],
                'track:"Reward Is Cheese (Madeon Remix)" artist:"deadmau5"',
            )
        )

    def test_compact_base_title_spacing_can_match_same_remix(self) -> None:
        candidate = self._candidate(
            "Badman - Skrillex Remix",
            ["The Ragga Twins", "Skrillex"],
        )

        match = self.matcher.match(
            "Ragga Twins",
            "Bad Man (Skrillex Remix)",
            [candidate],
            'track:"Bad Man (Skrillex Remix)" artist:"Ragga Twins"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_shared_remixer_and_artist_does_not_match_different_base_title(self) -> None:
        candidate = self._candidate(
            "Ragga Bomb (with Ragga Twins)",
            ["Skrillex", "Ragga Twins"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Ragga Twins",
            "Bad Man (Skrillex Remix)",
            [candidate],
            'track:"Bad Man (Skrillex Remix)" artist:"Ragga Twins"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Ragga Twins",
                "Bad Man (Skrillex Remix)",
                [candidate],
                'track:"Bad Man (Skrillex Remix)" artist:"Ragga Twins"',
            )
        )

    def test_bracketed_with_collaborator_does_not_block_same_remix_match(self) -> None:
        candidate = self._candidate(
            "Ragga Bomb (with Ragga Twins) - Skrillex & Zomboy Remix",
            ["Skrillex", "Ragga Twins", "Zomboy"],
        )

        match = self.matcher.match(
            "Skrillex",
            "Ragga Bomb (Skrillex & Zomboy Remix)",
            [candidate],
            'track:"Ragga Bomb (Skrillex & Zomboy Remix)" artist:"Skrillex"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_bracketed_with_collaborators_and_commas_does_not_block_same_remix_match(self) -> None:
        candidate = self._candidate(
            "Dirty Vibe (with Diplo, G-Dragon, and CL) - Habstrakt Remix",
            ["Skrillex", "CL", "Diplo", "Habstrakt"],
        )

        match = self.matcher.match(
            "Skrillex",
            "Dirty Vibe (Habstrakt Remix)",
            [candidate],
            'track:"Dirty Vibe (Habstrakt Remix)" artist:"Skrillex"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_remix_with_missing_source_subtitle_can_match_spotify_subtitle(self) -> None:
        candidate = self._candidate(
            "Open Your Eyes (Revelation) - Psychic Type Remix",
            ["Disco Fries", "Psychic Type"],
        )

        match = self.matcher.match(
            "The Disco Fries",
            "Open Your Eyes [Psychic Type Remix]",
            [candidate],
            'track:"Open Your Eyes [Psychic Type Remix]" artist:"The Disco Fries"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_remix_with_missing_bumaye_subtitle_can_match_spotify_subtitle(self) -> None:
        candidate = self._candidate(
            "Watch Out For This (Bumaye) (Dimitri Vegas & Like Mike Tomorrowland Remix)",
            [
                "Major Lazer",
                "Busy Signal",
                "The Flexican",
                "FS Green",
                "Dimitri Vegas",
                "Like Mike",
            ],
        )

        match = self.matcher.match(
            "Major Lazer",
            "Watch Out For This (Dimitri Vegas & Like Mike Tomorrowland Remix)",
            [candidate],
            'track:"Watch Out For This (Dimitri Vegas & Like Mike Tomorrowland Remix)" artist:"Major Lazer"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_remix_feature_block_matches_same_base_title_remix(self) -> None:
        wrong_candidate = self._candidate("Low Life (feat. The Weeknd)", ["Future", "The Weeknd"])
        remix = self._candidate(
            "Or Nah (feat. The Weeknd, Wiz Khalifa & DJ Mustard) [Remix]",
            ["Ty Dolla $ign", "The Weeknd"],
        )

        match = self.matcher.match(
            "The Weeknd",
            "Or Nah (Remix Feat. The Weeknd)",
            [wrong_candidate, remix],
            'track:"Or Nah (Remix Feat. The Weeknd)" artist:"The Weeknd"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, remix["id"])
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_remix_feature_block_does_not_match_different_base_title_feature(self) -> None:
        candidate = self._candidate("Low Life (feat. The Weeknd)", ["Future", "The Weeknd"])

        best_candidate = self.matcher.find_best_candidate(
            "The Weeknd",
            "Or Nah (Remix Feat. The Weeknd)",
            [candidate],
            'track:"Or Nah (Remix Feat. The Weeknd)" artist:"The Weeknd"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "The Weeknd",
                "Or Nah (Remix Feat. The Weeknd)",
                [candidate],
                'track:"Or Nah (Remix Feat. The Weeknd)" artist:"The Weeknd"',
            )
        )

    def test_gta_remix_matches_good_times_ahead_artist_rename(self) -> None:
        candidate = self._candidate(
            "6th Gear (feat. Kstylis) - GTA Remix",
            ["Alvaro", "Diplo", "Good Times Ahead", "Kstylis"],
        )

        match = self.matcher.match(
            "Diplo & Alvaro",
            "6th Gear (GTA Remix)",
            [candidate],
            'track:"6th Gear (GTA Remix)" artist:"Diplo & Alvaro"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_gta_source_artist_does_not_match_unrelated_track_named_gta(self) -> None:
        candidate = self._candidate("GTA", ["Future", "Metro Boomin"])

        normal_best = self.matcher.find_best_candidate(
            "GTA",
            "The Crowd (Ookay Remix)",
            [candidate],
            'track:"The Crowd (Ookay Remix)" artist:"GTA"',
        )
        swapped_best = self.matcher.find_best_candidate(
            "The Crowd (Ookay Remix)",
            "GTA",
            [candidate],
            'track:"GTA" artist:"The Crowd (Ookay Remix)"',
        )

        self.assertIsNotNone(normal_best)
        self.assertEqual(normal_best.match_score, 0.0)
        self.assertIsNotNone(swapped_best)
        self.assertLess(swapped_best.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "GTA",
                "The Crowd (Ookay Remix)",
                [candidate],
                'track:"The Crowd (Ookay Remix)" artist:"GTA"',
            )
        )
        self.assertIsNone(
            self.matcher.match_swapped_orientation(
                "GTA",
                "The Crowd (Ookay Remix)",
                [candidate],
                'track:"GTA" artist:"The Crowd (Ookay Remix)"',
            )
        )

    def test_x_collaboration_and_feature_apostrophe_match_spotify_formatting(self) -> None:
        candidate = self._candidate(
            "Crank It (feat. Lil' Jon)",
            ["Ghastly", "Mija", "Lil Jon"],
        )

        match = self.matcher.match(
            "Ghastly X Mija",
            "Crank It Ft. Lil Jon",
            [candidate],
            'track:"Crank It Ft. Lil Jon" artist:"Ghastly X Mija"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_good_times_ahead_remix_matches_gta_source_alias(self) -> None:
        candidate = self._candidate(
            "6th Gear (feat. Kstylis) - Good Times Ahead Remix",
            ["Alvaro", "Diplo", "Good Times Ahead", "Kstylis"],
        )

        match = self.matcher.match(
            "Diplo & Alvaro",
            "6th Gear (GTA Remix)",
            [candidate],
            'track:"6th Gear (GTA Remix)" artist:"Diplo & Alvaro"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_trailing_official_artist_decoration_does_not_block_exact_match(self) -> None:
        candidate = self._candidate("The Leaves Are Brown", ["Gameface Official", "Hucci"])

        match = self.matcher.match(
            "Hucci & GameFace",
            "The Leaves Are Brown",
            [candidate],
            'track:"The Leaves Are Brown" artist:"Hucci & GameFace"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_artist_alias_matches_teed_to_totally_enormous_extinct_dinosaurs(self) -> None:
        candidate = self._candidate("Without You", ["Dillon Francis", "TEED"])

        match = self.matcher.match(
            "Dillon Francis",
            "Without You Feat. Totally Enormous Extinct Dinosaurs",
            [candidate],
            'track:"Without You" artist:"Dillon Francis"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_artist_alias_matches_gordo_to_carnage(self) -> None:
        candidate = self._candidate("Example Track", ["Carnage"])

        match = self.matcher.match(
            "GORDO",
            "Example Track",
            [candidate],
            'track:"Example Track" artist:"GORDO"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_artist_alias_matches_clammyclams_to_clams_casino(self) -> None:
        candidate = self._candidate("Example Track", ["Clams Casino"])

        match = self.matcher.match(
            "clammyclams",
            "Example Track",
            [candidate],
            'track:"Example Track" artist:"clammyclams"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_artist_alias_matches_cookie_monsta_account_name(self) -> None:
        candidate = self._candidate("Soundboy", ["Cookie Monsta"])

        match = self.matcher.match(
            "cookiemonstatc",
            "Soundboy",
            [candidate],
            'track:"Soundboy" artist:"cookiemonstatc"',
            original_title="Soundboy",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_fuckmylife_to_deadmau5(self) -> None:
        candidate = self._candidate("Example Track", ["deadmau5"])

        match = self.matcher.match(
            "fuckmylife",
            "Example Track",
            [candidate],
            'track:"Example Track" artist:"fuckmylife"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_artist_alias_matches_spag_heddy_to_spag(self) -> None:
        candidate = self._candidate("Oh My!", ["SPAG"])

        match = self.matcher.match(
            "Spag Heddy",
            "Oh My!",
            [candidate],
            'track:"Oh My!" artist:"Spag Heddy"',
            original_title="Spag Heddy - Oh My!",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_blocked_fuckmylife_beneath_with_me_release_stays_unmatched(self) -> None:
        candidate = self._candidate(
            "Beneath with Me (feat. Skylar Grey)",
            ["Kaskade", "deadmau5", "Skylar Grey"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "fuckmylife",
            "beneath with me",
            [candidate],
            'track:"beneath with me" artist:"fuckmylife"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertEqual(best_candidate.match_score, 0.0)
        self.assertIsNone(
            self.matcher.match(
                "fuckmylife",
                "beneath with me",
                [candidate],
                'track:"beneath with me" artist:"fuckmylife"',
            )
        )

    def test_blocked_spotify_track_id_stays_unmatched(self) -> None:
        original_blocked_ids = SpotifyTrackMatcher.BLOCKED_SPOTIFY_TRACK_IDS
        SpotifyTrackMatcher.BLOCKED_SPOTIFY_TRACK_IDS = {"blocked-track-id"}
        try:
            candidate = self._candidate("Example Track", ["deadmau5"])
            candidate["id"] = "blocked-track-id"

            best_candidate = self.matcher.find_best_candidate(
                "deadmau5",
                "Example Track",
                [candidate],
                'track:"Example Track" artist:"deadmau5"',
            )

            self.assertIsNotNone(best_candidate)
            self.assertEqual(best_candidate.match_score, 0.0)
            self.assertIsNone(
                self.matcher.match(
                    "deadmau5",
                    "Example Track",
                    [candidate],
                    'track:"Example Track" artist:"deadmau5"',
                )
            )
        finally:
            SpotifyTrackMatcher.BLOCKED_SPOTIFY_TRACK_IDS = original_blocked_ids

    def test_artist_alias_matches_compact_dillonfrancis_to_dillon_francis(self) -> None:
        candidate = self._candidate(
            "Anywhere (feat. Will Heard)",
            ["Dillon Francis", "Will Heard"],
        )

        match = self.matcher.match(
            "DILLONFRANCIS",
            "Anywhere (feat. Will Heard)",
            [candidate],
            'track:"Anywhere (feat. Will Heard)" artist:"DILLONFRANCIS"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_fettywap1738_to_fetty_wap(self) -> None:
        candidate = self._candidate("Trap Queen", ["Fetty Wap"])

        match = self.matcher.match(
            "FettyWap1738",
            "Trap Queen",
            [candidate],
            'track:"Trap Queen" artist:"FettyWap1738"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_whoismgmt_to_mgmt(self) -> None:
        candidate = self._candidate("Congratulations", ["MGMT"])

        match = self.matcher.match(
            "whoismgmt",
            "Congratulations",
            [candidate],
            'track:"Congratulations" artist:"whoismgmt"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_mercer_to_dj_mercer(self) -> None:
        candidate = self._candidate("Encore", ["DJ MERCER"])

        match = self.matcher.match(
            "MERCER",
            "Encore",
            [candidate],
            'track:"Encore" artist:"MERCER"',
            original_title="MERCER - Encore (Original Mix)[OUT NOW]",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_diskord_email_to_diskord(self) -> None:
        candidate = self._candidate("Out There", ["Diskord"])

        match = self.matcher.match(
            "diskorduk@gmail.com",
            "Out There",
            [candidate],
            'track:"Out There" artist:"diskorduk@gmail.com"',
            original_title="Out There (Circus Records)",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_funtcaseuk_to_funtcase_with_featured_artist(self) -> None:
        candidate = self._candidate("4 Barz of Fury", ["FuntCase", "Merky ACE"])

        match = self.matcher.match(
            "FuntCaseUK",
            "4 Barz of Fury feat. Merky Ace",
            [candidate],
            'track:"4 Barz of Fury feat. Merky Ace" artist:"FuntCaseUK"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_rich_chigga_to_rich_brian_with_embedded_title_prefix(self) -> None:
        candidate = self._candidate("Who That Be", ["Rich Brian"])

        match = self.matcher.match(
            "Rich Chigga",
            "Rich Chigga - Who That Be (prod. Sihk)",
            [candidate],
            'track:"Rich Chigga - Who That Be" artist:"Rich Chigga"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_compact_dillonfrancis_source_does_not_match_same_title_wrong_artist(self) -> None:
        candidate = self._candidate("Anywhere", ["112"])

        best_candidate = self.matcher.find_best_candidate(
            "DILLONFRANCIS",
            "Anywhere (feat. Will Heard)",
            [candidate],
            'track:"Anywhere (feat. Will Heard)" artist:"DILLONFRANCIS"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "DILLONFRANCIS",
                "Anywhere (feat. Will Heard)",
                [candidate],
                'track:"Anywhere (feat. Will Heard)" artist:"DILLONFRANCIS"',
            )
        )

    def test_generic_unnamed_remix_source_can_match_plain_catalog_title_with_same_contributors(self) -> None:
        candidate = self._candidate("Weekend Millionaires", ["Skizzy Mars", "Katelyn Tarver"])

        match = self.matcher.match(
            "Skizzy Mars",
            "Weekend Millionaires (Remix) ft. Katelyn Tarver",
            [candidate],
            'track:"Weekend Millionaires (Remix) ft. Katelyn Tarver" artist:"Skizzy Mars"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_named_remix_source_can_match_plain_catalog_title_with_remixer_artist(self) -> None:
        candidate = self._candidate("Flash Funk", ["League of Legends", "Marshmello"])

        match = self.matcher.match(
            "League of Legends",
            "Flash Funk (Marshmello Remix)",
            [candidate],
            'track:"Flash Funk (Marshmello Remix)" artist:"League of Legends"',
            original_title="Flash Funk (Marshmello Remix)",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_artist_alias_matches_justin_blau_to_3lau_with_featured_artist(self) -> None:
        candidate = self._candidate("How You Love Me", ["3LAU", "Bright Lights"])

        match = self.matcher.match(
            "Justin Blau",
            "How You Love Me (feat. Bright Lights)",
            [candidate],
            'track:"How You Love Me (feat. Bright Lights)" artist:"Justin Blau"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_teed_alias_case_still_rejects_unrelated_candidate(self) -> None:
        candidate = self._candidate("Pillow Talking (feat. Brain)", ["Lil Dicky", "Brain"])

        best_candidate = self.matcher.find_best_candidate(
            "Dillon Francis",
            "Without You Feat. Totally Enormous Extinct Dinosaurs",
            [candidate],
            'track:"Without You" artist:"Dillon Francis"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Dillon Francis",
                "Without You Feat. Totally Enormous Extinct Dinosaurs",
                [candidate],
                'track:"Without You" artist:"Dillon Francis"',
            )
        )

    def test_rebirth_version_does_not_match_plain_original(self) -> None:
        candidate = self._candidate("Drunk All The Time", ["Dillon Francis", "Simon Lord"])

        best_candidate = self.matcher.find_best_candidate(
            "Dillon Francis",
            "Drunk All The Time (The Rebirth)",
            [candidate],
            'track:"Drunk All The Time (The Rebirth)" artist:"Dillon Francis"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Dillon Francis",
                "Drunk All The Time (The Rebirth)",
                [candidate],
                'track:"Drunk All The Time (The Rebirth)" artist:"Dillon Francis"',
            )
        )

    def test_original_title_rebirth_context_rejects_plain_original_after_parser_strips_version(self) -> None:
        candidate = self._candidate("Drunk All The Time", ["Dillon Francis", "Simon Lord"])

        best_candidate = self.matcher.find_best_candidate(
            "Dillon Francis",
            "Drunk All The Time",
            [candidate],
            'track:"Drunk All The Time" artist:"Dillon Francis"',
            original_title="Dillon Francis - Drunk All The Time (The Rebirth) [feat. Simon Lord]",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Dillon Francis",
                "Drunk All The Time",
                [candidate],
                'track:"Drunk All The Time" artist:"Dillon Francis"',
                original_title="Dillon Francis - Drunk All The Time (The Rebirth) [feat. Simon Lord]",
            )
        )

    def test_original_title_unreleased_verses_context_rejects_plain_original(self) -> None:
        candidate = self._candidate("sdp interlude", ["Travis Scott"])
        original_title = "Travis Scott - SDP Interlude (Unreleased Verses)"

        best_candidate = self.matcher.find_best_candidate(
            "Travis Scott",
            "SDP Interlude",
            [candidate],
            'track:"SDP Interlude" artist:"Travis Scott"',
            original_title=original_title,
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Travis Scott",
                "SDP Interlude",
                [candidate],
                'track:"SDP Interlude" artist:"Travis Scott"',
                original_title=original_title,
            )
        )

    def test_original_title_named_club_context_rejects_plain_original_after_parser_strips_version(self) -> None:
        candidate = self._candidate("Daddy", ["Emeli Sand\u00e9", "Naughty Boy"])

        best_candidate = self.matcher.find_best_candidate(
            "Emeli Sand\u00e9 Feat. Naughty Boy",
            "Daddy",
            [candidate],
            'track:"Daddy" artist:"Emeli Sand\u00e9 Feat. Naughty Boy"',
            original_title="Emeli Sand\u00e9 Feat. Naughty Boy - Daddy (LA Riots Club)",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Emeli Sand\u00e9 Feat. Naughty Boy",
                "Daddy",
                [candidate],
                'track:"Daddy" artist:"Emeli Sand\u00e9 Feat. Naughty Boy"',
                original_title="Emeli Sand\u00e9 Feat. Naughty Boy - Daddy (LA Riots Club)",
            )
        )

    def test_original_title_named_version_context_rejects_plain_original_after_parser_strips_version(self) -> None:
        candidate = self._candidate("Nigga Who", ["The Beatangers"])

        best_candidate = self.matcher.find_best_candidate(
            "The Beatangers",
            "Nigga Who",
            [candidate],
            'track:"Nigga Who" artist:"The Beatangers"',
            original_title="The Beatangers - Nigga Who [ svd.vcid Version ]",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "The Beatangers",
                "Nigga Who",
                [candidate],
                'track:"Nigga Who" artist:"The Beatangers"',
                original_title="The Beatangers - Nigga Who [ svd.vcid Version ]",
            )
        )

    def test_title_side_remix_does_not_match_unrelated_featured_artist_song(self) -> None:
        candidate = self._candidate(
            "FRANCHISE (feat. Young Thug & M.I.A.)",
            ["Travis Scott", "Young Thug", "M.I.A."],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Skyfall (RL Grime & Salva Remix)",
            "Travi$ Scott (Ft. Young Thug)",
            [candidate],
            'track:"Travi$ Scott (Ft. Young Thug)" artist:"Skyfall (RL Grime & Salva Remix)"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Skyfall (RL Grime & Salva Remix)",
                "Travi$ Scott (Ft. Young Thug)",
                [candidate],
                'track:"Travi$ Scott (Ft. Young Thug)" artist:"Skyfall (RL Grime & Salva Remix)"',
            )
        )

    def test_title_side_remix_does_not_match_plain_original_song(self) -> None:
        candidate = self._candidate(
            "Skyfall (feat. Young Thug)",
            ["Travis Scott", "Young Thug"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Skyfall (RL Grime & Salva Remix)",
            "Travi$ Scott (Ft. Young Thug)",
            [candidate],
            'track:"Travi$ Scott (Ft. Young Thug)" artist:"Skyfall (RL Grime & Salva Remix)"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Skyfall (RL Grime & Salva Remix)",
                "Travi$ Scott (Ft. Young Thug)",
                [candidate],
                'track:"Travi$ Scott (Ft. Young Thug)" artist:"Skyfall (RL Grime & Salva Remix)"',
            )
        )

    def test_title_side_remix_can_match_candidate_with_same_remix_identity(self) -> None:
        candidate = self._candidate(
            "Skyfall - RL Grime & Salva Remix",
            ["Travis Scott", "Young Thug", "RL Grime", "Salva"],
        )

        match = self.matcher.match(
            "Skyfall (RL Grime & Salva Remix)",
            "Travi$ Scott (Ft. Young Thug)",
            [candidate],
            'track:"Travi$ Scott (Ft. Young Thug)" artist:"Skyfall (RL Grime & Salva Remix)"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_plain_drunk_all_the_time_still_matches_original(self) -> None:
        candidate = self._candidate("Drunk All The Time", ["Dillon Francis", "Simon Lord"])

        match = self.matcher.match(
            "Dillon Francis",
            "Drunk All The Time (feat. Simon Lord)",
            [candidate],
            'track:"Drunk All The Time (feat. Simon Lord)" artist:"Dillon Francis"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_uploader_fallback_feature_title_does_not_match_original_missing_uploader(self) -> None:
        candidate = self._candidate("Mosh Pit (feat. Casino)", ["Flosstradamus", "Casino"])

        best_candidate = self.matcher.find_best_candidate(
            "baht",
            "Mosh Pit Ft. Casino",
            [candidate],
            'track:"Mosh Pit Ft. Casino" artist:"baht"',
            artist_source="Uploader Fallback",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "baht",
                "Mosh Pit Ft. Casino",
                [candidate],
                'track:"Mosh Pit Ft. Casino" artist:"baht"',
                artist_source="Uploader Fallback",
            )
        )

    def test_parsed_artist_feature_title_can_still_match_original(self) -> None:
        candidate = self._candidate("Mosh Pit (feat. Casino)", ["Flosstradamus", "Casino"])

        match = self.matcher.match(
            "Flosstradamus",
            "Mosh Pit Ft. Casino",
            [candidate],
            'track:"Mosh Pit Ft. Casino" artist:"Flosstradamus"',
            artist_source="Parsed from Title",
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_named_remix_contributors_can_rescue_label_uploader_match(self) -> None:
        candidate = self._candidate(
            "NRG - Skrillex, Kill The Noise, Milo & Otis Remix",
            [
                "A-Trak",
                "Armand Van Helden",
                "Duck Sauce",
                "Skrillex",
                "Kill The Noise",
                "Milo & Otis",
            ],
        )

        match = self.matcher.match(
            "Fool's Gold",
            "NRG (Skrillex, Kill The Noise, Milo & Otis Remix)",
            [candidate],
            'track:"NRG (Skrillex, Kill The Noise, Milo & Otis Remix)" artist:"Fool\'s Gold"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_plain_source_title_does_not_match_unrequested_named_remix(self) -> None:
        candidate = self._candidate(
            "Spectrum - Deniz Koyu Remix",
            ["Zedd", "Matthew Koma"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Zedd",
            "Spectrum (feat. Matthew Koma)",
            [candidate],
            'track:"Spectrum (feat. Matthew Koma)" artist:"Zedd"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Zedd",
                "Spectrum (feat. Matthew Koma)",
                [candidate],
                'track:"Spectrum (feat. Matthew Koma)" artist:"Zedd"',
            )
        )

    def test_plain_source_title_prefers_original_over_named_remix(self) -> None:
        original = self._candidate("Spectrum", ["Zedd", "Matthew Koma"])
        remix = self._candidate("Spectrum - Deniz Koyu Remix", ["Zedd", "Matthew Koma"])

        match = self.matcher.match(
            "Zedd",
            "Spectrum (feat. Matthew Koma)",
            [remix, original],
            'track:"Spectrum (feat. Matthew Koma)" artist:"Zedd"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, original["id"])

    def test_karaoke_cover_does_not_match_original_artist_source(self) -> None:
        candidate = self._candidate(
            "Bad (Originally Performed by David Guetta & Showtek ft. Vassy) [Karaoke Version]",
            ["Brass Tax Hit Makers"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "David Guetta & Showtek ft. Vassy",
            "BAD",
            [candidate],
            'track:"BAD" artist:"David Guetta & Showtek ft. Vassy"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "David Guetta & Showtek ft. Vassy",
                "BAD",
                [candidate],
                'track:"BAD" artist:"David Guetta & Showtek ft. Vassy"',
            )
        )

    def test_structured_artist_title_credit_matches_real_track_over_karaoke_cover(self) -> None:
        real_track = self._candidate(
            "Earthquake (DJ Fresh vs. Diplo) (Feat. Dominique Young Unique) [Explicit Edit]",
            ["DJ Fresh", "Diplo"],
        )
        karaoke_cover = self._candidate(
            "Earthquake (Originally Performed by DJ Fresh vs. Diplo Feat. Dominique Young Unique) - Vocal Version",
            ["Singer's Edge Karaoke"],
        )

        match = self.matcher.match(
            "DJ Fresh VS Diplo Feat. Dominique Young Unique",
            "'Earthquake'",
            [karaoke_cover, real_track],
            'track:"Earthquake" artist:"DJ Fresh VS Diplo Feat. Dominique Young Unique"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, real_track["id"])
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_karaoke_cover_with_original_artist_in_title_stays_unmatched(self) -> None:
        candidate = self._candidate(
            "Earthquake (Originally Performed by DJ Fresh vs. Diplo Feat. Dominique Young Unique) - Vocal Version",
            ["Singer's Edge Karaoke"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "DJ Fresh VS Diplo Feat. Dominique Young Unique",
            "'Earthquake'",
            [candidate],
            'track:"Earthquake" artist:"DJ Fresh VS Diplo Feat. Dominique Young Unique"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "DJ Fresh VS Diplo Feat. Dominique Young Unique",
                "'Earthquake'",
                [candidate],
                'track:"Earthquake" artist:"DJ Fresh VS Diplo Feat. Dominique Young Unique"',
            )
        )

    def test_radio_edit_storefront_title_matches_plain_source_title(self) -> None:
        candidate = self._candidate(
            "Bad (feat. Vassy) - Radio Edit",
            ["David Guetta", "Showtek", "Vassy"],
        )

        match = self.matcher.match(
            "David Guetta & Showtek ft. Vassy",
            "BAD",
            [candidate],
            'track:"BAD" artist:"David Guetta & Showtek ft. Vassy"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_original_mix_source_does_not_match_unrequested_vip_mix(self) -> None:
        candidate = self._candidate(
            "Secrets (feat. VASSY) - Don Diablo's VIP Mix",
            ["Tiësto", "KSHMR", "VASSY", "Don Diablo"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "Tiesto & KSHMR",
            "Secrets feat. Vassy",
            [candidate],
            'track:"Secrets feat. Vassy" artist:"Tiesto & KSHMR"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Tiesto & KSHMR",
                "Secrets feat. Vassy",
                [candidate],
                'track:"Secrets feat. Vassy" artist:"Tiesto & KSHMR"',
            )
        )

    def test_tiesto_ascii_source_matches_tiesto_accented_original(self) -> None:
        candidate = self._candidate("Secrets", ["Tiësto", "KSHMR", "VASSY"])

        match = self.matcher.match(
            "Tiesto & KSHMR",
            "Secrets feat. Vassy",
            [candidate],
            'track:"Secrets feat. Vassy" artist:"Tiesto & KSHMR"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_vs_artist_source_does_not_match_candidate_missing_vs_contributor(self) -> None:
        candidate = self._candidate("I Fink U Freeky", ["Die Antwoord"])

        best_candidate = self.matcher.find_best_candidate(
            "VANIC VS DIE ANTWOORD",
            "I Fink U Freeky",
            [candidate],
            'track:"I Fink U Freeky" artist:"VANIC VS DIE ANTWOORD"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "VANIC VS DIE ANTWOORD",
                "I Fink U Freeky",
                [candidate],
                'track:"I Fink U Freeky" artist:"VANIC VS DIE ANTWOORD"',
            )
        )

    def test_x_artist_source_does_not_match_candidate_missing_x_contributor(self) -> None:
        cases = [
            (
                "Vanic X Zella Day",
                "High",
                self._candidate("High", ["Zella Day"]),
            ),
            (
                "Vanic X K.Flay",
                "The Cops",
                self._candidate("The Cops", ["K.Flay"]),
            ),
        ]

        for artist, song, candidate in cases:
            with self.subTest(artist=artist, song=song):
                best_candidate = self.matcher.find_best_candidate(
                    artist,
                    song,
                    [candidate],
                    f'track:"{song}" artist:"{artist}"',
                )

                self.assertIsNotNone(best_candidate)
                self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
                self.assertIsNone(
                    self.matcher.match(
                        artist,
                        song,
                        [candidate],
                        f'track:"{song}" artist:"{artist}"',
                    )
                )

    def test_vs_artist_source_can_match_candidate_with_all_vs_contributors(self) -> None:
        candidate = self._candidate("I Fink U Freeky", ["Vanic", "Die Antwoord"])

        match = self.matcher.match(
            "VANIC VS DIE ANTWOORD",
            "I Fink U Freeky",
            [candidate],
            'track:"I Fink U Freeky" artist:"VANIC VS DIE ANTWOORD"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_x_artist_source_can_match_candidate_remix_by_x_contributor(self) -> None:
        candidate = self._candidate("Borderline - Vanic Remix", ["Tove Styrke", "Vanic"])

        match = self.matcher.match(
            "Vanic X Tove Styrke",
            "Borderline",
            [candidate],
            'track:"Borderline" artist:"Vanic X Tove Styrke"',
            original_title="Vanic X Tove Styrke - Borderline",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_release_copy_source_title_matches_original_mix_storefront_title(self) -> None:
        candidate = self._candidate("Error - Original Mix", ["Will Sparks"])

        match = self.matcher.match(
            "Will Sparks",
            "Error Out Soon!",
            [candidate],
            'track:"Error Out Soon!" artist:"Will Sparks"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_release_copy_original_title_label_tag_does_not_block_original_mix_match(self) -> None:
        candidate = self._candidate("Error - Original Mix", ["Will Sparks"])

        match = self.matcher.match(
            "Will Sparks",
            "Error Out Soon!",
            [candidate],
            'track:"Error Out Soon!" artist:"Will Sparks"',
            original_title="Will Sparks - Error (Original Mix) [Club Cartel Records] Out Soon!",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_plain_source_title_matches_spotify_original_suffix(self) -> None:
        candidate = self._candidate("Sonny - Original", ["Hearts"])

        match = self.matcher.match(
            "Hearts",
            "Sonny",
            [candidate],
            'track:"Sonny" artist:"Hearts"',
            original_title="[BC008] Hearts - Sonny (Original Mix)",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_stripped_original_mix_raw_title_does_not_block_exact_artist_match(self) -> None:
        candidate = self._candidate("Bring It Back", ["Will Sparks", "Joel Fletcher"])

        match = self.matcher.match(
            "Will Sparks & Joel Fletcher",
            "Bring It Back",
            [candidate],
            'track:"Bring It Back" artist:"Will Sparks & Joel Fletcher"',
            original_title="Will Sparks & Joel Fletcher - Bring It Back (Original Mix) [Mixmash Records] OUT NOW!",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_stripped_original_mix_source_can_match_original_mix_spotify_suffix(self) -> None:
        candidate = self._candidate("We Like to Party - Original Mix", ["Showtek"])

        match = self.matcher.match(
            "Showtek",
            "We Like To Party",
            [candidate],
            'track:"We Like To Party" artist:"Showtek"',
            original_title="Showtek - We Like To Party (Original Mix)",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_release_copy_source_title_still_rejects_unrelated_candidate(self) -> None:
        candidate = self._candidate("Pushing Me Away", ["Linkin Park"])

        best_candidate = self.matcher.find_best_candidate(
            "Will Sparks",
            "Error Out Soon!",
            [candidate],
            'track:"Error Out Soon!" artist:"Will Sparks"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Will Sparks",
                "Error Out Soon!",
                [candidate],
                'track:"Error Out Soon!" artist:"Will Sparks"',
            )
        )

    def test_unspaced_dash_version_suffix_can_match_spotify_remix_title(self) -> None:
        candidate = self._candidate(
            "Save The World - Zedd Remix",
            ["Swedish House Mafia", "Zedd"],
        )

        match = self.matcher.match(
            "alemirri",
            "Save the world (zedd remix)",
            [candidate],
            'track:"Save the world (zedd remix)" artist:"alemirri"',
            artist_source="Uploader Fallback",
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_unspaced_trailing_feature_artist_can_match_original_track(self) -> None:
        candidate = self._candidate("Melbourne Sound", ["Matty Lincoln", "Mandas"])

        match = self.matcher.match(
            "Matty Lincoln ft.Mandas",
            "Melbourne Sound",
            [candidate],
            'track:"Melbourne Sound" artist:"Matty Lincoln ft.Mandas"',
            artist_source="Parsed from Title",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_trailing_dash_artist_in_title_can_match_when_uploader_is_noise(self) -> None:
        candidate = self._candidate("Wade In Your Water", ["Common Kings"])

        match = self.matcher.match(
            "Kainalu Woodhall",
            "Wade In Your Water -Common Kings",
            [candidate],
            'track:"Wade In Your Water -Common Kings" artist:"Kainalu Woodhall"',
            artist_source="Uploader Fallback",
            original_title="Wade In Your Water -Common Kings",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_uploader_fallback_artist_is_kept_when_title_does_not_supply_artist(self) -> None:
        candidate = self._candidate("Wade In Your Water", ["Common Kings"])

        match = self.matcher.match(
            "Common Kings",
            "Wade In Your Water",
            [candidate],
            'track:"Wade In Your Water" artist:"Common Kings"',
            artist_source="Uploader Fallback",
            original_title="Wade In Your Water",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_full_mix_hd_source_title_matches_plain_spotify_title(self) -> None:
        candidate = self._candidate("Samurai Bounce", ["Bombs Away", "Dan Absent"])

        match = self.matcher.match(
            "Bombs Away & Dan Absent",
            "Samurai Bounce (Full Mix) HD",
            [candidate],
            'track:"Samurai Bounce (Full Mix) HD" artist:"Bombs Away & Dan Absent"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_vs_artist_remix_alias_can_match_spotify_renamed_artist(self) -> None:
        candidate = self._candidate(
            "Work Money Party Bitches - Deorro Vs Joel Fletcher Remix",
            ["Deorro", "Joel Fletcher", "Lowkiss", "Ryan Riback"],
        )

        match = self.matcher.match(
            "Ryan Riback Vs LowKiss",
            "Work Money Party Bitches [Joel Fletcher & Deorro aka TON!C Remix]",
            [candidate],
            'track:"Work Money Party Bitches" artist:"Ryan Riback Vs LowKiss"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_same_artist_wrong_title_stays_unmatched_below_threshold(self) -> None:
        candidate = self._candidate("Smash!", ["Ummet Ozcan"])

        best_candidate = self.matcher.find_best_candidate(
            "Ummet Ozcan",
            "Raise Your Hands",
            [candidate],
            'track:"Raise Your Hands" artist:"Ummet Ozcan"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Ummet Ozcan",
                "Raise Your Hands",
                [candidate],
                'track:"Raise Your Hands" artist:"Ummet Ozcan"',
            )
        )

    def test_censored_source_title_matches_real_track_not_commentary(self) -> None:
        commentary = self._candidate("About F*ck Up Some Commas - Commentary", ["Future"])
        real_track = self._candidate("Fuck Up Some Commas", ["Future"])

        commentary_best = self.matcher.find_best_candidate(
            "Future",
            "F Ck Up Some Commas",
            [commentary],
            'track:"F Ck Up Some Commas" artist:"Future"',
            original_title="F Ck Up Some Commas",
        )

        self.assertIsNotNone(commentary_best)
        self.assertLess(commentary_best.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Future",
                "F Ck Up Some Commas",
                [commentary],
                'track:"F Ck Up Some Commas" artist:"Future"',
                original_title="F Ck Up Some Commas",
            )
        )

        match = self.matcher.match(
            "Future",
            "F Ck Up Some Commas",
            [commentary, real_track],
            'track:"F Ck Up Some Commas" artist:"Future"',
            original_title="F Ck Up Some Commas",
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, real_track["id"])
        self.assertEqual(match.match_score, 1.0)

    def test_candidate_part_marker_does_not_match_plain_source_title(self) -> None:
        candidate = self._candidate("You Are Why I Am Invisible, Pt. 2", ["xxyyxx"])

        best_candidate = self.matcher.find_best_candidate(
            "xxyyxx",
            "You Are Why I Am Invisible",
            [candidate],
            'track:"You Are Why I Am Invisible" artist:"xxyyxx"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "xxyyxx",
                "You Are Why I Am Invisible",
                [candidate],
                'track:"You Are Why I Am Invisible" artist:"xxyyxx"',
            )
        )

    def test_matching_part_markers_can_match_with_roman_numeral_variant(self) -> None:
        candidate = self._candidate("You Are Why I Am Invisible, Pt. 2", ["xxyyxx"])

        match = self.matcher.match(
            "xxyyxx",
            "You Are Why I Am Invisible Pt. II",
            [candidate],
            'track:"You Are Why I Am Invisible Pt. II" artist:"xxyyxx"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    def test_tiny_plain_title_does_not_match_longer_title_containing_same_token(self) -> None:
        candidate = self._candidate("ID Summer Jam", ["Holly", "Baauer"])

        best_candidate = self.matcher.find_best_candidate(
            "Baauer",
            "ID",
            [candidate],
            'track:"ID" artist:"Baauer"',
            original_title="Baauer - ID (Nova Geração)",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Baauer",
                "ID",
                [candidate],
                'track:"ID" artist:"Baauer"',
                original_title="Baauer - ID (Nova Geração)",
            )
        )

    def test_tiny_plain_title_can_still_match_exact_title(self) -> None:
        candidate = self._candidate("ID", ["Holly", "Baauer"])

        match = self.matcher.match(
            "Baauer",
            "ID",
            [candidate],
            'track:"ID" artist:"Baauer"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_weak_short_phrase_title_does_not_match_longer_title_containing_phrase(self) -> None:
        candidate = self._candidate("There for U", ["Jauz", "Franky Nuts"])

        best_candidate = self.matcher.find_best_candidate(
            "JAUZ",
            "For U",
            [candidate],
            'track:"For U" artist:"JAUZ"',
            original_title="For U (Original Mix)",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "JAUZ",
                "For U",
                [candidate],
                'track:"For U" artist:"JAUZ"',
                original_title="For U (Original Mix)",
            )
        )

    def test_weak_short_phrase_title_does_not_match_longer_unrelated_artist_title(self) -> None:
        candidate = self._candidate("I want to die", ["Haunted Brock"])

        best_candidate = self.matcher.find_best_candidate(
            "Brock.",
            "Want To",
            [candidate],
            'track:"Want To" artist:"Brock."',
            original_title="Want To",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Brock.",
                "Want To",
                [candidate],
                'track:"Want To" artist:"Brock."',
                original_title="Want To",
            )
        )

    def test_weak_short_phrase_title_can_still_match_exact_title(self) -> None:
        candidate = self._candidate("For U", ["JAUZ"])

        match = self.matcher.match(
            "JAUZ",
            "For U",
            [candidate],
            'track:"For U" artist:"JAUZ"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_same_artist_radio_edit_beats_wrong_title_candidate(self) -> None:
        wrong_candidate = self._candidate("Smash!", ["Ummet Ozcan"])
        radio_edit = self._candidate("Raise Your Hands - Radio Edit", ["Ummet Ozcan"])

        match = self.matcher.match(
            "Ummet Ozcan",
            "Raise Your Hands",
            [wrong_candidate, radio_edit],
            'track:"Raise Your Hands" artist:"Ummet Ozcan"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, radio_edit["id"])
        self.assertEqual(match.match_score, 1.0)

    def test_trailing_freestyle_decoration_matches_plain_spotify_title(self) -> None:
        candidate = self._candidate("Back to Back", ["Drake"])

        match = self.matcher.match(
            "Drake",
            "Back To Back Freestyle",
            [candidate],
            'track:"Back To Back Freestyle" artist:"Drake"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.match_score, 1.0)

    def test_trailing_freestyle_exact_title_by_wrong_artist_stays_unmatched(self) -> None:
        candidate = self._candidate("Back To Back Freestyle", ["Itz Drakeo"])

        best_candidate = self.matcher.find_best_candidate(
            "Drake",
            "Back To Back Freestyle",
            [candidate],
            'track:"Back To Back Freestyle" artist:"Drake"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "Drake",
                "Back To Back Freestyle",
                [candidate],
                'track:"Back To Back Freestyle" artist:"Drake"',
            )
        )

    def test_trailing_freestyle_selects_real_plain_title_over_wrong_exact_title(self) -> None:
        wrong_candidate = self._candidate("Back To Back Freestyle", ["Itz Drakeo"])
        real_candidate = self._candidate("Back to Back", ["Drake"])

        match = self.matcher.match(
            "Drake",
            "Back To Back Freestyle",
            [wrong_candidate, real_candidate],
            'track:"Back To Back Freestyle" artist:"Drake"',
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.spotify_track_id, real_candidate["id"])

    def test_rework_source_does_not_match_different_spotify_remix(self) -> None:
        candidate = self._candidate(
            "Aftershock (feat. Jacquie) - SCNDL Remix",
            ["Cash Cash", "Jacquie", "SCNDL"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "SCNDL",
            "AFTERSHOCK (Tremor Re-Work)",
            [candidate],
            'track:"AFTERSHOCK (Tremor Re-Work)" artist:"SCNDL"',
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "SCNDL",
                "AFTERSHOCK (Tremor Re-Work)",
                [candidate],
                'track:"AFTERSHOCK (Tremor Re-Work)" artist:"SCNDL"',
            )
        )

    def test_original_title_rework_context_rejects_different_remix_after_parser_strips_version(self) -> None:
        candidate = self._candidate(
            "Aftershock (feat. Jacquie) - SCNDL Remix",
            ["Cash Cash", "Jacquie", "SCNDL"],
        )

        best_candidate = self.matcher.find_best_candidate(
            "SCNDL",
            "AFTERSHOCK",
            [candidate],
            'track:"AFTERSHOCK" artist:"SCNDL"',
            original_title="AFTERSHOCK (Tremor Re-Work) [FREE DOWNLOAD]",
        )

        self.assertIsNotNone(best_candidate)
        self.assertLess(best_candidate.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match(
                "SCNDL",
                "AFTERSHOCK",
                [candidate],
                'track:"AFTERSHOCK" artist:"SCNDL"',
                original_title="AFTERSHOCK (Tremor Re-Work) [FREE DOWNLOAD]",
            )
        )

    def test_swapped_orientation_can_recover_title_first_uploads(self) -> None:
        candidate = self._candidate("Freaks", ["Timmy Trumpet"])

        normal_match = self.matcher.match(
            "Freaks",
            "Timmy Trumpet",
            [candidate],
            'track:"Timmy Trumpet" artist:"Freaks"',
        )
        swapped_match = self.matcher.match_swapped_orientation(
            "Freaks",
            "Timmy Trumpet",
            [candidate],
            'track:"Freaks" artist:"Timmy Trumpet"',
        )

        self.assertIsNone(normal_match)
        self.assertIsNotNone(swapped_match)
        self.assertGreaterEqual(
            swapped_match.match_score,
            self.matcher.SWAPPED_ORIENTATION_MINIMUM_MATCH_SCORE,
        )

    def test_swapped_orientation_weak_title_and_fuzzy_artist_stays_below_threshold(self) -> None:
        candidate = self._candidate("Top Of The World", ["Goal Getters"])

        normal_best = self.matcher.find_best_candidate(
            "World",
            "Ookay & Getter",
            [candidate],
            'track:"Ookay & Getter" artist:"World"',
        )
        swapped_best = self.matcher.find_best_candidate(
            "Ookay & Getter",
            "World",
            [candidate],
            'track:"World" artist:"Ookay & Getter"',
        )

        self.assertIsNotNone(normal_best)
        self.assertEqual(normal_best.match_score, 0.0)
        self.assertIsNotNone(swapped_best)
        self.assertLess(swapped_best.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match_swapped_orientation(
                "World",
                "Ookay & Getter",
                [candidate],
                'track:"World" artist:"Ookay & Getter"',
            )
        )

    def test_swapped_orientation_original_title_vip_context_blocks_plain_original(self) -> None:
        candidate = self._candidate("El Chapo", ["The Game", "Skrillex"])
        original_title = "El Chapo [FAWKS VIP] - Skrillex & The Game"

        normal_best = self.matcher.find_best_candidate(
            "El Chapo",
            "Skrillex & The Game [FAWKS VIP]",
            [candidate],
            'track:"Skrillex & The Game [FAWKS VIP]" artist:"El Chapo"',
            original_title=original_title,
        )
        swapped_best = self.matcher.find_best_candidate(
            "Skrillex & The Game [FAWKS VIP]",
            "El Chapo",
            [candidate],
            'track:"El Chapo" artist:"Skrillex & The Game [FAWKS VIP]"',
            original_title=original_title,
        )

        self.assertIsNotNone(normal_best)
        self.assertEqual(normal_best.match_score, 0.0)
        self.assertIsNotNone(swapped_best)
        self.assertLess(swapped_best.match_score, self.matcher.MINIMUM_MATCH_SCORE)
        self.assertIsNone(
            self.matcher.match_swapped_orientation(
                "El Chapo",
                "Skrillex & The Game [FAWKS VIP]",
                [candidate],
                'track:"El Chapo" artist:"Skrillex & The Game [FAWKS VIP]"',
                original_title=original_title,
            )
        )

    def test_swapped_orientation_queries_strip_indexed_feature_title_prefix(self) -> None:
        candidate = self._candidate(
            "Operator (Ring Ring) [feat. Dances With White Girls]",
            ["Chris Lake", "Dances"],
        )
        parsed_artist = "5 Operator Ft. Dances With White Girls"
        parsed_song = "Chris Lake"
        responses = {
            'track:"operator" artist:"Chris Lake"': [candidate],
        }

        search_queries = self.matcher.build_swapped_orientation_search_queries(
            parsed_artist,
            parsed_song,
        )
        match = None
        matched_query = ""
        for search_query in search_queries:
            candidate_match = self.matcher.match_swapped_orientation(
                parsed_artist,
                parsed_song,
                responses.get(search_query, []),
                search_query,
                original_title="Chris Lake - Operator (Ring Ring) Ft. Dances With White Girls",
            )
            if candidate_match is not None:
                match = candidate_match
                matched_query = search_query
                break

        self.assertIn('track:"operator" artist:"Chris Lake"', search_queries)
        self.assertIsNotNone(match)
        self.assertEqual(matched_query, 'track:"operator" artist:"Chris Lake"')
        self.assertEqual(match.matched_artist, "Chris Lake, Dances")
        self.assertGreaterEqual(
            match.match_score,
            self.matcher.SWAPPED_ORIENTATION_MINIMUM_MATCH_SCORE,
        )

    def test_structured_spotify_artists_match_primary_artist_in_large_credit_list(self) -> None:
        candidate = self._candidate(
            "Revolution (feat. Faustix & Imanos and Kai) - Danny Diggz Remix",
            ["Diplo", "Faustix", "Danny Diggz", "Imanos", "kai"],
        )

        match = self.matcher.match(
            "Diplo",
            "Revolution (Danny Diggz Remix)",
            [candidate],
            'track:"Revolution (Danny Diggz Remix)" artist:"Diplo"',
        )

        self.assertIsNotNone(match)
        self.assertGreaterEqual(match.match_score, self.matcher.MINIMUM_MATCH_SCORE)

    @staticmethod
    def _candidate(name: str, artists: list[str]) -> dict[str, object]:
        return {
            "id": f"{name.lower().replace(' ', '-')}-id",
            "uri": f"spotify:track:{name.lower().replace(' ', '-')}",
            "name": name,
            "artists": [{"name": artist} for artist in artists],
            "album": {"name": "Album"},
            "external_urls": {"spotify": "https://open.spotify.com/track/example"},
        }


if __name__ == "__main__":
    unittest.main()
