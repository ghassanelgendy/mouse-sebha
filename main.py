import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QFontDatabase, QFont
from PyQt6.QtCore import Qt
from overlay_ui import SebhaOverlay
from input_listener import InputListener
from settings_ui import SettingsDialog

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load custom font (we don't apply it globally so English texts stay clean)
    QFontDatabase.addApplicationFont("font.ttf")

    # Load Logo
    app_icon = QIcon("logo.ico")
    app.setWindowIcon(app_icon)

    overlay = SebhaOverlay()
    listener = InputListener()
    
    settings_dialog = SettingsDialog()
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
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
