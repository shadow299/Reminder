# Reminder — a Samsung Reminder-style desktop todo app

A lightweight, native-feeling desktop app for managing your to-dos, inspired by
Samsung's One UI *Reminder* app. Built with Python + Qt (PySide6).

## Features

- Clean, rounded card UI with light and dark themes
- Sidebar with system filters: **All**, **Today**, **Scheduled**, **Important**, **Completed**
- Custom **lists** (categories) with colored labels — create, rename, delete
- Quick-add bar (Enter to save) + full editor for details
- **Due date & time** with a natural-language label (`Today · 15:30`, `Tomorrow`, etc.)
- **Repeat**: daily, weekly, monthly, yearly (auto-advances when completed)
- **Important** star flag
- Fast **search** across titles and notes
- **Overdue** highlighting in red
- **System tray** icon with quick actions; window minimizes to tray on close
- **Desktop notifications** when reminders are due (polled every 30 s)
- Local **JSON persistence** in `~/.local/share/reminder-app/reminders.json`
- Keyboard shortcuts: `Ctrl+N` new, `Ctrl+F` search, `Ctrl+D` toggle theme, `Ctrl+Q` quit

## Requirements

- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/)

Install dependencies (already done in this workspace):

```bash
python3 -m pip install --user PySide6
```

## Run

```bash
./run.sh
# or
python3 main.py
```

## Data location

Your reminders are stored as JSON at:

```
~/.local/share/reminder-app/reminders.json
```

Delete this file to reset the app.

## Project layout

```
reminder/
├── main.py                # entry point
├── run.sh                 # launcher script
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── models.py          # Reminder / Category dataclasses + JSON Store
    ├── theme.py           # Light + dark palettes and stylesheet
    ├── widgets.py         # ReminderCard, ReminderEditor, new-list dialog
    └── main_window.py     # Sidebar, list panel, tray, notifier
```

## Optional: launch from your app menu

Create `~/.local/share/applications/reminder.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Reminder
Comment=Manage your to-dos
Exec=/home/lemon/reminder/run.sh
Terminal=false
Categories=Utility;Office;
```

Then it will appear in your desktop's application launcher.
