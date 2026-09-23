#!/usr/bin/env python3
"""Entry point for the Reminder desktop app."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app import APP_NAME, ORG_NAME
from app.main_window import MainWindow
from app.models import Store


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)   # tray keeps it alive

    store = Store()
    window = MainWindow(store)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
