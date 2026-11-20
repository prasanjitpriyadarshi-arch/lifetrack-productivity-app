# LifeTrack — Personal Life & Productivity Manager

LifeTrack is a local, beginner-friendly productivity dashboard for managing a daily routine, study sessions, exercise, meditation, sleep, screen time, habits, goals, and a journal. It is built with Python, Streamlit, SQLite, Pandas, and Plotly. It does not use paid APIs or send your entries to an external service.

## Run LifeTrack

You need Python 3.10 or newer and an internet connection for the first package install.

### Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local address (usually `http://localhost:8501`). Open it in your browser. Stop the app with `Ctrl+C` in the terminal. The next time you run it, your records will still be there.

## First use

LifeTrack creates `lifetrack.db` beside `app.py` the first time it starts. It adds the sample daily routine and eight suggested habits only once. Edit or remove those defaults to match your day. Routine completion and habit completion are logged separately for each date. All other pages have forms for adding, editing, and deleting entries; deletions require an explicit confirmation.

Screen-time data is entered manually. Mark an entry as productive when it represents learning or another purposeful activity; LifeTrack does not automatically read phone usage. Sleep is assigned to the wake-up date, and if wake-up is earlier than bedtime the duration calculation rolls into the next day.

## Project structure

```text
app.py                 Streamlit navigation and application entry point
database.py            SQLite schema, initialization, and safe data helpers
modules/
  common.py             Shared theme, chart styling, and reusable record forms
  dashboard.py          Today's summary and seven-day productivity chart
  routine.py            Editable routine and date-specific completion
  trackers.py           Study, gym, meditation, skills, sleep, and screen time
  habits.py             Custom habits, streaks, and goals
  journal.py            Daily journal entries
  analytics.py          Interactive reports and CSV export
tests/
  test_database.py      Database CRUD, persistence, and overnight sleep tests
requirements.txt        Free Python dependencies
lifetrack.db            Created locally on first launch; do not commit personal data
```

### How the database works

SQLite stores the data in a single file, `lifetrack.db`. `database.py` creates the tables when the app starts. Each page reads or writes through the shared database helpers; SQLite commits successful changes and rolls back a failed transaction. Routine activities and habits are reusable definitions, while their daily completion checkboxes are stored with a date. The database file is local to this computer, so back it up if you want to keep your records when moving machines.

## Tests

With the virtual environment active, run:

```bash
python -m unittest discover -s tests -v
```

## GitHub submission

Create a GitHub repository, then from this project folder run:

```bash
git init
git add app.py database.py modules tests requirements.txt README.md .gitignore
git commit -m "Build LifeTrack productivity manager"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/LifeTrack.git
git push -u origin main
```

Do not add `.venv/`, `lifetrack.db`, or personal records to Git. For the GitHub website route, create an empty repository and upload the project files while excluding those local-only files.

## AIML Cohort Task 1 checklist

- [ ] Run the app and confirm the dashboard opens.
- [ ] Add and edit a routine activity, then mark it complete.
- [ ] Add at least one study, workout, meditation, skill, sleep, and screen-time entry.
- [ ] Complete a habit, create a goal, and save a journal entry.
- [ ] Restart the app and confirm entries are still present.
- [ ] Review the analytics and download a CSV.
- [ ] Run the unit tests and include this README in the GitHub submission.

## Scope notes

This is a single-user local app with manual record entry. It does not include Android automatic usage tracking, cloud sync, multi-user login, or automatic device notifications. Those need permissions or services outside this free, local-first project.
