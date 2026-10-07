import random
from app.database import db_session, init_db
from app.auth import hash_password

TOPICS_LIST = [
    {
        "title": "Sweat & Grit: Shaping Character & Leadership Through Sports",
        "description": "Examining how athletics cultivate grit, strategic decision making, and team leadership competencies."
    },
    {
        "title": "Digital Detox for Circadian Rhythm",
        "description": "Analyzing blue light impacts on melatonin synthesis, REM sleep architecture, and digital habit rewiring."
    },
    {
        "title": "Deconstructing Modern Diet Culture to Sustainable Balanced Diet",
        "description": "Debunking fad diets, micro-nutrient deficiencies, and building evidence-based intuitive nutrition protocols."
    },
    {
        "title": "Detangling Stress, Anxiety & Burnout in Students",
        "description": "Cognitive, neurological, and behavioral strategies to mitigate academic burnout and acute anxiety."
    },
    {
        "title": "Yoga for Ergonomic Posture",
        "description": "Biomechanical alignment, asana therapy for spinal health, and corrective desk-worker ergonomics."
    },
    {
        "title": "Sedentary Slump & Lifestyle Diseases in Youth",
        "description": "Pathophysiology of prolonged sitting, early metabolic syndrome, and desk-to-gym intervention models."
    },
    {
        "title": "Substance Abuse: Peer Dynamics And Chemical Dependencies",
        "description": "Neurochemistry of addiction, psychosocial triggers in campus settings, and systemic recovery protocols."
    },
    {
        "title": "Active Ageing Strategies to Combat Sarcopenia",
        "description": "Resistance training mechanisms, protein kinematics, and functional longevity preservation for older adults."
    },
    {
        "title": "CPR & Heimlich Maneuver as Emergency Protocols",
        "description": "Lifesaving BLS (Basic Life Support) algorithms, airway obstruction triage, and rapid crisis response."
    },
    {
        "title": "Physical Activity as a Preventive Medicine",
        "description": "Exercise as pharmaceutical-grade prophylaxis against cardiovascular, oncological, and neurodegenerative decline."
    }
]

PERSONAS = [
    "Planner",
    "Talker",
    "Creative",
    "Calm",
    "Problem solver",
    "Funny one",
    "Last-minute survivor",
    "Depends on the situation"
]

ATMOSPHERES = ["Very energetic", "Calm", "Balanced"]

PRIORITIES = [
    "Good communication",
    "Similar interests",
    "Different strengths",
    "Friendly atmosphere",
    "Everyone contributing",
    "Good planning"
]

PPT_CRASH_OPTIONS = [
    "Continue without PPT",
    "Start explaining confidently",
    "Make a joke and recover",
    "Ask another member to handle it",
    "Panic internally but continue",
    '"This was part of our plan."'
]

RUSH_10MIN_OPTIONS = [
    "The person making a plan",
    "The person doing the work",
    "The person motivating everyone",
    'The person saying "don\'t worry"',
    "The person somehow fixing everything",
    'The person asking "what happened?"'
]

TEAM_NAME_IDEAS = [
    "The Synergy Squad", "Precision Presenters", "Vitality Vanguard", "Apex Orators",
    "The Circadian Crew", "Quantum Speakers", "Ergonomic Elite", "Catalyst Collective",
    "Brainstorm Battalion", "The Equilibrium", "Dynamic Dispatch", "Pulse Pioneers"
]

