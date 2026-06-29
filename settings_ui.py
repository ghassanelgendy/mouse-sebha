import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QCheckBox,
                             QListWidget, QLineEdit, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QThread
from PyQt6.QtGui import QPainter, QColor, QFont
from pynput import mouse, keyboard

from config_path import CONFIG_PATH

class AssignButtonDialog(QDialog):
    finished_signal = pyqtSignal(str)

    def __init__(self, is_mouse=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Listening...")
        self.setFixedSize(250, 100)
        self.is_mouse = is_mouse
        self.result_value = None
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        self.label = QLabel("Press any button..." if not is_mouse else "Click any mouse button...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.finished_signal.connect(self.on_finished)
        
        self.listener = None
        if self.is_mouse:
            self.listener = mouse.Listener(on_click=self.on_mouse_click)
        else:
            self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.finished_signal.emit(str(button))
            return False # stop listener

    def on_key_press(self, key):
        try:
            k = key.char
            if k is None:
                k = str(key)
        except AttributeError:
            k = str(key)
            
        self.finished_signal.emit(k)
        return False # stop listener

    def on_finished(self, val):
        self.result_value = val
        self.accept()

    def closeEvent(self, event):
        if self.listener:
            self.listener.stop()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.listener:
                self.listener.stop()
            self.finished_signal.emit("Key.esc")
            event.accept()
        else:
            super().keyPressEvent(event)

class UpdateCheckerThread(QThread):
    update_downloaded = pyqtSignal(str)
    no_update_found = pyqtSignal()
    check_failed = pyqtSignal(str)

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
                        
                        urllib.request.urlretrieve(download_url, new_exe_path)
                        
                        if os.path.exists(new_exe_path) and os.path.getsize(new_exe_path) > 1000000:
                            self.update_downloaded.emit(new_exe_path)
                        else:
                            self.check_failed.emit("Downloaded file is empty or too small.")
                    else:
                        self.check_failed.emit(f"Could not find asset {expected_asset_name} in release.")
                else:
                    self.check_failed.emit(f"Unsupported operating system: {system_name}")
            else:
                self.no_update_found.emit()
        except Exception as e:
            self.check_failed.emit(str(e))

def apply_update_and_restart(new_exe_path):
    import subprocess
    import platform
    import sys
    
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
        sh_script = f'''
sleep 2
rm -f "{current_exe}"
mv "{new_exe_path}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
'''
        subprocess.Popen(["sh", "-c", sh_script])
        
    QApplication.quit()

class WeeklyBarChart(QWidget):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history or {}
        self.setMinimumHeight(150)
        
    def update_history(self, history):
        self.history = history or {}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate last 7 days
        from datetime import date, timedelta
        today = date.today()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        # Get data for each day
        counts = []
        for d in days:
            d_str = d.isoformat()
            day_data = self.history.get(d_str, {})
            # Activity score = free clicks + (morning_sessions * 33) + (night_sessions * 33)
            score = day_data.get("free_clicks", 0) + day_data.get("morning_sessions", 0) * 33 + day_data.get("night_sessions", 0) * 33
            counts.append((d.strftime("%a"), score))
            
        max_score = max([c[1] for c in counts] + [100]) # scale to at least 100
        
        w = self.width()
        h = self.height()
        padding_x = 25
        padding_y = 20
        chart_w = w - 2 * padding_x
        chart_h = h - 2 * padding_y - 20
        
        col_w = chart_w / 7
        bar_w = max(16, int(col_w * 0.5))
        
        for i, (day_name, score) in enumerate(counts):
            col_x = padding_x + i * col_w
            bar_h = int((score / max_score) * chart_h)
            bar_x = int(col_x + (col_w - bar_w) / 2)
            bar_y = h - padding_y - 20 - bar_h
            
            # Draw bottom line
            painter.setPen(QColor(230, 230, 230))
            painter.drawLine(padding_x, h - padding_y - 20, w - padding_x, h - padding_y - 20)
            
            if score > 0:
                painter.setBrush(QColor(76, 175, 80, 220)) # green color
            else:
                painter.setBrush(QColor(240, 240, 240)) # very light gray for zero
                bar_h = 4
                bar_y = h - padding_y - 20 - bar_h
                
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)
            
            # Draw score text on top of bar if > 0
            if score > 0:
                painter.setPen(QColor(80, 80, 80))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(QRect(bar_x - 15, bar_y - 18, bar_w + 30, 18), Qt.AlignmentFlag.AlignCenter, str(score))
                
            # Draw day name
            painter.setPen(QColor(130, 130, 130))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRect(int(col_x), h - padding_y - 15, int(col_w), 20), Qt.AlignmentFlag.AlignCenter, day_name)

