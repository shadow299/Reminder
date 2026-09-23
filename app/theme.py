"""Theme colors and stylesheet builder for Reminder."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str            # window background
    panel: str         # sidebar background
    card: str          # reminder card
    card_hover: str
    border: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    accent_hover: str
    accent_soft: str   # translucent accent (chip/hover)
    danger: str
    star: str
    overdue: str
    scrollbar: str


LIGHT = Palette(
    name="light",
    bg="#F4F5F7",
    panel="#EDEEF1",
    card="#FFFFFF",
    card_hover="#F7F8FA",
    border="#E1E3E8",
    text="#1F2328",
    text_muted="#5F6772",
    text_faint="#8A929C",
    accent="#3F7DE0",
    accent_hover="#3568C4",
    accent_soft="#E8F0FE",
    danger="#E14C4C",
    star="#F5B301",
    overdue="#E14C4C",
    scrollbar="#D0D4DA",
)

DARK = Palette(
    name="dark",
    bg="#141518",
    panel="#1B1D21",
    card="#24272C",
    card_hover="#2B2F35",
    border="#33373E",
    text="#ECEDEF",
    text_muted="#A7ADB6",
    text_faint="#7B818A",
    accent="#4B8BF5",
    accent_hover="#679EF8",
    accent_soft="#1E2A44",
    danger="#F26A6A",
    star="#F5C147",
    overdue="#F26A6A",
    scrollbar="#3B3F46",
)


def stylesheet(p: Palette) -> str:
    """Return the full application stylesheet for the given palette."""
    return f"""
    /* -------- base -------- */
    QWidget {{
        background: {p.bg};
        color: {p.text};
        font-family: "Inter", "Segoe UI", "SF Pro Text", "Ubuntu", "Noto Sans", sans-serif;
        font-size: 14px;
    }}
    QToolTip {{
        background: {p.card};
        color: {p.text};
        border: 1px solid {p.border};
        padding: 6px 10px;
        border-radius: 6px;
    }}

    /* -------- sidebar -------- */
    #Sidebar {{
        background: {p.panel};
        border: none;
    }}
    #SidebarTitle {{
        color: {p.text};
        font-size: 22px;
        font-weight: 700;
        padding: 6px 6px 12px 6px;
    }}
    #SidebarSection {{
        color: {p.text_faint};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 14px 8px 6px 8px;
    }}
    QListWidget#SidebarList {{
        background: transparent;
        border: none;
        outline: 0;
        padding: 2px;
    }}
    QListWidget#SidebarList::item {{
        padding: 10px 12px;
        margin: 2px 0;
        border-radius: 10px;
        color: {p.text};
    }}
    QListWidget#SidebarList::item:hover {{
        background: {p.card_hover};
    }}
    QListWidget#SidebarList::item:selected {{
        background: {p.accent_soft};
        color: {p.accent};
        font-weight: 600;
    }}

    /* -------- top bar -------- */
    #HeaderTitle {{
        font-size: 26px;
        font-weight: 700;
        color: {p.text};
        padding: 4px 0;
    }}
    #HeaderSubtitle {{
        color: {p.text_muted};
        font-size: 13px;
    }}
    QLineEdit#SearchInput {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 18px;
        padding: 8px 14px;
        color: {p.text};
        selection-background-color: {p.accent};
    }}
    QLineEdit#SearchInput:focus {{
        border-color: {p.accent};
    }}

    /* -------- quick add -------- */
    #QuickAddBar {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 24px;
    }}
    #QuickAddBar QLineEdit {{
        background: transparent;
        border: none;
        padding: 10px 4px;
        font-size: 14px;
        color: {p.text};
    }}
    #QuickAddBar QPushButton {{
        background: {p.accent};
        color: white;
        border: none;
        border-radius: 18px;
        padding: 6px 16px;
        font-weight: 600;
    }}
    #QuickAddBar QPushButton:hover {{
        background: {p.accent_hover};
    }}
    #QuickAddBar QPushButton:disabled {{
        background: {p.border};
        color: {p.text_faint};
    }}

    /* -------- reminder cards -------- */
    QScrollArea#ListScroll {{
        border: none;
        background: transparent;
    }}
    QScrollArea#ListScroll > QWidget > QWidget {{
        background: transparent;
    }}
    #ReminderCard {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 16px;
    }}
    #ReminderCard:hover {{
        background: {p.card_hover};
    }}
    #CardTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {p.text};
        background: transparent;
    }}
    #CardTitleDone {{
        font-size: 15px;
        font-weight: 500;
        color: {p.text_faint};
        background: transparent;
    }}
    #CardNote {{
        color: {p.text_muted};
        background: transparent;
    }}
    #CardMeta {{
        color: {p.text_muted};
        font-size: 12px;
        background: transparent;
    }}
    #CardMetaOverdue {{
        color: {p.overdue};
        font-size: 12px;
        font-weight: 600;
        background: transparent;
    }}
    #CategoryChip {{
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        color: white;
    }}
    #CheckButton {{
        border: 2px solid {p.text_faint};
        border-radius: 13px;
        background: transparent;
    }}
    #CheckButton:hover {{
        border-color: {p.accent};
    }}
    #CheckButtonDone {{
        border: 2px solid {p.accent};
        border-radius: 13px;
        background: {p.accent};
        color: white;
        font-weight: 700;
    }}
    #StarButton {{
        border: none;
        background: transparent;
        color: {p.text_faint};
        font-size: 18px;
    }}
    #StarButton:hover {{
        color: {p.star};
    }}
    #StarButtonOn {{
        border: none;
        background: transparent;
        color: {p.star};
        font-size: 18px;
    }}
    #MenuButton {{
        border: none;
        background: transparent;
        color: {p.text_muted};
        font-size: 18px;
        border-radius: 6px;
        padding: 2px 6px;
    }}
    #MenuButton:hover {{
        background: {p.card_hover};
        color: {p.text};
    }}

    /* -------- empty state -------- */
    #EmptyIcon {{
        font-size: 56px;
        color: {p.text_faint};
    }}
    #EmptyTitle {{
        font-size: 18px;
        font-weight: 600;
        color: {p.text_muted};
    }}
    #EmptySub {{
        color: {p.text_faint};
        font-size: 13px;
    }}

    /* -------- editor dialog -------- */
    QDialog {{
        background: {p.bg};
    }}
    QDialog QLabel {{
        color: {p.text};
        font-weight: 500;
    }}
    QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 8px 10px;
        color: {p.text};
        selection-background-color: {p.accent};
    }}
    QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
        border-color: {p.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QDateTimeEdit::up-button, QDateTimeEdit::down-button {{
        width: 16px;
    }}
    QCheckBox {{
        color: {p.text};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {p.text_faint};
        border-radius: 5px;
        background: {p.card};
    }}
    QCheckBox::indicator:checked {{
        background: {p.accent};
        border-color: {p.accent};
        image: none;
    }}

    /* -------- buttons -------- */
    QPushButton {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 12px;
        padding: 8px 16px;
        color: {p.text};
    }}
    QPushButton:hover {{
        background: {p.card_hover};
    }}
    QPushButton#PrimaryButton {{
        background: {p.accent};
        color: white;
        border: none;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {p.accent_hover};
    }}
    QPushButton#PrimaryButton:disabled {{
        background: {p.border};
        color: {p.text_faint};
    }}
    QPushButton#DangerButton {{
        color: {p.danger};
        border-color: {p.border};
    }}
    QPushButton#DangerButton:hover {{
        background: {p.card_hover};
    }}
    QPushButton#GhostButton {{
        background: transparent;
        border: none;
        color: {p.text_muted};
        padding: 6px 10px;
    }}
    QPushButton#GhostButton:hover {{
        color: {p.text};
        background: {p.card_hover};
    }}

    /* -------- menu -------- */
    QMenu {{
        background: {p.card};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 20px 8px 14px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {p.accent_soft};
        color: {p.accent};
    }}
    QMenu::separator {{
        height: 1px;
        background: {p.border};
        margin: 4px 6px;
    }}

    /* -------- calendar -------- */
    QCalendarWidget {{
        background: transparent;
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background: transparent;
        min-height: 30px;
    }}
    QCalendarWidget QToolButton {{
        background: transparent;
        color: {p.text};
        border: none;
        border-radius: 6px;
        padding: 4px 8px;
        margin: 2px;
        font-weight: 600;
    }}
    QCalendarWidget QToolButton:hover {{
        background: {p.card_hover};
    }}
    QCalendarWidget QToolButton::menu-indicator {{
        image: none;
    }}
    QCalendarWidget QSpinBox {{
        background: {p.card};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 6px;
        padding: 2px 4px;
    }}
    QCalendarWidget QMenu {{
        background: {p.card};
        color: {p.text};
        border: 1px solid {p.border};
    }}
    QCalendarWidget QAbstractItemView {{
        background: transparent;
        color: {p.text};
        selection-background-color: {p.accent};
        selection-color: white;
        outline: 0;
        border: none;
        gridline-color: transparent;
    }}
    QCalendarWidget QAbstractItemView:disabled {{
        color: {p.text_faint};
    }}
    QCalendarWidget QAbstractItemView:enabled {{
        color: {p.text};
    }}

    /* -------- scrollbar -------- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.scrollbar};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.text_faint};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
        border: none;
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.scrollbar};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
        border: none;
        width: 0;
    }}
    """
