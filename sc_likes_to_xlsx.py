import requests
import pandas as pd
from datetime import datetime
import time
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
SOUNDCLOUD_CLIENT_ID = os.getenv("SOUNDCLOUD_CLIENT_ID")
SOUNDCLOUD_USER_ID = os.getenv("SOUNDCLOUD_USER_ID")

if not SOUNDCLOUD_CLIENT_ID:
    raise ValueError("Missing SOUNDCLOUD_CLIENT_ID in environment.")

if not SOUNDCLOUD_USER_ID:
    raise ValueError("Missing SOUNDCLOUD_USER_ID in environment.")

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://soundcloud.com/",
    "Origin": "https://soundcloud.com",
    "Accept-Language": "en-US,en;q=0.9"
}

PAREN_KEYWORDS = ["remix", "edit", "flip", "bootleg", "rework", "vip", "ft.", "feat.", "mix"]

LIVESET_KEYWORDS = [
    "live set",
    "full set",
    "bbc",
    "b2b",
    "mixtape",
    "live at",
    "festival set",
    "diplo & friends",
    "diplo and friends",
    "hard summer",
    "escape psycho circus",
    "edc",
    "holy ship",
    "benzi",
    "ultra music festival",
    "beyond wonderland",
    "mini mix",
    "hello festival season",
    "halloween"
    "xs"
    "dtg"
    "caller id"
]



def clean_promotional(text):
    if not text:
        return text

    text = text.strip()

    # Remove entire (...) blocks for specific promo phrases
    text = re.sub(r"\([^)]*out now[^)]*\)", "", text, flags=re.IGNORECASE)

    # Remove everything after these phrases
    cutoff_patterns = [
        r"\bout now\b.*",
        r"\bsupported by\b.*",
        r"\bavailable\b.*",
        r"\bout\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\b.*"
    ]
    for pattern in cutoff_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove specific promo / label phrases
    remove_patterns = [
        r"\bfree download\b",
        r"\bofficial video in description\b",
        r"\bbuy = free\b",
        r"\bmusic video in description\b",
        r"\bclick buy\b",
        r"\bnew version in description\b",
        r"\bclick buy 4 free dl\b",
        r"\bbillboard premiere\b",
        r"\bbeatport\b",
        r"\brecords\b",
        r"\belectro house\b",
        r"\bpreview\b",
        r"\boriginal mix\b",
        r"\bradio edit\b",
        r"\bradio mix\b",
        r"\[mixmash\]"
    ]
    for pattern in remove_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove chart tags like "#15 chart"
    text = re.sub(r"#\d+\s*chart\b", "", text, flags=re.IGNORECASE)

    # Remove *...* blocks
    text = re.sub(r"\*.*?\*", "", text)

    # Cleanup
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*-\s*$", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = text.strip()

    return text


