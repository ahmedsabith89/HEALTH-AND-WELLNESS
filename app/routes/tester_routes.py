from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from app.database import db_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/tester", tags=["tester"])

def require_tester_or_admin(user: Dict[str, Any] = Depends(get_current_user)):
    if user.get("role") not in ("TESTER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Tester or Admin privileges required")
    return user

@router.get("/dashboard")
def get_tester_dashboard(user: Dict[str, Any] = Depends(require_tester_or_admin)):
    """
    Returns tester diagnostic overview.
    Testers are NOT members of the 69 students and are NEVER placed in groups.
    Testers can audit class readiness, view group presentation plans, and preview both perspectives.
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Class counts
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT'")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'TESTER'")
        total_testers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questionnaires")
        completed_q = cursor.fetchone()[0]

        cursor.execute("SELECT id, group_number, max_members, finalized, topic_id FROM groups ORDER BY group_number ASC")
        groups = cursor.fetchall()

        group_summaries = []
        for g in groups:
            cursor.execute("SELECT COUNT(*) FROM students WHERE group_id = ?", (g["id"],))
            assigned_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM speaking_confirmations WHERE group_id = ?", (g["id"],))
            confirmations_count = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(speaking_seconds), 0) FROM presentation_sections WHERE group_id = ?", (g["id"],))
            dur = cursor.fetchone()[0]

            cursor.execute("SELECT title FROM topics WHERE id = ?", (g["topic_id"],))
            top_row = cursor.fetchone()

            group_summaries.append({
                "id": g["id"],
                "group_number": g["group_number"],
                "max_members": g["max_members"],
                "current_members": assigned_count,
                "confirmed_members": confirmations_count,
                "total_duration_seconds": dur,
                "total_duration_formatted": f"{dur // 60}:{dur % 60:02d}",
                "topic_title": top_row["title"] if top_row else "Not Assigned",
                "finalized": bool(g["finalized"]),
                "is_ready": (g["finalized"] and g["topic_id"] and assigned_count > 0 and 
                             confirmations_count == assigned_count and 60 <= dur <= 900)
            })

        return {
            "tester": {
                "id": user["id"],
                "full_name": user["full_name"],
                "admission_number": user["admission_number"],
                "role": user["role"]
            },
            "class_metrics": {
                "total_enrolled_students": total_students,
                "target_students": 69,
                "total_independent_testers": total_testers,
                "questionnaires_completed": completed_q,
                "groups_count": len(groups)
            },
            "groups": group_summaries
        }
