# Ophi brand assets

Logo files and social images. Colours: forest `#193a30`, ivory `#f4f2e9`, orange period `#d96335`.

| File | Size | Use it for |
|---|---|---|
| `profile/ophi-avatar-mark-1080.png` | 1080×1080 | Profile photo on Instagram, Facebook, TikTok |
| `profile/ophi-avatar-mark-400.png` | 400×400 | Profile photo on X, LinkedIn, Google |
| `profile/ophi-avatar-wordmark-*.png` | same | Other profile photo option: the "ophi." wordmark |
| `banner/ophi-x-header-1500x500.png` | 1500×500 | X / Twitter header |
| `banner/ophi-linkedin-cover-1128x191.png` | 1128×191 | LinkedIn company page cover |
| `banner/ophi-facebook-cover-1640x624.png` | 1640×624 | Facebook page cover |
| `logo/ophi-wordmark.svg` / `.png` | vector / 2400 wide | Wordmark on light backgrounds (docs, decks, press) |
| `logo/ophi-wordmark-ivory.svg` / `.png` | vector / 2400 wide | Wordmark on dark backgrounds |
| `logo/ophi-mark.svg`, `ophi-mark-1024.png` | vector / 1024 | App-style icon (same as the site favicon) |

Profile photos are full-bleed squares with clear space, so the platforms' circle crop keeps the whole mark.
Banners keep their text and tooth away from the bottom-left corner, where each platform puts the profile photo.
The Facebook cover keeps its content inside the middle area that stays visible when phones crop the sides.

## Regenerate

1. Wordmark SVGs, outlined from DM Sans so they need no font installed:
   `python3 -m venv /tmp/fontenv && /tmp/fontenv/bin/pip install fonttools brotli uharfbuzz`, then
   `/tmp/fontenv/bin/python scripts/brand-wordmark.py`
2. Every PNG. Banners are screenshots of the live poster, so start the site first (`cd site && pnpm dev --port 3111`):
   `.venv/bin/python scripts/brand-assets.py`
