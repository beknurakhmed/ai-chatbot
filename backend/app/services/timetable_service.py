"""Timetable service — parses AUT schedule from aut.edupage.org via headless browser.

Data flow:
  1. Fetch from edupage → save to DB (via admin /timetable/refresh)
  2. Serve from DB (via get_timetable / get_classes)
  3. JSON file cache is kept as secondary fallback
"""

import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

CACHE_FILE = Path(__file__).parent.parent / "data" / "timetable_cache.json"
CACHE_MAX_AGE = 7 * 86400  # 7 days — refreshes weekly

_cache = None
_cache_time = 0


def _fetch_timetable_data() -> dict:
    """Fetch timetable data from edupage using headless browser."""
    from playwright.sync_api import sync_playwright

    result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        api_data = {}

        def handle_response(response):
            if "regulartt" in response.url:
                try:
                    api_data["tt"] = response.json()
                except Exception:
                    pass

        page.on("response", handle_response)
        page.goto(
            "https://aut.edupage.org/timetable/",
            wait_until="networkidle",
            timeout=30000,
        )
        time.sleep(3)
        browser.close()

    if "tt" not in api_data:
        return {}

    r = api_data["tt"].get("r", {})
    dbi = r.get("dbiAccessorRes", {})
    tables = {t["id"]: t.get("data_rows", []) for t in dbi.get("tables", [])}

    # Build lookup maps
    classes = {c["id"]: c for c in tables.get("classes", [])}
    subjects = {s["id"]: s for s in tables.get("subjects", [])}
    teachers = {t["id"]: t for t in tables.get("teachers", [])}
    classrooms = {cr["id"]: cr for cr in tables.get("classrooms", [])}
    periods = {p["id"]: p for p in tables.get("periods", [])}
    days_list = tables.get("days", [])
    lessons = {l["id"]: l for l in tables.get("lessons", [])}
    cards = tables.get("cards", [])
    groups = {g["id"]: g for g in tables.get("groups", [])}

    # Build schedule per class + room occupancy
    schedule = {}
    room_occupancy = {}  # room -> {day_period -> info}

    for card in cards:
        lesson_id = card.get("lessonid", "")
        lesson = lessons.get(lesson_id, {})

        # Get day (0=Mon, 1=Tue, etc)
        days_str = card.get("days", "00000")
        day_idx = None
        for i, ch in enumerate(days_str):
            if ch == "1":
                day_idx = i
                break

        if day_idx is None or day_idx >= len(days_list):
            continue

        day_name = days_list[day_idx].get("short", f"Day{day_idx}")

        # Get period
        period_id = card.get("period", "")
        period = periods.get(period_id, {})
        period_name = period.get("short", period.get("name", ""))
        start = period.get("starttime", "")
        end = period.get("endtime", "")
        time_str = f"{start}-{end}" if start else period_name

        # Get subject
        subject_id = lesson.get("subjectid", "")
        subject = subjects.get(subject_id, {})
        subject_name = subject.get("name", subject.get("short", "Unknown"))

        # Get teacher(s)
        teacher_names = []
        for tid in lesson.get("teacherids", []):
            t = teachers.get(tid, {})
            teacher_names.append(t.get("short", ""))

        # Get classroom(s)
        room_names = []
        for rid in card.get("classroomids", []):
            cr = classrooms.get(rid, {})
            room_names.append(cr.get("short", cr.get("name", "")))

        # Get class(es)
        for cid in lesson.get("classids", []):
            cls = classes.get(cid, {})
            class_name = cls.get("short", cls.get("name", ""))

            if class_name not in schedule:
                schedule[class_name] = []

            entry = {
                "day": day_name,
                "period": period_name,
                "time": time_str,
                "subject": subject_name,
                "teacher": ", ".join(teacher_names),
                "room": ", ".join(room_names),
            }

            schedule[class_name].append(entry)

            # Also track room occupancy
            for rn in room_names:
                if rn:
                    key = f"{day_name}_{period_name}"
                    if rn not in room_occupancy:
                        room_occupancy[rn] = {}
                    room_occupancy[rn][key] = {
                        "class": class_name,
                        "subject": subject_name,
                        "teacher": ", ".join(teacher_names),
                    }

    # Sort each class schedule by day then time
    day_order = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
    for cls_name in schedule:
        schedule[cls_name].sort(key=lambda x: (day_order.get(x["day"], 9), x["time"]))

    result = {
        "schedule": schedule,
        "room_occupancy": room_occupancy,
        "classes": [c.get("short", c.get("name", "")) for c in classes.values()],
        "teachers": [t.get("short", "") for t in teachers.values()],
        "subjects": [s.get("name", s.get("short", "")) for s in subjects.values()],
        "classrooms": [cr.get("short", cr.get("name", "")) for cr in classrooms.values()],
        "periods": [
            {"name": p.get("short", ""), "start": p.get("starttime", ""), "end": p.get("endtime", "")}
            for p in sorted(periods.values(), key=lambda x: x.get("starttime", ""))
        ],
        "updated": datetime.now().isoformat(),
    }

    return result


