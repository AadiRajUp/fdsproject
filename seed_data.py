import sqlite3
import random
import numpy as np
from math import exp
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

DATABASE_PATH = Path(__file__).with_name("users.db")

def compute_score(study_hours, focus_score, sleep_hours, phone_usage_hours):
    study_weight = 11.812612
    focus_weight =  6.597617
    sleep_weight =  5.476603
    phone_weight = -5.393503
    intercept    = 50.146637

    raw_score = (
        intercept
        + study_weight * study_hours
        + focus_weight * focus_score
        + sleep_weight * sleep_hours
        + phone_weight * phone_usage_hours
    )
    score = 100 / (1 + exp(-(raw_score - 550) / 100))
    return round(max(0, min(100, score)), 4)

# 20 fake users
fake_users = [
    ("Aarav Sharma",    "aarav@example.com"),
    ("Bipana Thapa",    "bipana@example.com"),
    ("Chirag Adhikari", "chirag@example.com"),
    ("Disha Karki",     "disha@example.com"),
    ("Emon Shrestha",   "emon@example.com"),
    ("Falak Rai",       "falak@example.com"),
    ("Gaurav Poudel",   "gaurav@example.com"),
    ("Hira Tamang",     "hira@example.com"),
    ("Ishan Basnet",    "ishan@example.com"),
    ("Jyoti Maharjan",  "jyoti@example.com"),
    ("Kiran Bhandari",  "kiran@example.com"),
    ("Laxmi Gurung",    "laxmi@example.com"),
    ("Manish Dahal",    "manish@example.com"),
    ("Nisha Limbu",     "nisha@example.com"),
    ("Om Pandey",       "om@example.com"),
    ("Priya Magar",     "priya@example.com"),
    ("Qumar Ansari",    "qumar@example.com"),
    ("Rajan Hamal",     "rajan@example.com"),
    ("Sita Neupane",    "sita@example.com"),
    ("Tenzing Lama",    "tenzing@example.com"),
]

# Personality profiles — each user has different habits
profiles = [
    {"study": (6, 8),   "focus": (80, 95), "sleep": (7, 9),   "phone": (1, 3)},  # high performer
    {"study": (5, 7),   "focus": (70, 85), "sleep": (6, 8),   "phone": (2, 4)},
    {"study": (4, 6),   "focus": (60, 75), "sleep": (6, 8),   "phone": (3, 5)},
    {"study": (3, 5),   "focus": (50, 70), "sleep": (5, 7),   "phone": (4, 6)},
    {"study": (2, 4),   "focus": (40, 60), "sleep": (5, 7),   "phone": (5, 7)},  # low performer
    {"study": (7, 9),   "focus": (85, 98), "sleep": (8, 9),   "phone": (1, 2)},  # top performer
    {"study": (5, 8),   "focus": (65, 80), "sleep": (7, 8),   "phone": (2, 4)},
    {"study": (4, 7),   "focus": (55, 75), "sleep": (6, 7),   "phone": (3, 5)},
    {"study": (3, 6),   "focus": (50, 65), "sleep": (5, 6),   "phone": (4, 7)},
    {"study": (6, 9),   "focus": (75, 90), "sleep": (7, 9),   "phone": (1, 3)},
    {"study": (2, 5),   "focus": (45, 65), "sleep": (4, 6),   "phone": (5, 8)},
    {"study": (5, 7),   "focus": (70, 82), "sleep": (6, 8),   "phone": (2, 4)},
    {"study": (4, 6),   "focus": (60, 78), "sleep": (6, 7),   "phone": (3, 6)},
    {"study": (3, 5),   "focus": (55, 70), "sleep": (5, 7),   "phone": (4, 6)},
    {"study": (6, 8),   "focus": (78, 92), "sleep": (7, 8),   "phone": (1, 3)},
    {"study": (5, 7),   "focus": (68, 84), "sleep": (6, 8),   "phone": (2, 5)},
    {"study": (4, 6),   "focus": (58, 74), "sleep": (6, 7),   "phone": (3, 5)},
    {"study": (3, 5),   "focus": (48, 65), "sleep": (5, 6),   "phone": (5, 7)},
    {"study": (7, 9),   "focus": (82, 96), "sleep": (8, 9),   "phone": (1, 2)},
    {"study": (2, 4),   "focus": (42, 58), "sleep": (4, 6),   "phone": (6, 9)},  # low performer
]

