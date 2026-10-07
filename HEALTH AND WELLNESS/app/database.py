import sqlite3
import os
import json
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "presentation_hub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

@contextmanager
def db_session():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_session() as conn:
        cursor = conn.cursor()

        # Groups table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_number INTEGER UNIQUE NOT NULL,
            max_members INTEGER NOT NULL,
            is_locked INTEGER NOT NULL DEFAULT 0,
            topic_id INTEGER,
            finalized INTEGER NOT NULL DEFAULT 0,
            custom_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
        )
        """)

        # Topics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            description TEXT
        )
        """)

        # Students / Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_number TEXT UNIQUE NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'STUDENT',
            group_id INTEGER,
            is_locked INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
        )
        """)

        # Questionnaires table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questionnaires (
            student_id INTEGER PRIMARY KEY,
            q_speaking_comfort INTEGER NOT NULL,
            q_speaking_no_ppt INTEGER NOT NULL,
            q_persona TEXT NOT NULL,
            q_social_comfort INTEGER NOT NULL,
            q_atmosphere TEXT NOT NULL,
            q_leadership_comfort INTEGER NOT NULL,
            q_priority TEXT NOT NULL,
            q_fun_ppt_crash TEXT NOT NULL,
            q_fun_10min_rush TEXT NOT NULL,
            q_fun_team_name TEXT NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)

        # Group topic preferences
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_topic_preferences (
            group_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            rank_preference INTEGER NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, rank_preference),
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
        """)

        # Admin constraints (Keep together / Keep apart)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_constraints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_a_id INTEGER NOT NULL,
            student_b_id INTEGER NOT NULL,
            constraint_type TEXT NOT NULL CHECK(constraint_type IN ('TOGETHER', 'APART')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_a_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (student_b_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_a_id, student_b_id, constraint_type)
        )
        """)

        # Presentation sections
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS presentation_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            speaking_seconds INTEGER NOT NULL DEFAULT 120,
            notes TEXT DEFAULT '',
            order_index INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)

        # Speaking confirmations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS speaking_confirmations (
            group_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, student_id),
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)

        # Group Assignment History for Undo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_json TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # System settings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_group ON students(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sections_group ON presentation_sections(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_confirm_group ON speaking_confirmations(group_id)")
