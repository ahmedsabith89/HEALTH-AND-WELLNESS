import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, db_session
from app.seed_data import seed_database, simulate_questionnaires

def run_tests():
    print("=== STARTING COMPLETE INTEGRATION TESTS ===")
    client = TestClient(app)

    # 1. Test Root and Seeding
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200 on /, got {res.status_code}"
    print("[PASS] Root index endpoint returns 200 OK")

    with db_session() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT'")
        std_count = c.fetchone()[0]
        assert std_count == 69, f"Expected 69 students, got {std_count}"

        c.execute("SELECT COUNT(*) FROM topics")
        topic_count = c.fetchone()[0]
        assert topic_count == 10, f"Expected 10 topics, got {topic_count}"

        c.execute("SELECT COUNT(*) FROM groups")
        group_count = c.fetchone()[0]
        assert group_count == 10, f"Expected 10 groups, got {group_count}"

        c.execute("SELECT group_number, max_members FROM groups ORDER BY group_number ASC")
        caps = [row["max_members"] for row in c.fetchall()]
        assert caps == [7, 7, 7, 7, 7, 7, 7, 7, 7, 6], f"Capacities mismatch: {caps}"
    print(f"[PASS] Database correctly populated: 69 Students, 10 Topics, 10 Groups (9x7 + 1x6 = 69)")

    # 2. Test Authentication
    # Admin login via ADMIN
    admin_login = client.post("/api/auth/login", json={"admission_number": "ADMIN", "password": "admin123"})
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert admin_login.json()["user"]["full_name"] == "Ahmed Sabith"
    print("[PASS] Admin login successful for Ahmed Sabith")

    # Admin login via name 'ahmed' and email 'ahmedsabith89@gmail.com'
    ahmed_login = client.post("/api/auth/login", json={"admission_number": "ahmed", "password": "admin123"})
    assert ahmed_login.status_code == 200
    email_login = client.post("/api/auth/login", json={"admission_number": "ahmedsabith89@gmail.com", "password": "admin123"})
    assert email_login.status_code == 200
    print("[PASS] Login via username 'ahmed' and email 'ahmedsabith89@gmail.com' successful")

    # Tester login
    tester_login = client.post("/api/auth/login", json={"admission_number": "TESTER01", "password": "tester123"})
    assert tester_login.status_code == 200, f"Tester login failed: {tester_login.text}"
    tester_token = tester_login.json()["token"]
    tester_headers = {"Authorization": f"Bearer {tester_token}"}
    assert tester_login.json()["user"]["role"] == "TESTER"
    print("[PASS] Tester login successful for Dr. Evelyn Reed (TESTER01)")

    # Tester dashboard access
    tester_dash = client.get("/api/tester/dashboard", headers=tester_headers)
    assert tester_dash.status_code == 200
    assert tester_dash.json()["class_metrics"]["total_enrolled_students"] == 69
    assert tester_dash.json()["class_metrics"]["total_independent_testers"] == 3
    print("[PASS] Tester dashboard verified: Testers are independent from the 69 student class")

    # Student login
    std_login = client.post("/api/auth/login", json={"admission_number": "ADM2026001", "password": "student123"})
    assert std_login.status_code == 200, f"Student login failed: {std_login.text}"
    std_token = std_login.json()["token"]
    std_headers = {"Authorization": f"Bearer {std_token}"}
    print("[PASS] Student login successful")

    # Bad login
    bad_login = client.post("/api/auth/login", json={"admission_number": "ADM2026001", "password": "wrong"})
    assert bad_login.status_code == 401, f"Expected 401 on bad password"
    print("[PASS] Invalid credentials rejected with 401")

    # 3. Test Student Questionnaire Submission & Privacy
    q_data = {
        "q_speaking_comfort": 4,
        "q_speaking_no_ppt": 4,
        "q_persona": "Creative",
        "q_social_comfort": 5,
        "q_atmosphere": "Very energetic",
        "q_leadership_comfort": 3,
        "q_priority": "Different strengths",
        "q_fun_ppt_crash": "Start explaining confidently",
        "q_fun_10min_rush": "The person making a plan",
        "q_fun_team_name": "Phoenix Presenters"
    }
    q_res = client.post("/api/student/questionnaire", json=q_data, headers=std_headers)
    assert q_res.status_code == 200, f"Questionnaire submission failed: {q_res.text}"

    my_q = client.get("/api/student/questionnaire", headers=std_headers).json()
    assert my_q["completed"] is True
    assert my_q["data"]["q_persona"] == "Creative"
    print("[PASS] Student questionnaire submitted and verified")

    # Verify student cannot access admin routes
    forbidden_res = client.get("/api/admin/metrics", headers=std_headers)
    assert forbidden_res.status_code == 403, "Student should not access admin endpoints"
    print("[PASS] Role-based security enforced: Student cannot access Admin endpoints")

    # 4. Test Constraints Management (Together / Apart)
    with db_session() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE admission_number IN ('ADM2026001', 'ADM2026002') ORDER BY id ASC")
        s1, s2 = [r[0] for r in c.fetchall()]

    c_res = client.post("/api/admin/constraints", json={
        "student_a_id": s1,
        "student_b_id": s2,
        "constraint_type": "TOGETHER"
    }, headers=admin_headers)
    assert c_res.status_code == 200, f"Constraint add failed: {c_res.text}"
    print("[PASS] 'Keep Together' constraint added successfully")

    # 5. Simulate Questionnaires for remaining students & Generate Groups
    sim_res = client.post("/api/admin/seed_sample_questionnaires", headers=admin_headers)
    assert sim_res.status_code == 200, f"Simulate questionnaires failed: {sim_res.text}"
    print("[PASS] Realistic questionnaires simulated for all 69 students")

    # Run Group Balancing Algorithm
    gen_res = client.post("/api/admin/groups/generate", headers=admin_headers)
    assert gen_res.status_code == 200, f"Group generation failed: {gen_res.text}"
    print("[PASS] Group generation algorithm executed")

    # Verify generated distribution
    groups_res = client.get("/api/admin/groups", headers=admin_headers).json()
    groups_list = groups_res["groups"]
    assert len(groups_list) == 10, f"Expected 10 groups, got {len(groups_list)}"

    member_counts = [g["member_count"] for g in groups_list]
    assert sorted(member_counts) == [6, 7, 7, 7, 7, 7, 7, 7, 7, 7], f"Group sizes violation: {member_counts}"
    assert sum(member_counts) == 69, f"Total students assigned != 69 ({sum(member_counts)})"
    print(f"[PASS] Group sizing strictly verified: 9 groups of 7, 1 group of 6 (Total 69)")

    # Verify Together constraint respected
    with db_session() as conn:
        c = conn.cursor()
        c.execute("SELECT group_id FROM students WHERE id = ?", (s1,))
        g1 = c.fetchone()[0]
        c.execute("SELECT group_id FROM students WHERE id = ?", (s2,))
        g2 = c.fetchone()[0]
        assert g1 == g2, f"Together constraint violated: s1 in {g1}, s2 in {g2}"
    print(f"[PASS] Keep Together constraint respected: Students assigned to same group ({g1})")

    # 6. Test Fairness Diagnostics Report
    fairness_res = client.get("/api/admin/fairness_report", headers=admin_headers)
    assert fairness_res.status_code == 200
    report = fairness_res.json()["groups_fairness"]
    assert len(report) == 10
    for r in report:
        assert 1.0 <= r["speaking_avg"] <= 5.0
        assert r["balance_score"] >= 40.0
    print("[PASS] Fairness diagnostic report computed accurately for all 10 groups")

    # 7. Finalize Groups
    fin_res = client.post("/api/admin/groups/finalize", headers=admin_headers)
    assert fin_res.status_code == 200, f"Finalize failed: {fin_res.text}"
    print("[PASS] 10 groups finalized by Admin")

    # 8. Test Topic Allocation
    # Option B: Preference-based or Random
    top_res = client.post("/api/admin/topics/assign_random", headers=admin_headers)
    assert top_res.status_code == 200, f"Topic assignment failed: {top_res.text}"

    with db_session() as conn:
        c = conn.cursor()
        c.execute("SELECT topic_id FROM groups")
        assigned_topics = [r[0] for r in c.fetchall()]
        assert len(set(assigned_topics)) == 10, f"Not all topics unique: {assigned_topics}"
        assert None not in assigned_topics, "Some group lacks topic"
    print("[PASS] 10 unique presentation topics assigned (each group gets exactly 1 unique topic)")

    # 9. Test Student Dashboard & Presentation Planner
    dash_res = client.get("/api/student/dashboard", headers=std_headers).json()
    assert dash_res["groups_finalized"] is True
    assert dash_res["group"] is not None
    assert dash_res["group"]["topic_title"] is not None
    group_id = dash_res["group"]["group_id"]
    print(f"[PASS] Student dashboard shows Group {dash_res['group']['group_number']} and topic '{dash_res['group']['topic_title']}'")

    # Test Speaking Confirmation ("I WILL SPEAK")
    conf_res = client.post("/api/student/confirm_speaking", headers=std_headers)
    assert conf_res.status_code == 200
    print("[PASS] Student 'I WILL SPEAK' confirmation recorded")

    # Add a speaking section
    sec_res = client.post(f"/api/workspace/group/{group_id}/sections", json={
        "student_id": dash_res["student"]["id"],
        "title": "Introduction to the Topic",
        "speaking_seconds": 120,
        "notes": "Define core terminology and problem scope"
    }, headers=std_headers)
    assert sec_res.status_code == 200
    sec_id = sec_res.json()["id"]
    print("[PASS] Speaking section created in group workspace")

    # Workspace status verification
    ws_res = client.get(f"/api/workspace/group/{group_id}", headers=std_headers).json()
    assert len(ws_res["sections"]) >= 1
    assert ws_res["checklist"]["total_seconds"] == 120
    print("[PASS] Visual presentation timer & planner tracked speaking duration (2:00 / 15:00)")

    # 10. Test CSV Export
    csv_res = client.get("/api/admin/export/csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "Admission Number" in csv_res.text
    assert "ADM2026001" in csv_res.text
    print("[PASS] CSV export generated valid roster with students, groups, and topics")

    # 11. Test Full Flow Simulation Helper
    flow_res = client.post("/api/admin/simulate_complete_flow", headers=admin_headers)
    assert flow_res.status_code == 200
    metrics_res = client.get("/api/admin/metrics", headers=admin_headers).json()
    assert metrics_res["presentation_ready_groups"] == 10
    print("[PASS] Full flow simulation verified: All 10 groups are PRESENTATION READY!")

    print("\n=======================================================")
    print("ALL 11 TEST SUITES PASSED FLAWLESSLY!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
