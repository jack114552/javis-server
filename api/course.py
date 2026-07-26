"""课程表 CRUD API"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from db.database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/courses", tags=["courses"])


class CourseCreate(BaseModel):
    name: str
    teacher: str = ""
    location: str = ""
    day_of_week: int = Field(..., ge=1, le=7, description="1=周一 至 7=周日")
    start_time: str = Field(..., description="HH:MM 格式")
    end_time: str = Field(..., description="HH:MM 格式")
    week_type: str = "all"  # all / odd / even


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    teacher: Optional[str] = None
    location: Optional[str] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    week_type: Optional[str] = None


@router.get("")
async def list_courses(
    day: Optional[int] = Query(None, ge=1, le=7, description="按星期几筛选"),
):
    """获取课程列表"""
    conn = get_connection()
    if day:
        rows = conn.execute(
            "SELECT * FROM courses WHERE day_of_week = ? ORDER BY start_time ASC",
            (day,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM courses ORDER BY day_of_week, start_time ASC"
        ).fetchall()
    return {"courses": [dict(r) for r in rows], "count": len(rows)}


@router.post("")
async def create_course(course: CourseCreate):
    """添加课程"""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO courses (name, teacher, location, day_of_week, start_time, end_time, week_type)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (course.name, course.teacher, course.location, course.day_of_week,
         course.start_time, course.end_time, course.week_type),
    )
    conn.commit()
    course_id = cur.lastrowid
    logger.info(f"已添加课程 #{course_id}: {course.name}")
    return {"success": True, "id": course_id}


@router.get("/{course_id}")
async def get_course(course_id: int):
    """获取单个课程"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="课程不存在")
    return dict(row)


@router.put("/{course_id}")
async def update_course(course_id: int, update: CourseUpdate):
    """更新课程"""
    conn = get_connection()
    existing = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="课程不存在")

    fields = []
    values = []
    for key, value in update.dict(exclude_unset=True).items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    if not fields:
        return {"success": False, "error": "没有需要更新的字段"}

    values.append(course_id)
    conn.execute(
        f"UPDATE courses SET {', '.join(fields)} WHERE id = ?",
        values,
    )
    conn.commit()
    return {"success": True}


@router.delete("/{course_id}")
async def delete_course(course_id: int):
    """删除课程"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="课程不存在")
    return {"success": True}
