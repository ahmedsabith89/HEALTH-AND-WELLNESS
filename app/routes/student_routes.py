from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.database import db_session
from app.auth import get_current_user, require_student

router = APIRouter(prefix="/api/student", tags=["student"])

class QuestionnaireSubmission(BaseModel):
    q_speaking_comfort: int = Field(..., ge=1, le=5)
    q_speaking_no_ppt: int = Field(..., ge=1, le=5)
    q_persona: str
    q_social_comfort: int = Field(..., ge=1, le=5)
    q_atmosphere: str
    q_leadership_comfort: int = Field(..., ge=1, le=5)
    q_priority: str
    q_fun_ppt_crash: str
    q_fun_10min_rush: str
    q_fun_team_name: str

class TopicPreferencesSubmission(BaseModel):
    first_choice_id: int
    second_choice_id: int
    third_choice_id: int

@router.get("/dashboard")
def get_student_dashboard(user: Dict[str, Any] = Depends(require_student)):
    """
    Returns student dashboard information:
    - Profile info
    - Group info (if finalized)
    - Topic info (if assigned)
    - Student's own speaking section
    - Group members list with speaking confirmation status
    - Overall presentation readiness progress
    """
    student_id = user["id"]

    with db_session() as conn:
        cursor = conn.cursor()

        # 1. Fetch student info
        cursor.execute(
            """
            SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email, s.group_id,
                   g.group_number, g.finalized as group_finalized,
                   t.id as topic_id, t.title as topic_title, t.description as topic_description
            FROM students s
            LEFT JOIN groups g ON s.group_id = g.id
            LEFT JOIN topics t ON g.topic_id = t.id
            WHERE s.id = ?
            """,
            (student_id,)
        )
        student_info = cursor.fetchone()
        if not student_info:
            raise HTTPException(status_code=404, detail="Student not found")

        # 2. Check questionnaire completion
        cursor.execute("SELECT * FROM questionnaires WHERE student_id = ?", (student_id,))
        questionnaire_row = cursor.fetchone()
        has_completed_q = questionnaire_row is not None

        group_id = student_info["group_id"]
        group_finalized = bool(student_info["group_finalized"]) if student_info["group_finalized"] is not None else False

        # If groups not finalized yet, do not reveal group details to student
        group_data = None
        members_data = []
        my_section_data = None
        group_progress = {}

        if group_id and group_finalized:
            # Fetch all members of the group
            cursor.execute(
                """
                SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email,
                       (SELECT confirmed_at FROM speaking_confirmations sc WHERE sc.group_id = s.group_id AND sc.student_id = s.id) as confirmed_at
                FROM students s
                WHERE s.group_id = ?
                ORDER BY s.roll_number ASC
                """,
                (group_id,)
            )
            members_rows = cursor.fetchall()

            # Fetch presentation sections for this group
            cursor.execute(
                """
                SELECT id, student_id, title, speaking_seconds, notes, order_index
                FROM presentation_sections
                WHERE group_id = ?
                ORDER BY order_index ASC, id ASC
                """,
                (group_id,)
            )
            sections_rows = cursor.fetchall()
            sections_by_student = {}
            total_duration_seconds = 0
            for sec in sections_rows:
                s_id = sec["student_id"]
                if s_id not in sections_by_student:
                    sections_by_student[s_id] = []
                sections_by_student[s_id].append(dict(sec))
                total_duration_seconds += sec["speaking_seconds"]

            # Student's own section(s)
            my_sections = sections_by_student.get(student_id, [])
            if my_sections:
                my_sec = my_sections[0]
                my_section_data = {
                    "title": my_sec["title"],
                    "speaking_seconds": my_sec["speaking_seconds"],
                    "speaking_time_formatted": f"{my_sec['speaking_seconds'] // 60}:{my_sec['speaking_seconds'] % 60:02d}",
                    "notes": my_sec.get("notes", ""),
                    "all_sections": my_sections
                }

            confirmed_count = 0
            for m in members_rows:
                is_confirmed = m["confirmed_at"] is not None
                if is_confirmed:
                    confirmed_count += 1

                m_sections = sections_by_student.get(m["id"], [])
                members_data.append({
                    "id": m["id"],
                    "roll_number": m["roll_number"],
                    "admission_number": m["admission_number"],
                    "full_name": m["full_name"],
                    "is_confirmed": is_confirmed,
                    "is_self": m["id"] == student_id,
                    "sections_count": len(m_sections),
                    "speaking_time_total": sum(s["speaking_seconds"] for s in m_sections),
                    "sections_summary": ", ".join(s["title"] for s in m_sections) if m_sections else "Unassigned"
                })

            member_count = len(members_rows)
            all_assigned = all(len(sections_by_student.get(m["id"], [])) > 0 for m in members_rows)
            all_confirmed = (confirmed_count == member_count and member_count > 0)
            within_time_limit = (total_duration_seconds <= 900)  # 15 minutes = 900 seconds
            has_minimum_time = (total_duration_seconds >= 60)

            is_presentation_ready = (
                group_finalized and
                student_info["topic_id"] is not None and
                all_assigned and
                all_confirmed and
                within_time_limit and
                has_minimum_time
            )

            group_data = {
                "group_id": group_id,
                "group_number": student_info["group_number"],
                "member_count": member_count,
                "topic_id": student_info["topic_id"],
                "topic_title": student_info["topic_title"] or "Topic Allocation In Progress",
                "topic_description": student_info["topic_description"] or ""
            }

            group_progress = {
                "total_members": member_count,
                "confirmed_members": confirmed_count,
                "all_confirmed": all_confirmed,
                "all_assigned": all_assigned,
                "total_duration_seconds": total_duration_seconds,
                "total_duration_formatted": f"{total_duration_seconds // 60}:{total_duration_seconds % 60:02d}",
                "max_duration_seconds": 900,
                "max_duration_formatted": "15:00",
                "is_over_time": total_duration_seconds > 900,
                "is_presentation_ready": is_presentation_ready,
                "status_text": "PRESENTATION READY" if is_presentation_ready else (
                    "Over 15-Minute Limit" if total_duration_seconds > 900 else (
                        f"In Progress ({confirmed_count}/{member_count} Confirmed)"
                    )
                )
            }

        # Check if student confirmed speaking
        my_confirmed = False
        if group_id:
            cursor.execute("SELECT confirmed_at FROM speaking_confirmations WHERE group_id = ? AND student_id = ?", (group_id, student_id))
            my_confirmed = cursor.fetchone() is not None

        return {
            "student": {
                "id": student_info["id"],
                "full_name": student_info["full_name"],
                "admission_number": student_info["admission_number"],
                "roll_number": student_info["roll_number"],
                "email": student_info["email"],
                "has_completed_questionnaire": has_completed_q,
                "my_confirmed": my_confirmed
            },
            "group": group_data,
            "members": members_data,
            "my_section": my_section_data,
            "progress": group_progress,
            "groups_finalized": group_finalized
        }

