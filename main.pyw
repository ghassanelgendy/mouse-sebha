import sys
import os
import socket

# Ultra-fast early socket IPC sender (< 30ms, no PyQt import overhead)
SOCKET_NAME = f"/tmp/mouse_sebha_{os.getuid()}.sock" if sys.platform != "win32" else "mouse_sebha_ipc_socket"

if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg in ("--increment", "-i", "increment", "--show", "-s", "show"):
        try:
            s = socket.socket(socket.AF_UNIX if sys.platform != "win32" else socket.AF_INET, socket.SOCK_STREAM)
            s.connect(SOCKET_NAME)
            cmd = "INCREMENT" if arg in ("--increment", "-i", "increment") else "SHOW"
            s.sendall(cmd.encode("utf-8"))
            s.close()
            sys.exit(0)
        except Exception:
            pass # App not running yet, proceed to full launch

import json
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QFontDatabase, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from overlay_ui import SebhaOverlay
from input_listener import InputListener
from settings_ui import SettingsDialog, UpdateCheckerThread, apply_update_and_restart

APP_VERSION = "v1.0.26"
from config_path import CONFIG_PATH

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Set QT_QPA_PLATFORM and High-DPI scaling for Linux
if sys.platform.startswith("linux"):
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

def handle_existing_instance():
    try:
        s = socket.socket(socket.AF_UNIX if sys.platform != "win32" else socket.AF_INET, socket.SOCK_STREAM)
        s.connect(SOCKET_NAME)
        cmd = "INCREMENT" if ("--increment" in sys.argv or "-i" in sys.argv) else "SHOW"
        s.sendall(cmd.encode("utf-8"))
        s.close()
        return True
    except Exception:
        return False

