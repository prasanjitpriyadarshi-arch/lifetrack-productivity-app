"""Focused tests for SQLite CRUD, durable storage, seeding, and sleep math."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

import database as db


class LifeTrackDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "test_lifetrack.db"
        db.initialize_database()

    def tearDown(self) -> None:
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_add_edit_delete_and_reopen_record(self) -> None:
        record_id = db.insert_record(
            "workouts",
            {"workout_date": "2026-11-20", "exercise": "Push day", "duration_minutes": 45, "notes": "Test record"},
        )
        self.assertEqual(len(db.read_table("workouts")), 1)
        db.update_record("workouts", record_id, {"exercise": "Leg day", "duration_minutes": 60})
        updated = db.read_table("workouts")
        self.assertEqual(updated.loc[0, "exercise"], "Leg day")
        self.assertEqual(int(updated.loc[0, "duration_minutes"]), 60)
        db.delete_record("workouts", record_id)
        self.assertTrue(db.read_table("workouts").empty)

    def test_daily_completion_is_upserted_and_persists(self) -> None:
        activity_id = int(db.read_table("activities").iloc[0]["id"])
        today = date(2026, 11, 20)
        db.upsert_daily_log("activity_logs", "activity_id", activity_id, today, True)
        db.upsert_daily_log("activity_logs", "activity_id", activity_id, today, False)
        logs = db.read_table("activity_logs")
        self.assertEqual(len(logs), 1)
        self.assertEqual(int(logs.iloc[0]["completed"]), 0)

    def test_screen_time_updates_existing_day_and_app(self) -> None:
        today = date(2026, 11, 20)
        db.upsert_screen_time(today, "Education", 40, True)
        db.upsert_screen_time(today, "Education", 55, True)
        entries = db.read_table("screen_time")
        self.assertEqual(len(entries), 1)
        self.assertEqual(int(entries.iloc[0]["minutes"]), 55)

    def test_sleep_duration_rolls_over_midnight(self) -> None:
        self.assertEqual(db.calculate_sleep_minutes("22:30", "06:30"), 480)
        self.assertEqual(db.calculate_sleep_minutes("23:45", "00:15"), 30)
        self.assertEqual(db.calculate_sleep_minutes("08:00", "09:30"), 90)

    def test_defaults_are_seeded_once(self) -> None:
        self.assertEqual(len(db.read_table("activities")), len(db.DEFAULT_ROUTINE))
        for activity_id in db.read_table("activities")["id"].astype(int).tolist():
            db.delete_record("activities", activity_id)
        db.initialize_database()
        self.assertTrue(db.read_table("activities").empty)


if __name__ == "__main__":
    unittest.main()