def postprocess_text(text):
    if not text:
        return text

    text = text.strip()

    # Run promo cleanup again after parsing
    text = clean_promotional(text)

    # Remove empty bracket/paren leftovers
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)

    # Remove dangling unmatched brackets/parens
    text = re.sub(r"\(\s*$", "", text)
    text = re.sub(r"^\s*\)", "", text)
    text = re.sub(r"\[\s*$", "", text)
    text = re.sub(r"^\s*\]", "", text)

    # Remove stray punctuation at the end
    text = re.sub(r"[\-\|:,;/]+\s*$", "", text)

    # Normalize spacing around brackets/parens
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\[\s+", "[", text)
    text = re.sub(r"\s+\]", "]", text)

    # Collapse duplicate whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_liveset(song, artist="", original_title=""):
    text = f"{artist} {song} {original_title}".lower()

    for keyword in LIVESET_KEYWORDS:
        if keyword in text:
            return True

    return False


def parse_title(title, uploader):
    if not title:
        return uploader, "", "Uploader Fallback"

    original_title = clean_promotional(title.strip())

    # Handle [brackets]
    bracket_contents = re.findall(r"\[(.*?)\]", original_title)

    keep_brackets = []
    for content in bracket_contents:
        if re.search(r"remix|edit|flip|bootleg|rework|vip|mix", content, re.IGNORECASE):
            keep_brackets.append(f"[{content.strip()}]")

    # Remove all brackets before parsing
    title = re.sub(r"\[.*?\]", "", original_title)

    # Handle (parentheses): keep only if keyword appears
    def keep_paren(match):
        content = match.group(1).strip()
        if any(k in content.lower() for k in PAREN_KEYWORDS):
            return f"({content})"
        return ""

    title = re.sub(r"\((.*?)\)", keep_paren, title)

    # Cleanup before split
    title = re.sub(r"[–—]", "-", title)
    title = re.sub(r"\s+", " ", title).strip()

    # Split only on real delimiters with spaces around them
    parts = re.split(r"\s+[-–—|]\s+", title, maxsplit=1)

    if len(parts) == 2:
        artist = parts[0].strip()
        song = parts[1].strip()
        source = "Parsed from Title"
    else:
        artist = uploader
        song = title.strip()
        source = "Uploader Fallback"

    # Append meaningful bracket content back onto song
    if keep_brackets:
        song = f"{song} {' '.join(keep_brackets)}".strip()

    # Final cleanup pass
    artist = postprocess_text(artist)
    song = postprocess_text(song)

    return artist, song, source


def get_likes(client_id, user_id):
    print("Fetching liked tracks...")
    likes = []

    url = f"https://api-v2.soundcloud.com/users/{user_id}/likes?client_id={client_id}&limit=200&offset=0"

    while url:
        for attempt in range(3):
            res = requests.get(url, headers=headers)

            if res.status_code == 200:
                break
            elif res.status_code == 429:
                print("Rate limited. Sleeping 30s...")
                time.sleep(30)
            elif res.status_code == 401:
                print("401 received. Retrying after short delay...")
                time.sleep(5)
            else:
                print(f"HTTP {res.status_code} — retry {attempt + 1}/3")
                time.sleep(5)
        else:
            print("Failed page after retries — stopping pagination")
            return likes

        data = res.json()
        print("Loaded:", len(data.get("collection", [])))

        for item in data.get("collection", []):
            track = item.get("track")
            if not track:
                continue

            raw_title = track.get("title", "")
            cleaned_title = clean_promotional(raw_title)

            user = track.get("user", {})
            uploader = user.get("username", "Unknown")

            # Trust title structure first. Otherwise use uploader fallback.
            artist, song, source = parse_title(cleaned_title, uploader)

            likes.append({
                "Artist": artist,
                "Song": song,
                "Artist Source": source,
                "Original Title": raw_title,
                "Date Uploaded": track.get("created_at"),
                "Date Liked": item.get("created_at"),
                "SoundCloud URL": track.get("permalink_url")
            })

        next_href = data.get("next_href")
        if next_href:
            if "client_id=" not in next_href:
                next_href += f"&client_id={client_id}"
            url = next_href
        else:
            url = None

        print("Next page:", bool(url))
        time.sleep(1)

    print("DEBUG total likes:", len(likes))
    return likes


def main():
    likes = get_likes(SOUNDCLOUD_CLIENT_ID, SOUNDCLOUD_USER_ID)

    print(f"Pages completed. Total likes collected: {len(likes)}")

    if len(likes) == 0:
        print("No likes fetched (unexpected).")
        return

    df = pd.DataFrame(likes)

    # Clean datetime columns
    for col in ["Date Uploaded", "Date Liked"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.tz_localize(None)

    # Split live sets using Song + Artist + Original Title
    df["Is_Liveset"] = df.apply(
        lambda row: is_liveset(
            row["Song"],
            row["Artist"],
            row["Original Title"]
        ),
        axis=1
    )

    df_livesets = df[df["Is_Liveset"]].drop(columns=["Is_Liveset"])
    df_tracks = df[~df["Is_Liveset"]].drop(columns=["Is_Liveset"])

    df_tracks.to_excel("soundcloud_likes.xlsx", index=False)
    df_livesets.to_excel("soundcloud_livesets.xlsx", index=False)

    print("\nBreakdown:")
    print(f"Tracks: {len(df_tracks)}")
    print(f"Live sets: {len(df_livesets)}")

    print("\nArtist Source Breakdown:")
    print(df["Artist Source"].value_counts())

    print("Done.")


if __name__ == "__main__":
    main()