def main():
    if handle_existing_instance():
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load custom font (we don't apply it globally so English texts stay clean)
    default_font_path = resource_path("assets/fonts/font.ttf")
    if not os.path.exists(default_font_path):
        default_font_path = resource_path("assets/font.ttf")
    QFontDatabase.addApplicationFont(default_font_path)

    # Load Logo
    app_icon = QIcon(resource_path("assets/logo.ico"))
    app.setWindowIcon(app_icon)

    overlay = SebhaOverlay()
    listener = InputListener()
    
    # Set up Local Server for IPC (Wayland shortcuts, CLI incrementing, & single-instance focus)
    QLocalServer.removeServer(SOCKET_NAME)
    ipc_server = QLocalServer()
    if ipc_server.listen(SOCKET_NAME):
        def on_ipc_connection():
            conn = ipc_server.nextPendingConnection()
            if conn:
                if conn.waitForReadyRead(500):
                    data = conn.readAll().data().decode("utf-8").strip()
                    if data == "INCREMENT":
                        overlay.increment_count()
                    elif data == "SHOW":
                        overlay.show_overlay()
                conn.disconnectFromServer()
        ipc_server.newConnection.connect(on_ipc_connection)
        app.ipc_server = ipc_server

    # Handle --increment flag on cold start
    if "--increment" in sys.argv or "-i" in sys.argv:
        overlay.increment_count()
    
    settings_dialog = SettingsDialog(APP_VERSION)
    settings_dialog.config_updated.connect(listener.reload)
    settings_dialog.config_updated.connect(overlay.load_config)
    overlay.open_settings_requested.connect(settings_dialog.show)

    listener.signals.triggered.connect(overlay.increment_count)
    listener.start()
    
    # Periodic Hadith Reminders Timer
    hadith_timer = QThread() # Use QTimer on app looper
    from PyQt6.QtCore import QTimer
    hadith_qtimer = QTimer(app)
    
    def trigger_hadith_reminder():
        hadith_list = overlay.db.get("hadith", [])
        if not hadith_list:
            return
        import random
        # Pick from top 100 concise Hadiths
        h = random.choice(hadith_list[:min(100, len(hadith_list))])
        
        # Display overlay card and/or native notification
        overlay.show_hadith_notification(h)

    def update_hadith_timer():
        enabled = True
        interval_min = 30
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    enabled = cfg.get("hadith_reminder_enabled", True)
                    interval_min = cfg.get("hadith_reminder_interval", 30)
            except Exception:
                pass
        
        hadith_qtimer.stop()
        if enabled:
            interval_ms = max(5, interval_min) * 60 * 1000
            hadith_qtimer.setInterval(interval_ms)
            hadith_qtimer.start()

    hadith_qtimer.timeout.connect(trigger_hadith_reminder)
    settings_dialog.config_updated.connect(update_hadith_timer)
    update_hadith_timer()

    # System Tray
    tray_icon = QSystemTrayIcon(app_icon, app)
    tray_icon.setToolTip("Sebha")
    tray_icon.messageClicked.connect(overlay.open_athkar_modal)
    
    menu = QMenu()
    show_action = menu.addAction("إظهار الواجهة (Show Overlay)")
    show_action.triggered.connect(overlay.show_overlay)
    
    choose_athkar_action = menu.addAction("اختيار الورد... (Choose Athkar)")
    choose_athkar_action.triggered.connect(overlay.open_athkar_modal)
    
    menu.addSeparator()
    
    morning_action = menu.addAction("أذكار الصباح")
    morning_action.setCheckable(True)
    morning_action.triggered.connect(lambda: overlay.toggle_session('MORNING'))
    
    night_action = menu.addAction("أذكار المساء")
    night_action.setCheckable(True)
    night_action.triggered.connect(lambda: overlay.toggle_session('NIGHT'))
    
    free_action = menu.addAction("الوضع الحر")
    free_action.setCheckable(True)
    free_action.triggered.connect(overlay.exit_session)
    
    hadith_action = menu.addAction("حديث شريف")
    hadith_action.triggered.connect(trigger_hadith_reminder)
    
    menu.addSeparator()
    
    reset_action = menu.addAction("إعادة تعيين العداد (Reset Counter)")
    reset_action.triggered.connect(overlay.reset_count)
    
    settings_action = menu.addAction("الإعدادات (Settings)")
    settings_action.triggered.connect(settings_dialog.show)
    
    menu.addSeparator()
    
    quit_action = menu.addAction("خروج (Quit)")
    def on_quit():
        listener.stop()
        app.quit()
    quit_action.triggered.connect(on_quit)
    
    def update_menu_checks():
        morning_action.setChecked(overlay.mode == 'MORNING')
        night_action.setChecked(overlay.mode == 'NIGHT')
        free_action.setChecked(overlay.mode == 'FREE')
        
    menu.aboutToShow.connect(update_menu_checks)
    tray_icon.setContextMenu(menu)
    
    def update_tray_visibility():
        show_tray = True
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    show_tray = json.load(f).get("show_tray_icon", True)
            except Exception:
                pass
        if show_tray and QSystemTrayIcon.isSystemTrayAvailable():
            tray_icon.show()
        else:
            tray_icon.hide()

    settings_dialog.config_updated.connect(update_tray_visibility)
    update_tray_visibility()
    
    if getattr(overlay, "display_mode", "overlay") in ("overlay", "both"):
        overlay.show_overlay()
    
    # Check for updates if enabled
    auto_update = True
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                auto_update = data.get("auto_update", True)
        except Exception:
            pass

    if auto_update and getattr(sys, 'frozen', False):
        updater_thread = UpdateCheckerThread(APP_VERSION)
        
        def on_update_ready(new_exe_path, latest_version=""):
            msg = QMessageBox()
            msg.setWindowTitle("Update Available")
            msg.setText(f"A new update ({latest_version}) has been downloaded successfully!" if latest_version else "A new update has been downloaded successfully!")
            msg.setInformativeText("The application will restart to apply the update.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            apply_update_and_restart(new_exe_path)
            
        updater_thread.update_downloaded.connect(on_update_ready)
        updater_thread.start()
        app.updater = updater_thread # prevent garbage collection
    
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print("Fatal error launching Sebha:\n", err)
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Sebha Launch Error", f"Failed to start Sebha:\n\n{e}\n\n{err}")
        except Exception:
            pass
