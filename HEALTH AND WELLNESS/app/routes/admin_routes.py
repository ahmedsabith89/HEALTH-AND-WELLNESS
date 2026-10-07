import json
import csv
import io
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.database import db_session
from app.auth import get_current_user, require_admin, hash_password
from app.algorithm import (
    solve_group_balancing,
    calculate_group_metrics,
    calculate_student_features,
    allocate_topics_random,
    allocate_topics_preference
)
from app.seed_data import seed_database, simulate_questionnaires

router = APIRouter(prefix="/api/admin", tags=["admin"])

# --- Request Models ---
class StudentCreate(BaseModel):
    admission_number: str
    roll_number: str
    full_name: str
    email: Optional[str] = None
    password: Optional[str] = "student123"

class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    roll_number: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None

class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=4)

class ConstraintCreate(BaseModel):
    student_a_id: int
    student_b_id: int
    constraint_type: str  # 'TOGETHER' or 'APART'

class MoveStudentReq(BaseModel):
    student_id: int
    target_group_id: int

class SwapStudentsReq(BaseModel):
    student_a_id: int
    student_b_id: int

class ManualTopicAssignReq(BaseModel):
    group_id: int
    topic_id: int

# --- Helper: Save Group Snapshot for Undo ---
def save_group_snapshot(conn, description: str = "Group Generation Snapshot"):
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_id, is_locked FROM students WHERE role = 'STUDENT'")
    students_state = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id, is_locked, finalized, topic_id FROM groups")
    groups_state = [dict(r) for r in cursor.fetchall()]

    snapshot = {
        "students": students_state,
        "groups": groups_state
    }
    cursor.execute(
        "INSERT INTO group_history (snapshot_json, description) VALUES (?, ?)",
        (json.dumps(snapshot), description)
    )

