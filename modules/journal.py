"""One editable journal entry per date."""

from datetime import date

import pandas as pd
import streamlit as st

import database as db
from modules.common import page_heading

MOODS = ["Great", "Good", "Okay", "Low", "Stressed"]


def render() -> None:
    page_heading("Daily journal", "Capture wins, lessons, challenges, and a clear next step.")
    entry_date = st.date_input("Journal date", value=date.today(), key="journal_date")
    history = db.read_table("journal", order_by="entry_date DESC")
    matches = history.loc[history["entry_date"] == entry_date.isoformat()] if not history.empty else pd.DataFrame()
    current = matches.iloc[0].to_dict() if not matches.empty else {}

    with st.form(f"journal_form_{entry_date.isoformat()}"):
        achievements = st.text_area("Today's achievements", value=str(current.get("achievements", "")), height=100, key=f"journal_achievements_{entry_date}", placeholder="What went well today?")
        learned = st.text_area("What I learned", value=str(current.get("learned", "")), height=100, key=f"journal_learned_{entry_date}", placeholder="A concept, idea, or insight worth remembering")
        challenges = st.text_area("Challenges faced", value=str(current.get("challenges", "")), height=100, key=f"journal_challenges_{entry_date}", placeholder="What was difficult, and what can you try next?")
        mood_default = current.get("mood", "Okay")
        mood = st.selectbox("Mood", MOODS, index=MOODS.index(mood_default) if mood_default in MOODS else 2, key=f"journal_mood_{entry_date}")
        tomorrow = st.text_area("Tomorrow's priorities", value=str(current.get("tomorrow_priorities", "")), height=100, key=f"journal_tomorrow_{entry_date}", placeholder="Choose a small number of important tasks")
        saved = st.form_submit_button("Update journal" if current else "Save today's journal", type="primary")
    if saved:
        values = {
            "entry_date": entry_date.isoformat(),
            "achievements": achievements.strip(),
            "learned": learned.strip(),
            "challenges": challenges.strip(),
            "mood": mood,
            "tomorrow_priorities": tomorrow.strip(),
        }
        try:
            if current:
                db.update_record("journal", int(current["id"]), values)
                st.success("Journal entry updated.")
            else:
                db.insert_record("journal", values)
                st.success("Journal entry saved.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not save this journal entry: {error}")

    if current:
        with st.expander("Delete this journal entry"):
            with st.form(f"journal_delete_{entry_date.isoformat()}"):
                confirmed = st.checkbox("I understand this journal entry cannot be recovered", key=f"journal_delete_confirm_{entry_date}")
                deleted = st.form_submit_button("Delete entry")
            if deleted:
                if not confirmed:
                    st.warning("Confirm before deleting this entry.")
                else:
                    db.delete_record("journal", int(current["id"]))
                    st.success("Journal entry deleted.")
                    st.rerun()

    if not history.empty:
        st.subheader("Journal history")
        st.dataframe(history.drop(columns=["id"], errors="ignore"), hide_index=True, use_container_width=True)
