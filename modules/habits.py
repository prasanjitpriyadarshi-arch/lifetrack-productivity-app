"""Custom habits with streaks and a period-based goals manager."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database as db
from modules.common import page_heading, show_records_editor


def render_habits() -> None:
    page_heading("Habit tracker", "Check in daily and see the streaks you are building.")
    focus_date = st.date_input("Habit check-in date", value=date.today(), key="habit_focus_date")
    habits = db.read_table("habits", order_by="name ASC", active_only=True)
    logs = db.read_table("habit_logs", order_by="log_date DESC")
    day_logs = logs.loc[logs["log_date"] == focus_date.isoformat()] if not logs.empty else pd.DataFrame()
    completed_ids = set(day_logs.loc[day_logs["completed"] == 1, "habit_id"].astype(int)) if not day_logs.empty else set()
    completed_count = len(completed_ids.intersection(set(habits["id"].astype(int)))) if not habits.empty else 0
    progress = completed_count / len(habits) if len(habits) else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Habits", len(habits))
    col_b.metric("Completed", completed_count)
    col_c.metric("Daily completion", f"{progress:.0%}")
    st.progress(progress, text=f"{completed_count} of {len(habits)} habits complete")

    if habits.empty:
        st.info("Add a habit below to start your tracker.")
    else:
        for _, habit in habits.iterrows():
            habit_id = int(habit["id"])
            key = f"habit_done_{focus_date.isoformat()}_{habit_id}"
            columns = st.columns([0.08, 0.58, 0.34])
            columns[0].checkbox(
                "Completed", value=habit_id in completed_ids, key=key,
                label_visibility="collapsed", on_change=_save_habit_completion,
                args=(key, habit_id, focus_date),
            )
            columns[1].write(str(habit["name"]))
            columns[2].caption(f"Current streak: {_streak(logs, habit_id, focus_date)} days")

    st.divider()
    st.subheader("Create a custom habit")
    with st.form("add_habit_form"):
        name = st.text_input("Habit name", placeholder="For example: Review lecture notes", max_chars=100)
        submitted = st.form_submit_button("Add habit", type="primary")
    if submitted:
        if not name.strip():
            st.error("Enter a name for your habit.")
        else:
            try:
                db.insert_record("habits", {"name": name.strip(), "active": 1})
                st.success("Habit added.")
                st.rerun()
            except Exception:
                st.error("That habit already exists. Choose a different name.")

    if not habits.empty:
        with st.expander("Remove a habit", expanded=False):
            by_id = {int(row["id"]): row["name"] for row in habits.to_dict("records")}
            with st.form("delete_habit_form"):
                delete_id = st.selectbox("Habit to remove", list(by_id), format_func=lambda value: by_id[int(value)], key="delete_habit_choice")
                confirmed = st.checkbox("I understand this removes the habit's completion history", key="delete_habit_confirm")
                delete = st.form_submit_button("Remove habit")
            if delete:
                if not confirmed:
                    st.warning("Confirm before removing this habit.")
                else:
                    db.delete_record("habits", int(delete_id))
                    st.success("Habit removed.")
                    st.rerun()

    if not logs.empty:
        names = habits.set_index("id")["name"].to_dict() if not habits.empty else {}
        history = logs.copy()
        history["habit"] = history["habit_id"].map(names).fillna("Removed habit")
        history["status"] = history["completed"].map({1: "Complete", 0: "Not complete"})
        st.subheader("Habit history")
        st.dataframe(history[["log_date", "habit", "status"]], hide_index=True, use_container_width=True)


def _save_habit_completion(key: str, habit_id: int, log_date: date) -> None:
    db.upsert_daily_log("habit_logs", "habit_id", habit_id, log_date, bool(st.session_state[key]))


def _streak(logs: pd.DataFrame, habit_id: int, through_date: date) -> int:
    if logs.empty:
        return 0
    complete_dates = set(
        logs.loc[(logs["habit_id"] == habit_id) & (logs["completed"] == 1), "log_date"].astype(str)
    )
    streak = 0
    day = through_date
    while day.isoformat() in complete_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def render_goals() -> None:
    page_heading("Goals", "Keep daily, weekly, and monthly priorities visible and actionable.")
    goals = db.read_table("goals", order_by="deadline ASC")
    completed = int((goals["status"] == "Completed").sum()) if not goals.empty else 0
    open_goals = len(goals) - completed
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Active goals", open_goals)
    col_b.metric("Completed", completed)
    col_c.metric("Total goals", len(goals))
    fields = [
        {"name": "title", "label": "Goal title", "kind": "text"},
        {"name": "goal_period", "label": "Goal period", "kind": "select", "options": ["Daily", "Weekly", "Monthly"], "default": "Weekly"},
        {"name": "description", "label": "Description", "kind": "textarea"},
        {"name": "deadline", "label": "Deadline", "kind": "date", "default": date.today()},
        {"name": "priority", "label": "Priority", "kind": "select", "options": ["Low", "Medium", "High"], "default": "Medium"},
        {"name": "status", "label": "Status", "kind": "select", "options": ["Not started", "In progress", "Completed"], "default": "Not started"},
    ]
    show_records_editor("goals", fields, "deadline ASC", ("goal_period", "title"))
