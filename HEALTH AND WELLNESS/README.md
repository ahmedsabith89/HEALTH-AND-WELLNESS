# HEALTH AND WELLNESS - PRESENTATION

A complete, production-ready private college-class presentation management system designed for **exactly 69 students** organized into **10 wellness presentation teams**.

---

## 🏛️ Class & System Architecture

### 1. Class Structure
- **Enrolled Students:** Exactly **69 students** (`Student 001` to `Student 069`).
- **Presentation Teams:** Exactly **10 groups**:
  - **9 groups of 7 students** ($9 \times 7 = 63$)
  - **1 group of 6 students** ($1 \times 6 = 6$)
  - **Total = 69 students**.
- **Assignment Guarantee:** Every student belongs to exactly ONE group. No unassigned students. No student in multiple groups.

### 2. The 10 Wellness Presentation Topics
Each group is assigned exactly ONE topic; all 10 topics are uniquely allocated without duplicates:
1. `Sweat & Grit: Shaping Character & Leadership Through Sports`
2. `Digital Detox for Circadian Rhythm`
3. `Deconstructing Modern Diet Culture to Sustainable Balanced Diet`
4. `Detangling Stress, Anxiety & Burnout in Students`
5. `Yoga for Ergonomic Posture`
6. `Sedentary Slump & Lifestyle Diseases in Youth`
7. `Substance Abuse: Peer Dynamics And Chemical Dependencies`
8. `Active Ageing Strategies to Combat Sarcopenia`
9. `CPR & Heimlich Maneuver as Emergency Protocols`
10. `Physical Activity as a Preventive Medicine`

---

## 🔐 Credentials & Evaluation Switcher

The application includes an instant **Quick-Switch Evaluation Login** bar on the login screen:

### 👑 Course Coordinator / Admin
- **Name:** Ahmed Sabith
- **Email:** `ahmedsabith89@gmail.com`
- **Username / Admission No:** `ADMIN`, `ahmed`, or `ahmedsabith89@gmail.com`
- **Password:** `admin123`
- **Capabilities:** Full administration, student management, Keep Together/Apart constraints, balanced group generation, fairness diagnostics, topic assignment, CSV export.

### 🔍 Independent Tester Profiles (Excluded from Groups)
These tester profiles allow QA evaluators to test student and group flows without altering the 69 student roster:
| Tester Name | Admission / Login | Password | Role |
| :--- | :--- | :--- | :--- |
| **Dr. Evelyn Reed** | `TESTER01` | `tester123` | QA Specialist / Sandbox Evaluator |
| **Marcus Chen** | `TESTER02` | `tester123` | Curriculum & Wellness Auditor |
| **Aria Sharma** | `TESTER03` | `tester123` | Student Experience / UX Reviewer |

### 🎓 Enrolled Students (69 Group Members)
- **Admission Numbers:** `ADM2026001` to `ADM2026069`
- **Password:** `student123`
- **Default Rolls:** `R01` to `R69`

---

## 🌿 Catchy UI/UX & Design Combos
- **Emerald Vitality & Oceanic Cyan:** Modern collegiate aesthetic tailored for Health & Wellness.
- **Glassmorphic Cards:** Translucent frosted panels with soft ambient glow and subtle green borders.
- **Micro-Interactions:** Pulsing indicators for presentation readiness, dynamic timer gauges, and animated status badges.
- **Mobile First:** Optimized for seamless usage on smartphones and tablets.

---

## 📦 Git Configuration

Git has been configured with your credentials:
- **Git User Name:** `Ahmed Sabith`
- **Git User Email:** `ahmedsabith89@gmail.com`
- **Git Repository:** Initialized on `main` branch with complete version tracking.

---

## 🏃 Running the Application

### Start the Server:
```powershell
python run.py
```
Or directly with uvicorn:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open in your browser:
**`http://127.0.0.1:8000`**

### Run Automated Integration Tests:
```powershell
python test_app.py
```
All 11 end-to-end integration test suites run automatically.
