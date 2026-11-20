"""Shared page styling, charts, and reusable SQLite record forms."""

from __future__ import annotations

from datetime import date, time
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db


def apply_theme(theme: str) -> None:
    dark = theme == "Dark"
    page = "#0b1110" if dark else "#f5f7f3"
    panel = "#121a18" if dark else "#ffffff"
    text = "#edf2ec" if dark else "#18231e"
    muted = "#98a59e" if dark else "#67756d"
    border = "#26332e" if dark else "#e0e7e1"
    sidebar = "#0e1513" if dark else "#edf2ed"
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: {'dark' if dark else 'light'}; }}
        html, body, [data-testid="stAppViewContainer"] {{ background: {page}; color: {text}; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{ background: {sidebar}; border-right: 1px solid {border}; }}
        [data-testid="stSidebar"] > div {{ padding-top: 1.4rem; }}
        .block-container {{ max-width: 1360px; padding-top: 2rem; padding-bottom: 3rem; }}
        h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] {{ color: {text}; }}
        h1 {{ letter-spacing: -0.04em; font-size: clamp(2rem, 4vw, 3rem); }}
        [data-testid="stMetric"] {{ background: {panel}; border: 1px solid {border}; border-radius: 14px; padding: 1rem 1.15rem; }}
        [data-testid="stMetricLabel"] {{ color: {muted}; }}
        [data-testid="stMetricValue"] {{ color: {text}; }}
        [data-testid="stMetricDeltaContainer"] {{ background: transparent !important; padding: 0 !important; }}
        [data-testid="stMetricDelta"] {{ background: transparent !important; color: #98c957 !important; font-weight: 600; }}
        [data-testid="stMetricDelta"] * {{ color: inherit !important; }}
        [role="progressbar"] {{ background: transparent !important; border-radius: 999px; }}
        [data-testid="stProgressBarTrack"] {{ background: {border} !important; border-radius: 999px; }}
        [data-testid="stProgressBarTrack"] > div {{ background: #b6e75c !important; border-radius: 999px; }}
        [data-testid="stSelectbox"] [role="group"] {{ background: {panel} !important; border: 1px solid {border} !important; border-radius: 9px; }}
        [data-testid="stSelectbox"] [role="combobox"] {{ background: transparent !important; color: {text} !important; }}
        [data-testid="stSelectbox"] button[aria-label="Open"] {{ background: transparent !important; color: {text} !important; }}
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input,
        input, textarea {{ background: {panel} !important; color: {text} !important; border-color: {border} !important; }}
        [data-testid="stForm"] {{ background: {panel}; border: 1px solid {border}; border-radius: 14px; padding: 1rem; }}
        [data-testid="stDataFrame"] {{ border: 1px solid {border}; border-radius: 12px; overflow: hidden; }}
        div.stButton > button, div.stFormSubmitButton > button {{ border-radius: 9px; min-height: 2.6rem; }}
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {{ background: #b6e75c; color: #13200d; border: 0; font-weight: 650; }}
        [data-testid="stExpander"] {{ border-color: {border}; border-radius: 12px; }}
        .life-brand {{ font-size: 1.25rem; font-weight: 750; letter-spacing: .08em; margin: .35rem 0 .2rem; color: {text}; }}
        .life-tagline {{ color: {muted}; font-size: .82rem; margin-bottom: 1.2rem; }}
        .life-eyebrow {{ color: #82a942; font-size: .75rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; margin-bottom: .25rem; }}
        .life-note {{ color: {muted}; font-size: .9rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_heading(title: str, subtitle: str) -> None:
    st.markdown('<div class="life-eyebrow">LIFETRACK / DAILY SYSTEM</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def style_chart(fig: go.Figure) -> go.Figure:
    dark = st.session_state.get("lifetrack_theme", "Dark") == "Dark"
    text = "#dfe7e0" if dark else "#34433a"
    grid = "#26332e" if dark else "#e1e8e2"
    background = "#121a18" if dark else "#ffffff"
    fig.update_layout(
        paper_bgcolor=background,
        plot_bgcolor=background,
        font={"color": text, "family": "Arial, sans-serif", "size": 12},
        title_font={"color": text, "size": 15},
        margin={"l": 12, "r": 12, "t": 36, "b": 12},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        hoverlabel={"bgcolor": background, "font_color": text},
    )
    fig.update_xaxes(showgrid=False, linecolor=grid, tickfont={"color": text})
    fig.update_yaxes(showgrid=True, gridcolor=grid, zerolinecolor=grid, tickfont={"color": text}, rangemode="tozero")
    return fig


def show_chart(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(style_chart(fig), use_container_width=True, key=key, config={"displayModeBar": False})


def show_records_editor(
    table: str,
    fields: list[dict[str, Any]],
    order_by: str,
    label_fields: tuple[str, ...],
    empty_message: str = "No records yet. Add your first entry above.",
    normalize_values: Any | None = None,
) -> pd.DataFrame:
    """Render add/edit/delete forms for a simple table and show its history."""
    data = db.read_table(table, order_by=order_by)
    rows = data.to_dict("records")
    row_by_id = {int(row["id"]): row for row in rows}
    st.subheader("Add or edit records")
    selected_id = st.selectbox(
        "Select an entry to edit, or start a new one",
        options=[0, *row_by_id.keys()],
        format_func=lambda value: "＋ New record" if value == 0 else _record_label(row_by_id[int(value)], label_fields),
        key=f"{table}_edit_selector",
    )
    current = row_by_id.get(int(selected_id), {})
    editor_key = f"{table}_{selected_id}"
    is_edit = bool(current)

    with st.form(f"{editor_key}_form"):
        columns = st.columns(2)
        values: dict[str, Any] = {}
        for index, field in enumerate(fields):
            if field["kind"] == "textarea":
                values[field["name"]] = _field_widget(field, current, editor_key)
            else:
                with columns[index % 2]:
                    values[field["name"]] = _field_widget(field, current, editor_key)
        submitted = st.form_submit_button("Save changes" if is_edit else "Add record", type="primary")
    if submitted:
        missing = [
            field["label"]
            for field in fields
            if field["kind"] == "text" and field.get("required", True)
            and not str(values.get(field["name"], "")).strip()
        ]
        if missing:
            st.error("Complete the required field(s): " + ", ".join(missing))
        else:
            try:
                if normalize_values:
                    values = normalize_values(values)
                if is_edit:
                    db.update_record(table, int(selected_id), values)
                    st.success("Record updated.")
                else:
                    db.insert_record(table, values)
                    st.success("Record saved.")
                st.rerun()
            except (ValueError, TypeError) as error:
                st.error(str(error))
            except Exception as error:
                st.error(f"Could not save this record: {error}")

    data = db.read_table(table, order_by=order_by)
    if data.empty:
        st.info(empty_message)
        return data
    _delete_form(table, data, label_fields)
    st.subheader("History")
    st.dataframe(data.drop(columns=["id"], errors="ignore"), hide_index=True, use_container_width=True)
    return data


def _field_widget(field: dict[str, Any], current: dict[str, Any], key_prefix: str) -> Any:
    name = field["name"]
    kind = field["kind"]
    raw = current.get(name, field.get("default"))
    key = f"{key_prefix}_{name}"
    if kind == "date":
        value = date.fromisoformat(str(raw)) if raw else field.get("default", date.today())
        return st.date_input(field["label"], value=value, key=key).isoformat()
    if kind == "time":
        value = time.fromisoformat(str(raw)) if raw else field.get("default", time(9, 0))
        return st.time_input(field["label"], value=value, key=key).strftime("%H:%M")
    if kind == "number":
        default = int(raw if raw is not None else field.get("default", 1))
        return st.number_input(
            field["label"], min_value=field.get("min", 1), max_value=field.get("max", 1440),
            step=field.get("step", 5), value=default, key=key,
        )
    if kind == "select":
        options = field["options"]
        selected = raw if raw in options else field.get("default", options[0])
        return st.selectbox(field["label"], options, index=options.index(selected), key=key)
    if kind == "checkbox":
        return st.checkbox(field["label"], value=bool(raw), key=key)
    if kind == "textarea":
        return st.text_area(field["label"], value=str(raw or ""), height=90, key=key)
    return st.text_input(field["label"], value=str(raw or ""), key=key, max_chars=field.get("max_chars"))


def _record_label(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    parts = [str(row.get(field, "")) for field in fields]
    return f"#{row['id']} · " + " — ".join(part for part in parts if part)


def _delete_form(table: str, data: pd.DataFrame, label_fields: tuple[str, ...]) -> None:
    rows = data.to_dict("records")
    row_by_id = {int(row["id"]): row for row in rows}
    with st.expander("Delete an entry", expanded=False):
        with st.form(f"{table}_delete_form"):
            selected = st.selectbox(
                "Choose the entry",
                options=list(row_by_id),
                format_func=lambda value: _record_label(row_by_id[int(value)], label_fields),
                key=f"{table}_delete_selector",
            )
            confirmed = st.checkbox("I understand this cannot be undone", key=f"{table}_delete_confirm")
            deleted = st.form_submit_button("Delete selected entry")
        if deleted:
            if not confirmed:
                st.warning("Confirm the deletion first.")
            else:
                try:
                    db.delete_record(table, int(selected))
                    st.success("Entry deleted.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not delete this entry: {error}")


def format_hours(minutes: int | float) -> str:
    hours, remainder = divmod(int(minutes), 60)
    return f"{hours}h {remainder:02d}m" if hours else f"{remainder}m"


def date_filter(data: pd.DataFrame, column: str, start: date, end: date) -> pd.DataFrame:
    if data.empty or column not in data:
        return data.copy()
    values = pd.to_datetime(data[column], errors="coerce").dt.date
    return data.loc[(values >= start) & (values <= end)].copy()