def _get_cached_data() -> dict:
    """Get timetable data, using cache if fresh enough."""
    global _cache, _cache_time

    now = time.time()

    # Memory cache
    if _cache and (now - _cache_time) < CACHE_MAX_AGE:
        return _cache

    # File cache
    stale_data = None
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            file_age = now - CACHE_FILE.stat().st_mtime
            if file_age < CACHE_MAX_AGE:
                _cache = data
                _cache_time = now
                return data
            # Cache is stale but keep as fallback
            stale_data = data
        except Exception:
            pass

    # Fetch fresh data
    try:
        data = _fetch_timetable_data()
        if data:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            _cache = data
            _cache_time = now
            return data
    except Exception as e:
        print(f"Timetable fetch error: {e}")

    # Use stale cache as fallback rather than returning nothing
    if stale_data:
        print("[Timetable] Using stale cache as fallback")
        _cache = stale_data
        _cache_time = now
        return stale_data

    return {}


async def save_timetable_to_db(data: dict) -> int:
    """Save parsed timetable data to database. Returns number of entries saved."""
    from sqlalchemy import delete
    from ..database import async_session
    from ..models.db_models import TimetableEntry

    schedule = data.get("schedule", {})
    if not schedule:
        return 0

    async with async_session() as db:
        # Clear existing entries
        await db.execute(delete(TimetableEntry))
        count = 0
        for group_name, lessons in schedule.items():
            for lesson in lessons:
                entry = TimetableEntry(
                    group=group_name,
                    day=lesson.get("day", ""),
                    period=lesson.get("period", ""),
                    time_str=lesson.get("time", ""),
                    subject=lesson.get("subject", ""),
                    teacher=lesson.get("teacher", ""),
                    room=lesson.get("room", ""),
                )
                db.add(entry)
                count += 1
        await db.commit()
    return count


async def _get_timetable_from_db(group: str) -> dict | None:
    """Try to get timetable for a group from DB."""
    from sqlalchemy import select
    from ..database import async_session
    from ..models.db_models import TimetableEntry

    try:
        async with async_session() as db:
            # Check if DB has any entries
            result = await db.execute(
                select(TimetableEntry).where(
                    TimetableEntry.is_active == True,
                    TimetableEntry.group.ilike(f"%{group}%")
                ).order_by(TimetableEntry.day, TimetableEntry.period)
            )
            entries = result.scalars().all()
            if not entries:
                return None

            matched_group = entries[0].group
            lessons = [
                {
                    "day": e.day,
                    "period": e.period,
                    "time": e.time_str,
                    "subject": e.subject,
                    "teacher": e.teacher or "",
                    "room": e.room or "",
                }
                for e in entries if e.group == matched_group
            ]
            return {
                "available": True,
                "group": matched_group,
                "lessons": lessons,
                "count": len(lessons),
            }
    except Exception:
        return None


async def _get_classes_from_db() -> list[str]:
    """Get all unique group names from DB."""
    from sqlalchemy import select, distinct
    from ..database import async_session
    from ..models.db_models import TimetableEntry

    try:
        async with async_session() as db:
            result = await db.execute(
                select(distinct(TimetableEntry.group))
                .where(TimetableEntry.is_active == True)
                .order_by(TimetableEntry.group)
            )
            return [row[0] for row in result.fetchall()]
    except Exception:
        return []


async def get_timetable(group: str = "", date_str: str = "") -> dict:
    """Get timetable for a specific group. Reads from DB first, falls back to JSON cache."""
    if not group:
        classes = await get_classes()
        return {
            "available": True,
            "classes": classes,
            "message": "Specify a group name to see the schedule.",
        }

    # Try DB first
    db_result = await _get_timetable_from_db(group)
    if db_result:
        return db_result

    # Fallback to JSON cache
    data = await asyncio.to_thread(_get_cached_data)
    if not data:
        return {
            "available": False,
            "message": "Could not load timetable. Visit aut.edupage.org/timetable",
            "url": "https://aut.edupage.org/timetable/",
        }

    _CYR_TO_LAT = str.maketrans(
        "АВСЕНКМОРТХУаvsенкмортху",
        "ABCEHKMOPTXYabcehkmoptxy",
    )
    schedule = data.get("schedule", {})
    matched = None
    group_norm = group.translate(_CYR_TO_LAT).lower()
    for cls_name, lessons in schedule.items():
        if group_norm in cls_name.lower():
            matched = cls_name
            break

    if not matched:
        return {
            "available": True,
            "classes": data.get("classes", []),
            "message": f"Group '{group}' not found. Available groups listed.",
        }

    return {
        "available": True,
        "group": matched,
        "lessons": schedule[matched],
        "count": len(schedule[matched]),
        "periods": data.get("periods", []),
    }


