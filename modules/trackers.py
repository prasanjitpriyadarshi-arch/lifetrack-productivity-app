"""Fitness, meditation, study, skill, sleep, and manual screen-time trackers."""

from datetime import date, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from modules.common import format_hours, page_heading, show_chart, show_records_editor

STUDY_TYPES = ["College subject", "Assignment work", "Revision", "Extra study", "Competitive exam preparation"]
SKILL_NAMES = ["Python", "C Programming", "Data Structures and Algorithms", "AI and Machine Learning", "Web Development", "Other"]
APPS = ["Instagram", "YouTube", "WhatsApp", "Browser", "Gaming", "Education", "Other applications"]


def render_gym() -> None:
    page_heading("Gym & fitness", "Record workouts and build consistency one session at a time.")
    data = db.read_table("workouts", order_by="workout_date DESC")
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week = _date_range(data, "workout_date", week_start, today)
    minutes = int(week["duration_minutes"].sum()) if not week.empty else 0
    sessions = len(week)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("This week", format_hours(minutes))
    col_b.metric("Sessions", sessions)
    col_c.metric("Average session", format_hours(minutes // sessions if sessions else 0))
    fields = [
        {"name": "workout_date", "label": "Workout date", "kind": "date", "default": today},
        {"name": "exercise", "label": "Exercise or workout", "kind": "text"},
        {"name": "duration_minutes", "label": "Duration (minutes)", "kind": "number", "min": 1, "max": 720, "default": 45, "step": 5},
        {"name": "notes", "label": "Workout notes", "kind": "textarea"},
    ]
    data = show_records_editor("workouts", fields, "workout_date DESC", ("workout_date", "exercise"))
    if not week.empty:
        chart = week.groupby("workout_date", as_index=False)["duration_minutes"].sum()
        chart["date"] = pd.to_datetime(chart["workout_date"])
        fig = px.bar(chart, x="date", y="duration_minutes", title="Exercise minutes this week", labels={"date": "Date", "duration_minutes": "Minutes"}, color_discrete_sequence=["#b6e75c"])
        show_chart(fig, "gym_week_chart")


def render_meditation() -> None:
    page_heading("Meditation", "Keep a simple record of your daily mindfulness practice.")
    data = db.read_table("meditation", order_by="meditation_date DESC")
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week = _date_range(data, "meditation_date", week_start, today)
    minutes = int(week.loc[week["completed"] == 1, "duration_minutes"].sum()) if not week.empty else 0
    completed_days = week.loc[week["completed"] == 1, "meditation_date"].nunique() if not week.empty else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("This week", format_hours(minutes))
    col_b.metric("Practice days", int(completed_days))
    col_c.metric("Daily goal", "10 min")
    fields = [
        {"name": "meditation_date", "label": "Meditation date", "kind": "date", "default": today},
        {"name": "duration_minutes", "label": "Duration (minutes)", "kind": "number", "min": 1, "max": 600, "default": 10, "step": 5},
        {"name": "completed", "label": "Practice completed", "kind": "checkbox", "default": True},
        {"name": "notes", "label": "Notes (optional)", "kind": "textarea"},
    ]
    data = show_records_editor("meditation", fields, "meditation_date DESC", ("meditation_date", "duration_minutes"))
    if not week.empty:
        chart = week.groupby("meditation_date", as_index=False)["duration_minutes"].sum()
        chart["date"] = pd.to_datetime(chart["meditation_date"])
        fig = px.bar(chart, x="date", y="duration_minutes", title="Meditation minutes this week", labels={"date": "Date", "duration_minutes": "Minutes"}, color_discrete_sequence=["#9b8af7"])
        show_chart(fig, "meditation_week_chart")


def render_study() -> None:
    page_heading("Study tracker", "Separate coursework, assignments, revision, and exam preparation.")
    data = db.read_table("study_sessions", order_by="session_date DESC")
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week = _date_range(data, "session_date", week_start, today)
    today_rows = _date_range(data, "session_date", today, today)
    today_minutes = int(today_rows["duration_minutes"].sum()) if not today_rows.empty else 0
    week_minutes = int(week["duration_minutes"].sum()) if not week.empty else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Today", format_hours(today_minutes))
    col_b.metric("This week", format_hours(week_minutes))
    col_c.metric("Study sessions", len(data))
    fields = [
        {"name": "session_date", "label": "Study date", "kind": "date", "default": today},
        {"name": "study_type", "label": "Study category", "kind": "select", "options": STUDY_TYPES, "default": STUDY_TYPES[0]},
        {"name": "subject", "label": "Subject or exam", "kind": "text"},
        {"name": "topic", "label": "Topic", "kind": "text"},
        {"name": "duration_minutes", "label": "Duration (minutes)", "kind": "number", "min": 1, "max": 1440, "default": 60, "step": 5},
        {"name": "notes", "label": "Notes (optional)", "kind": "textarea"},
    ]
    data = show_records_editor("study_sessions", fields, "session_date DESC", ("session_date", "subject", "topic"))
    if not week.empty:
        chart = week.groupby("session_date", as_index=False)["duration_minutes"].sum()
        chart["date"] = pd.to_datetime(chart["session_date"])
        chart["hours"] = chart["duration_minutes"] / 60
        fig = px.bar(chart, x="date", y="hours", title="Study hours this week", labels={"date": "Date", "hours": "Hours"}, color_discrete_sequence=["#5bc5a4"])
        show_chart(fig, "study_week_chart")


def render_skills() -> None:
    page_heading("Skills", "Capture what you learn, how long you practise, and finished topics.")
    data = db.read_table("skill_sessions", order_by="learning_date DESC")
    minutes = int(data["time_spent_minutes"].sum()) if not data.empty else 0
    completed_topics = int((data["progress_status"] == "Completed").sum()) if not data.empty else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Learning time", format_hours(minutes))
    col_b.metric("Topics completed", completed_topics)
    col_c.metric("Skills tracked", int(data["skill_name"].nunique()) if not data.empty else 0)
    fields = [
        {"name": "learning_date", "label": "Learning date", "kind": "date", "default": date.today()},
        {"name": "skill_name", "label": "Skill name", "kind": "text", "default": "Python"},
        {"name": "topic", "label": "Topic learned", "kind": "text"},
        {"name": "time_spent_minutes", "label": "Time spent (minutes)", "kind": "number", "min": 1, "max": 1440, "default": 45, "step": 5},
        {"name": "progress_status", "label": "Progress status", "kind": "select", "options": ["In progress", "Completed"], "default": "In progress"},
        {"name": "notes", "label": "Notes (optional)", "kind": "textarea"},
    ]
    data = show_records_editor("skill_sessions", fields, "learning_date DESC", ("learning_date", "skill_name", "topic"))
    if not data.empty:
        summary = data.groupby("skill_name", as_index=False)["time_spent_minutes"].sum()
        fig = px.bar(summary, x="skill_name", y="time_spent_minutes", title="Time invested by skill", labels={"skill_name": "Skill", "time_spent_minutes": "Minutes"}, color_discrete_sequence=["#e7a55c"])
        show_chart(fig, "skills_chart")
    st.caption("Suggested names: Python, C Programming, Data Structures and Algorithms, AI and Machine Learning, Web Development, or any skill you choose.")


def render_sleep() -> None:
    page_heading("Sleep tracker", "Log bedtime and wake-up time; overnight sleep is calculated automatically.")
    data = db.read_table("sleep_records", order_by="record_date DESC")
    today = date.today()
    recent = _date_range(data, "record_date", today - timedelta(days=6), today)
    total = int(recent["duration_minutes"].sum()) if not recent.empty else 0
    average = total // len(recent) if len(recent) else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Last 7 days", format_hours(total))
    col_b.metric("Average per night", format_hours(average))
    col_c.metric("Records", len(data))
    from modules.common import show_records_editor
    data = show_records_editor(
        "sleep_records",
        [
            {"name": "record_date", "label": "Wake-up date", "kind": "date", "default": today},
            {"name": "bedtime", "label": "Bedtime", "kind": "time", "default": time(22, 0)},
            {"name": "wake_time", "label": "Wake-up time", "kind": "time", "default": time(6, 0)},
            {"name": "notes", "label": "Sleep notes (optional)", "kind": "textarea"},
        ],
        "record_date DESC",
        ("record_date", "bedtime", "wake_time"),
        normalize_values=_add_sleep_duration,
    )
    if not recent.empty:
        chart = recent.copy()
        chart["date"] = pd.to_datetime(chart["record_date"])
        chart["hours"] = chart["duration_minutes"] / 60
        fig = px.line(chart, x="date", y="hours", markers=True, title="Sleep duration over the past week", labels={"date": "Wake-up date", "hours": "Hours"}, color_discrete_sequence=["#7e9df5"])
        fig.add_hline(y=8, line_dash="dot", line_color="#b6e75c", annotation_text="8-hour reference")
        show_chart(fig, "sleep_week_chart")


def _add_sleep_duration(values: dict) -> dict:
    values["duration_minutes"] = db.calculate_sleep_minutes(values["bedtime"], values["wake_time"])
    values["record_date"] = values["record_date"].isoformat() if isinstance(values["record_date"], date) else values["record_date"]
    return values


def render_screen_time() -> None:
    page_heading("Screen time", "Manually record app usage and see learning time separately from entertainment.")
    target = int(db.get_setting("screen_time_target", "180") or 180)
    with st.form("screen_target_form"):
        new_target = st.number_input("Daily screen-time target (minutes)", min_value=15, max_value=1440, step=15, value=target)
        save_target = st.form_submit_button("Save target")
    if save_target:
        db.set_setting("screen_time_target", str(int(new_target)))
        st.success("Daily target saved.")
        st.rerun()

    data = db.read_table("screen_time", order_by="record_date DESC")
    today = date.today()
    day = data.loc[data["record_date"] == today.isoformat()] if not data.empty else pd.DataFrame()
    total = int(day["minutes"].sum()) if not day.empty else 0
    productive = int(day.loc[day["productive"] == 1, "minutes"].sum()) if not day.empty else 0
    entertainment = total - productive
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Today", format_hours(total), f"{total - target:+d} min vs target" if total else f"Target {target} min")
    col_b.metric("Productive", format_hours(productive))
    col_c.metric("Entertainment / other", format_hours(entertainment))
    st.progress(min(total / target, 1.0), text=f"{total} of {target} minutes · {max(target - total, 0)} minutes remaining" if total <= target else f"Target exceeded by {total - target} minutes")

    rows = data.to_dict("records")
    by_id = {int(row["id"]): row for row in rows}
    selected_id = st.selectbox(
        "Choose a saved app entry to edit, or add a new one",
        options=[0, *by_id],
        format_func=lambda value: "+ Add app usage" if value == 0 else f"{by_id[int(value)]['record_date']} · {by_id[int(value)]['app_name']}",
        key="screen_time_selector",
    )
    current = by_id.get(int(selected_id), {})
    with st.form(f"screen_time_form_{selected_id}"):
        first, second = st.columns(2)
        with first:
            record_date = st.date_input("Usage date", value=date.fromisoformat(current["record_date"]) if current else today, key=f"screen_date_{selected_id}")
            app_name = st.selectbox("Application", APPS, index=APPS.index(current["app_name"]) if current and current["app_name"] in APPS else 0, key=f"screen_app_{selected_id}")
        with second:
            minutes = st.number_input("Usage (minutes)", min_value=0, max_value=1440, step=5, value=int(current.get("minutes", 30)), key=f"screen_minutes_{selected_id}")
            productive_flag = st.checkbox("Count as productive screen time", value=bool(current.get("productive", 0)), key=f"screen_productive_{selected_id}")
        saved = st.form_submit_button("Update app usage" if current else "Save app usage", type="primary")
    if saved:
        try:
            if not app_name.strip():
                st.error("Choose an application before saving.")
            elif selected_id:
                db.update_record("screen_time", int(selected_id), {"record_date": record_date.isoformat(), "app_name": app_name, "minutes": int(minutes), "productive": int(productive_flag)})
                st.success("App usage updated.")
                st.rerun()
            else:
                db.upsert_screen_time(record_date, app_name, int(minutes), productive_flag)
                st.success("App usage saved. An existing app entry for that date is updated instead of duplicated.")
                st.rerun()
        except Exception as error:
            st.error(f"Could not save screen time: {error}")

    if not data.empty:
        from modules.common import _delete_form
        _delete_form("screen_time", data, ("record_date", "app_name"))
        st.subheader("Usage history")
        display = data.copy()
        display["usage_type"] = display["productive"].map({1: "Productive", 0: "Entertainment / other"})
        st.dataframe(display.drop(columns=["id", "productive"], errors="ignore"), hide_index=True, use_container_width=True)
        week = _date_range(data, "record_date", today - timedelta(days=6), today)
        if not week.empty:
            chart = week.groupby(["record_date", "productive"], as_index=False)["minutes"].sum()
            chart["date"] = pd.to_datetime(chart["record_date"])
            chart["category"] = chart["productive"].map({1: "Productive", 0: "Entertainment / other"})
            fig = px.bar(chart, x="date", y="minutes", color="category", title="Screen time this week", labels={"date": "Date", "minutes": "Minutes", "category": "Usage type"}, color_discrete_map={"Productive": "#5bc5a4", "Entertainment / other": "#e78572"})
            show_chart(fig, "screen_time_week_chart")
    else:
        st.info("No screen-time entries yet. Add app usage above; entries are manual, not collected from Android.")


def _date_range(data: pd.DataFrame, column: str, start: date, end: date) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    dates = pd.to_datetime(data[column], errors="coerce").dt.date
    return data.loc[(dates >= start) & (dates <= end)].copy()
