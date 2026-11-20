"""Interactive productivity reports and per-table CSV export."""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from modules.common import page_heading, show_chart

EXPORT_TABLES = {
    "Daily routine": "activities",
    "Routine check-ins": "activity_logs",
    "Workouts": "workouts",
    "Meditation": "meditation",
    "Study sessions": "study_sessions",
    "Skill sessions": "skill_sessions",
    "Sleep records": "sleep_records",
    "Screen-time entries": "screen_time",
    "Habits": "habits",
    "Habit check-ins": "habit_logs",
    "Goals": "goals",
    "Journal": "journal",
}


def render() -> None:
    page_heading("Analytics & export", "Explore patterns in your routine and download your records as CSV.")
    today = date.today()
    start = today - timedelta(days=29)
    study = _between(db.read_table("study_sessions", order_by="session_date ASC"), "session_date", start, today)
    screen = _between(db.read_table("screen_time", order_by="record_date ASC"), "record_date", start, today)
    sleep = _between(db.read_table("sleep_records", order_by="record_date ASC"), "record_date", start, today)
    workouts = _between(db.read_table("workouts", order_by="workout_date ASC"), "workout_date", start, today)
    meditation = _between(db.read_table("meditation", order_by="meditation_date ASC"), "meditation_date", start, today)
    skills = _between(db.read_table("skill_sessions", order_by="learning_date ASC"), "learning_date", start, today)
    habit_logs = _between(db.read_table("habit_logs", order_by="log_date ASC"), "log_date", start, today)
    habits = db.read_table("habits", order_by="name ASC", active_only=True)
    routine = db.read_table("activities", order_by="start_time ASC", active_only=True)
    routine_logs = _between(db.read_table("activity_logs", order_by="log_date ASC"), "log_date", start, today)

    metric_columns = st.columns(4)
    metric_columns[0].metric("Study hours · 30 days", f"{study['duration_minutes'].sum() / 60:.1f}" if not study.empty else "0.0")
    metric_columns[1].metric("Workouts · 30 days", len(workouts))
    metric_columns[2].metric("Screen time · 30 days", f"{screen['minutes'].sum() / 60:.1f} h" if not screen.empty else "0.0 h")
    metric_columns[3].metric("Average sleep", f"{sleep['duration_minutes'].mean() / 60:.1f} h" if not sleep.empty else "—")

    top_left, top_right = st.columns(2)
    with top_left:
        daily = _daily_productivity(today, routine, routine_logs, habits, habit_logs)
        fig = px.line(daily, x="date", y="completion", markers=True, title="Daily productivity · 30 days", labels={"date": "Date", "completion": "Completion (%)"}, color_discrete_sequence=["#b6e75c"])
        fig.update_yaxes(range=[0, 100])
        show_chart(fig, "analytics_productivity")
    with top_right:
        weekly_study = _study_by_day(study, today - timedelta(days=6), today)
        fig = px.bar(weekly_study, x="date", y="hours", title="Study hours · this week", labels={"date": "Date", "hours": "Hours"}, color_discrete_sequence=["#5bc5a4"])
        show_chart(fig, "analytics_study_week")

    middle_left, middle_right = st.columns(2)
    with middle_left:
        monthly_study = _study_by_month(study, today)
        fig = px.bar(monthly_study, x="month", y="hours", title="Study hours · last 6 months", labels={"month": "Month", "hours": "Hours"}, color_discrete_sequence=["#7e9df5"])
        show_chart(fig, "analytics_study_month")
    with middle_right:
        if screen.empty:
            st.info("Add screen-time entries to see your usage trend.")
        else:
            screen_summary = screen.groupby(["record_date", "productive"], as_index=False)["minutes"].sum()
            screen_summary["date"] = pd.to_datetime(screen_summary["record_date"])
            screen_summary["Usage"] = screen_summary["productive"].map({1: "Productive", 0: "Entertainment / other"})
            fig = px.bar(screen_summary, x="date", y="minutes", color="Usage", title="Screen time · 30 days", labels={"date": "Date", "minutes": "Minutes"}, color_discrete_map={"Productive": "#5bc5a4", "Entertainment / other": "#e78572"})
            show_chart(fig, "analytics_screen_time")

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        if sleep.empty:
            st.info("Add sleep records to see your sleep trend.")
        else:
            sleep_plot = sleep.copy()
            sleep_plot["date"] = pd.to_datetime(sleep_plot["record_date"])
            sleep_plot["hours"] = sleep_plot["duration_minutes"] / 60
            fig = px.line(sleep_plot, x="date", y="hours", markers=True, title="Sleep · 30 days", labels={"date": "Wake-up date", "hours": "Hours"}, color_discrete_sequence=["#9b8af7"])
            fig.add_hline(y=8, line_dash="dot", line_color="#b6e75c", annotation_text="8-hour reference")
            show_chart(fig, "analytics_sleep")
    with bottom_right:
        exercise_week = _weekly_counts(workouts, "workout_date", today, "Workouts")
        meditation_week = _weekly_counts(meditation, "meditation_date", today, "Meditation days", completed_only=True)
        consistency = exercise_week.merge(meditation_week, on="week", how="outer").fillna(0)
        fig = px.bar(consistency, x="week", y=["Workouts", "Meditation days"], barmode="group", title="Exercise and meditation consistency", labels={"week": "Week", "value": "Sessions", "variable": "Activity"}, color_discrete_sequence=["#e7a55c", "#9b8af7"])
        show_chart(fig, "analytics_consistency")

    habit_left, skill_right = st.columns(2)
    with habit_left:
        if habits.empty:
            st.info("Add habits to see daily completion analytics.")
        else:
            habit_summary = _habit_completion(today, habits, habit_logs)
            fig = px.line(habit_summary, x="date", y="completion", markers=True, title="Habit completion · 30 days", labels={"date": "Date", "completion": "Completion (%)"}, color_discrete_sequence=["#e7a55c"])
            fig.update_yaxes(range=[0, 100])
            show_chart(fig, "analytics_habits")
    with skill_right:
        if skills.empty:
            st.info("Add skill sessions to see your learning distribution.")
        else:
            skill_summary = skills.groupby("skill_name", as_index=False)["time_spent_minutes"].sum()
            fig = px.bar(skill_summary, x="skill_name", y="time_spent_minutes", title="Skill development · 30 days", labels={"skill_name": "Skill", "time_spent_minutes": "Minutes"}, color_discrete_sequence=["#e7a55c"])
            show_chart(fig, "analytics_skills")

    st.divider()
    st.subheader("Export records")
    selected = st.selectbox("Choose a dataset", list(EXPORT_TABLES))
    export_data = db.read_table(EXPORT_TABLES[selected], order_by="id ASC")
    if export_data.empty:
        st.info(f"There are no {selected.lower()} records to export yet.")
    else:
        st.download_button(
            f"Download {selected} CSV",
            data=export_data.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"lifetrack_{EXPORT_TABLES[selected]}.csv",
            mime="text/csv",
            key=f"export_{EXPORT_TABLES[selected]}",
            type="primary",
        )


