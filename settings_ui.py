import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QCheckBox,
                             QListWidget, QLineEdit, QMessageBox, QApplication,
                             QComboBox, QListWidgetItem)
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
                        # If the release exists but doesn't have the binary for our OS yet,
                        # treat it as no update found for our platform.
                        self.no_update_found.emit()
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
    import os
    
    current_exe = sys.executable
    current_pid = os.getpid()
    system_name = platform.system()
    
    # Clean PyInstaller environment variables in the parent python process environment copy
    env = os.environ.copy()
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    for key in list(env.keys()):
        if key.startswith("_PYI_") or key in ("_MEIPASS2", "_MEIPASS"):
            env.pop(key, None)
            
    if system_name == "Windows":
        # In Windows, Start-Process inside PowerShell can bypass PowerShell's environment.
        # We explicitly clear all PyInstaller environment variables inside the PowerShell session 
        # before invoking Start-Process to guarantee the child runs in a clean environment.
        ps_script = f'''
$proc = Get-Process -Id {current_pid} -ErrorAction SilentlyContinue
if ($proc) {{
    $proc.WaitForExit(5000)
}}
Remove-Item -Force "{current_exe}" -ErrorAction SilentlyContinue
Move-Item -Force "{new_exe_path}" "{current_exe}"

Remove-Item env:_MEIPASS -ErrorAction SilentlyContinue
Remove-Item env:_MEIPASS2 -ErrorAction SilentlyContinue
Get-ChildItem env:* | Where-Object {{ $_.Name -like "_PYI_*" }} | Remove-Item -ErrorAction SilentlyContinue
$env:PYINSTALLER_RESET_ENVIRONMENT = "1"

Start-Process "{current_exe}"
'''
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
    else:
        # In Unix, we do the same env cleaning inside the bash/sh shell before launching the new process.
        sh_script = f'''
sleep 2
rm -f "{current_exe}"
mv "{new_exe_path}" "{current_exe}"
chmod +x "{current_exe}"

unset _MEIPASS
unset _MEIPASS2
for var in \$(env | cut -d= -f1); do
  if [[ "\$var" =~ ^_PYI_ ]]; then
    unset "\$var"
  fi
done
export PYINSTALLER_RESET_ENVIRONMENT=1

"{current_exe}" &
'''
        subprocess.Popen(["sh", "-c", sh_script], env=env)
        
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

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def get_available_font_families(self):
        from PyQt6.QtGui import QFontDatabase
        fonts_dir = self.resource_path("assets/fonts")
        families = []
        if os.path.exists(fonts_dir):
            for filename in os.listdir(fonts_dir):
                if filename.lower().endswith((".ttf", ".otf")):
                    path = os.path.join(fonts_dir, filename)
                    font_id = QFontDatabase.addApplicationFont(path)
                    if font_id != -1:
                        fams = QFontDatabase.applicationFontFamilies(font_id)
                        if fams and fams[0] not in families:
                            families.append(fams[0])
        if not families:
            families = ["Segoe UI"]
        return families

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
        
        # Font Settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Arabic Font Family:"))
        self.font_combo = QComboBox()
        
        available_fonts = self.get_available_font_families()
        self.font_combo.addItems(available_fonts)
        
        current_font = self.config.get("font_family", "")
        if current_font in available_fonts:
            self.font_combo.setCurrentText(current_font)
        elif available_fonts:
            self.font_combo.setCurrentIndex(0)
            self.config["font_family"] = available_fonts[0]
            
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_combo)
        settings_layout.addLayout(font_layout)
        
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
        self.zikr_list_widget.itemChanged.connect(self.on_zikr_item_changed)
        for text in self.config.get("azkar_list", ["سبحان الله"]):
            self.add_editable_item(text)
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
        
        # About Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.setSpacing(12)
        about_layout.setContentsMargins(20, 20, 20, 20)
        
        app_title = QLabel("📿 Sebha")
        app_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(app_title)
        
        app_version_lbl = QLabel(f"Version: {self.current_version}")
        app_version_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        app_version_lbl.setStyleSheet("color: #888888;")
        app_version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(app_version_lbl)
        
        app_desc = QLabel(
            "Sebha is a desktop application designed to keep you connected with "
            "Dhikr and Athkar sessions (Morning/Evening) directly from your screen.\n\n"
            "Use the configured hotkey or mouse buttons to increment your count while working."
        )
        app_desc.setWordWrap(True)
        app_desc.setFont(QFont("Segoe UI", 10))
        app_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_desc.setStyleSheet("color: #bbbbbb; line-height: 1.4;")
        about_layout.addWidget(app_desc)
        
        about_layout.addStretch()
        
        github_link = QLabel('<a href="https://github.com/ghassanelgendy/mouse-sebha" style="color: #4CAF50; text-decoration: none;">GitHub Repository</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        github_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(github_link)
        
        license_lbl = QLabel("Released under the MIT License.")
        license_lbl.setFont(QFont("Segoe UI", 9))
        license_lbl.setStyleSheet("color: #666666;")
        license_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(license_lbl)
        
        tabs.addTab(about_tab, "About")
        
        layout.addWidget(tabs)

    def showEvent(self, event):
        self.load_config()
        self.update_ui_from_config()
        self.refresh_stats_ui()
        super().showEvent(event)

    def update_ui_from_config(self):
        self.startup_checkbox.blockSignals(True)
        self.autoupdate_checkbox.blockSignals(True)
        self.font_combo.blockSignals(True)
        
        # 1. Hotkey
        hotkey = self.config.get("trigger_keyboard", "")
        self.key_btn_lbl.setText(hotkey if hotkey else "None")
        
        # 2. Mouse Trigger
        mouse_trig = self.config.get("trigger_mouse", "")
        self.mouse_btn_lbl.setText(mouse_trig if mouse_trig else "None")
        
        # 3. Startup
        self.startup_checkbox.setChecked(self.check_startup())
        
        # 4. Auto Update
        self.autoupdate_checkbox.setChecked(self.config.get("auto_update", True))
        
        # 5. Font Combo
        available_fonts = self.get_available_font_families()
        current_font = self.config.get("font_family", "")
        self.font_combo.clear()
        self.font_combo.addItems(available_fonts)
        if current_font in available_fonts:
            self.font_combo.setCurrentText(current_font)
        elif available_fonts:
            self.font_combo.setCurrentIndex(0)
            self.config["font_family"] = available_fonts[0]
            
        self.startup_checkbox.blockSignals(False)
        self.autoupdate_checkbox.blockSignals(False)
        self.font_combo.blockSignals(False)

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
        
        self.zikr_list_widget.blockSignals(True)
        self.zikr_list_widget.clear()
        for text in self.config.get("azkar_list", ["سبحان الله"]):
            self.add_editable_item(text)
        self.zikr_list_widget.blockSignals(False)

    def add_editable_item(self, text):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.zikr_list_widget.addItem(item)

    def on_zikr_item_changed(self, item):
        text = item.text().strip()
        if not text:
            QMessageBox.warning(self, "Invalid Text", "Dhikr text cannot be empty.")
            self.refresh_stats_ui()
            return
            
        azkar = []
        for i in range(self.zikr_list_widget.count()):
            azkar.append(self.zikr_list_widget.item(i).text().strip())
            
        row = self.zikr_list_widget.row(item)
        if azkar.count(text) > 1:
            QMessageBox.warning(self, "Duplicate", "This Dhikr is already in your list.")
            self.refresh_stats_ui()
            return
            
        self.config["azkar_list"] = azkar
        self.save_config()

    def add_zikr_item(self):
        text = self.new_zikr_input.text().strip()
        if not text:
            return
        if text in self.config.get("azkar_list", []):
            QMessageBox.warning(self, "Duplicate", "This Dhikr is already in your list.")
            return
        self.config["azkar_list"] = self.config.get("azkar_list", []) + [text]
        
        self.zikr_list_widget.blockSignals(True)
        self.add_editable_item(text)
        self.zikr_list_widget.blockSignals(False)
        
        self.new_zikr_input.clear()
        self.save_config()
        
    def delete_zikr_item(self):
        selected = self.zikr_list_widget.currentRow()
        if selected == -1:
            return
        if self.zikr_list_widget.count() <= 1:
            QMessageBox.warning(self, "Warning", "You must keep at least one Dhikr in the list.")
            return
        
        self.zikr_list_widget.blockSignals(True)
        item = self.zikr_list_widget.takeItem(selected)
        del item
        self.zikr_list_widget.blockSignals(False)
        
        azkar = []
        for i in range(self.zikr_list_widget.count()):
            azkar.append(self.zikr_list_widget.item(i).text())
        self.config["azkar_list"] = azkar
        self.save_config()
        
    def move_zikr_up(self):
        row = self.zikr_list_widget.currentRow()
        if row <= 0:
            return
        self.zikr_list_widget.blockSignals(True)
        current_item = self.zikr_list_widget.takeItem(row)
        self.zikr_list_widget.insertItem(row - 1, current_item)
        self.zikr_list_widget.setCurrentRow(row - 1)
        self.zikr_list_widget.blockSignals(False)
        self.save_reordered_list()
        
    def move_zikr_down(self):
        row = self.zikr_list_widget.currentRow()
        if row == -1 or row >= self.zikr_list_widget.count() - 1:
            return
        self.zikr_list_widget.blockSignals(True)
        current_item = self.zikr_list_widget.takeItem(row)
        self.zikr_list_widget.insertItem(row + 1, current_item)
        self.zikr_list_widget.setCurrentRow(row + 1)
        self.zikr_list_widget.blockSignals(False)
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
        if sys.platform != "win32":
            return False
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                val, _ = winreg.QueryValueEx(key, "Sebha")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def toggle_startup(self, checked):
        if sys.platform != "win32":
            return
        
        # Clean up old shortcut if it exists to avoid duplicate launches
        try:
            startup_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_dir, 'Sebha.lnk')
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
        except Exception:
            pass

        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if checked:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                    cmd = f'"{exe_path}"'
                else:
                    pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.pyw')
                    cmd = f'"{pythonw_exe}" "{script_path}"'
                winreg.SetValueEx(key, "Sebha", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "Sebha")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print("Error toggling startup:", e)

    def toggle_autoupdate(self, checked):
        self.config["auto_update"] = checked
        self.save_config()

    def on_font_changed(self, text):
        self.config["font_family"] = text
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
