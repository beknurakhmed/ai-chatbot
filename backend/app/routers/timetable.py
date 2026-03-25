from fastapi import APIRouter, Query
from ..services.timetable_service import get_timetable, get_classes, get_teachers, get_subjects, find_free_rooms

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


@router.get("")
async def timetable_endpoint(
    group: str = Query(default=""),
    date: str = Query(default=""),
):
    """Get timetable for a group. First call may be slow (fetching data)."""
    return await get_timetable(group, date)


@router.get("/classes")
async def classes_endpoint():
    """Get list of all class groups."""
    return {"classes": await get_classes()}


@router.get("/teachers")
async def teachers_endpoint():
    """Get list of all teachers."""
    return {"teachers": await get_teachers()}


@router.get("/subjects")
async def subjects_endpoint():
    """Get list of all subjects."""
    return {"subjects": await get_subjects()}


@router.get("/free-rooms")
async def free_rooms_endpoint(
    day: str = Query(default=""),
    time: str = Query(default=""),
    period: str = Query(default=""),
):
    """Find free classrooms at a given day and time."""
    return await find_free_rooms(day, time, period)
