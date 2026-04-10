# SoundCloud Likes → Excel → Spotify Pipeline (WIP)

## Overview

This project extracts a user's liked tracks from SoundCloud and exports them into a structured Excel file. It is the first stage of a larger pipeline that will:

1. Extract SoundCloud likes  
2. Export them to Excel  
3. Match tracks on Spotify  
4. Create a Spotify playlist  
5. Update Excel with Spotify match status  

---

## Current Features

- Fetch liked tracks from SoundCloud API
- Extract:
  - Artist name
  - Track title
  - Date Uploaded
  - Date Liked
  - SoundCloud URL
  - Duration
- Export results into Excel (.xlsx)

---

## Future Roadmap

### Phase 1 (Current)
- [x] SoundCloud likes extraction  
- [x] Excel export  
- [x] Modular user input system  

### Phase 2
- [ ] Spotify search integration  
- [ ] Track matching logic (title + artist fuzzy match)  
- [ ] Excel update with Spotify IDs  

### Phase 3
- [ ] Spotify playlist creation via API  
- [ ] Automatic playlist syncing  

---

## Installation

### 1. Clone repository
```bash
git clone https://github.com/jose-reyes808/soundcloud-parser.git
cd soundcloud-parser
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file or export variables manually.

### Required:
- `SOUNDCLOUD_CLIENT_ID`
- `SOUNDCLOUD_USER_ID`

Example:
```bash
SOUNDCLOUD_CLIENT_ID=your_client_id
SOUNDCLOUD_USER_ID=your_user_id
```

---

## Usage

```bash
python sc_likes_to_xlsx.py
```

### Output

Generates:
```
soundcloud_likes.xlsx
```

---

## Output Schema

| Column            | Description                                 | 
|------------------|----------------------------------------------|
| Artist           | Artist                                       |
| Title            | Cleaned up Title                             |
| Artist Source    | Whether it was parsed from title or Username |
| Original Title   | Original Title of Song                       |
| Date Uploaded    | Timestamp                                    |
| Date Liked       | Timestamp                                    |
| Soundcloud URL   | Direct SoundCloud link                       |

---

## Dependencies

```
requests
pandas
openpyxl
```

Install manually:
```bash
pip install requests pandas openpyxl
```

---

## Notes

- SoundCloud API responses can be inconsistent; missing fields are handled safely.
- Rate limits may apply depending on client ID usage.
- This project assumes public API accessibility via client ID.

---

## Next Step (Spotify Integration)

The next module will:
- Search Spotify for each track
- Match using:
  - normalized title
  - artist string similarity
- Append:
  - Spotify track ID
  - Match confidence score
  - Found / not found status