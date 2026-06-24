import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QWidget, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from pynput import mouse, keyboard

CONFIG_PATH = "config.json"

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

class SettingsDialog(QDialog):
    config_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sebha Settings")
        self.setFixedSize(400, 300)
        
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
        self.mouse_btn_lbl = QLabel(self.config.get("trigger_mouse", "Button.x2"))
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
        
        settings_layout.addStretch()
        tabs.addTab(settings_tab, "Settings")
        
        # Stats Tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats = self.config.get("stats", {})
        free_clicks = stats.get("total_free_clicks", 0)
        mornings = stats.get("morning_sessions_completed", 0)
        nights = stats.get("night_sessions_completed", 0)
        
        lbl_f = QLabel(f"Total Free Clicks: {free_clicks}")
        lbl_f.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(lbl_f)
        
        lbl_m = QLabel(f"Morning Sessions Completed: {mornings}")
        lbl_m.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(lbl_m)
        
        lbl_n = QLabel(f"Night Sessions Completed: {nights}")
        lbl_n.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(lbl_n)
        
        stats_layout.addStretch()
        
        tabs.addTab(stats_tab, "Statistics")
        
        layout.addWidget(tabs)

    def assign_mouse(self):
        d = AssignButtonDialog(is_mouse=True, parent=self)
        if d.exec():
            if d.result_value:
                self.config["trigger_mouse"] = d.result_value
                self.mouse_btn_lbl.setText(d.result_value)
                self.save_config()

    def assign_keyboard(self):
        d = AssignButtonDialog(is_mouse=False, parent=self)
        if d.exec():
            if d.result_value:
                self.config["trigger_keyboard"] = d.result_value
                self.key_btn_lbl.setText(d.result_value)
                self.save_config()

    def check_startup(self):
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        return os.path.exists(os.path.join(startup_dir, 'Sebha.lnk'))

    def toggle_startup(self, checked):
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_dir, 'Sebha.lnk')
        if checked:
            pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            script_path = os.path.abspath('main.py')
            working_dir = os.path.abspath('.')
            ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{pythonw_exe}"
$Shortcut.Arguments = '"{script_path}"'
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Save()
'''
            subprocess.run(["powershell", "-Command", ps_script])
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