async def get_classes() -> list[str]:
    # Try DB first
    db_classes = await _get_classes_from_db()
    if db_classes:
        return db_classes
    # Fallback to JSON cache
    data = await asyncio.to_thread(_get_cached_data)
    return data.get("classes", [])


async def get_teachers() -> list[str]:
    data = await asyncio.to_thread(_get_cached_data)
    return data.get("teachers", [])


async def get_subjects() -> list[str]:
    data = await asyncio.to_thread(_get_cached_data)
    return data.get("subjects", [])


# Day name to code mapping
DAY_NAMES_TO_CODE = {
    "monday": "Mo", "mon": "Mo", "mo": "Mo",
    "tuesday": "Tu", "tue": "Tu", "tu": "Tu",
    "wednesday": "We", "wed": "We", "we": "We",
    "thursday": "Th", "thu": "Th", "th": "Th",
    "friday": "Fr", "fri": "Fr", "fr": "Fr",
}

PERIOD_TIMES = {
    "A": ("08:30", "09:45"),
    "B": ("10:00", "11:15"),
    "C": ("11:30", "12:45"),
    "D": ("13:30", "14:45"),
    "E": ("15:00", "16:15"),
    "F": ("16:30", "17:45"),
    "G": ("18:00", "19:15"),
}


def _time_to_period(time_str: str) -> str | None:
    """Convert a time like '12:00' to the matching period letter."""
    try:
        h, m = map(int, time_str.split(":"))
        t = h * 60 + m
        for period, (start, end) in PERIOD_TIMES.items():
            sh, sm = map(int, start.split(":"))
            eh, em = map(int, end.split(":"))
            if sh * 60 + sm <= t <= eh * 60 + em:
                return period
        # If between periods, find the next one
        for period, (start, _) in PERIOD_TIMES.items():
            sh, sm = map(int, start.split(":"))
            if t < sh * 60 + sm:
                return period
    except Exception:
        pass
    return None


async def find_free_rooms(day: str = "", time_str: str = "", period: str = "") -> dict:
    """Find classrooms that are free at a given day+time.

    Args:
        day: Day name (Monday, Mon, Mo, etc.) — defaults to today
        time_str: Time like "12:00" — used to find the period
        period: Period letter (A-G) — overrides time_str
    """
    data = await asyncio.to_thread(_get_cached_data)
    if not data:
        return {"available": False, "message": "Timetable data not loaded."}

    # Resolve day
    if day:
        day_code = DAY_NAMES_TO_CODE.get(day.lower().strip(), day.strip()[:2].capitalize())
    else:
        import calendar
        today = datetime.now().weekday()  # 0=Mon
        codes = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        day_code = codes[today] if today < 5 else "Mo"

    # Resolve period
    if not period and time_str:
        period = _time_to_period(time_str) or "C"
    elif not period:
        # Default: current time
        now = datetime.now()
        period = _time_to_period(f"{now.hour}:{now.minute:02d}") or "C"

    # Get all rooms and check occupancy
    all_rooms = data.get("classrooms", [])
    room_occ = data.get("room_occupancy", {})
    key = f"{day_code}_{period}"

    free_rooms = []
    busy_rooms = []

    for room in sorted(all_rooms):
        if not room:
            continue
        occ = room_occ.get(room, {}).get(key)
        if occ:
            busy_rooms.append({
                "room": room,
                "class": occ["class"],
                "subject": occ["subject"],
                "teacher": occ["teacher"],
            })
        else:
            free_rooms.append(room)

    period_time = PERIOD_TIMES.get(period, ("?", "?"))

    return {
        "available": True,
        "day": day_code,
        "period": period,
        "time": f"{period_time[0]}-{period_time[1]}",
        "free_rooms": free_rooms,
        "free_count": len(free_rooms),
        "busy_rooms": busy_rooms,
        "busy_count": len(busy_rooms),
        "total_rooms": len(all_rooms),
    }
