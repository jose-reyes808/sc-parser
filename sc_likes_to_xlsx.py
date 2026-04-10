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


def parse_title(title, uploader):
    if not title:
        return uploader, "", "Uploader Fallback"

    original_title = title.strip()

    # --- STEP 1: Extract [bracketed] content ---
    bracket_contents = re.findall(r"\[(.*?)\]", original_title)

    KEYWORDS = ["remix", "edit", "flip", "bootleg", "rework", "vip"]

    keep_brackets = []
    for content in bracket_contents:
        if any(re.search(k, content, re.IGNORECASE) for k in KEYWORDS):
            keep_brackets.append(f"[{content}]")

    # --- STEP 2: Remove ALL brackets from title ---
    title = re.sub(r"\[.*?\]", "", original_title).strip()

    # Remove promotional junk like *FREE DOWNLOAD*
    title = re.sub(r"\*.*?\*", "", title).strip()

    # Normalize dash types
    title = re.sub(r"[–—]", "-", title)

    # --- STEP 3: Split artist/title ---
    parts = re.split(r"\s*-\s*", title, maxsplit=1)

    if len(parts) == 2:
        artist = parts[0].strip()
        song = parts[1].strip()
        source = "Parsed from Title"
    else:
        artist = uploader
        song = title.strip()
        source = "Uploader Fallback"

    # --- STEP 4: Append valid brackets to song ---
    if keep_brackets:
        song = f"{song} {' '.join(keep_brackets)}".strip()

    return artist, song, source


def get_likes(client_id, user_id, backup_every=100):
    print("Fetching liked tracks...")
    likes = []

    url = f"https://api-v2.soundcloud.com/users/{user_id}/likes?client_id={client_id}&limit=200&offset=0"

    while url:

        # --- REQUEST WITH RETRIES ---
        for attempt in range(3):
            res = requests.get(url, headers=headers)

            if res.status_code == 200:
                break

            if res.status_code == 429:
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

        # --- PARSE TRACKS ---
        for item in data.get("collection", []):
            track = item.get("track")

            if not track:
                continue

            title = track.get("title", "")
            artist_field = track.get("artist")
            user = track.get("user", {})
            uploader = user.get("username", "Unknown")

            if artist_field:
                artist = artist_field
                song = title
                source = "API Artist Field"
            else:
                artist, song, source = parse_title(title, uploader)

            likes.append({
                "Artist": artist,
                "Song": song,
                "Artist Source": source,
                "Original Title": title,
                "Date Uploaded": track.get("created_at"),
                "Date Liked": item.get("created_at"),
                "SoundCloud URL": track.get("permalink_url")
            })

        # --- PAGINATION ---
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

    if len(likes) > 0:
        df = pd.DataFrame(likes)

        # Clean datetime columns
        for col in ['Date Uploaded', 'Date Liked']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.tz_localize(None)

        # Optional: quick breakdown of sources
        print("\nArtist Source Breakdown:")
        print(df["Artist Source"].value_counts())

        df.to_excel("soundcloud_likes.xlsx", index=False)

        print(len(likes))
        print(df["SoundCloud URL"].nunique())

        print(f"Done. Saved {len(df)} tracks.")
    else:
        print("No likes fetched (unexpected).")


if __name__ == "__main__":
    main()