def calculate_streak(history):
    from datetime import date, timedelta
    if not history:
        return 0
    today = date.today()
    streak = 0
    current_date = today
    
    # Check if active today
    today_data = history.get(today.isoformat(), {})
    today_active = (today_data.get("free_clicks", 0) > 0 or 
                    today_data.get("morning_sessions", 0) > 0 or 
                    today_data.get("night_sessions", 0) > 0)
                    
    # If not active today, check if active yesterday (streak might be active until yesterday if today is not over yet)
    if not today_active:
        current_date = today - timedelta(days=1)
        
    while True:
        d_str = current_date.isoformat()
        day_data = history.get(d_str, {})
        is_active = (day_data.get("free_clicks", 0) > 0 or 
                     day_data.get("morning_sessions", 0) > 0 or 
                     day_data.get("night_sessions", 0) > 0)
        if is_active:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
            
    return streak

class SettingsDialog(QDialog):
    config_updated = pyqtSignal()
    
    def __init__(self, current_version="1.0.0", parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.setWindowTitle("Sebha Settings")
        self.setFixedSize(450, 400)
        
        self.config = {}
        self.load_config()
        
        self.initUI()
        
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print("Error loading config in settings:", e)
                self.config = {}

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
        self.config_updated.emit()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # Settings Tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Triggers
        trigger_layout = QVBoxLayout()
        
        # Mouse Trigger
        mouse_layout = QHBoxLayout()
        mouse_layout.addWidget(QLabel("Mouse Button:"))
        trigger_m = self.config.get("trigger_mouse", "Button.x2")
        self.mouse_btn_lbl = QLabel(trigger_m if trigger_m else "None")
        mouse_layout.addWidget(self.mouse_btn_lbl)
        self.assign_mouse_btn = QPushButton("Assign")
        self.assign_mouse_btn.clicked.connect(self.assign_mouse)
        mouse_layout.addWidget(self.assign_mouse_btn)
        trigger_layout.addLayout(mouse_layout)
        
        # Keyboard Trigger
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Keyboard Key:"))
        self.key_btn_lbl = QLabel(self.config.get("trigger_keyboard", "None"))
        if not self.key_btn_lbl.text(): self.key_btn_lbl.setText("None")
        key_layout.addWidget(self.key_btn_lbl)
        self.assign_key_btn = QPushButton("Assign")
        self.assign_key_btn.clicked.connect(self.assign_keyboard)
        key_layout.addWidget(self.assign_key_btn)
        trigger_layout.addLayout(key_layout)
        
        settings_layout.addLayout(trigger_layout)
        
        # Startup Settings
        self.startup_checkbox = QCheckBox("Run at Windows Startup")
        self.startup_checkbox.setChecked(self.check_startup())
        self.startup_checkbox.toggled.connect(self.toggle_startup)
        settings_layout.addWidget(self.startup_checkbox)
        
        # Auto Update Settings
        self.autoupdate_checkbox = QCheckBox("Enable Automatic Updates")
        self.autoupdate_checkbox.setChecked(self.config.get("auto_update", True))
        self.autoupdate_checkbox.toggled.connect(self.toggle_autoupdate)
        settings_layout.addWidget(self.autoupdate_checkbox)
        
        # Check for Updates Button
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.clicked.connect(self.manual_update_check)
        settings_layout.addWidget(self.update_btn)
        
        settings_layout.addStretch()
        tabs.addTab(settings_tab, "Settings")
        
        # Stats Tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats = self.config.get("stats", {})
        free_clicks = stats.get("total_free_clicks", 0)
        mornings = stats.get("morning_sessions_completed", 0)
        nights = stats.get("night_sessions_completed", 0)
        history = stats.get("history", {})
        
        # Streak Banner
        streak = calculate_streak(history)
        self.streak_label = QLabel(f"🔥 Dhikr Streak: {streak} Day{'s' if streak != 1 else ''}")
        self.streak_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800; margin-bottom: 5px;")
        stats_layout.addWidget(self.streak_label)
        
        # Lifetime Grid layout
        lifetime_layout = QHBoxLayout()
        
        self.lbl_f = QLabel(f"Free Clicks\n{free_clicks}")
        self.lbl_f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_f.setStyleSheet("background-color: #E8F5E9; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: bold; color: #2E7D32;")
        
        self.lbl_m = QLabel(f"Morning Sessions\n{mornings}")
        self.lbl_m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_m.setStyleSheet("background-color: #E3F2FD; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: bold; color: #1565C0;")
        
        self.lbl_n = QLabel(f"Night Sessions\n{nights}")
        self.lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_n.setStyleSheet("background-color: #FFF3E0; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: bold; color: #E65100;")
        
        lifetime_layout.addWidget(self.lbl_f)
        lifetime_layout.addWidget(self.lbl_m)
        lifetime_layout.addWidget(self.lbl_n)
        stats_layout.addLayout(lifetime_layout)
        
        # Weekly Activity Chart
        chart_title = QLabel("Weekly Activity (Points)")
        chart_title.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 10px; color: #555555;")
        stats_layout.addWidget(chart_title)
        
        self.chart = WeeklyBarChart(history, self)
        stats_layout.addWidget(self.chart)
        
        stats_layout.addStretch()
        tabs.addTab(stats_tab, "Statistics")
        
        # Dhikr Editor Tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        
        self.zikr_list_widget = QListWidget()
        self.zikr_list_widget.addItems(self.config.get("azkar_list", ["سبحان الله"]))
        editor_layout.addWidget(self.zikr_list_widget)
        
        add_layout = QHBoxLayout()
        self.new_zikr_input = QLineEdit()
        self.new_zikr_input.setPlaceholderText("Enter new Dhikr text...")
        add_layout.addWidget(self.new_zikr_input)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_zikr_item)
        add_layout.addWidget(add_btn)
        editor_layout.addLayout(add_layout)
        
        ctrl_layout = QHBoxLayout()
        
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(self.move_zikr_up)
        ctrl_layout.addWidget(up_btn)
        
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(self.move_zikr_down)
        ctrl_layout.addWidget(down_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: rgba(255, 80, 80, 200); color: white;")
        delete_btn.clicked.connect(self.delete_zikr_item)
        ctrl_layout.addWidget(delete_btn)
        
        editor_layout.addLayout(ctrl_layout)
        tabs.addTab(editor_tab, "Dhikr Editor")
        
        layout.addWidget(tabs)

    def showEvent(self, event):
        self.load_config()
        self.refresh_stats_ui()
        super().showEvent(event)

    def refresh_stats_ui(self):
        stats = self.config.get("stats", {})
        free_clicks = stats.get("total_free_clicks", 0)
        mornings = stats.get("morning_sessions_completed", 0)
        nights = stats.get("night_sessions_completed", 0)
        history = stats.get("history", {})
        
        self.lbl_f.setText(f"Free Clicks\n{free_clicks}")
        self.lbl_m.setText(f"Morning Sessions\n{mornings}")
        self.lbl_n.setText(f"Night Sessions\n{nights}")
        
        streak = calculate_streak(history)
        self.streak_label.setText(f"🔥 Dhikr Streak: {streak} Day{'s' if streak != 1 else ''}")
        self.chart.update_history(history)
        
        self.zikr_list_widget.clear()
        self.zikr_list_widget.addItems(self.config.get("azkar_list", ["سبحان الله"]))

    def add_zikr_item(self):
        text = self.new_zikr_input.text().strip()
        if not text:
            return
        if text in self.config.get("azkar_list", []):
            QMessageBox.warning(self, "Duplicate", "This Dhikr is already in your list.")
            return
        self.config["azkar_list"] = self.config.get("azkar_list", []) + [text]
        self.zikr_list_widget.addItem(text)
        self.new_zikr_input.clear()
        self.save_config()
        
    def delete_zikr_item(self):
        selected = self.zikr_list_widget.currentRow()
        if selected == -1:
            return
        if self.zikr_list_widget.count() <= 1:
            QMessageBox.warning(self, "Warning", "You must keep at least one Dhikr in the list.")
            return
        
        item = self.zikr_list_widget.takeItem(selected)
        del item
        
        azkar = []
        for i in range(self.zikr_list_widget.count()):
            azkar.append(self.zikr_list_widget.item(i).text())
        self.config["azkar_list"] = azkar
        self.save_config()
        
    def move_zikr_up(self):
        row = self.zikr_list_widget.currentRow()
        if row <= 0:
            return
        current_item = self.zikr_list_widget.takeItem(row)
        self.zikr_list_widget.insertItem(row - 1, current_item)
        self.zikr_list_widget.setCurrentRow(row - 1)
        self.save_reordered_list()
        
    def move_zikr_down(self):
        row = self.zikr_list_widget.currentRow()
        if row == -1 or row >= self.zikr_list_widget.count() - 1:
            return
        current_item = self.zikr_list_widget.takeItem(row)
        self.zikr_list_widget.insertItem(row + 1, current_item)
        self.zikr_list_widget.setCurrentRow(row + 1)
        self.save_reordered_list()
        
    def save_reordered_list(self):
        azkar = []
        for i in range(self.zikr_list_widget.count()):
            azkar.append(self.zikr_list_widget.item(i).text())
        self.config["azkar_list"] = azkar
        self.save_config()

    def assign_mouse(self):
        d = AssignButtonDialog(is_mouse=True, parent=self)
        if d.exec():
            val = d.result_value if (d.result_value and d.result_value != "Key.esc") else ""
            self.config["trigger_mouse"] = val
            self.mouse_btn_lbl.setText(val if val else "None")
            self.save_config()

    def assign_keyboard(self):
        d = AssignButtonDialog(is_mouse=False, parent=self)
        if d.exec():
            val = d.result_value if (d.result_value and d.result_value != "Key.esc") else ""
            self.config["trigger_keyboard"] = val
            self.key_btn_lbl.setText(val if val else "None")
            self.save_config()

    def check_startup(self):
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        return os.path.exists(os.path.join(startup_dir, 'Sebha.lnk'))

    def toggle_startup(self, checked):
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_dir, 'Sebha.lnk')
        if checked:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                working_dir = os.path.dirname(exe_path)
                ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Save()
