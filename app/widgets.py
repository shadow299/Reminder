"""Reusable widgets: reminder card, editor dialog, category dialog."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QDateTime, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .models import Category, Reminder, Repeat, Store


CHECK_MARK = "\u2713"       # ✓
STAR_ON = "\u2605"          # ★
STAR_OFF = "\u2606"         # ☆
MENU_DOTS = "\u22EE"        # ⋮


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _drop_shadow(widget: QWidget, *, blur: int = 18, y: int = 4, alpha: int = 28) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


def _text_color_for(bg_hex: str) -> str:
    bg = QColor(bg_hex)
    luminance = (0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()) / 255
    return "#FFFFFF" if luminance < 0.6 else "#1F2328"


# ---------------------------------------------------------------------------
# Reminder card
# ---------------------------------------------------------------------------

class ReminderCard(QFrame):
    """Single reminder row rendered as a rounded card."""

    toggled = Signal(str)           # reminder id (done toggled)
    important_toggled = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, reminder: Reminder, category: Optional[Category], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.reminder = reminder
        self.category = category
        self.setObjectName("ReminderCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(64)
        _drop_shadow(self)

        self._build()

    # -- build -------------------------------------------------------------

    def _build(self) -> None:
        r = self.reminder

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 12, 12)
        outer.setSpacing(12)

        # Check circle
        self.check_btn = QPushButton(CHECK_MARK if r.done else "")
        self.check_btn.setObjectName("CheckButtonDone" if r.done else "CheckButton")
        self.check_btn.setFixedSize(26, 26)
        self.check_btn.setCursor(Qt.PointingHandCursor)
        self.check_btn.clicked.connect(lambda: self.toggled.emit(r.id))
        outer.addWidget(self.check_btn, 0, Qt.AlignTop)

        # Text block
        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(0, 0, 0, 0)
        text_wrap.setSpacing(3)

        title = QLabel(r.title or "Untitled")
        title.setObjectName("CardTitleDone" if r.done else "CardTitle")
        title.setWordWrap(True)
        if r.done:
            font = title.font()
            font.setStrikeOut(True)
            title.setFont(font)
        text_wrap.addWidget(title)

        if r.note:
            note = QLabel(r.note.strip().splitlines()[0][:180])
            note.setObjectName("CardNote")
            note.setWordWrap(False)
            text_wrap.addWidget(note)

        # meta row: due + repeat + category chip
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 2, 0, 0)
        meta_row.setSpacing(8)

        due_text = r.format_due()
        if due_text:
            due_lbl = QLabel(due_text + (f"  \u21BB {Repeat(r.repeat).label}" if r.repeat != Repeat.NONE.value else ""))
            due_lbl.setObjectName("CardMetaOverdue" if r.is_overdue() else "CardMeta")
            meta_row.addWidget(due_lbl)

        if self.category:
            chip = QLabel(self.category.name)
            chip.setObjectName("CategoryChip")
            chip.setStyleSheet(
                f"background: {self.category.color}; color: {_text_color_for(self.category.color)};"
            )
            meta_row.addWidget(chip)

        meta_row.addStretch(1)
        if due_text or self.category:
            text_wrap.addLayout(meta_row)

        outer.addLayout(text_wrap, 1)

        # Star button
        self.star_btn = QPushButton(STAR_ON if r.important else STAR_OFF)
        self.star_btn.setObjectName("StarButtonOn" if r.important else "StarButton")
        self.star_btn.setFixedSize(28, 28)
        self.star_btn.setCursor(Qt.PointingHandCursor)
        self.star_btn.setToolTip("Toggle important")
        self.star_btn.clicked.connect(lambda: self.important_toggled.emit(r.id))
        outer.addWidget(self.star_btn, 0, Qt.AlignTop)

        # Menu button
        self.menu_btn = QPushButton(MENU_DOTS)
        self.menu_btn.setObjectName("MenuButton")
        self.menu_btn.setFixedSize(28, 28)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setToolTip("More")
        self.menu_btn.clicked.connect(self._open_menu)
        outer.addWidget(self.menu_btn, 0, Qt.AlignTop)

    # -- interactions ------------------------------------------------------

    def _open_menu(self) -> None:
        menu = QMenu(self)
        edit_a = menu.addAction("Edit\u2026")
        toggle_a = menu.addAction("Mark as not done" if self.reminder.done else "Mark as done")
        star_a = menu.addAction("Remove star" if self.reminder.important else "Mark as important")
        menu.addSeparator()
        delete_a = menu.addAction("Delete")

        chosen = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight()))
        if chosen == edit_a:
            self.edit_requested.emit(self.reminder.id)
        elif chosen == toggle_a:
            self.toggled.emit(self.reminder.id)
        elif chosen == star_a:
            self.important_toggled.emit(self.reminder.id)
        elif chosen == delete_a:
            self.delete_requested.emit(self.reminder.id)

    def mouseDoubleClickEvent(self, e) -> None:                         # noqa: N802
        self.edit_requested.emit(self.reminder.id)
        super().mouseDoubleClickEvent(e)


# ---------------------------------------------------------------------------
# Editor dialog
# ---------------------------------------------------------------------------

class ReminderEditor(QDialog):
    """Modal editor for a single reminder."""

    def __init__(self, store: Store, reminder: Optional[Reminder] = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self.reminder = reminder or Reminder()
        self.is_new = reminder is None
        self.setWindowTitle("New reminder" if self.is_new else "Edit reminder")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build()
        self._populate()

    # -- build -------------------------------------------------------------

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        header = QLabel(self.windowTitle())
        header_font = QFont(header.font())
        header_font.setPointSize(header_font.pointSize() + 4)
        header_font.setBold(True)
        header.setFont(header_font)
        root.addWidget(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setContentsMargins(0, 4, 0, 0)
        form.setSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What do you want to be reminded of?")
        form.addRow("Title", self.title_edit)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Add a note (optional)")
        self.note_edit.setFixedHeight(90)
        form.addRow("Note", self.note_edit)

        # Due date/time row
        due_row = QHBoxLayout()
        due_row.setSpacing(8)
        self.due_enabled = QCheckBox("Set date & time")
        self.due_edit = QDateTimeEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("ddd, dd MMM yyyy  HH:mm")
        self.due_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.due_edit.setEnabled(False)
        self.due_enabled.toggled.connect(self.due_edit.setEnabled)
        due_row.addWidget(self.due_enabled)
        due_row.addWidget(self.due_edit, 1)
        form.addRow("Due", due_row)

        # Repeat combo
        self.repeat_combo = QComboBox()
        for r in Repeat:
            self.repeat_combo.addItem(r.label, r.value)
        form.addRow("Repeat", self.repeat_combo)

        # Category combo
        self.category_combo = QComboBox()
        self.category_combo.addItem("No category", None)
        for cat in self.store.categories:
            self.category_combo.addItem(cat.name, cat.id)
        form.addRow("Category", self.category_combo)

        # Important
        self.important_check = QCheckBox("Mark as important")
        form.addRow("", self.important_check)

        root.addLayout(form)
        root.addStretch(1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        if not self.is_new:
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("DangerButton")
            delete_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(delete_btn)
        btn_row.addStretch(1)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # -- populate ----------------------------------------------------------

    def _populate(self) -> None:
        r = self.reminder
        self.title_edit.setText(r.title)
        self.note_edit.setPlainText(r.note)

        dt = r.due_dt
        if dt:
            self.due_enabled.setChecked(True)
            self.due_edit.setDateTime(QDateTime(dt))
        else:
            self.due_enabled.setChecked(False)

        idx = self.repeat_combo.findData(r.repeat)
        if idx >= 0:
            self.repeat_combo.setCurrentIndex(idx)

        idx = self.category_combo.findData(r.category_id)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        self.important_check.setChecked(r.important)

    # -- actions -----------------------------------------------------------

    def _on_save(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Please enter a title for the reminder.")
            self.title_edit.setFocus()
            return

        r = self.reminder
        r.title = title
        r.note = self.note_edit.toPlainText().strip()
        if self.due_enabled.isChecked():
            r.due_dt = self.due_edit.dateTime().toPython()
        else:
            r.due = None
        r.repeat = self.repeat_combo.currentData() or Repeat.NONE.value
        r.category_id = self.category_combo.currentData()
        r.important = self.important_check.isChecked()
        r.notified = False

        if self.is_new:
            self.store.add(r)
        else:
            self.store.update(r)
        self.accept()

    def _on_delete(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Delete reminder",
            "Are you sure you want to delete this reminder?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.store.delete(self.reminder.id)
            self.done(QDialog.Accepted)


# ---------------------------------------------------------------------------
# New-category dialog helper
# ---------------------------------------------------------------------------

PRESET_COLORS = [
    "#4B8BF5", "#2FB673", "#F5883C", "#E14C4C",
    "#8B5CF6", "#EC4899", "#0EA5E9", "#F59E0B",
    "#10B981", "#6B7280",
]


def ask_new_category(parent: QWidget, store: Store) -> Optional[Category]:
    dlg = QDialog(parent)
    dlg.setWindowTitle("New list")
    dlg.setMinimumWidth(360)
    root = QVBoxLayout(dlg)
    root.setContentsMargins(20, 20, 20, 20)
    root.setSpacing(12)

    title = QLabel("New list")
    f = QFont(title.font())
    f.setPointSize(f.pointSize() + 3)
    f.setBold(True)
    title.setFont(f)
    root.addWidget(title)

    name_edit = QLineEdit()
    name_edit.setPlaceholderText("List name")
    root.addWidget(name_edit)

    color_lbl = QLabel("Color")
    root.addWidget(color_lbl)

    color_row = QHBoxLayout()
    color_row.setSpacing(6)
    selected_color = {"value": PRESET_COLORS[0]}
    swatches: list[QPushButton] = []

    def _select(idx: int) -> None:
        selected_color["value"] = PRESET_COLORS[idx]
        for i, s in enumerate(swatches):
            border = "3px solid #1F2328" if i == idx else "2px solid transparent"
            s.setStyleSheet(f"background:{PRESET_COLORS[i]}; border-radius:14px; border:{border};")

    for i, col in enumerate(PRESET_COLORS):
        btn = QPushButton()
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _=False, idx=i: _select(idx))
        swatches.append(btn)
        color_row.addWidget(btn)
    color_row.addStretch(1)
    root.addLayout(color_row)
    _select(0)

    btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    ok_btn = btns.button(QDialogButtonBox.Ok)
    ok_btn.setObjectName("PrimaryButton")
    ok_btn.setText("Create")
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    root.addWidget(btns)

    name_edit.setFocus()
    if dlg.exec() != QDialog.Accepted:
        return None

    name = name_edit.text().strip()
    if not name:
        return None
    return store.add_category(name, selected_color["value"])
