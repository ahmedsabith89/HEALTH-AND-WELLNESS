from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.database import db_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/workspace", tags=["presentation_workspace"])

class SectionCreate(BaseModel):
    student_id: int
    title: str = Field(..., min_length=2)
    speaking_seconds: int = Field(..., ge=30, le=900)
    notes: Optional[str] = ""

class SectionUpdate(BaseModel):
    student_id: Optional[int] = None
    title: Optional[str] = None
    speaking_seconds: Optional[int] = None
    notes: Optional[str] = None
    order_index: Optional[int] = None

def get_group_for_user(conn, user: Dict[str, Any], requested_group_id: Optional[int] = None) -> int:
    """Validate user access to group workspace."""
    cursor = conn.cursor()
    if user["role"] == "ADMIN":
        if not requested_group_id:
            raise HTTPException(status_code=400, detail="Group ID required for admin access")
        return requested_group_id
    else:
        cursor.execute("SELECT group_id FROM students WHERE id = ?", (user["id"],))
        s_row = cursor.fetchone()
        if not s_row or not s_row["group_id"]:
            raise HTTPException(status_code=403, detail="You are not assigned to any group")
        group_id = s_row["group_id"]
        if requested_group_id and requested_group_id != group_id:
            raise HTTPException(status_code=403, detail="Access denied: You cannot view or edit another group's workspace")
        return group_id

@router.get("/group/{group_id}")
def get_group_workspace(group_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns full workspace details for a group:
    - Group info, assigned topic
    - Group members list with speaking confirmation status
    - Speaking sections with timing and notes
    - Readiness checklist (all members assigned, all confirmed, total time <= 15:00)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        authorized_group_id = get_group_for_user(conn, user, group_id)

        # 1. Group info
        cursor.execute(
            """
            SELECT g.id, g.group_number, g.max_members, g.finalized,
                   t.id as topic_id, t.title as topic_title, t.description as topic_description
            FROM groups g
            LEFT JOIN topics t ON g.topic_id = t.id
            WHERE g.id = ?
            """,
            (authorized_group_id,)
        )
        group = cursor.fetchone()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # 2. Members info
        cursor.execute(
            """
            SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email,
                   (SELECT confirmed_at FROM speaking_confirmations sc WHERE sc.group_id = s.group_id AND sc.student_id = s.id) as confirmed_at
            FROM students s
            WHERE s.group_id = ?
            ORDER BY s.roll_number ASC
            """,
            (authorized_group_id,)
        )
        members = [dict(m) for m in cursor.fetchall()]

        # 3. Sections info
        cursor.execute(
            """
            SELECT ps.id, ps.group_id, ps.student_id, ps.title, ps.speaking_seconds, ps.notes, ps.order_index,
                   s.full_name as presenter_name, s.roll_number as presenter_roll
            FROM presentation_sections ps
            JOIN students s ON ps.student_id = s.id
            WHERE ps.group_id = ?
            ORDER BY ps.order_index ASC, ps.id ASC
            """,
            (authorized_group_id,)
        )
        sections = [dict(sec) for sec in cursor.fetchall()]

        # 4. Compute timings and readiness checks
        total_seconds = sum(sec["speaking_seconds"] for sec in sections)
        assigned_student_ids = {sec["student_id"] for sec in sections}
        member_ids = {m["id"] for m in members}

        unassigned_members = [m for m in members if m["id"] not in assigned_student_ids]
        all_members_assigned = (len(unassigned_members) == 0 and len(members) > 0)

        confirmed_members_count = sum(1 for m in members if m["confirmed_at"] is not None)
        all_confirmed = (confirmed_members_count == len(members) and len(members) > 0)

        within_time_limit = (total_seconds <= 900)
        has_min_time = (total_seconds >= 60)

        is_presentation_ready = (
            bool(group["finalized"]) and
            group["topic_id"] is not None and
            all_members_assigned and
            all_confirmed and
            within_time_limit and
            has_min_time
        )

        return {
            "group": dict(group),
            "members": members,
            "sections": sections,
            "checklist": {
                "member_count": len(members),
                "all_members_assigned": all_members_assigned,
                "unassigned_count": len(unassigned_members),
                "unassigned_members": [m["full_name"] for m in unassigned_members],
                "confirmed_members_count": confirmed_members_count,
                "all_confirmed": all_confirmed,
                "total_seconds": total_seconds,
                "total_time_formatted": f"{total_seconds // 60}:{total_seconds % 60:02d}",
                "max_seconds": 900,
                "max_time_formatted": "15:00",
                "within_time_limit": within_time_limit,
                "is_presentation_ready": is_presentation_ready,
                "status_badge": "READY" if is_presentation_ready else (
                    "OVER_TIME" if not within_time_limit else "IN_PROGRESS"
                )
            }
        }

@router.post("/group/{group_id}/sections")
def create_section(group_id: int, sec: SectionCreate, user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new speaking section in the group presentation planner."""
    with db_session() as conn:
        cursor = conn.cursor()
        authorized_group_id = get_group_for_user(conn, user, group_id)

        # Verify student belongs to this group
        cursor.execute("SELECT id FROM students WHERE id = ? AND group_id = ?", (sec.student_id, authorized_group_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Assigned speaker must be a member of this group")

        # Get highest order_index
        cursor.execute("SELECT COALESCE(MAX(order_index), 0) + 1 FROM presentation_sections WHERE group_id = ?", (authorized_group_id,))
        next_order = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO presentation_sections (group_id, student_id, title, speaking_seconds, notes, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (authorized_group_id, sec.student_id, sec.title.strip(), sec.speaking_seconds, (sec.notes or "").strip(), next_order)
        )
        new_id = cursor.lastrowid

    return {"status": "success", "id": new_id, "message": "Speaking section added"}

@router.put("/sections/{section_id}")
def update_section(section_id: int, sec: SectionUpdate, user: Dict[str, Any] = Depends(get_current_user)):
    """Edit an existing speaking section."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM presentation_sections WHERE id = ?", (section_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Section not found")

        authorized_group_id = get_group_for_user(conn, user, existing["group_id"])

        target_student_id = sec.student_id if sec.student_id is not None else existing["student_id"]
        # Verify student belongs to this group
        cursor.execute("SELECT id FROM students WHERE id = ? AND group_id = ?", (target_student_id, authorized_group_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Assigned presenter must be a member of this group")

        target_title = sec.title if sec.title is not None else existing["title"]
        target_seconds = sec.speaking_seconds if sec.speaking_seconds is not None else existing["speaking_seconds"]
        target_notes = sec.notes if sec.notes is not None else existing["notes"]
        target_order = sec.order_index if sec.order_index is not None else existing["order_index"]

        cursor.execute(
            """
            UPDATE presentation_sections
            SET student_id = ?, title = ?, speaking_seconds = ?, notes = ?, order_index = ?
            WHERE id = ?
            """,
            (target_student_id, target_title.strip(), target_seconds, target_notes.strip(), target_order, section_id)
        )

    return {"status": "success", "message": "Section updated"}

@router.delete("/sections/{section_id}")
def delete_section(section_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a speaking section."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM presentation_sections WHERE id = ?", (section_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Section not found")

        get_group_for_user(conn, user, existing["group_id"])

        cursor.execute("DELETE FROM presentation_sections WHERE id = ?", (section_id,))

    return {"status": "success", "message": "Section deleted"}