'''
            else:
                pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                script_path = os.path.abspath('main.pyw')
                working_dir = os.path.abspath('.')
                ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{pythonw_exe}"
$Shortcut.Arguments = '"{script_path}"'
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Save()
'''
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

    def toggle_autoupdate(self, checked):
        self.config["auto_update"] = checked
        self.save_config()

    def manual_update_check(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Checking...")
        
        self.manual_updater = UpdateCheckerThread(self.current_version)
        
        def on_downloaded(new_exe_path):
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Check for Updates")
            msg = QMessageBox(self)
            msg.setWindowTitle("Update Available")
            msg.setText("A new update has been downloaded successfully!")
            msg.setInformativeText("The application will restart to apply the update.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            apply_update_and_restart(new_exe_path)
            
        def on_no_update():
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Check for Updates")
            msg = QMessageBox(self)
            msg.setWindowTitle("Up to Date")
            msg.setText("You are running the latest version!")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
        def on_failed(err_msg):
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Check for Updates")
            msg = QMessageBox(self)
            msg.setWindowTitle("Check Failed")
            msg.setText(f"Failed to check for updates:\n{err_msg}")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
        self.manual_updater.update_downloaded.connect(on_downloaded)
        self.manual_updater.no_update_found.connect(on_no_update)
        self.manual_updater.check_failed.connect(on_failed)
        self.manual_updater.start()
