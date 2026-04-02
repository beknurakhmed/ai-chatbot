"""Seed service — migrates hardcoded data to DB on first startup.

Runs only if the tables are empty. Safe to call on every startup.
"""

import re
from sqlalchemy import select, func
from ..database import async_session
from ..models.db_models import KnowledgeEntry, Keyword, StaffMember, Building


# ── Knowledge entries ────────────────────────────────────────────────────────

def _parse_knowledge_sections() -> list[dict]:
    """Parse AUT_KNOWLEDGE markdown into individual DB entries by section."""
    from .knowledge_base import AUT_KNOWLEDGE

    entries = []
    # Split by ## headings
    sections = re.split(r'\n## ', AUT_KNOWLEDGE)

    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().splitlines()
        title = lines[0].strip().lstrip('#').strip()
        content = '\n'.join(lines[1:]).strip()

        if not content:
            continue

        # Derive category from title
        title_lower = title.lower()
        if any(w in title_lower for w in ['general', 'about']):
            category = 'general'
        elif any(w in title_lower for w in ['history']):
            category = 'history'
        elif any(w in title_lower for w in ['why choose', 'why aut']):
            category = 'general'
        elif any(w in title_lower for w in ['fact', 'statistic']):
            category = 'facts'
        elif any(w in title_lower for w in ['leadership', 'rector', 'vice']):
            category = 'leadership'
        elif any(w in title_lower for w in ['subject', 'curriculum']):
            category = 'curriculum'
        elif 'academic' in title_lower or 'program' in title_lower or 'department' in title_lower:
            category = 'academic'
        elif 'tuition' in title_lower or 'fee' in title_lower:
            category = 'fees'
        elif 'admission' in title_lower:
            category = 'admission'
        elif any(w in title_lower for w in ['campus', 'building', 'room', 'facilit']):
            category = 'campus'
        elif any(w in title_lower for w in ['transport', 'bus', 'how to reach']):
            category = 'transport'
        elif 'student' in title_lower or 'club' in title_lower:
            category = 'student_life'
        elif 'online' in title_lower or 'platform' in title_lower:
            category = 'platforms'
        elif 'research' in title_lower:
            category = 'research'
        elif 'timetable' in title_lower or 'schedule' in title_lower:
            category = 'timetable'
        elif 'contact' in title_lower:
            category = 'contacts'
        else:
            category = 'general'

        entries.append({
            'category': category,
            'title': title,
            'content': content,
            'language': 'en',
        })

    return entries


# ── Keywords ─────────────────────────────────────────────────────────────────

SEED_KEYWORDS = [
    # Timetable
    {"keyword": "timetable", "intent": "timetable", "language": "en"},
    {"keyword": "schedule", "intent": "timetable", "language": "en"},
    {"keyword": "lesson", "intent": "timetable", "language": "en"},
    {"keyword": "class schedule", "intent": "timetable", "language": "en"},
    {"keyword": "what class", "intent": "timetable", "language": "en"},
    {"keyword": "расписание", "intent": "timetable", "language": "ru"},
    {"keyword": "пары", "intent": "timetable", "language": "ru"},
    {"keyword": "занятия", "intent": "timetable", "language": "ru"},
    {"keyword": "dars", "intent": "timetable", "language": "uz"},
    {"keyword": "jadval", "intent": "timetable", "language": "uz"},
    {"keyword": "시간표", "intent": "timetable", "language": "kr"},
    {"keyword": "수업", "intent": "timetable", "language": "kr"},

    # Map / Location
    {"keyword": "map", "intent": "map", "language": "en"},
    {"keyword": "campus map", "intent": "map", "language": "en"},
    {"keyword": "where is", "intent": "map", "language": "en"},
    {"keyword": "location", "intent": "map", "language": "en"},
    {"keyword": "building", "intent": "map", "language": "en"},
    {"keyword": "how to get", "intent": "map", "language": "en"},
    {"keyword": "карта", "intent": "map", "language": "ru"},
    {"keyword": "где находится", "intent": "map", "language": "ru"},
    {"keyword": "здание", "intent": "map", "language": "ru"},
    {"keyword": "корпус", "intent": "map", "language": "ru"},
    {"keyword": "xarita", "intent": "map", "language": "uz"},
    {"keyword": "qayerda", "intent": "map", "language": "uz"},
    {"keyword": "bino", "intent": "map", "language": "uz"},
    {"keyword": "지도", "intent": "map", "language": "kr"},
    {"keyword": "어디", "intent": "map", "language": "kr"},
    {"keyword": "건물", "intent": "map", "language": "kr"},

    # Free rooms
    {"keyword": "free room", "intent": "free_room", "language": "en"},
    {"keyword": "empty room", "intent": "free_room", "language": "en"},
    {"keyword": "available room", "intent": "free_room", "language": "en"},
    {"keyword": "vacant", "intent": "free_room", "language": "en"},
    {"keyword": "свободн", "intent": "free_room", "language": "ru"},
    {"keyword": "пустой", "intent": "free_room", "language": "ru"},
    {"keyword": "bo'sh xona", "intent": "free_room", "language": "uz"},
    {"keyword": "빈 교실", "intent": "free_room", "language": "kr"},

    # Staff
    {"keyword": "rector", "intent": "staff", "language": "en"},
    {"keyword": "dean", "intent": "staff", "language": "en"},
    {"keyword": "professor", "intent": "staff", "language": "en"},
    {"keyword": "teacher", "intent": "staff", "language": "en"},
    {"keyword": "staff", "intent": "staff", "language": "en"},
    {"keyword": "ректор", "intent": "staff", "language": "ru"},
    {"keyword": "декан", "intent": "staff", "language": "ru"},
    {"keyword": "преподаватель", "intent": "staff", "language": "ru"},
    {"keyword": "rektor", "intent": "staff", "language": "uz"},
    {"keyword": "o'qituvchi", "intent": "staff", "language": "uz"},
    {"keyword": "총장", "intent": "staff", "language": "kr"},
    {"keyword": "교수", "intent": "staff", "language": "kr"},

    # News
    {"keyword": "news", "intent": "news", "language": "en"},
    {"keyword": "events", "intent": "news", "language": "en"},
    {"keyword": "announcement", "intent": "news", "language": "en"},
    {"keyword": "новости", "intent": "news", "language": "ru"},
    {"keyword": "yangiliklar", "intent": "news", "language": "uz"},
    {"keyword": "뉴스", "intent": "news", "language": "kr"},

    # Admission
    {"keyword": "admission", "intent": "admission", "language": "en"},
    {"keyword": "apply", "intent": "admission", "language": "en"},
    {"keyword": "enroll", "intent": "admission", "language": "en"},
    {"keyword": "поступить", "intent": "admission", "language": "ru"},
    {"keyword": "qabul", "intent": "admission", "language": "uz"},
    {"keyword": "입학", "intent": "admission", "language": "kr"},

    # Contacts
    {"keyword": "contact", "intent": "contacts", "language": "en"},
    {"keyword": "phone", "intent": "contacts", "language": "en"},
    {"keyword": "email", "intent": "contacts", "language": "en"},
    {"keyword": "контакт", "intent": "contacts", "language": "ru"},
    {"keyword": "telefon", "intent": "contacts", "language": "uz"},
    {"keyword": "연락처", "intent": "contacts", "language": "kr"},
]


