"""Editable daily routine and per-date completion log."""

from datetime import date, time

import pandas as pd
import streamlit as st

import database as db
from modules.common import page_heading

CATEGORIES = ["College", "Study", "Gym", "Meditation", "Sleep", "Skills", "Personal", "Other"]


def render() -> None:
    page_heading("Daily routine", "Shape a repeatable day, then log what you complete.")
    focus_date = st.date_input("Routine date", value=date.today(), key="routine_focus_date")
    activities = db.read_table("activities", order_by="start_time ASC", active_only=True)
    logs = db.read_table("activity_logs", order_by="log_date DESC")
    day_logs = logs.loc[logs["log_date"] == focus_date.isoformat()] if not logs.empty else pd.DataFrame()
    completed_ids = set(day_logs.loc[day_logs["completed"] == 1, "activity_id"].astype(int)) if not day_logs.empty else set()

    total = len(activities)
    completed_count = len(completed_ids.intersection(set(activities["id"].astype(int)))) if total else 0
    progress = completed_count / total if total else 0
    metric_columns = st.columns(3)
    metric_columns[0].metric("Activities", total)
    metric_columns[1].metric("Completed", completed_count)
    metric_columns[2].metric("Daily progress", f"{progress:.0%}")
    st.progress(progress, text=f"{completed_count} of {total} activities complete")

    st.subheader("Your schedule")
    if activities.empty:
        st.info("No routine activities yet. Add your first activity below.")
    else:
        for _, activity in activities.iterrows():
            activity_id = int(activity["id"])
            widget_key = f"activity_done_{focus_date.isoformat()}_{activity_id}"
            columns = st.columns([0.08, 0.24, 0.18, 0.5])
            columns[0].checkbox(
                "Completed",
                value=activity_id in completed_ids,
                key=widget_key,
                label_visibility="collapsed",
                on_change=_save_activity_completion,
                args=(widget_key, activity_id, focus_date),
            )
            columns[1].write(str(activity["title"]))
            columns[2].caption(str(activity["category"]))
            columns[3].caption(f"{activity['start_time']} – {activity['end_time']}")

    pending = activities.loc[~activities["id"].astype(int).isin(completed_ids)] if not activities.empty else activities
    st.caption(f"Pending: {', '.join(pending['title'].astype(str).tolist()) if not pending.empty else 'Nothing — all done.'}")

    st.divider()
    st.subheader("Edit your routine")
    _activity_editor(activities)


def _save_activity_completion(widget_key: str, activity_id: int, log_date: date) -> None:
    db.upsert_daily_log("activity_logs", "activity_id", activity_id, log_date, bool(st.session_state[widget_key]))


def _activity_editor(activities: pd.DataFrame) -> None:
    rows = activities.to_dict("records")
    by_id = {int(row["id"]): row for row in rows}
    selected_id = st.selectbox(
        "Select an activity to edit, or add a new one",
        options=[0, *by_id],
        format_func=lambda value: "+ Add activity" if value == 0 else f"{by_id[int(value)]['title']} · {by_id[int(value)]['start_time']}",
        key="routine_activity_picker",
    )
    selected = by_id.get(int(selected_id), {})
    with st.form(f"routine_activity_form_{selected_id}"):
        first, second = st.columns(2)
        with first:
            title = st.text_input("Activity name", value=str(selected.get("title", "")), key=f"routine_title_{selected_id}", max_chars=100)
            category_default = selected.get("category", "Study")
            category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(category_default) if category_default in CATEGORIES else len(CATEGORIES) - 1, key=f"routine_category_{selected_id}")
            start_default = time.fromisoformat(selected["start_time"]) if selected.get("start_time") else time(9, 0)
            start_time = st.time_input("Start time", value=start_default, key=f"routine_start_{selected_id}").strftime("%H:%M")
        with second:
            end_default = time.fromisoformat(selected["end_time"]) if selected.get("end_time") else time(10, 0)
            end_time = st.time_input("End time", value=end_default, key=f"routine_end_{selected_id}").strftime("%H:%M")
            notes = st.text_area("Notes (optional)", value=str(selected.get("notes", "")), key=f"routine_notes_{selected_id}", height=90)
        saved = st.form_submit_button("Save changes" if selected else "Add activity", type="primary")
    if saved:
        if not title.strip():
            st.error("Enter an activity name before saving.")
        elif start_time == end_time:
            st.error("Start and end times must be different.")
        else:
            values = {"title": title.strip(), "category": category, "start_time": start_time, "end_time": end_time, "notes": notes.strip(), "active": 1}
            try:
                if selected:
                    db.update_record("activities", int(selected_id), values)
                    st.success("Activity updated.")
                else:
                    db.insert_record("activities", values)
                    st.success("Activity added.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save this activity: {error}")

    if by_id:
        with st.expander("Remove a routine activity"):
            with st.form("routine_activity_delete"):
                delete_id = st.selectbox("Activity to remove", list(by_id), format_func=lambda value: by_id[int(value)]["title"], key="routine_delete_choice")
                confirmed = st.checkbox("I understand its completion history will also be removed", key="routine_delete_confirm")
                submitted = st.form_submit_button("Remove activity")
            if submitted:
                if not confirmed:
                    st.warning("Confirm before removing this activity.")
                else:
                    try:
                        db.delete_record("activities", int(delete_id))
                        st.success("Activity removed.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not remove the activity: {error}")