# --- 1. Admin Metrics & Overview ---
@router.get("/metrics")
def get_admin_metrics(user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT'")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questionnaires")
        completed_questionnaires = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM groups")
        total_groups = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT' AND group_id IS NOT NULL")
        assigned_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM groups WHERE topic_id IS NOT NULL")
        assigned_topics = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM groups WHERE finalized = 1")
        finalized_groups = cursor.fetchone()[0]

        # Calculate Presentation-Ready groups
        cursor.execute("SELECT id, group_number, max_members, finalized, topic_id FROM groups")
        groups = cursor.fetchall()

        presentation_ready_count = 0
        incomplete_count = 0

        for g in groups:
            g_id = g["id"]
            if not g["finalized"] or not g["topic_id"]:
                incomplete_count += 1
                continue

            # check members count
            cursor.execute("SELECT COUNT(*) FROM students WHERE group_id = ?", (g_id,))
            m_count = cursor.fetchone()[0]

            # check confirmations
            cursor.execute("SELECT COUNT(*) FROM speaking_confirmations WHERE group_id = ?", (g_id,))
            c_count = cursor.fetchone()[0]

            # check duration and sections
            cursor.execute("SELECT COALESCE(SUM(speaking_seconds), 0), COUNT(DISTINCT student_id) FROM presentation_sections WHERE group_id = ?", (g_id,))
            sec_row = cursor.fetchone()
            total_duration = sec_row[0]
            assigned_speakers_count = sec_row[1]

            if (m_count > 0 and 
                c_count == m_count and 
                assigned_speakers_count == m_count and 
                60 <= total_duration <= 900):
                presentation_ready_count += 1
            else:
                incomplete_count += 1

        return {
            "total_students": total_students,
            "target_students": 69,
            "questionnaires_completed": completed_questionnaires,
            "groups_count": total_groups,
            "target_groups": 10,
            "students_assigned": assigned_students,
            "topics_assigned": assigned_topics,
            "finalized_groups": finalized_groups,
            "presentation_ready_groups": presentation_ready_count,
            "incomplete_groups": incomplete_count,
            "groups_are_finalized": finalized_groups == 10
        }

# --- 2. Student Management ---
@router.get("/students")
def list_students(user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email, s.role, s.is_locked,
                   s.group_id, g.group_number,
                   t.title as topic_title,
                   (CASE WHEN q.student_id IS NOT NULL THEN 1 ELSE 0 END) as questionnaire_completed,
                   (SELECT confirmed_at FROM speaking_confirmations sc WHERE sc.group_id = s.group_id AND sc.student_id = s.id) as speaking_confirmed
            FROM students s
            LEFT JOIN groups g ON s.group_id = g.id
            LEFT JOIN topics t ON g.topic_id = t.id
            LEFT JOIN questionnaires q ON s.id = q.student_id
            WHERE s.role = 'STUDENT'
            ORDER BY s.roll_number ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

@router.post("/students")
def create_student(req: StudentCreate, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        pwd_hash = hash_password(req.password or "student123")
        try:
            cursor.execute(
                """
                INSERT INTO students (admission_number, roll_number, full_name, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?, 'STUDENT')
                """,
                (req.admission_number.strip().upper(), req.roll_number.strip(), req.full_name.strip(), (req.email or "").strip(), pwd_hash)
            )
            return {"status": "success", "id": cursor.lastrowid, "message": "Student added successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not add student: {str(e)}")

@router.put("/students/{student_id}")
def update_student(student_id: int, req: StudentUpdate, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM students WHERE id = ? AND role = 'STUDENT'", (student_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Student not found")

        updates = []
        params = []
        if req.admission_number:
            updates.append("admission_number = ?")
            params.append(req.admission_number.strip().upper())
        if req.roll_number:
            updates.append("roll_number = ?")
            params.append(req.roll_number.strip())
        if req.full_name:
            updates.append("full_name = ?")
            params.append(req.full_name.strip())
        if req.email is not None:
            updates.append("email = ?")
            params.append(req.email.strip())

        if updates:
            params.append(student_id)
            cursor.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = ?", params)

        return {"status": "success", "message": "Student updated successfully"}

@router.delete("/students/{student_id}")
def delete_student(student_id: int, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ? AND role = 'STUDENT'", (student_id,))
        return {"status": "success", "message": "Student deleted"}

@router.post("/students/{student_id}/reset_password")
def reset_student_password(student_id: int, req: PasswordReset, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        new_hash = hash_password(req.new_password)
        cursor.execute("UPDATE students SET password_hash = ? WHERE id = ?", (new_hash, student_id))
        return {"status": "success", "message": "Password reset successfully"}

@router.post("/students/{student_id}/toggle_lock")
def toggle_student_lock(student_id: int, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_locked, group_id FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student not found")
        if not row["group_id"]:
            raise HTTPException(status_code=400, detail="Cannot lock student without an assigned group")

        new_status = 0 if row["is_locked"] else 1
        cursor.execute("UPDATE students SET is_locked = ? WHERE id = ?", (new_status, student_id))
        return {"status": "success", "is_locked": bool(new_status)}

# --- 3. Constraints Management (Together / Apart) ---
@router.get("/constraints")
def get_constraints(user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id, c.student_a_id, c.student_b_id, c.constraint_type, c.created_at,
                   sa.full_name as student_a_name, sa.roll_number as student_a_roll,
                   sb.full_name as student_b_name, sb.roll_number as student_b_roll
            FROM group_constraints c
            JOIN students sa ON c.student_a_id = sa.id
            JOIN students sb ON c.student_b_id = sb.id
            ORDER BY c.id DESC
            """
        )
        return [dict(r) for r in cursor.fetchall()]

@router.post("/constraints")
def add_constraint(req: ConstraintCreate, user: Dict[str, Any] = Depends(require_admin)):
    if req.student_a_id == req.student_b_id:
        raise HTTPException(status_code=400, detail="Cannot create constraint between the same student")

    c_type = req.constraint_type.upper()
    if c_type not in ("TOGETHER", "APART"):
        raise HTTPException(status_code=400, detail="Constraint type must be TOGETHER or APART")

    # Order student IDs consistently
    a_id, b_id = min(req.student_a_id, req.student_b_id), max(req.student_a_id, req.student_b_id)

    with db_session() as conn:
        cursor = conn.cursor()
        # Check opposite constraint
        opp_type = "APART" if c_type == "TOGETHER" else "TOGETHER"
        cursor.execute(
            "SELECT id FROM group_constraints WHERE student_a_id = ? AND student_b_id = ? AND constraint_type = ?",
            (a_id, b_id, opp_type)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Conflicting {opp_type} constraint already exists for these students")

        cursor.execute(
            """
            INSERT INTO group_constraints (student_a_id, student_b_id, constraint_type)
            VALUES (?, ?, ?)
            ON CONFLICT(student_a_id, student_b_id, constraint_type) DO NOTHING
            """,
            (a_id, b_id, c_type)
        )
        return {"status": "success", "message": f"{c_type} constraint added"}

@router.delete("/constraints/{constraint_id}")
def delete_constraint(constraint_id: int, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_constraints WHERE id = ?", (constraint_id,))
        return {"status": "success", "message": "Constraint deleted"}

# --- 4. Group Generation & Review ---
@router.get("/groups")
def get_all_groups(user: Dict[str, Any] = Depends(require_admin)):
    """
    Returns all 10 groups with members, speaking confidence metrics, balance score, and compatibility summary.
    This diagnostic information is strictly for ADMIN only.
    """
    with db_session() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT g.id, g.group_number, g.max_members, g.is_locked, g.finalized, g.custom_name,
                   t.id as topic_id, t.title as topic_title, t.description as topic_description
            FROM groups g
            LEFT JOIN topics t ON g.topic_id = t.id
            ORDER BY g.group_number ASC
            """
        )
        groups = [dict(g) for g in cursor.fetchall()]

        # Fetch all questionnaires
        cursor.execute("SELECT * FROM questionnaires")
        q_map = {row["student_id"]: dict(row) for row in cursor.fetchall()}

        # Fetch all students
        cursor.execute(
            """
            SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email, s.group_id, s.is_locked,
                   (SELECT COUNT(*) FROM presentation_sections ps WHERE ps.group_id = s.group_id AND ps.student_id = s.id) as sections_count,
                   (SELECT confirmed_at FROM speaking_confirmations sc WHERE sc.group_id = s.group_id AND sc.student_id = s.id) as confirmed_at
            FROM students s
            WHERE s.role = 'STUDENT'
            ORDER BY s.roll_number ASC
            """
        )
        students = [dict(s) for s in cursor.fetchall()]

        members_by_group = {g["id"]: [] for g in groups}
        for s in students:
            if s["group_id"] in members_by_group:
                members_by_group[s["group_id"]].append(s)

        # Enrich each group with metrics
        enriched_groups = []
        for g in groups:
            mems = members_by_group[g["id"]]
            mems_features = [calculate_student_features(m, q_map.get(m["id"])) for m in mems]
            metrics = calculate_group_metrics(mems_features)

            # Check presentation readiness
            total_duration = 0
            cursor.execute("SELECT COALESCE(SUM(speaking_seconds), 0) FROM presentation_sections WHERE group_id = ?", (g["id"],))
            total_duration = cursor.fetchone()[0]

            confirmed_count = sum(1 for m in mems if m["confirmed_at"] is not None)
            all_assigned = all(m["sections_count"] > 0 for m in mems) if mems else False
            is_ready = (
                bool(g["finalized"]) and
                g["topic_id"] is not None and
                all_assigned and
                confirmed_count == len(mems) and
                60 <= total_duration <= 900 and
                len(mems) > 0
            )

            g_data = {
                "id": g["id"],
                "group_number": g["group_number"],
                "max_members": g["max_members"],
                "is_locked": bool(g["is_locked"]),
                "finalized": bool(g["finalized"]),
                "topic_id": g["topic_id"],
                "topic_title": g["topic_title"],
                "topic_description": g["topic_description"],
                "member_count": len(mems),
                "members": mems,
                "metrics": metrics,
                "presentation_status": {
                    "is_ready": is_ready,
                    "total_duration_seconds": total_duration,
                    "total_duration_formatted": f"{total_duration // 60}:{total_duration % 60:02d}",
                    "confirmed_count": confirmed_count,
                    "all_assigned": all_assigned
                }
            }
            enriched_groups.append(g_data)

        # Check if undo is available
        cursor.execute("SELECT COUNT(*) FROM group_history")
        history_count = cursor.fetchone()[0]

        return {
            "groups": enriched_groups,
            "can_undo": history_count > 0
        }

@router.post("/groups/generate")
def generate_groups(user: Dict[str, Any] = Depends(require_admin)):
    """
    Executes the group-generation algorithm:
    - Exactly 10 groups: 9 of 7, 1 of 6.
    - Balances speaking confidence, social comfort, leadership, persona diversity.
    - Respects Keep Together and Keep Apart constraints.
    - Respects locked groups and locked students.
    - Saves state snapshot for undo.
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Save snapshot before modifying
        save_group_snapshot(conn, "Pre-Generation Snapshot")

        cursor.execute("SELECT * FROM students WHERE role = 'STUDENT' ORDER BY id ASC")
        students = [dict(s) for s in cursor.fetchall()]

        if len(students) != 69:
            raise HTTPException(status_code=400, detail=f"Expected exactly 69 students, found {len(students)}. Please adjust student roster.")

        cursor.execute("SELECT * FROM groups ORDER BY group_number ASC")
        groups_config = [dict(g) for g in cursor.fetchall()]

        if len(groups_config) != 10:
            raise HTTPException(status_code=400, detail="Expected exactly 10 groups.")

        cursor.execute("SELECT * FROM questionnaires")
        q_map = {row["student_id"]: dict(row) for row in cursor.fetchall()}

        cursor.execute("SELECT student_a_id, student_b_id, constraint_type FROM group_constraints")
        c_rows = cursor.fetchall()
        together_pairs = [(r["student_a_id"], r["student_b_id"]) for r in c_rows if r["constraint_type"] == "TOGETHER"]
        apart_pairs = [(r["student_a_id"], r["student_b_id"]) for r in c_rows if r["constraint_type"] == "APART"]

        locked_groups = {g["id"] for g in groups_config if g["is_locked"]}
        locked_students = {s["id"]: s["group_id"] for s in students if s["is_locked"] and s["group_id"] is not None}

        # Run balancing solver
        assignment = solve_group_balancing(
            students=students,
            questionnaires_map=q_map,
            groups_config=groups_config,
            together_pairs=together_pairs,
            apart_pairs=apart_pairs,
            locked_groups=locked_groups,
            locked_students=locked_students
        )

        # Apply assignment to database
        for g_id, member_ids in assignment.items():
            for m_id in member_ids:
                cursor.execute("UPDATE students SET group_id = ? WHERE id = ?", (g_id, m_id))

        return {"status": "success", "message": "10 Balanced groups generated successfully"}

@router.post("/groups/{group_id}/toggle_lock")
def toggle_group_lock(group_id: int, user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_locked FROM groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Group not found")

        new_status = 0 if row["is_locked"] else 1
        cursor.execute("UPDATE groups SET is_locked = ? WHERE id = ?", (new_status, group_id))
        return {"status": "success", "is_locked": bool(new_status)}

@router.post("/groups/move_student")
def move_student(req: MoveStudentReq, user: Dict[str, Any] = Depends(require_admin)):
    """Move student between groups, validating capacity limits."""
    with db_session() as conn:
        cursor = conn.cursor()
        save_group_snapshot(conn, f"Move Student {req.student_id}")

        cursor.execute("SELECT id, max_members FROM groups WHERE id = ?", (req.target_group_id,))
        target_group = cursor.fetchone()
        if not target_group:
            raise HTTPException(status_code=404, detail="Target group not found")

        cursor.execute("SELECT COUNT(*) FROM students WHERE group_id = ?", (req.target_group_id,))
        current_target_count = cursor.fetchone()[0]

        if current_target_count >= target_group["max_members"]:
            raise HTTPException(
                status_code=400,
                detail=f"Group is full (capacity {target_group['max_members']}). Swap with another student instead."
            )

        cursor.execute("UPDATE students SET group_id = ? WHERE id = ?", (req.target_group_id, req.student_id))
        return {"status": "success", "message": "Student moved successfully"}

@router.post("/groups/swap_students")
def swap_students(req: SwapStudentsReq, user: Dict[str, Any] = Depends(require_admin)):
    """Swap two students between groups."""
    with db_session() as conn:
        cursor = conn.cursor()
        save_group_snapshot(conn, f"Swap Student {req.student_a_id} and {req.student_b_id}")

        cursor.execute("SELECT id, group_id FROM students WHERE id = ?", (req.student_a_id,))
        sa = cursor.fetchone()
        cursor.execute("SELECT id, group_id FROM students WHERE id = ?", (req.student_b_id,))
        sb = cursor.fetchone()

        if not sa or not sb:
            raise HTTPException(status_code=404, detail="One or both students not found")

        cursor.execute("UPDATE students SET group_id = ? WHERE id = ?", (sb["group_id"], sa["id"]))
        cursor.execute("UPDATE students SET group_id = ? WHERE id = ?", (sa["group_id"], sb["id"]))

        return {"status": "success", "message": "Students swapped successfully"}

@router.post("/groups/undo")
def undo_groups(user: Dict[str, Any] = Depends(require_admin)):
    """Reverts to the most recent saved group snapshot."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, snapshot_json FROM group_history ORDER BY id DESC LIMIT 1")
        last_history = cursor.fetchone()
        if not last_history:
            raise HTTPException(status_code=400, detail="No undo history available")

        snapshot = json.loads(last_history["snapshot_json"])

        # Revert students
        for s in snapshot["students"]:
            cursor.execute("UPDATE students SET group_id = ?, is_locked = ? WHERE id = ?", (s["group_id"], s["is_locked"], s["id"]))

        # Delete that snapshot entry
        cursor.execute("DELETE FROM group_history WHERE id = ?", (last_history["id"],))

        return {"status": "success", "message": "Previous group assignment restored"}

@router.post("/groups/finalize")
def finalize_groups(user: Dict[str, Any] = Depends(require_admin)):
    """
    Finalize groups: marks all 10 groups as finalized.
    Once finalized, students can view their assigned group and topic.
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Check total assigned
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT' AND group_id IS NULL")
        unassigned = cursor.fetchone()[0]
        if unassigned > 0:
            raise HTTPException(status_code=400, detail=f"Cannot finalize: {unassigned} students remain unassigned to groups")

        # Verify group sizes: 9 of 7 and 1 of 6
        for g_num in range(1, 11):
            expected_cap = 7 if g_num <= 9 else 6
            cursor.execute(
                """
                SELECT COUNT(*) FROM students s
                JOIN groups g ON s.group_id = g.id
                WHERE g.group_number = ?
                """,
                (g_num,)
            )
            cnt = cursor.fetchone()[0]
            if cnt != expected_cap:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot finalize: Group {g_num} has {cnt} members, expected exactly {expected_cap}."
                )

        cursor.execute("UPDATE groups SET finalized = 1")
        return {"status": "success", "message": "Groups finalized! Students can now view their group."}

@router.post("/groups/unfinalize")
def unfinalize_groups(user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET finalized = 0")
        return {"status": "success", "message": "Groups unlocked for adjustments"}

# --- 5. Fairness Diagnostic Report ---
@router.get("/fairness_report")
def get_fairness_report(user: Dict[str, Any] = Depends(require_admin)):
    """Detailed diagnostic report of all 10 groups (strictly admin only)."""
    with db_session() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM questionnaires")
        q_map = {row["student_id"]: dict(row) for row in cursor.fetchall()}

        cursor.execute("SELECT * FROM groups ORDER BY group_number ASC")
        groups = cursor.fetchall()

        report = []
        for g in groups:
            cursor.execute("SELECT * FROM students WHERE group_id = ? ORDER BY roll_number ASC", (g["id"],))
            mems = [dict(r) for r in cursor.fetchall()]
            feats = [calculate_student_features(m, q_map.get(m["id"])) for m in mems]
            metrics = calculate_group_metrics(feats)

            report.append({
                "group_number": g["group_number"],
                "target_members": g["max_members"],
                "current_members": len(mems),
                "speaking_avg": metrics["speaking_avg"],
                "no_ppt_avg": metrics["no_ppt_avg"],
                "social_avg": metrics["social_avg"],
                "leadership_avg": metrics["leadership_avg"],
                "high_speakers": metrics["high_speakers_count"],
                "low_speakers": metrics["low_speakers_count"],
                "leaders_count": metrics["leaders_count"],
                "unique_personas": len(metrics["personas_count"]),
                "personas_breakdown": metrics["personas_count"],
                "balance_score": metrics["balance_score"],
                "compatibility_summary": metrics["summary"]
            })

        return {"groups_fairness": report}

# --- 6. Topic Assignment ---
@router.get("/topics")
def get_all_topics(user: Dict[str, Any] = Depends(require_admin)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.id, t.title, t.description,
                   g.id as assigned_group_id, g.group_number as assigned_group_number
            FROM topics t
            LEFT JOIN groups g ON g.topic_id = t.id
            ORDER BY t.id ASC
            """
        )
        topics = [dict(t) for t in cursor.fetchall()]

        # Preferences submitted per group
        cursor.execute(
            """
            SELECT p.group_id, p.topic_id, p.rank_preference, g.group_number, t.title
            FROM group_topic_preferences p
            JOIN groups g ON p.group_id = g.id
            JOIN topics t ON p.topic_id = t.id
            ORDER BY p.group_id ASC, p.rank_preference ASC
            """
        )
        prefs_raw = cursor.fetchall()
        prefs_by_group = {}
        for p in prefs_raw:
            g_id = p["group_id"]
            if g_id not in prefs_by_group:
                prefs_by_group[g_id] = []
            prefs_by_group[g_id].append(dict(p))

        return {
            "topics": topics,
            "group_preferences": prefs_by_group
        }

@router.post("/topics/assign_random")
def assign_topics_randomly(user: Dict[str, Any] = Depends(require_admin)):
    """Option A: Random unique topic draw across the 10 groups."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_number FROM groups ORDER BY group_number ASC")
        groups = [dict(g) for g in cursor.fetchall()]

        cursor.execute("SELECT id, title FROM topics ORDER BY id ASC")
        topics = [dict(t) for t in cursor.fetchall()]

        if len(groups) != 10 or len(topics) != 10:
            raise HTTPException(status_code=400, detail="Must have exactly 10 groups and 10 topics")

        assignment = allocate_topics_random(groups, topics)

        # Apply assignment
        for g_id, t_id in assignment.items():
            cursor.execute("UPDATE groups SET topic_id = ? WHERE id = ?", (t_id, g_id))

        return {"status": "success", "message": "10 Topics randomly drawn and assigned uniquely to 10 groups"}

@router.post("/topics/assign_preference")
def assign_topics_by_preference(user: Dict[str, Any] = Depends(require_admin)):
    """
    Option B: Preference-based allocation algorithm.
    Maximizes preference satisfaction while ensuring each topic is assigned exactly once.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_number FROM groups ORDER BY group_number ASC")
        groups = [dict(g) for g in cursor.fetchall()]

        cursor.execute("SELECT id, title FROM topics ORDER BY id ASC")
        topics = [dict(t) for t in cursor.fetchall()]

        cursor.execute("SELECT group_id, topic_id, rank_preference FROM group_topic_preferences ORDER BY group_id, rank_preference")
        prefs_raw = cursor.fetchall()
        prefs_map = {}
        for p in prefs_raw:
            g_id = p["group_id"]
            if g_id not in prefs_map:
                prefs_map[g_id] = []
            prefs_map[g_id].append(p["topic_id"])

        assignment = allocate_topics_preference(groups, topics, prefs_map)

        for g_id, t_id in assignment.items():
            cursor.execute("UPDATE groups SET topic_id = ? WHERE id = ?", (t_id, g_id))

        return {"status": "success", "message": "10 Topics assigned via preference-optimization algorithm"}

@router.post("/topics/assign_manual")
def assign_topic_manually(req: ManualTopicAssignReq, user: Dict[str, Any] = Depends(require_admin)):
    """Manual admin topic assignment or swap."""
    with db_session() as conn:
        cursor = conn.cursor()

        # Check if another group already has this topic
        cursor.execute("SELECT id, group_number FROM groups WHERE topic_id = ? AND id != ?", (req.topic_id, req.group_id))
        other_group = cursor.fetchone()

        if other_group:
            # Swap topics between the two groups
            cursor.execute("SELECT topic_id FROM groups WHERE id = ?", (req.group_id,))
            current_t = cursor.fetchone()["topic_id"]
            cursor.execute("UPDATE groups SET topic_id = ? WHERE id = ?", (current_t, other_group["id"]))

        cursor.execute("UPDATE groups SET topic_id = ? WHERE id = ?", (req.topic_id, req.group_id))
        return {"status": "success", "message": "Topic assigned"}

# --- 7. Testing & Simulation Utilities for Evaluators ---
@router.post("/seed_sample_questionnaires")
def seed_sample_questionnaires_endpoint(user: Dict[str, Any] = Depends(require_admin)):
    """Fills realistic sample questionnaire responses for testing the group algorithm instantly."""
    res = simulate_questionnaires(69)
    return {"status": "success", "message": "Simulated realistic questionnaires for all 69 students!", "details": res}

@router.post("/simulate_complete_flow")
def simulate_complete_flow(user: Dict[str, Any] = Depends(require_admin)):
    """
    One-click helper for evaluators:
    1. Simulates questionnaires for all 69 students.
    2. Runs balanced group generation (9 groups of 7, 1 group of 6).
    3. Finalizes groups.
    4. Assigns 10 unique topics.
    5. Populates balanced speaking sections for each group (every member gets a section, <= 15:00 total).
    6. Confirms speaking commitments.
    Result: All 10 groups become PRESENTATION READY!
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # 1. Simulate questionnaires
        simulate_questionnaires(69)

        # 2. Generate balanced groups
        cursor.execute("SELECT * FROM students WHERE role = 'STUDENT' ORDER BY id ASC")
        students = [dict(s) for s in cursor.fetchall()]
        cursor.execute("SELECT * FROM groups ORDER BY group_number ASC")
        groups_config = [dict(g) for g in cursor.fetchall()]
        cursor.execute("SELECT * FROM questionnaires")
        q_map = {row["student_id"]: dict(row) for row in cursor.fetchall()}

        assignment = solve_group_balancing(
            students=students,
            questionnaires_map=q_map,
            groups_config=groups_config,
            together_pairs=[],
            apart_pairs=[],
            locked_groups=set(),
            locked_students={}
        )

        for g_id, member_ids in assignment.items():
            for m_id in member_ids:
                cursor.execute("UPDATE students SET group_id = ? WHERE id = ?", (g_id, m_id))

        # 3. Finalize groups
        cursor.execute("UPDATE groups SET finalized = 1")

        # 4. Assign 10 topics uniquely
        cursor.execute("SELECT id FROM topics ORDER BY id ASC")
        topics = [dict(t) for t in cursor.fetchall()]
        for idx, g in enumerate(groups_config):
            cursor.execute("UPDATE groups SET topic_id = ? WHERE id = ?", (topics[idx]["id"], g["id"]))

        # 5. Populate speaking sections and confirmations
        cursor.execute("DELETE FROM presentation_sections")
        cursor.execute("DELETE FROM speaking_confirmations")

        section_titles = [
            "Introduction & Contextual Framework",
            "Root Causes & Biomechanical Factors",
            "Evidence-Based Case Studies",
            "Symptomology & Early Risk Markers",
            "Preventative Protocols & Interventions",
            "Clinical Guidelines & Daily Applications",
            "Conclusion, Q&A & Key Takeaways"
        ]

        for g in groups_config:
            g_id = g["id"]
            cursor.execute("SELECT id, full_name FROM students WHERE group_id = ? ORDER BY roll_number ASC", (g_id,))
            mems = cursor.fetchall()
            n = len(mems)
            # Duration per speaker ~ 110-120 seconds (total 13-14 mins <= 15:00)
            base_secs = 115 if n == 7 else 135

            for idx, m in enumerate(mems):
                s_id = m["id"]
                title = section_titles[idx % len(section_titles)]
                cursor.execute(
                    """
                    INSERT INTO presentation_sections (group_id, student_id, title, speaking_seconds, notes, order_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (g_id, s_id, title, base_secs, f"Key points and analytical review for {title}.", idx + 1)
                )
                # Confirm speaking
                cursor.execute(
                    """
                    INSERT INTO speaking_confirmations (group_id, student_id, confirmed_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (g_id, s_id)
                )

        return {
            "status": "success",
            "message": "Full end-to-end presentation flow simulated! All 10 groups are now PRESENTATION READY."
        }

@router.post("/reset_class")
def reset_class_data(user: Dict[str, Any] = Depends(require_admin)):
    """Reset to freshly initialized 69 students and 10 groups."""
    seed_database(force_reseed=True)
    return {"status": "success", "message": "Class data reset to pristine state"}

# --- 8. Export CSV & Print Views ---
@router.get("/export/csv")
def export_class_csv(user: Dict[str, Any] = Depends(require_admin)):
    """Export complete class presentation roster as CSV."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.admission_number, s.roll_number, s.full_name, s.email,
                   g.group_number,
                   t.title as assigned_topic,
                   (CASE WHEN sc.confirmed_at IS NOT NULL THEN 'CONFIRMED' ELSE 'PENDING' END) as speaking_status,
                   (SELECT GROUP_CONCAT(ps.title || ' (' || (ps.speaking_seconds/60) || 'm ' || (ps.speaking_seconds%60) || 's)', '; ')
                    FROM presentation_sections ps
                    WHERE ps.group_id = s.group_id AND ps.student_id = s.id) as speaking_sections
            FROM students s
            LEFT JOIN groups g ON s.group_id = g.id
            LEFT JOIN topics t ON g.topic_id = t.id
            LEFT JOIN speaking_confirmations sc ON sc.group_id = s.group_id AND sc.student_id = s.id
            WHERE s.role = 'STUDENT'
            ORDER BY g.group_number ASC, s.roll_number ASC
            """
        )
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Admission Number", "Roll Number", "Student Name", "Email",
            "Group Number", "Assigned Topic", "Speaking Confirmation", "Speaking Sections"
        ])

        for r in rows:
            writer.writerow([
                r["admission_number"],
                r["roll_number"],
                r["full_name"],
                r["email"] or "",
                f"Group {r['group_number']}" if r["group_number"] else "Unassigned",
                r["assigned_topic"] or "Unassigned",
                r["speaking_status"],
                r["speaking_sections"] or "None"
            ])

        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=class_presentation_hub_roster.csv"
        return response