@router.get("/questionnaire")
def get_my_questionnaire(user: Dict[str, Any] = Depends(require_student)):
    """Fetches the current student's questionnaire. Cannot see other students' answers."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questionnaires WHERE student_id = ?", (user["id"],))
        row = cursor.fetchone()
        if not row:
            return {"completed": False, "data": None}
        return {"completed": True, "data": dict(row)}

@router.post("/questionnaire")
def submit_my_questionnaire(data: QuestionnaireSubmission, user: Dict[str, Any] = Depends(require_student)):
    """Submits or updates the student's questionnaire responses."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO questionnaires 
            (student_id, q_speaking_comfort, q_speaking_no_ppt, q_persona, q_social_comfort,
             q_atmosphere, q_leadership_comfort, q_priority, q_fun_ppt_crash, q_fun_10min_rush, q_fun_team_name, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id) DO UPDATE SET
                q_speaking_comfort = excluded.q_speaking_comfort,
                q_speaking_no_ppt = excluded.q_speaking_no_ppt,
                q_persona = excluded.q_persona,
                q_social_comfort = excluded.q_social_comfort,
                q_atmosphere = excluded.q_atmosphere,
                q_leadership_comfort = excluded.q_leadership_comfort,
                q_priority = excluded.q_priority,
                q_fun_ppt_crash = excluded.q_fun_ppt_crash,
                q_fun_10min_rush = excluded.q_fun_10min_rush,
                q_fun_team_name = excluded.q_fun_team_name,
                completed_at = CURRENT_TIMESTAMP
            """,
            (
                user["id"],
                data.q_speaking_comfort,
                data.q_speaking_no_ppt,
                data.q_persona.strip(),
                data.q_social_comfort,
                data.q_atmosphere.strip(),
                data.q_leadership_comfort,
                data.q_priority.strip(),
                data.q_fun_ppt_crash.strip(),
                data.q_fun_10min_rush.strip(),
                data.q_fun_team_name.strip()
            )
        )
    return {"status": "success", "message": "Questionnaire submitted successfully"}

@router.post("/confirm_speaking")
def confirm_speaking(user: Dict[str, Any] = Depends(require_student)):
    """
    Student confirms: 'I WILL SPEAK'.
    Only the student themselves can confirm their speaking role.
    """
    student_id = user["id"]
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        if not row or not row["group_id"]:
            raise HTTPException(status_code=400, detail="You are not assigned to a group yet")

        group_id = row["group_id"]

        # Check if group has finalized
        cursor.execute("SELECT finalized FROM groups WHERE id = ?", (group_id,))
        g_row = cursor.fetchone()
        if not g_row or not g_row["finalized"]:
            raise HTTPException(status_code=400, detail="Groups have not been finalized by the administrator")

        # Insert speaking confirmation
        cursor.execute(
            """
            INSERT INTO speaking_confirmations (group_id, student_id, confirmed_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(group_id, student_id) DO UPDATE SET confirmed_at = CURRENT_TIMESTAMP
            """,
            (group_id, student_id)
        )

    return {"status": "success", "message": "Speaking commitment confirmed!"}

@router.get("/topic_preferences")
def get_topic_preferences(user: Dict[str, Any] = Depends(require_student)):
    """Get group's topic preferences."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM students WHERE id = ?", (user["id"],))
        s_row = cursor.fetchone()
        if not s_row or not s_row["group_id"]:
            return {"preferences": []}

        group_id = s_row["group_id"]
        cursor.execute(
            """
            SELECT p.rank_preference, t.id as topic_id, t.title, t.description
            FROM group_topic_preferences p
            JOIN topics t ON p.topic_id = t.id
            WHERE p.group_id = ?
            ORDER BY p.rank_preference ASC
            """,
            (group_id,)
        )
        prefs = cursor.fetchall()
        return {"preferences": [dict(p) for p in prefs]}

@router.post("/topic_preferences")
def submit_topic_preferences(req: TopicPreferencesSubmission, user: Dict[str, Any] = Depends(require_student)):
    """Submit 1st, 2nd, 3rd topic preferences for the group."""
    if len({req.first_choice_id, req.second_choice_id, req.third_choice_id}) < 3:
        raise HTTPException(status_code=400, detail="Please select 3 distinct topics for your preferences")

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM students WHERE id = ?", (user["id"],))
        s_row = cursor.fetchone()
        if not s_row or not s_row["group_id"]:
            raise HTTPException(status_code=400, detail="You must belong to a group to submit preferences")

        group_id = s_row["group_id"]

        # Insert or update preferences
        cursor.execute("DELETE FROM group_topic_preferences WHERE group_id = ?", (group_id,))
        for rank, t_id in enumerate([req.first_choice_id, req.second_choice_id, req.third_choice_id], start=1):
            cursor.execute(
                """
                INSERT INTO group_topic_preferences (group_id, topic_id, rank_preference)
                VALUES (?, ?, ?)
                """,
                (group_id, t_id, rank)
            )

    return {"status": "success", "message": "Group topic preferences saved successfully"}
