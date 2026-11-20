"""LifeTrack entry point. Run with: streamlit run app.py"""

from __future__ import annotations

import streamlit as st

import database as db
from modules import analytics, dashboard, habits, journal, routine, trackers
from modules.common import apply_theme

st.set_page_config(
    page_title="LifeTrack · Personal Productivity",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    db.initialize_database()
except Exception as error:
    st.error(f"LifeTrack could not open its SQLite database: {error}")
    st.stop()

PAGES = {
    "Overview": dashboard.render,
    "Daily routine": routine.render,
    "Study": trackers.render_study,
    "Gym & fitness": trackers.render_gym,
    "Meditation": trackers.render_meditation,
    "Skills": trackers.render_skills,
    "Sleep": trackers.render_sleep,
    "Screen time": trackers.render_screen_time,
    "Habits": habits.render_habits,
    "Goals": habits.render_goals,
    "Daily journal": journal.render,
    "Analytics & export": analytics.render,
}

with st.sidebar:
    st.markdown('<div class="life-brand">LIFETRACK</div>', unsafe_allow_html=True)
    st.markdown('<div class="life-tagline">Make your days count.</div>', unsafe_allow_html=True)
    st.markdown("---")
    selected_page = st.radio(
        "Navigation",
        list(PAGES),
        label_visibility="collapsed",
    )
    st.markdown("---")
    saved_theme = db.get_setting("theme", "Dark")
    theme = st.selectbox("Appearance", ["Dark", "Light"], index=0 if saved_theme != "Light" else 1)
    if theme != saved_theme:
        db.set_setting("theme", theme)
    st.caption("Your data stays in a local SQLite file.")

st.session_state["lifetrack_theme"] = theme
apply_theme(theme)

try:
    PAGES[selected_page]()
except Exception as error:
    st.error(f"This section could not be loaded: {error}")
    st.caption("Your existing entries are still in the local database. Check the app log for details.")
