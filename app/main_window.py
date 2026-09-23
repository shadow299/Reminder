"""Main window: sidebar, list panel, quick add, tray icon, notifications."""
from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME
from .models import Category, Reminder, Store
from .theme import DARK, LIGHT, stylesheet
from .widgets import ReminderCard, ReminderEditor, ask_new_category


# ---------------------------------------------------------------------------
# Filter definitions
# ---------------------------------------------------------------------------

FILTER_ALL       = "all"
FILTER_TODAY     = "today"
FILTER_SCHEDULED = "scheduled"
FILTER_IMPORTANT = "important"
FILTER_COMPLETED = "completed"

SYSTEM_FILTERS = [
    (FILTER_ALL,       "All reminders",  "\u25CE"),   # ◎
    (FILTER_TODAY,     "Today",          "\u2600"),   # ☀
    (FILTER_SCHEDULED, "Scheduled",      "\u23F0"),   # ⏰
    (FILTER_IMPORTANT, "Important",      "\u2605"),   # ★
    (FILTER_COMPLETED, "Completed",      "\u2713"),   # ✓
]


# ---------------------------------------------------------------------------
# App icon (drawn programmatically)
# ---------------------------------------------------------------------------

def make_app_icon(color: str = "#4B8BF5") -> QIcon:
    """A simple bell-shaped icon rendered to a QPixmap."""
    px = QPixmap(64, 64)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(QPen(QColor(color).darker(120), 2))
    # Bell body
    painter.drawRoundedRect(14, 14, 36, 32, 14, 14)
    painter.drawRoundedRect(10, 40, 44, 8, 4, 4)
    # Clapper
    painter.setBrush(QColor(color).darker(120))
    painter.drawEllipse(28, 50, 8, 8)
    painter.end()
    return QIcon(px)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):

    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store
        self.palette_theme = LIGHT
        self.current_filter: str = FILTER_ALL
        self.search_text: str = ""

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(880, 600)
        self.resize(1080, 720)
        self.setWindowIcon(make_app_icon())

        self._build_ui()
        self._install_shortcuts()
        self._apply_theme(self.palette_theme)
        self._refresh_sidebar(select_key=self.current_filter)
        self._refresh_list()

        # Tray + notifier
        self.tray = self._make_tray()
        self.notifier_timer = QTimer(self)
        self.notifier_timer.setInterval(30 * 1000)
        self.notifier_timer.timeout.connect(self._check_notifications)
        self.notifier_timer.start()
        QTimer.singleShot(1500, self._check_notifications)

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # ---- Sidebar ----
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(16, 18, 16, 16)
        sb.setSpacing(4)

        title = QLabel("Reminders")
        title.setObjectName("SidebarTitle")
        sb.addWidget(title)

        self.system_list = QListWidget()
        self.system_list.setObjectName("SidebarList")
        self.system_list.setFrameShape(QFrame.NoFrame)
        self.system_list.setSelectionMode(QListWidget.SingleSelection)
        self.system_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.system_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.system_list.setFixedHeight(5 * 40 + 6)
        self.system_list.itemSelectionChanged.connect(self._on_system_selection)
        sb.addWidget(self.system_list)

        list_header_row = QHBoxLayout()
        list_header = QLabel("MY LISTS")
        list_header.setObjectName("SidebarSection")
        list_header_row.addWidget(list_header)
        list_header_row.addStretch(1)
        add_list_btn = QPushButton("+")
        add_list_btn.setObjectName("GhostButton")
        add_list_btn.setFixedWidth(28)
        add_list_btn.setToolTip("New list")
        add_list_btn.clicked.connect(self._on_new_category)
        list_header_row.addWidget(add_list_btn)
        sb.addLayout(list_header_row)

        self.category_list = QListWidget()
        self.category_list.setObjectName("SidebarList")
        self.category_list.setFrameShape(QFrame.NoFrame)
        self.category_list.setSelectionMode(QListWidget.SingleSelection)
        self.category_list.itemSelectionChanged.connect(self._on_category_selection)
        self.category_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_list.customContextMenuRequested.connect(self._on_category_context_menu)
        sb.addWidget(self.category_list, 1)

        # Bottom row: theme toggle
        theme_btn = QPushButton("\u263D  Dark mode")
        theme_btn.setObjectName("GhostButton")
        theme_btn.clicked.connect(self._toggle_theme)
        self.theme_btn = theme_btn
        sb.addWidget(theme_btn)

        h.addWidget(sidebar)

        # ---- Main panel ----
        panel = QWidget()
        p = QVBoxLayout(panel)
        p.setContentsMargins(28, 22, 28, 22)
        p.setSpacing(14)

        # Header (title + search)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        header_texts = QVBoxLayout()
        header_texts.setSpacing(0)
        self.header_title = QLabel("All reminders")
        self.header_title.setObjectName("HeaderTitle")
        self.header_subtitle = QLabel("")
        self.header_subtitle.setObjectName("HeaderSubtitle")
        header_texts.addWidget(self.header_title)
        header_texts.addWidget(self.header_subtitle)
        header_row.addLayout(header_texts, 1)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("SearchInput")
        self.search_edit.setPlaceholderText("\U0001F50D  Search reminders")
        self.search_edit.setFixedWidth(260)
        self.search_edit.textChanged.connect(self._on_search)
        header_row.addWidget(self.search_edit, 0, Qt.AlignVCenter)
        p.addLayout(header_row)

        # Quick add bar
        quick = QFrame()
        quick.setObjectName("QuickAddBar")
        qh = QHBoxLayout(quick)
        qh.setContentsMargins(16, 6, 8, 6)
        qh.setSpacing(8)
        plus = QLabel("+")
        plus.setStyleSheet("font-size:20px; color:#8A929C; padding:0 4px;")
        qh.addWidget(plus)
        self.quick_edit = QLineEdit()
        self.quick_edit.setPlaceholderText("Add a reminder\u2026")
        self.quick_edit.returnPressed.connect(self._on_quick_add)
        qh.addWidget(self.quick_edit, 1)
        more_btn = QPushButton("Add details")
        more_btn.clicked.connect(self._on_new_detailed)
        qh.addWidget(more_btn)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._on_quick_add)
        qh.addWidget(add_btn)
        p.addWidget(quick)

        # List scroll area
        self.scroll = QScrollArea()
        self.scroll.setObjectName("ListScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(2, 4, 2, 20)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_container)
        p.addWidget(self.scroll, 1)

        h.addWidget(panel, 1)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._on_new_detailed)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_edit.setFocus())
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_theme)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self._quit)

    # -- theming -----------------------------------------------------------

    def _apply_theme(self, palette) -> None:
        self.palette_theme = palette
        QApplication.instance().setStyleSheet(stylesheet(palette))
        self.theme_btn.setText("\u2600  Light mode" if palette.name == "dark" else "\u263D  Dark mode")

    def _toggle_theme(self) -> None:
        self._apply_theme(DARK if self.palette_theme.name == "light" else LIGHT)

    # -- sidebar refresh ---------------------------------------------------

    def _refresh_sidebar(self, *, select_key: Optional[str] = None) -> None:
        # -- system filters
        self.system_list.blockSignals(True)
        self.system_list.clear()
        counts = self._compute_counts()
        for key, label, glyph in SYSTEM_FILTERS:
            n = counts.get(key, 0)
            item = QListWidgetItem(f"  {glyph}   {label}" + (f"     {n}" if n else ""))
            item.setData(Qt.UserRole, ("system", key))
            item.setSizeHint(QSize(0, 38))
            self.system_list.addItem(item)
            if select_key == key:
                self.system_list.setCurrentItem(item)
        self.system_list.blockSignals(False)

        # -- user categories
        self.category_list.blockSignals(True)
        self.category_list.clear()
        for cat in self.store.categories:
            n = sum(1 for r in self.store.reminders if r.category_id == cat.id and not r.done)
            item = QListWidgetItem(f"  \u25CF  {cat.name}" + (f"     {n}" if n else ""))
            item.setData(Qt.UserRole, ("category", cat.id))
            item.setForeground(QColor(cat.color))
            item.setSizeHint(QSize(0, 38))
            self.category_list.addItem(item)
            if select_key == cat.id:
                self.category_list.setCurrentItem(item)
        self.category_list.blockSignals(False)

    def _compute_counts(self) -> dict[str, int]:
        today = date.today()
        counts = {k: 0 for k, *_ in SYSTEM_FILTERS}
        for r in self.store.reminders:
            if r.done:
                counts[FILTER_COMPLETED] += 1
                continue
            counts[FILTER_ALL] += 1
            dt = r.due_dt
            if dt and dt.date() == today:
                counts[FILTER_TODAY] += 1
            if dt:
                counts[FILTER_SCHEDULED] += 1
            if r.important:
                counts[FILTER_IMPORTANT] += 1
        return counts

    # -- list refresh ------------------------------------------------------

    def _matches_filter(self, r: Reminder) -> bool:
        f = self.current_filter
        if f == FILTER_COMPLETED:
            base = r.done
        else:
            base = not r.done
        if not base:
            return False

        if f == FILTER_ALL or f == FILTER_COMPLETED:
            pass
        elif f == FILTER_TODAY:
            dt = r.due_dt
            if not dt or dt.date() != date.today():
                return False
        elif f == FILTER_SCHEDULED:
            if not r.due_dt:
                return False
        elif f == FILTER_IMPORTANT:
            if not r.important:
                return False
        else:
            # category id
            if r.category_id != f:
                return False

        if self.search_text:
            hay = f"{r.title}\n{r.note}".lower()
            if self.search_text not in hay:
                return False
        return True

    def _sort_key(self, r: Reminder):
        dt = r.due_dt
        # None due dates come last; then by due asc; then by creation
        return (dt is None, dt or datetime.max, r.created)

    def _current_header(self) -> tuple[str, str]:
        f = self.current_filter
        for key, label, _ in SYSTEM_FILTERS:
            if key == f:
                return label, ""
        cat = self.store.category(f)
        if cat:
            return cat.name, "My list"
        return "Reminders", ""

    def _refresh_list(self) -> None:
        # clear existing cards
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        title, subtitle = self._current_header()
        self.header_title.setText(title)

        matched = [r for r in self.store.reminders if self._matches_filter(r)]
        matched.sort(key=self._sort_key)

        if not matched:
            self.header_subtitle.setText(subtitle)
            self.list_layout.insertWidget(0, self._make_empty_state())
            return

        n = len(matched)
        remaining = sum(1 for r in matched if not r.done)
        pieces = [f"{n} {'item' if n == 1 else 'items'}"]
        if self.current_filter != FILTER_COMPLETED and remaining != n:
            pieces.append(f"{remaining} remaining")
        if subtitle:
            pieces.append(subtitle)
        self.header_subtitle.setText("  \u00B7  ".join(pieces))

        for i, r in enumerate(matched):
            cat = self.store.category(r.category_id)
            card = ReminderCard(r, cat, self.list_container)
            card.toggled.connect(self._on_toggle_done)
            card.important_toggled.connect(self._on_toggle_important)
            card.edit_requested.connect(self._on_edit)
            card.delete_requested.connect(self._on_delete)
            self.list_layout.insertWidget(i, card)

    def _make_empty_state(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 60, 0, 0)
        v.setSpacing(6)
        v.setAlignment(Qt.AlignHCenter)
        icon = QLabel("\U0001F5C2")   # 🗂
        icon.setObjectName("EmptyIcon")
        icon.setAlignment(Qt.AlignCenter)
        v.addWidget(icon)
        title = QLabel("Nothing here yet")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        sub = QLabel("Type a reminder above and press Enter to add it.")
        sub.setObjectName("EmptySub")
        sub.setAlignment(Qt.AlignCenter)
        v.addWidget(sub)
        return wrap

    # -- selection handlers ------------------------------------------------

    def _on_system_selection(self) -> None:
        item = self.system_list.currentItem()
        if not item:
            return
        self.category_list.blockSignals(True)
        self.category_list.clearSelection()
        self.category_list.blockSignals(False)
        _, key = item.data(Qt.UserRole)
        self.current_filter = key
        self._refresh_list()

    def _on_category_selection(self) -> None:
        item = self.category_list.currentItem()
        if not item:
            return
        self.system_list.blockSignals(True)
        self.system_list.clearSelection()
        self.system_list.blockSignals(False)
        _, cat_id = item.data(Qt.UserRole)
        self.current_filter = cat_id
        self._refresh_list()

    def _on_category_context_menu(self, pos) -> None:
        item = self.category_list.itemAt(pos)
        if not item:
            return
        _, cat_id = item.data(Qt.UserRole)
        cat = self.store.category(cat_id)
        if not cat:
            return
        menu = QMenu(self)
        rename_a = menu.addAction("Rename\u2026")
        delete_a = menu.addAction("Delete list")
        chosen = menu.exec(self.category_list.viewport().mapToGlobal(pos))
        if chosen == rename_a:
            from PySide6.QtWidgets import QInputDialog
            new_name, ok = QInputDialog.getText(self, "Rename list", "New name:", text=cat.name)
            if ok and new_name.strip():
                cat.name = new_name.strip()
                self.store.save()
                self._refresh_sidebar(select_key=self._selected_key())
                self._refresh_list()
        elif chosen == delete_a:
            if QMessageBox.question(
                self,
                "Delete list",
                f"Delete list '{cat.name}'?\nReminders in this list will be kept but uncategorized.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            ) == QMessageBox.Yes:
                self.store.delete_category(cat.id)
                self.current_filter = FILTER_ALL
                self._refresh_sidebar(select_key=FILTER_ALL)
                self._refresh_list()

    def _selected_key(self) -> str:
        return self.current_filter

    def _on_search(self, text: str) -> None:
        self.search_text = text.strip().lower()
        self._refresh_list()

    # -- CRUD handlers -----------------------------------------------------

    def _on_quick_add(self) -> None:
        title = self.quick_edit.text().strip()
        if not title:
            return
        r = Reminder(title=title)
        # If viewing a category, default to it
        if self.current_filter not in {k for k, *_ in SYSTEM_FILTERS}:
            r.category_id = self.current_filter
        if self.current_filter == FILTER_IMPORTANT:
            r.important = True
        if self.current_filter == FILTER_TODAY:
            from datetime import time as _time
            r.due_dt = datetime.combine(date.today(), _time(9, 0))
        self.store.add(r)
        self.quick_edit.clear()
        self._refresh_sidebar(select_key=self.current_filter)
        self._refresh_list()

    def _on_new_detailed(self) -> None:
        r = Reminder()
        # Preselect current category if applicable
        if self.current_filter not in {k for k, *_ in SYSTEM_FILTERS}:
            r.category_id = self.current_filter
        if self.current_filter == FILTER_IMPORTANT:
            r.important = True
        dlg = ReminderEditor(self.store, None, self)
        dlg.reminder = r
        dlg._populate()
        if dlg.exec():
            self._refresh_sidebar(select_key=self.current_filter)
            self._refresh_list()

    def _on_edit(self, reminder_id: str) -> None:
        r = self.store.get(reminder_id)
        if not r:
            return
        dlg = ReminderEditor(self.store, r, self)
        if dlg.exec():
            self._refresh_sidebar(select_key=self.current_filter)
            self._refresh_list()

    def _on_toggle_done(self, reminder_id: str) -> None:
        self.store.toggle_done(reminder_id)
        self._refresh_sidebar(select_key=self.current_filter)
        self._refresh_list()

    def _on_toggle_important(self, reminder_id: str) -> None:
        r = self.store.get(reminder_id)
        if not r:
            return
        r.important = not r.important
        self.store.update(r)
        self._refresh_sidebar(select_key=self.current_filter)
        self._refresh_list()

    def _on_delete(self, reminder_id: str) -> None:
        r = self.store.get(reminder_id)
        if not r:
            return
        if QMessageBox.question(
            self,
            "Delete reminder",
            f"Delete '{r.title or 'this reminder'}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.store.delete(reminder_id)
        self._refresh_sidebar(select_key=self.current_filter)
        self._refresh_list()

    def _on_new_category(self) -> None:
        cat = ask_new_category(self, self.store)
        if cat:
            self.current_filter = cat.id
            self._refresh_sidebar(select_key=cat.id)
            self._refresh_list()

    # -- tray & notifications ---------------------------------------------

    def _make_tray(self) -> Optional[QSystemTrayIcon]:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None
        tray = QSystemTrayIcon(make_app_icon(), self)
        tray.setToolTip(APP_NAME)
        menu = QMenu()
        show_a = QAction("Show window", self)
        show_a.triggered.connect(self._show_and_raise)
        add_a = QAction("New reminder", self)
        add_a.triggered.connect(self._on_new_detailed)
        quit_a = QAction("Quit", self)
        quit_a.triggered.connect(self._quit)
        menu.addAction(show_a)
        menu.addAction(add_a)
        menu.addSeparator()
        menu.addAction(quit_a)
        tray.setContextMenu(menu)
        tray.activated.connect(
            lambda reason: self._show_and_raise() if reason == QSystemTrayIcon.Trigger else None
        )
        tray.show()
        return tray

    def _show_and_raise(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _check_notifications(self) -> None:
        now = datetime.now()
        dirty = False
        for r in self.store.reminders:
            if r.done or r.notified:
                continue
            dt = r.due_dt
            if not dt or dt > now:
                continue
            r.notified = True
            dirty = True
            self._notify(r)
        if dirty:
            self.store.save()
            self._refresh_sidebar(select_key=self.current_filter)
            self._refresh_list()

    def _notify(self, r: Reminder) -> None:
        title = f"{APP_NAME}: {r.title or 'Reminder'}"
        body = r.note.strip().splitlines()[0] if r.note else "It's time!"
        if self.tray:
            self.tray.showMessage(title, body, QSystemTrayIcon.Information, 8000)

    # -- close -------------------------------------------------------------

    def closeEvent(self, e) -> None:                                # noqa: N802
        if self.tray:
            # Minimize to tray instead of quitting
            e.ignore()
            self.hide()
            self.tray.showMessage(
                APP_NAME,
                "Still running in the background. Right-click the tray icon to quit.",
                QSystemTrayIcon.Information,
                3500,
            )
            return
        super().closeEvent(e)

    def _quit(self) -> None:
        if self.tray:
            self.tray.hide()
        QApplication.instance().quit()
