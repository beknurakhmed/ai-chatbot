"""Staff service — parses staff data from ajou.uz and serves it."""

import json
import time
import re
import asyncio
from pathlib import Path
import httpx

CACHE_FILE = Path(__file__).parent.parent / "data" / "staff_cache.json"
CACHE_MAX_AGE = 7 * 86400  # 7 days

_cache = None
_cache_time = 0

BASE_URL = "https://ajou.uz"

# Staff pages to parse
PAGES = [
    ("/en/vice-rectors/rector", "leadership"),
    ("/en/vice-rectors/vice-rectors", "leadership"),
    ("/en/vice-rectors/dean", "deans"),
    ("/en/staff/index?category=1", "staff"),
    ("/en/staff/lecturers?category=2", "lecturers"),
]


def _parse_staff_page(html: str, category: str) -> list[dict]:
    """Extract staff members from HTML page."""
    members = []

    # Find staff cards — they typically have image + name + position
    # Pattern for rector/vice-rector pages
    if category == "leadership":
        # Find img + name blocks
        blocks = re.findall(
            r'<img[^>]*src="(/uploads/rectors/[^"]+)"[^>]*>.*?'
            r'<[^>]*>([^<]+(?:Rector|Vice|Doctor|Professor)[^<]*)<',
            html, re.DOTALL | re.IGNORECASE
        )
        for photo, title in blocks:
            # Try to extract name from nearby text
            name_match = re.search(r'(?:Prof\.\s*|Doctor\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', title)
            members.append({
                "name": name_match.group(1) if name_match else title.strip(),
                "position": title.strip(),
                "photo": f"{BASE_URL}{photo}",
                "category": category,
            })

    # Pattern for staff/dean list pages
    # Look for common patterns: card with image, name, position
    img_blocks = re.findall(
        r'<img[^>]*src="(/uploads/staff/[^"]+)"[^>]*>',
        html
    )
    name_blocks = re.findall(
        r'<(?:h[2-5]|strong|b|span)[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)<',
        html, re.IGNORECASE
    )

    # Alternative: find all staff card divs
    cards = re.findall(
        r'<div[^>]*class="[^"]*staff[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html, re.DOTALL | re.IGNORECASE
    )

    if not cards:
        # Try simpler pattern — just find all name+photo pairs
        cards = re.findall(
            r'<a[^>]*href="/en/staff/view\?id=\d+"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

    for card_html in cards:
        photo_m = re.search(r'src="([^"]*(?:uploads/staff|uploads/rectors)[^"]*)"', card_html)
        name_m = re.search(r'>([A-Z][a-zA-Z\s\'-]+(?:\s[A-Z][a-zA-Z\'-]+)+)<', card_html)
        pos_m = re.search(r'(?:Professor|Instructor|Associate|Head|Dean|Director|Lecturer|Ph\.D)[^<]*', card_html)

        if name_m:
            member = {
                "name": name_m.group(1).strip(),
                "position": pos_m.group(0).strip() if pos_m else category,
                "photo": f"{BASE_URL}{photo_m.group(1)}" if photo_m else "",
                "category": category,
            }
            members.append(member)

    return members


def _fetch_staff_data() -> dict:
    """Fetch all staff data from ajou.uz."""
    all_staff = []

    with httpx.Client(follow_redirects=True, timeout=15) as client:
        for path, category in PAGES:
            try:
                r = client.get(f"{BASE_URL}{path}")
                if r.status_code == 200:
                    members = _parse_staff_page(r.text, category)
                    all_staff.extend(members)
            except Exception as e:
                print(f"Staff fetch error for {path}: {e}")

    # Deduplicate by name
    seen = set()
    unique = []
    for m in all_staff:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)

    return {
        "staff": unique,
        "updated": time.strftime("%Y-%m-%d %H:%M"),
    }


def _get_cached_data() -> dict:
    global _cache, _cache_time
    now = time.time()

    if _cache and (now - _cache_time) < CACHE_MAX_AGE:
        return _cache

    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if (now - CACHE_FILE.stat().st_mtime) < CACHE_MAX_AGE:
                _cache = data
                _cache_time = now
                return data
        except Exception:
            pass

    data = _fetch_staff_data()
    if data.get("staff"):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        _cache = data
        _cache_time = now

    return data


