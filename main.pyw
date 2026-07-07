import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QFontDatabase, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from overlay_ui import SebhaOverlay
from input_listener import InputListener
from settings_ui import SettingsDialog, UpdateCheckerThread, apply_update_and_restart

APP_VERSION = "v1.0.12"
from config_path import CONFIG_PATH

# Updater thread and restarter are imported from settings_ui

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
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
    
    settings_dialog = SettingsDialog(APP_VERSION)
    settings_dialog.config_updated.connect(listener.reload)
    settings_dialog.config_updated.connect(overlay.load_config)

    listener.signals.triggered.connect(overlay.increment_count)
    listener.start()
    
    # System Tray
    tray_icon = QSystemTrayIcon(app_icon, app)
    tray_icon.setToolTip("Sebha")
    
    menu = QMenu()
    show_action = menu.addAction("Show Overlay")
    show_action.triggered.connect(overlay.show_overlay)
    
    settings_action = menu.addAction("⚙️ Settings")
    settings_action.triggered.connect(settings_dialog.show)
    
    menu.addSeparator()
    
    quit_action = menu.addAction("Quit")
    def on_quit():
        listener.stop()
        app.quit()
    quit_action.triggered.connect(on_quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    
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
        
        def on_update_ready(new_exe_path):
            msg = QMessageBox()
            msg.setWindowTitle("Update Available")
            msg.setText("A new update has been downloaded successfully!")
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
    main()