today = datetime.now().date()

with sqlite3.connect(DATABASE_PATH) as conn:

    # ── Insert 20 fake users ──────────────────────────────────────
    user_ids = []
    for i, (name, email) in enumerate(fake_users):
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing:
            user_ids.append(existing[0])
            print(f"  User exists: {name}")
        else:
            uid = f"USR-{uuid4().hex[:12].upper()}"
            conn.execute(
                "INSERT INTO users (uid, full_name, email, password) VALUES (?, ?, ?, ?)",
                (uid, name, email, "1234"),
            )
            user_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()[0]
            user_ids.append(user_id)
            print(f"  Created user: {name}")

    print(f"\nTotal users in DB: {len(user_ids)}")

    # ── Insert 15 days of data for each user ──────────────────────
    total_inserted = 0
    for idx, user_id in enumerate(user_ids):
        profile = profiles[idx % len(profiles)]

        for day_offset in range(14, -1, -1):  # 14 days ago → today
            activity_date = (today - timedelta(days=day_offset)).isoformat()

            # Skip randomly to simulate missed days (20% chance)
            if day_offset > 0 and random.random() < 0.2:
                continue

            # Generate realistic values based on profile
            study_hours       = round(random.uniform(*profile["study"]), 1)
            focus_score       = random.randint(*profile["focus"])
            sleep_hours       = round(random.uniform(*profile["sleep"]), 1)
            phone_usage_hours = round(random.uniform(*profile["phone"]), 1)

            # Add slight daily variation
            study_hours       = round(max(0, study_hours + random.uniform(-0.5, 0.5)), 1)
            focus_score       = max(0, min(100, focus_score + random.randint(-5, 5)))
            sleep_hours       = round(max(0, sleep_hours + random.uniform(-0.5, 0.5)), 1)
            phone_usage_hours = round(max(0, phone_usage_hours + random.uniform(-0.5, 0.5)), 1)

            score = compute_score(study_hours, focus_score, sleep_hours, phone_usage_hours)

            conn.execute(
                """
                INSERT INTO daily_productivity (
                    user_id, activity_date, study_hours,
                    focus_score, sleep_hours, phone_usage_hours, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, activity_date) DO UPDATE SET
                    study_hours       = excluded.study_hours,
                    focus_score       = excluded.focus_score,
                    sleep_hours       = excluded.sleep_hours,
                    phone_usage_hours = excluded.phone_usage_hours,
                    score             = excluded.score
                """,
                (user_id, activity_date, study_hours,
                 focus_score, sleep_hours, phone_usage_hours, score),
            )
            total_inserted += 1

    print(f"Inserted {total_inserted} daily records across {len(user_ids)} users")
    print(f"Date range: {(today - timedelta(days=14)).isoformat()} → {today.isoformat()}")

    # ── Verify ────────────────────────────────────────────────────
    total = conn.execute("SELECT COUNT(*) FROM daily_productivity").fetchone()[0]
    avg   = conn.execute("SELECT ROUND(AVG(score),2) FROM daily_productivity").fetchone()[0]
    mn    = conn.execute("SELECT ROUND(MIN(score),2) FROM daily_productivity").fetchone()[0]
    mx    = conn.execute("SELECT ROUND(MAX(score),2) FROM daily_productivity").fetchone()[0]

    print(f"\n=== Database Summary ===")
    print(f"Total records : {total}")
    print(f"Average score : {avg}")
    print(f"Min score     : {mn}")
    print(f"Max score     : {mx}")
    print(f"\nDone! Run python3 main.py to see the graphs.")