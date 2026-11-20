"""Today's metrics and a compact seven-day productivity trend."""

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from modules.common import format_hours, page_heading, show_chart


def render() -> None:
    now = datetime.now()
    greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
    today = date.today()
    page_heading(f"{greeting}", today.strftime("%A, %B %-d, %Y"))
    st.write("A clear view of your day, one small step at a time.")

    activities = db.read_table("activities", order_by="start_time ASC", active_only=True)
    activity_logs = db.read_table("activity_logs", order_by="log_date DESC")
    today_logs = activity_logs.loc[activity_logs["log_date"] == today.isoformat()] if not activity_logs.empty else pd.DataFrame()
    done_activity_ids = set(today_logs.loc[today_logs["completed"] == 1, "activity_id"].astype(int)) if not today_logs.empty else set()
    total_tasks = len(activities)
    completed_tasks = len(done_activity_ids.intersection(set(activities["id"].astype(int)))) if total_tasks else 0
    pending_tasks = max(total_tasks - completed_tasks, 0)

    habits = db.read_table("habits", order_by="name ASC", active_only=True)
    habit_logs = db.read_table("habit_logs", order_by="log_date DESC")
    today_habits = habit_logs.loc[habit_logs["log_date"] == today.isoformat()] if not habit_logs.empty else pd.DataFrame()
    completed_habits = int(today_habits.loc[today_habits["completed"] == 1, "habit_id"].nunique()) if not today_habits.empty else 0
    habit_total = len(habits)
    routine_ratio = completed_tasks / total_tasks if total_tasks else 0
    habit_ratio = completed_habits / habit_total if habit_total else 0
    progress_values = [ratio for ratio, total in [(routine_ratio, total_tasks), (habit_ratio, habit_total)] if total]
    daily_progress = sum(progress_values) / len(progress_values) if progress_values else 0

    study = _for_date(db.read_table("study_sessions", order_by="session_date DESC"), "session_date", today)
    skills = _for_date(db.read_table("skill_sessions", order_by="learning_date DESC"), "learning_date", today)
    workouts = _for_date(db.read_table("workouts", order_by="workout_date DESC"), "workout_date", today)
    meditation = _for_date(db.read_table("meditation", order_by="meditation_date DESC"), "meditation_date", today)
    sleep = _for_date(db.read_table("sleep_records", order_by="record_date DESC"), "record_date", today)
    screen = _for_date(db.read_table("screen_time", order_by="record_date DESC"), "record_date", today)

    study_minutes = int(study["duration_minutes"].sum()) if not study.empty else 0
    skill_minutes = int(skills["time_spent_minutes"].sum()) if not skills.empty else 0
    productive_screen = int(screen.loc[screen["productive"] == 1, "minutes"].sum()) if not screen.empty else 0
    productive_minutes = study_minutes + skill_minutes + productive_screen
    workout_minutes = int(workouts["duration_minutes"].sum()) if not workouts.empty else 0
    meditation_minutes = int(meditation.loc[meditation["completed"] == 1, "duration_minutes"].sum()) if not meditation.empty else 0
    sleep_minutes = int(sleep["duration_minutes"].iloc[0]) if not sleep.empty else 0
    screen_minutes = int(screen["minutes"].sum()) if not screen.empty else 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Daily progress", f"{daily_progress:.0%}", f"{completed_tasks} tasks · {completed_habits} habits")
    metric_cols[1].metric("Productive time", format_hours(productive_minutes), "Study + skills + productive apps")
    metric_cols[2].metric("Tasks remaining", pending_tasks, f"{completed_tasks} of {total_tasks} complete")
    metric_cols[3].metric("Screen time", format_hours(screen_minutes), f"{productive_screen} productive minutes")

    second_row = st.columns(4)
    second_row[0].metric("Study", format_hours(study_minutes))
    second_row[1].metric("Gym & exercise", format_hours(workout_minutes))
    second_row[2].metric("Meditation", format_hours(meditation_minutes))
    second_row[3].metric("Sleep", format_hours(sleep_minutes))

    st.progress(daily_progress, text=f"Daily momentum · {daily_progress:.0%}")
    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Weekly productivity")
        chart_data = _weekly_productivity(today, activities, activity_logs, habits, habit_logs)
        fig = px.bar(
            chart_data,
            x="date",
            y="productivity",
            title="Routine and habit completion",
            labels={"date": "Day", "productivity": "Completion (%)"},
            color_discrete_sequence=["#b6e75c"],
        )
        fig.update_yaxes(range=[0, 100])
        show_chart(fig, "dashboard_weekly_productivity")
    with right:
        st.subheader("Today at a glance")
        if activities.empty:
            st.info("Add routine activities to see your schedule here.")
        else:
            for _, activity in activities.head(7).iterrows():
                done = int(activity["id"]) in done_activity_ids
                status = "Done" if done else "Next up"
                st.write(f"**{activity['start_time']}** · {activity['title']}")
                st.caption(f"{activity['category']} · {status}")
        if total_tasks > 7:
            st.caption(f"And {total_tasks - 7} more activities in your routine.")

    st.caption("Productive time combines study, skill practice, and screen-time entries you marked as productive. Screen-time data is entered manually.")


def _for_date(data: pd.DataFrame, column: str, target: date) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    return data.loc[data[column].astype(str) == target.isoformat()].copy()


def _weekly_productivity(today: date, activities: pd.DataFrame, activity_logs: pd.DataFrame, habits: pd.DataFrame, habit_logs: pd.DataFrame) -> pd.DataFrame:
    dates = [today - timedelta(days=offset) for offset in reversed(range(7))]
    routine_count = len(activities)
    habit_count = len(habits)
    rows = []
    for day in dates:
        done_routine = 0
        done_habits = 0
        if not activity_logs.empty:
            day_rows = activity_logs.loc[(activity_logs["log_date"] == day.isoformat()) & (activity_logs["completed"] == 1)]
            done_routine = day_rows["activity_id"].nunique()
        if not habit_logs.empty:
            day_rows = habit_logs.loc[(habit_logs["log_date"] == day.isoformat()) & (habit_logs["completed"] == 1)]
            done_habits = day_rows["habit_id"].nunique()
        totals = routine_count + habit_count
        productivity = ((done_routine + done_habits) / totals * 100) if totals else 0
        rows.append({"date": day, "productivity": productivity})
    return pd.DataFrame(rows)
