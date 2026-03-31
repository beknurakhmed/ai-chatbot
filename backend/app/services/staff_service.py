"""Staff service — parses staff data from ajou.uz and serves it."""

import time
import re
from pathlib import Path
import httpx

# In-memory cache of staff from DB
_db_staff_cache: list[dict] = []

BASE_URL = "https://ajou.uz"

# Staff pages to parse
PAGES = [
    ("/en/vice-rectors/rector", "leadership"),
    ("/en/vice-rectors/vice-rectors", "leadership"),
    ("/en/vice-rectors/dean", "deans"),
    ("/en/staff/index?category=1", "staff"),
    ("/en/staff/lecturers?category=2", "lecturers"),
]


def _clean(text: str) -> str:
    """Decode HTML entities and strip whitespace."""
    text = re.sub(r'&ndash;', '–', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    return text.strip()


def _parse_staff_page(html: str, category: str) -> list[dict]:
    """Extract staff members from HTML page."""
    members = []

    if category in ("leadership", "deans"):
        photos = re.findall(r'/uploads/rectors/[^"]+', html)
        spans_18 = re.findall(
            r'font-size:18\.0pt[^>]*>.*?<span[^>]*>([^<]+)</span>',
            html, re.DOTALL
        )
        spans_18 = [_clean(s) for s in spans_18 if s.strip()]
        pos_keywords = {'doctor', 'dean', 'rector', 'vice', 'professor', 'phd', 'ph.d', 'associate'}

        i = 0
        photo_idx = 0
        while i < len(spans_18):
            s = spans_18[i]
            is_pos = any(kw in s.lower() for kw in pos_keywords) and not re.match(r'^Prof\.\s+[A-Z]', s)
            if not is_pos:
                name = s
                position = _clean(spans_18[i + 1]) if i + 1 < len(spans_18) else ""
                members.append({
                    "name": name,
                    "position": position,
                    "photo": f"{BASE_URL}{photos[photo_idx]}" if photo_idx < len(photos) else "",
                    "category": category,
                })
                photo_idx += 1
                i += 2
            else:
                i += 1

    else:
        cards = re.findall(
            r'<div[^>]*class="[^"]*singel-teachers[^"]*"[^>]*>(.*?)</div>\s*<!--',
            html, re.DOTALL | re.IGNORECASE
        )
        if not cards:
            cards = re.findall(
                r'<div[^>]*class="[^"]*singel-teachers[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
                html, re.DOTALL | re.IGNORECASE
            )

        for card_html in cards:
            photo_m = re.search(r'src="(/uploads/staff/[^"]+)"', card_html)
            name_m = re.search(r'<h6[^>]*>([^<]+)</h6>', card_html)
            pos_m = re.search(r'<span[^>]*>([^<]+)</span>', card_html)

            if name_m:
                name = re.split(r'\s*/\s*(?:Ph\.?D|Associate Professor)', _clean(name_m.group(1)))[0].strip()
                members.append({
                    "name": name,
                    "position": _clean(pos_m.group(1)) if pos_m else category,
                    "photo": f"{BASE_URL}{photo_m.group(1)}" if photo_m else "",
                    "category": category,
                })

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


async def load_staff_cache() -> None:
    """Load staff from DB into in-memory cache. Call on startup."""
    global _db_staff_cache
    from sqlalchemy import select
    from ..database import async_session
    from ..models.db_models import StaffMember

    try:
        async with async_session() as db:
            result = await db.execute(
                select(StaffMember).where(StaffMember.is_active == True)
            )
            members = result.scalars().all()
            _db_staff_cache = [
                {"name": m.name, "position": m.position, "photo": m.photo, "category": m.category}
                for m in members
            ]
    except Exception:
        _db_staff_cache = []


async def save_staff_to_db(staff_list: list[dict]) -> int:
    """Save staff list to DB, replacing existing records."""
    from sqlalchemy import delete
    from ..database import async_session
    from ..models.db_models import StaffMember

    async with async_session() as db:
        await db.execute(delete(StaffMember))
        for s in staff_list:
            member = StaffMember(
                name=s["name"],
                position=s.get("position", ""),
                photo=s.get("photo", ""),
                category=s.get("category", ""),
            )
            db.add(member)
        await db.commit()
    # Refresh in-memory cache
    await load_staff_cache()
    return len(staff_list)


async def find_staff_from_db(query: str) -> list[dict]:
    """Search staff from DB by name or position."""
    from sqlalchemy import select, or_
    from ..database import async_session
    from ..models.db_models import StaffMember

    try:
        async with async_session() as db:
            result = await db.execute(
                select(StaffMember).where(
                    StaffMember.is_active == True,
                    or_(
                        StaffMember.name.ilike(f"%{query}%"),
                        StaffMember.position.ilike(f"%{query}%"),
                    )
                )
            )
            members = result.scalars().all()
            return [{"name": m.name, "position": m.position, "photo": m.photo, "category": m.category} for m in members]
    except Exception:
        return []


def find_staff(query: str) -> list[dict]:
    """Find staff members matching a query. Searches DB staff only."""
    query_lower = query.lower()
    results = []

    for s in _db_staff_cache:
        if query_lower in s["name"].lower() or query_lower in s.get("position", "").lower():
            if not any(r["name"] == s["name"] for r in results):
                results.append(s)

    return results


def find_staff_by_keywords(message: str) -> list[dict]:
    """Find staff mentioned in a message using DB data."""
    msg_lower = message.lower()
    results = []

    staff_list = _db_staff_cache

    if not staff_list:
        return []

    # Check for role keywords
    role_keywords = {
        "rector": ["rector", "ректор", "총장"],
        "vice": ["vice-rector", "vice rector", "вице-ректор", "부총장"],
        "dean": ["dean", "декан", "학장"],
    }

    for role, keywords in role_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            for s in staff_list:
                if role in s.get("position", "").lower() or role in s.get("category", ""):
                    if not any(r["name"] == s["name"] for r in results):
                        results.append(s)

    # Check for specific names
    for s in staff_list:
        name_parts = s["name"].lower().split()
        if any(part in msg_lower for part in name_parts if len(part) > 3):
            if not any(r["name"] == s["name"] for r in results):
                results.append(s)

    return results
