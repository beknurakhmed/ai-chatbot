"""Timetable service — parses AUT schedule from aut.edupage.org via headless browser.

Data flow:
  1. Fetch from edupage → save to DB (via admin /timetable/refresh)
  2. Serve from DB (via get_timetable / get_classes)
"""

import time
from datetime import datetime


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
    """Get timetable for a specific group from DB only."""
    if not group:
        classes = await get_classes()
        return {
            "available": True,
            "classes": classes,
            "message": "Specify a group name to see the schedule.",
        }

    db_result = await _get_timetable_from_db(group)
    if db_result:
        return db_result

    return {
        "available": False,
        "message": "Could not load timetable. Visit aut.edupage.org/timetable",
        "url": "https://aut.edupage.org/timetable/",
    }


async def get_classes() -> list[str]:
    return await _get_classes_from_db()


async def get_teachers() -> list[str]:
    from sqlalchemy import select, distinct
    from ..database import async_session
    from ..models.db_models import TimetableEntry
    try:
        async with async_session() as db:
            result = await db.execute(
                select(distinct(TimetableEntry.teacher))
                .where(TimetableEntry.is_active == True, TimetableEntry.teacher != None, TimetableEntry.teacher != "")
            )
            return [row[0] for row in result.fetchall()]
    except Exception:
        return []


async def get_subjects() -> list[str]:
    from sqlalchemy import select, distinct
    from ..database import async_session
    from ..models.db_models import TimetableEntry
    try:
        async with async_session() as db:
            result = await db.execute(
                select(distinct(TimetableEntry.subject))
                .where(TimetableEntry.is_active == True)
            )
            return [row[0] for row in result.fetchall()]
    except Exception:
        return []


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
    """Find classrooms that are free at a given day+time using Room + TimetableEntry tables."""
    from sqlalchemy import select
    from ..database import async_session
    from ..models.db_models import TimetableEntry, Room

    # Resolve day
    if day:
        day_code = DAY_NAMES_TO_CODE.get(day.lower().strip(), day.strip()[:2].capitalize())
    else:
        today = datetime.now().weekday()  # 0=Mon
        codes = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        day_code = codes[today] if today < 5 else "Mo"

    # Resolve period
    if not period and time_str:
        period = _time_to_period(time_str) or "C"
    elif not period:
        now = datetime.now()
        period = _time_to_period(f"{now.hour}:{now.minute:02d}") or "C"

    try:
        async with async_session() as db:
            # Get all rooms from Room table
            rooms_result = await db.execute(
                select(Room).where(Room.is_active == True).order_by(Room.block, Room.name)
            )
            all_room_records = rooms_result.scalars().all()

            if not all_room_records:
                return {"available": False, "message": "No rooms in database. Sync rooms from timetable first."}

            # Build room info map
            room_info = {r.name: {"block": r.block or "", "floor": r.floor} for r in all_room_records}
            all_room_names = [r.name for r in all_room_records]

            # Get busy rooms for this day+period
            busy_result = await db.execute(
                select(TimetableEntry)
                .where(
                    TimetableEntry.is_active == True,
                    TimetableEntry.day == day_code,
                    TimetableEntry.period == period,
                )
            )
            busy_entries = busy_result.scalars().all()

            busy_rooms_set = set()
            busy_rooms = []
            for e in busy_entries:
                if e.room and e.room not in busy_rooms_set:
                    busy_rooms_set.add(e.room)
                    info = room_info.get(e.room, {})
                    busy_rooms.append({
                        "room": e.room,
                        "block": info.get("block", ""),
                        "class": e.group,
                        "subject": e.subject,
                        "teacher": e.teacher or "",
                    })

            # Group free rooms by block
            free_rooms = []
            free_by_block = {}
            for name in all_room_names:
                if name not in busy_rooms_set:
                    free_rooms.append(name)
                    block = room_info[name].get("block", "Other")
                    free_by_block.setdefault(block, []).append(name)

        period_time = PERIOD_TIMES.get(period, ("?", "?"))

        return {
            "available": True,
            "day": day_code,
            "period": period,
            "time": f"{period_time[0]}-{period_time[1]}",
            "free_rooms": free_rooms,
            "free_by_block": free_by_block,
            "free_count": len(free_rooms),
            "busy_rooms": busy_rooms,
            "busy_count": len(busy_rooms),
            "total_rooms": len(all_room_names),
        }
    except Exception:
        return {"available": False, "message": "No rooms in database."}