def seed_database(force_reseed: bool = False):
    """Seed the database with the initial 10 topics, 10 groups, admin user, and 69 students."""
    init_db()

    with db_session() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT'")
        count = cursor.fetchone()[0]
        if count == 69 and not force_reseed:
            return {"status": "already_seeded", "students": count}

        if force_reseed:
            cursor.execute("DELETE FROM speaking_confirmations")
            cursor.execute("DELETE FROM presentation_sections")
            cursor.execute("DELETE FROM group_constraints")
            cursor.execute("DELETE FROM group_topic_preferences")
            cursor.execute("DELETE FROM questionnaires")
            cursor.execute("DELETE FROM students")
            cursor.execute("DELETE FROM groups")
            cursor.execute("DELETE FROM topics")
            cursor.execute("DELETE FROM group_history")

        # 1. Insert 10 Topics
        cursor.execute("SELECT COUNT(*) FROM topics")
        if cursor.fetchone()[0] == 0:
            for t in TOPICS_LIST:
                cursor.execute(
                    "INSERT INTO topics (title, description) VALUES (?, ?)",
                    (t["title"], t["description"])
                )

        # 2. Insert 10 Groups (9 groups of 7, 1 group of 6)
        cursor.execute("SELECT COUNT(*) FROM groups")
        if cursor.fetchone()[0] == 0:
            for g_num in range(1, 11):
                max_members = 7 if g_num <= 9 else 6
                cursor.execute(
                    "INSERT INTO groups (group_number, max_members, is_locked, finalized) VALUES (?, ?, 0, 0)",
                    (g_num, max_members)
                )

        # 3. Insert Admin Account (Ahmed Sabith)
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'ADMIN'")
        if cursor.fetchone()[0] == 0:
            admin_pwd_hash = hash_password("admin123")
            cursor.execute(
                """
                INSERT INTO students (admission_number, roll_number, full_name, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?, 'ADMIN')
                """,
                ("ADMIN", "ADMIN", "Ahmed Sabith", "ahmedsabith89@gmail.com", admin_pwd_hash)
            )

        # 4. Insert Tester Profiles (Evaluators / QA - Not included in groups)
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'TESTER'")
        if cursor.fetchone()[0] == 0:
            tester_pwd_hash = hash_password("tester123")
            testers_data = [
                ("TESTER01", "TEST-01", "Dr. Evelyn Reed (QA Evaluator)", "evelyn.qa@college.edu"),
                ("TESTER02", "TEST-02", "Marcus Chen (Wellness Auditor)", "marcus.audit@college.edu"),
                ("TESTER03", "TEST-03", "Aria Sharma (UX Reviewer)", "aria.ux@college.edu")
            ]
            for adm, roll, name, em in testers_data:
                cursor.execute(
                    """
                    INSERT INTO students (admission_number, roll_number, full_name, email, password_hash, role)
                    VALUES (?, ?, ?, ?, ?, 'TESTER')
                    """,
                    (adm, roll, name, em, tester_pwd_hash)
                )

        # 5. Insert exactly 69 Students (Exclusively form the 10 presentation groups)
        cursor.execute("SELECT COUNT(*) FROM students WHERE role = 'STUDENT'")
        if cursor.fetchone()[0] == 0:
            std_pwd_hash = hash_password("student123")
            for i in range(1, 70):
                adm_no = f"ADM2026{i:03d}"
                roll_no = f"R{i:02d}"
                full_name = f"Student {i:03d}"
                email = f"student{i:03d}@college.edu"
                cursor.execute(
                    """
                    INSERT INTO students (admission_number, roll_number, full_name, email, password_hash, role)
                    VALUES (?, ?, ?, ?, ?, 'STUDENT')
                    """,
                    (adm_no, roll_no, full_name, email, std_pwd_hash)
                )

    return {"status": "success", "students_seeded": 69, "groups_seeded": 10, "topics_seeded": 10}


def simulate_questionnaires(sample_count: int = 69):
    """
    Simulate questionnaire answers for testing and algorithmic balance verification.
    Uses realistic distribution of speaking confidence, diverse personas, and varied preferences.
    """
    random.seed(42)  # For reproducible realistic benchmark data

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM students WHERE role = 'STUDENT' ORDER BY id ASC LIMIT ?", (sample_count,))
        students = [row[0] for row in cursor.fetchall()]

        # Generate realistic diversified profiles
        # approx 25% low confidence (1-2), 50% medium (3), 25% high (4-5)
        for idx, student_id in enumerate(students):
            # Varied speaking profile
            tier = idx % 4
            if tier == 0:
                speak_conf = random.choice([4, 5])
                no_ppt = random.choice([3, 4, 5])
                leader_conf = random.choice([4, 5])
            elif tier == 1:
                speak_conf = random.choice([1, 2])
                no_ppt = random.choice([1, 2, 3])
                leader_conf = random.choice([1, 2, 3])
            else:
                speak_conf = random.choice([2, 3, 4])
                no_ppt = random.choice([2, 3, 4])
                leader_conf = random.choice([2, 3, 4])

            social_conf = random.randint(2, 5)
            persona = PERSONAS[idx % len(PERSONAS)]
            atmosphere = ATMOSPHERES[idx % len(ATMOSPHERES)]
            priority = PRIORITIES[idx % len(PRIORITIES)]
            fun_ppt = PPT_CRASH_OPTIONS[idx % len(PPT_CRASH_OPTIONS)]
            fun_rush = RUSH_10MIN_OPTIONS[idx % len(RUSH_10MIN_OPTIONS)]
            team_name = TEAM_NAME_IDEAS[idx % len(TEAM_NAME_IDEAS)]

            cursor.execute(
                """
                INSERT INTO questionnaires 
                (student_id, q_speaking_comfort, q_speaking_no_ppt, q_persona, q_social_comfort, 
                 q_atmosphere, q_leadership_comfort, q_priority, q_fun_ppt_crash, q_fun_10min_rush, q_fun_team_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                (student_id, speak_conf, no_ppt, persona, social_conf, atmosphere, leader_conf, priority, fun_ppt, fun_rush, team_name)
            )

    return {"status": "success", "simulated": len(students)}
