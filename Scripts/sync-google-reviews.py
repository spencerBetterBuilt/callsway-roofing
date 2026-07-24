"""
Pulls the current rating and review count for Callsway Roof Co. from the
Google Places API and rewrites the hardcoded values baked into the site's
HTML (both the schema.org JSON-LD used by search engines and the visible
"X.X on Google (NN Reviews)" trust badge). Run on a schedule via
.github/workflows/sync-google-reviews.yml — direct client-side calls aren't
used here because search engines expect structured data to be present in
the raw HTML, not injected by JS after the page loads.
"""

import glob
import os
import re
import sys
import urllib.request


def load_dotenv(path=".env"):
    """Minimal .env loader for local runs; GitHub Actions sets the real env var directly."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


load_dotenv()

PLACE_ID = "ChIJd3BWfBfERoYRM_uclTZe7EY"
API_KEY = os.environ["GOOGLE_PLACES_API_KEY"]

SCHEMA_FILES = (
    ["index.html"]
    + glob.glob("Areas/*/index.html")
    + glob.glob("Services/*/index.html")
)
BADGE_FILES = SCHEMA_FILES + ["about.html"]

SCHEMA_PATTERN = re.compile(
    r'"ratingValue":\s*"[\d.]+",(\s*)"reviewCount":\s*"\d+"'
)
BADGE_PATTERN = re.compile(r"[\d.]+ ★ on Google \(\d+ Reviews\)")


def fetch_rating():
    url = f"https://places.googleapis.com/v1/places/{PLACE_ID}"
    request = urllib.request.Request(
        url,
        headers={
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "rating,userRatingCount",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        import json

        data = json.load(response)
    return data["rating"], data["userRatingCount"]


def update_file(path, pattern, replacement):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    new_content, count = pattern.subn(replacement, content)
    if count and new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    rating, review_count = fetch_rating()
    rating_str = f"{rating:.1f}"
    print(f"Fetched from Google: {rating_str} stars, {review_count} reviews")

    changed = []

    for path in SCHEMA_FILES:
        replacement = f'"ratingValue": "{rating_str}",\\1"reviewCount": "{review_count}"'
        if update_file(path, SCHEMA_PATTERN, replacement):
            changed.append(path)

    for path in BADGE_FILES:
        replacement = f"{rating_str} ★ on Google ({review_count} Reviews)"
        if update_file(path, BADGE_PATTERN, replacement):
            changed.append(path)

    if changed:
        print("Updated:", ", ".join(sorted(set(changed))))
    else:
        print("No changes — values already up to date.")

    # Signal to the workflow whether there's anything to commit (only set in CI).
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        sys.exit(1)