def _between(data: pd.DataFrame, column: str, start: date, end: date) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    dates = pd.to_datetime(data[column], errors="coerce").dt.date
    return data.loc[(dates >= start) & (dates <= end)].copy()


def _daily_productivity(today: date, routine: pd.DataFrame, routine_logs: pd.DataFrame, habits: pd.DataFrame, habit_logs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for offset in reversed(range(30)):
        day = today - timedelta(days=offset)
        total = len(routine) + len(habits)
        done_routine = 0
        done_habits = 0
        if not routine_logs.empty:
            logs = routine_logs.loc[(routine_logs["log_date"] == day.isoformat()) & (routine_logs["completed"] == 1)]
            done_routine = logs["activity_id"].nunique()
        if not habit_logs.empty:
            logs = habit_logs.loc[(habit_logs["log_date"] == day.isoformat()) & (habit_logs["completed"] == 1)]
            done_habits = logs["habit_id"].nunique()
        rows.append({"date": day, "completion": (done_routine + done_habits) * 100 / total if total else 0})
    return pd.DataFrame(rows)


def _study_by_day(study: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    days = pd.DataFrame({"date": [start + timedelta(days=offset) for offset in range((end - start).days + 1)]})
    if study.empty:
        days["hours"] = 0.0
        return days
    summary = study.groupby("session_date", as_index=False)["duration_minutes"].sum()
    summary["date"] = pd.to_datetime(summary["session_date"]).dt.date
    summary["hours"] = summary["duration_minutes"] / 60
    return days.merge(summary[["date", "hours"]], on="date", how="left").fillna({"hours": 0})


def _study_by_month(study: pd.DataFrame, today: date) -> pd.DataFrame:
    start = (today.replace(day=1) - pd.DateOffset(months=5)).date()
    months = pd.date_range(start=start, periods=6, freq="MS")
    result = pd.DataFrame({"month_key": months})
    result["month"] = result["month_key"].dt.strftime("%b %Y")
    if study.empty:
        result["hours"] = 0.0
        return result
    summary = study.copy()
    summary["month_key"] = pd.to_datetime(summary["session_date"]).dt.to_period("M").dt.to_timestamp()
    summary = summary.groupby("month_key", as_index=False)["duration_minutes"].sum()
    summary["hours"] = summary["duration_minutes"] / 60
    return result.merge(summary[["month_key", "hours"]], on="month_key", how="left").fillna({"hours": 0})


def _weekly_counts(data: pd.DataFrame, date_column: str, today: date, label: str, completed_only: bool = False) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame({"week": ["This week"], label: [0]})
    rows = data.copy()
    if completed_only and "completed" in rows:
        rows = rows.loc[rows["completed"] == 1]
    dates = pd.to_datetime(rows[date_column])
    rows["week"] = (dates - pd.to_timedelta(dates.dt.weekday, unit="D")).dt.strftime("%b %d")
    rows = rows.loc[pd.to_datetime(rows[date_column]).dt.date >= today - timedelta(days=29)]
    return rows.groupby("week", as_index=False).size().rename(columns={"size": label})


def _habit_completion(today: date, habits: pd.DataFrame, logs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for offset in reversed(range(30)):
        day = today - timedelta(days=offset)
        checked = 0
        if not logs.empty:
            selected = logs.loc[(logs["log_date"] == day.isoformat()) & (logs["completed"] == 1)]
            checked = selected["habit_id"].nunique()
        rows.append({"date": day, "completion": checked * 100 / len(habits) if len(habits) else 0})
    return pd.DataFrame(rows)