# Hardcoded key staff with confirmed photos (fallback if parsing fails)
KEY_STAFF = [
    {"name": "Muratov Gayrat Azatovich", "position": "Rector", "photo": "/staff/rector.png", "category": "leadership"},
    {"name": "Byung Kwan Kim", "position": "First Vice-Rector, Dean of Business Administration", "photo": "/staff/byung_kwan_kim.png", "category": "leadership"},
    {"name": "Kuchkarov Bokhodir Makhkamovich", "position": "Vice-Rector", "photo": "/staff/kuchkarov.png", "category": "leadership"},
    {"name": "Oh Seok Kyu", "position": "Dean of Architecture & Interior Design", "photo": "", "category": "deans"},
    {"name": "Yung Seok Shin", "position": "Dean of Civil Systems Engineering", "photo": "", "category": "deans"},
    {"name": "Min Young Hun", "position": "Dean of IT Business", "photo": "", "category": "deans"},
    {"name": "Park Sang Woo", "position": "Dean of Korean Philology & English Philology", "photo": "/staff/park_sang_woo.png", "category": "deans"},
    {"name": "Seok-Won Lee", "position": "Dean of Software", "photo": "", "category": "deans"},
    {"name": "Andy Hwang", "position": "Dean of Electrical and Computer Engineering", "photo": "", "category": "deans"},
    {"name": "Ji Hyo Seon", "position": "Professor, Civil Systems Engineering", "photo": "/staff/ji_hyo_seon.png", "category": "lecturers"},
    {"name": "Chang-Hwan Park", "position": "Professor, Civil Systems Engineering", "photo": "/staff/chang_hwan_park.png", "category": "lecturers"},
    {"name": "Hwang Myeon-Eun", "position": "Professor, ECE", "photo": "/staff/hwang_myeon_eun.jpg", "category": "lecturers"},
    {"name": "Kim Yoon Kee", "position": "Professor, ECE", "photo": "/staff/kim_yoon_kee.png", "category": "lecturers"},
    {"name": "Albert Daehyun Park", "position": "Professor, IT Business", "photo": "/staff/albert_park.png", "category": "lecturers"},
    {"name": "Kim Sook", "position": "Professor, Korean Philology", "photo": "/staff/kim_sook.png", "category": "lecturers"},
    {"name": "Shokirov Bakhodir", "position": "English Instructor", "photo": "/staff/shokirov.png", "category": "lecturers"},
    {"name": "Pardayeva Zulaykho", "position": "Associate Professor, English", "photo": "/staff/pardayeva.png", "category": "lecturers"},
]


def find_staff(query: str) -> list[dict]:
    """Find staff members matching a query. Uses key staff list + cached data."""
    query_lower = query.lower()
    results = []

    # Search key staff first
    for s in KEY_STAFF:
        if query_lower in s["name"].lower() or query_lower in s["position"].lower():
            results.append(s)

    # Also search cached data
    data = _get_cached_data() if CACHE_FILE.exists() else {}
    for s in data.get("staff", []):
        if query_lower in s["name"].lower() or query_lower in s.get("position", "").lower():
            if not any(r["name"] == s["name"] for r in results):
                results.append(s)

    return results


def find_staff_by_keywords(message: str) -> list[dict]:
    """Find staff mentioned in a message."""
    msg_lower = message.lower()
    results = []

    # Check for role keywords
    role_keywords = {
        "rector": ["rector", "ректор", "총장"],
        "vice": ["vice-rector", "vice rector", "вице-ректор", "부총장"],
        "dean": ["dean", "декан", "학장"],
    }

    for role, keywords in role_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            for s in KEY_STAFF:
                if role in s["position"].lower() or role in s["category"]:
                    if not any(r["name"] == s["name"] for r in results):
                        results.append(s)

    # Check for specific names
    for s in KEY_STAFF:
        name_parts = s["name"].lower().split()
        if any(part in msg_lower for part in name_parts if len(part) > 3):
            if not any(r["name"] == s["name"] for r in results):
                results.append(s)

    return results
