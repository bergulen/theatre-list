"""
Reads the play pages listed in plays.txt from tiyatrolar.com.tr,
pulls every performance (date, time, venue) from the "Seanslar" section,
and writes the combined result to data.json for the web page to show.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = Path(__file__).parent
PLAYS_FILE = ROOT / "plays.txt"
DATA_FILE = ROOT / "data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (personal theatre reminder list; checks a few pages once a day)",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}
DELAY_SECONDS = 2  # pause between pages so we stay polite to the site

# Example performance line: "26.10.2026 Pazartesi / 20:30"
SESSION_RE = re.compile(
    r"(\d{2})\.(\d{2})\.(\d{4})\s+([^\s/]+)\s*/\s*(\d{1,2}:\d{2})"
)


def read_play_urls():
    urls = []
    for line in PLAYS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line.split()[0])
    # keep order, drop duplicates
    return list(dict.fromkeys(urls))


def load_previous():
    if not DATA_FILE.exists():
        return {}
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {p["url"]: p for p in data.get("plays", [])}


def meta(soup, prop):
    tag = soup.find("meta", attrs={"property": prop}) or soup.find(
        "meta", attrs={"name": prop}
    )
    return tag["content"].strip() if tag and tag.get("content") else None


def find_sessions_heading(soup):
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        if tag.get_text(strip=True).lower() == "seanslar":
            return tag
    # fallback in case the site stops using a heading tag for it
    text = soup.find(string=re.compile(r"^\s*Seanslar\s*$", re.I))
    return text.parent if text else None


def parse_sessions(soup):
    """Walk the page from the 'Seanslar' heading onward, reading text in
    order and pairing each date/time with the venue link that follows it."""
    heading = find_sessions_heading(soup)
    if heading is None:
        return []

    sessions = []
    buffer = ""

    def flush(text, venue_link=None):
        matches = list(SESSION_RE.finditer(text))
        for idx, m in enumerate(matches):
            day, month, year, weekday, hhmm = m.groups()
            s = {
                "date": f"{year}-{month}-{day}",
                "weekday_tr": weekday,
                "time": hhmm.zfill(5),
                "venue": "",
                "city": "",
                "venue_url": "",
            }
            # the venue link belongs to the last date read before it
            if venue_link is not None and idx == len(matches) - 1:
                label = venue_link.get("title") or venue_link.get_text(" ", strip=True)
                venue, sep, city = label.rpartition(" / ")
                if not sep:
                    venue, city = label, ""
                s.update(venue=venue.strip(), city=city.strip(),
                         venue_url=venue_link.get("href", ""))
            sessions.append(s)

    for node in heading.next_elements:
        if isinstance(node, Tag):
            href = node.get("href") or ""
            # stop at the ticket button or the next section heading
            if node.name == "a" and "tiyatro-bilet" in href:
                break
            if re.match(r"^h[1-6]$", node.name or ""):
                break
            if node.name == "a" and "/sahne/" in href:
                flush(buffer, node)
                buffer = ""
        elif isinstance(node, NavigableString) and not isinstance(node, Comment):
            if node.parent and node.parent.name in ("script", "style"):
                continue
            buffer += " " + str(node)

    flush(buffer)

    # de-duplicate (the site sometimes repeats blocks for "show more")
    seen, unique = set(), []
    for s in sessions:
        key = (s["date"], s["time"], s["venue"])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def parse_play(url, html):
    soup = BeautifulSoup(html, "html.parser")

    title = meta(soup, "og:title") or (soup.title.string if soup.title else url)
    title = title.split("|")[0].strip()

    ticket = soup.find("a", href=re.compile(r"/tiyatro-bilet/"))
    return {
        "url": url,
        "title": title,
        "image": meta(soup, "og:image"),
        "ticket_url": ticket["href"] if ticket else url,
        "sessions": parse_sessions(soup),
        "error": None,
    }


def session_key(s):
    return f'{s["date"]}|{s["time"]}|{s["venue"]}'


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous = load_previous()
    plays = []

    for i, url in enumerate(read_play_urls()):
        if i:
            time.sleep(DELAY_SECONDS)
        old = previous.get(url)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            play = parse_play(url, resp.text)
        except Exception as exc:  # keep yesterday's data if today's check fails
            print(f"ERROR {url}: {exc}")
            if old:
                old["error"] = f"Last check failed: {exc}"
                plays.append(old)
            else:
                plays.append({"url": url, "title": url, "image": None,
                              "ticket_url": url, "sessions": [],
                              "error": f"Could not read page: {exc}"})
            continue

        # remember when each performance first appeared, to flag new dates
        first_seen = {}
        if old:
            first_seen = {session_key(s): s.get("first_seen") for s in old["sessions"]}
        for s in play["sessions"]:
            s["first_seen"] = first_seen.get(session_key(s)) or now

        print(f"OK    {play['title']}: {len(play['sessions'])} performance(s)")
        plays.append(play)

    DATA_FILE.write_text(
        json.dumps({"updated_at": now, "plays": plays}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def check(urls):
    """Test mode: print what the script reads from each page, change nothing.
    Usage: python scrape.py --check https://tiyatrolar.com.tr/tiyatro/ehlikeyf"""
    for url in urls:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        play = parse_play(url, resp.text)
        print(f"\n{play['title']}  ({len(play['sessions'])} performance(s))")
        print(f"  tickets: {play['ticket_url']}")
        for s in play["sessions"]:
            print(f"  {s['date']} {s['time']}  {s['venue']} / {s['city']}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--check":
        check(sys.argv[2:])
    else:
        main()