# ── Staff seed data ──────────────────────────────────────────────────────

SEED_STAFF = [
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


SEED_BUILDINGS = [
    {"num": 1, "name": "Entrance Gate", "description": "Main entry to campus", "color": "bg-gray-500"},
    {"num": 2, "name": "A Block", "description": "Lesson rooms, Library", "color": "bg-blue-500"},
    {"num": 3, "name": "B Block", "description": "Administration, Lesson rooms", "color": "bg-emerald-500"},
    {"num": 4, "name": "C Block", "description": "Canteen, Conference Hall, Sports Hall", "color": "bg-orange-500"},
    {"num": 5, "name": "Dormitory", "description": "Student housing", "color": "bg-purple-500"},
    {"num": 6, "name": "Parking lot", "description": "Vehicle parking", "color": "bg-pink-500"},
]


async def reseed_knowledge() -> int:
    """Delete all knowledge entries and re-seed from AUT_KNOWLEDGE. Returns count."""
    from sqlalchemy import delete
    async with async_session() as db:
        await db.execute(delete(KnowledgeEntry))
        entries = _parse_knowledge_sections()
        for e in entries:
            db.add(KnowledgeEntry(**e))
        await db.commit()
    # Refresh the in-memory cache
    from .knowledge_db_service import refresh
    await refresh()
    print(f"[Seed] Re-seeded {len(entries)} knowledge entries")
    return len(entries)


# ── Main seed function ────────────────────────────────────────────────────────

async def seed_if_empty() -> dict:
    """Seed DB with hardcoded data if tables are empty. Returns counts of inserted records."""
    counts = {"knowledge": 0, "keywords": 0, "staff": 0, "buildings": 0}

    async with async_session() as db:
        # Seed knowledge entries
        kb_count = await db.scalar(select(func.count()).select_from(KnowledgeEntry))
        if kb_count == 0:
            entries = _parse_knowledge_sections()
            for e in entries:
                db.add(KnowledgeEntry(**e))
            counts["knowledge"] = len(entries)

        # Seed keywords
        kw_count = await db.scalar(select(func.count()).select_from(Keyword))
        if kw_count == 0:
            for kw in SEED_KEYWORDS:
                db.add(Keyword(**kw))
            counts["keywords"] = len(SEED_KEYWORDS)

        # Seed staff
        staff_count = await db.scalar(select(func.count()).select_from(StaffMember))
        if staff_count == 0:
            for s in SEED_STAFF:
                db.add(StaffMember(**s))
            counts["staff"] = len(SEED_STAFF)

        # Seed buildings
        bld_count = await db.scalar(select(func.count()).select_from(Building))
        if bld_count == 0:
            for b in SEED_BUILDINGS:
                db.add(Building(**b))
            counts["buildings"] = len(SEED_BUILDINGS)

        await db.commit()

    if any(counts.values()):
        print(f"[Seed] Inserted: {counts}")
    else:
        print("[Seed] DB already populated, skipping.")

    return counts
