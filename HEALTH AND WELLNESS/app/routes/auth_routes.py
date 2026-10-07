from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import db_session
from app.auth import hash_password, verify_password, create_session_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    admission_number: str
    password: str

@router.post("/login")
def login(req: LoginRequest, response: Response):
    adm = req.admission_number.strip()
    pwd = req.password.strip()

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, admission_number, roll_number, full_name, email, password_hash, role, group_id
            FROM students
            WHERE UPPER(admission_number) = UPPER(?) 
               OR LOWER(email) = LOWER(?)
               OR (role = 'ADMIN' AND UPPER(?) IN ('AHMED', 'ADMIN', 'COORDINATOR'))
            """,
            (adm, adm, adm)
        )
        user = cursor.fetchone()

        if not user or not verify_password(pwd, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid Admission Number, Email, or Password")

        # Check questionnaire completion if student
        has_completed_q = False
        if user["role"] == "STUDENT":
            cursor.execute("SELECT student_id FROM questionnaires WHERE student_id = ?", (user["id"],))
            has_completed_q = cursor.fetchone() is not None

        token_payload = {
            "id": user["id"],
            "admission_number": user["admission_number"],
            "roll_number": user["roll_number"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
        token = create_session_token(token_payload)

        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=7 * 24 * 3600
        )

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "admission_number": user["admission_number"],
                "roll_number": user["roll_number"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "group_id": user["group_id"],
                "has_completed_questionnaire": has_completed_q
            }
        }

@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.admission_number, s.roll_number, s.full_name, s.email, s.role, s.group_id,
                   g.group_number, g.finalized as group_finalized,
                   t.title as topic_title
            FROM students s
            LEFT JOIN groups g ON s.group_id = g.id
            LEFT JOIN topics t ON g.topic_id = t.id
            WHERE s.id = ?
            """,
            (user["id"],)
        )
        db_user = cursor.fetchone()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        has_completed_q = False
        if db_user["role"] == "STUDENT":
            cursor.execute("SELECT student_id FROM questionnaires WHERE student_id = ?", (user["id"],))
            has_completed_q = cursor.fetchone() is not None

        return {
            "id": db_user["id"],
            "admission_number": db_user["admission_number"],
            "roll_number": db_user["roll_number"],
            "full_name": db_user["full_name"],
            "email": db_user["email"],
            "role": db_user["role"],
            "group_id": db_user["group_id"],
            "group_number": db_user["group_number"],
            "group_finalized": bool(db_user["group_finalized"]) if db_user["group_finalized"] is not None else False,
            "topic_title": db_user["topic_title"],
            "has_completed_questionnaire": has_completed_q
        }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}

@router.get("/quick_switch")
def quick_switch_candidates():
    """Returns sample logins for demonstration and seamless evaluation."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT admission_number, full_name, email, role FROM students WHERE role = 'ADMIN' LIMIT 1")
        admin_u = cursor.fetchone()

        cursor.execute("SELECT admission_number, full_name, email, role FROM students WHERE role = 'TESTER' ORDER BY id ASC")
        testers = cursor.fetchall()

        cursor.execute("SELECT admission_number, full_name, email, role FROM students WHERE role = 'STUDENT' ORDER BY id ASC LIMIT 5")
        students = cursor.fetchall()

        cursor.execute("SELECT admission_number, full_name, email, role FROM students WHERE role = 'STUDENT' AND admission_number = 'ADM2026069' LIMIT 1")
        last_student = cursor.fetchone()

        return {
            "admin": dict(admin_u) if admin_u else None,
            "testers": [dict(t) for t in testers],
            "students": [dict(s) for s in students] + ([dict(last_student)] if last_student and last_student not in students else [])
        }
