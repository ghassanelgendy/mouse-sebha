import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QFontDatabase, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from overlay_ui import SebhaOverlay
from input_listener import InputListener
from settings_ui import SettingsDialog

APP_VERSION = "v1.0.0"
CONFIG_PATH = "config.json"

class UpdateCheckerThread(QThread):
    update_downloaded = pyqtSignal(str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            import urllib.request
            import platform
            url = "https://api.github.com/repos/ghassanelgendy/mouse-sebha/releases/latest"
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get("tag_name", "").strip("v")
            current = self.current_version.strip("v")
            
            if latest_version and latest_version != current:
                assets = data.get("assets", [])
                
                system_name = platform.system()
                if system_name == "Windows":
                    expected_asset_name = "Sebha-Windows.exe"
                elif system_name == "Linux":
                    expected_asset_name = "Sebha-Linux"
                elif system_name == "Darwin":
                    expected_asset_name = "Sebha-macOS"
                else:
                    expected_asset_name = None
                    
                if expected_asset_name:
                    download_url = None
                    for asset in assets:
                        if asset.get("name") == expected_asset_name:
                            download_url = asset.get("browser_download_url")
                            break
                            
                    if download_url:
                        import tempfile
                        temp_dir = tempfile.gettempdir()
                        new_file_name = "Sebha.new.exe" if system_name == "Windows" else "Sebha.new"
                        new_exe_path = os.path.join(temp_dir, new_file_name)
                        
                        # Download file
                        urllib.request.urlretrieve(download_url, new_exe_path)
                        
                        if os.path.exists(new_exe_path) and os.path.getsize(new_exe_path) > 1000000:
                            self.update_downloaded.emit(new_exe_path)
        except Exception as e:
            print("Error checking/downloading update:", e)

def apply_update_and_restart(new_exe_path):
    import subprocess
    import platform
    
    current_exe = sys.executable
    current_pid = os.getpid()
    system_name = platform.system()
    
    if system_name == "Windows":
        ps_script = f'''
$proc = Get-Process -Id {current_pid} -ErrorAction SilentlyContinue
if ($proc) {{
    $proc.WaitForExit(5000)
}}
Remove-Item -Force "{current_exe}" -ErrorAction SilentlyContinue
Move-Item -Force "{new_exe_path}" "{current_exe}"
Start-Process "{current_exe}"
'''
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        # Unix (Linux / macOS) shell script
        sh_script = f'''
sleep 2
rm -f "{current_exe}"
mv "{new_exe_path}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
'''
        subprocess.Popen(["sh", "-c", sh_script])
        
    QApplication.quit()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load custom font (we don't apply it globally so English texts stay clean)
    QFontDatabase.addApplicationFont(resource_path("assets/font.ttf"))

    # Load Logo
    app_icon = QIcon(resource_path("assets/logo.ico"))
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
