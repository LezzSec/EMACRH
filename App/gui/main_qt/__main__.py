# -*- coding: utf-8 -*-
"""Point d'entrée pour: py -m gui.main_qt"""
import sys
import traceback
import datetime as dt

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import qInstallMessageHandler

from infrastructure.logging.logging_config import get_logger, get_logs_dir, set_log_context

logger = get_logger(__name__)

# Handler silencieux pour les messages Qt
qInstallMessageHandler(lambda *_: None)


def _crash_handler(exc_type, exc_value, exc_tb):
    crash_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    crash_file = get_logs_dir() / 'crash.log'
    with open(crash_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n{dt.datetime.now()}\n{crash_msg}\n")
    print(crash_msg, file=sys.stderr)
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _crash_handler

app = QApplication(sys.argv)

from gui.main_qt._shared import get_theme_components
EmacTheme = get_theme_components()['EmacTheme']
EmacTheme.apply(app)

from gui.screens.admin.login_dialog import LoginDialog
login_dialog = LoginDialog()

if login_dialog.exec_() == LoginDialog.Accepted:
    try:
        from domain.services.admin.auth_service import get_current_user
        user = get_current_user()
        if user:
            set_log_context(user_id=user.get('username') or user.get('nom'), screen='MainWindow')
    except Exception:
        pass

    from gui.main_qt.main_window import MainWindow
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
else:
    sys.exit(0)
