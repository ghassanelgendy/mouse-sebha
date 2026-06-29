import os
import json
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPalette, QFont, QFontDatabase

from config_path import CONFIG_PATH

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("db.json")

class SebhaOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Load Arabic Font specifically for Arabic text
        self.arabic_font_family = "Segoe UI" # fallback
        font_id = QFontDatabase.addApplicationFont(resource_path("assets/font.ttf"))
        if font_id != -1:
            self.arabic_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            
        self.count = 0
        self.zikr = "سبحان الله"
        self.azkar_list = []
        
        self.mode = 'FREE'
        self.session_index = 0
        self.session_count = 0
        self.db = {"morning": [], "night": []}
        self.stats = {
            "total_free_clicks": 0,
            "morning_sessions_completed": 0,
            "night_sessions_completed": 0
        }

        self.load_config()
        self.load_db()
        
        self.zikr_index = 0
        if self.zikr in self.azkar_list:
            self.zikr_index = self.azkar_list.index(self.zikr)

        # Setup persistent geometry animation to avoid instantiation lag on hover
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.initUI()

        # Setup persistent opacity animation for smooth transitions
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(200)
        self.fade_anim.finished.connect(self.on_fade_finished)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide_overlay)
        self.hide_timer.setInterval(5000)

        # Warm up styles, layouts, and fonts to prevent lag on first hover
        self.warm_up()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.count = data.get("count", 0)
                    self.zikr = data.get("zikr", "سبحان الله")
                    self.azkar_list = data.get("azkar_list", ["سبحان الله"])
                    if "stats" in data:
                        self.stats = data["stats"]
                        
                    if self.zikr not in self.azkar_list:
                        if self.azkar_list:
                            self.zikr = self.azkar_list[0]
                            self.zikr_index = 0
                        else:
                            self.zikr = "سبحان الله"
                            self.azkar_list = ["سبحان الله"]
                            self.zikr_index = 0
                    else:
                        self.zikr_index = self.azkar_list.index(self.zikr)
            except Exception as e:
                print("Error loading config:", e)

    def load_db(self):
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            except Exception as e:
                print("Error loading db:", e)

    def save_config(self):
        try:
            current_data = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as c:
                    try:
                        current_data = json.load(c)
                    except Exception:
                        pass
            
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                current_data.update({
                    "count": self.count,
                    "zikr": self.zikr,
                    "azkar_list": self.azkar_list,
                    "stats": self.stats
                })
                json.dump(current_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Error saving config:", e)

    def get_arabic_font(self, size, bold=False):
        font = QFont(self.arabic_font_family, size)
        font.setBold(bold)
        return font
        
    def get_english_font(self, size, bold=False):
        font = QFont("Segoe UI", size)
        font.setBold(bold)
        return font

    def get_dynamic_font_size(self, text, base_size):
        length = len(text)
        if length > 300:
            return max(11, base_size - 6)
        elif length > 150:
            return max(13, base_size - 4)
        elif length > 50:
            return max(15, base_size - 2)
        return base_size

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.container = QWidget(self)
        self.container.setObjectName("glassyContainer")
        self.container.setStyleSheet("""
            #glassyContainer {
                background-color: rgba(30, 30, 30, 200);
                border-radius: 15px;
            }
        """)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.container)
        self.container.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)

        self.zikr_label = QLabel(self.zikr)
        self.zikr_label.setFont(self.get_arabic_font(18, True)) # Slightly larger for Arabic
        self.zikr_label.setStyleSheet("color: white;")
        self.zikr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zikr_label.setWordWrap(True)
        self.zikr_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        self.benefit_label = QLabel("")
        self.benefit_label.setFont(self.get_arabic_font(14, False))
        self.benefit_label.setStyleSheet("color: #AAAAAA;")
        self.benefit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.benefit_label.setWordWrap(True)
        self.benefit_label.setVisible(False)
        self.benefit_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        self.count_label = QLabel(str(self.count))
        self.count_label.setFont(self.get_english_font(20, True)) # Use English/Numbers font
        self.count_label.setStyleSheet("color: #4CAF50;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.options_container = QWidget()
        options_layout = QHBoxLayout(self.options_container)
        options_layout.setContentsMargins(0, 10, 0, 0)
        options_layout.setSpacing(8)
        options_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 40);
                color: white;
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 80);
            }
        """
        self.reset_btn = QPushButton("✖")
        self.reset_btn.setFont(self.get_english_font(12, True))
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(self.btn_style.replace("40", "80").replace("255, 255, 255", "255, 80, 80"))
        self.reset_btn.clicked.connect(self.reset_count)
        
        self.morning_btn = QPushButton("☀️")
        self.morning_btn.setFont(self.get_arabic_font(12, True))
        self.morning_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.morning_btn.setStyleSheet(self.btn_style)
        self.morning_btn.clicked.connect(lambda: self.start_session('MORNING'))
        
        self.night_btn = QPushButton("🌙")
        self.night_btn.setFont(self.get_arabic_font(12, True))
        self.night_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.night_btn.setStyleSheet(self.btn_style)
        self.night_btn.clicked.connect(lambda: self.start_session('NIGHT'))

        self.exit_btn = QPushButton("✖")
        self.exit_btn.setFont(self.get_english_font(12, True))
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.setStyleSheet(self.btn_style.replace("40", "80").replace("255, 255, 255", "255, 80, 80"))
        self.exit_btn.clicked.connect(self.exit_session)
        self.exit_btn.setVisible(False)

        self.back_btn = QPushButton("◀")
        self.back_btn.setFont(self.get_english_font(12, True))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(self.btn_style)
        self.back_btn.clicked.connect(self.next_zikr) # Left button moves forward (next)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFont(self.get_english_font(12, True))
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet(self.btn_style)
        self.next_btn.clicked.connect(self.prev_zikr) # Right button moves backward (prev)

        options_layout.addWidget(self.back_btn)
        options_layout.addWidget(self.morning_btn)
        options_layout.addWidget(self.night_btn)
        options_layout.addWidget(self.reset_btn)
        options_layout.addWidget(self.exit_btn)
        options_layout.addWidget(self.next_btn)
        
        self.options_container.setVisible(False)

        container_layout.addWidget(self.zikr_label)
        container_layout.addWidget(self.benefit_label)
        container_layout.addWidget(self.count_label)
        container_layout.addWidget(self.options_container)
        
        self.main_layout.addWidget(self.container)
        self.update_ui_state()

    def is_cursor_inside(self):
        # Robust physical cursor check to prevent synthetic animation glitches
        pos = self.mapFromGlobal(self.cursor().pos())
        return self.rect().contains(pos)

    def warm_up(self):
        # Force compilation of styles, layout generation, and font rasterization for both states
        self.options_container.setVisible(True)
        self.update_ui_state(force_hovered=True)
        self.options_container.setVisible(False)
        self.update_ui_state(force_hovered=False)

    def update_ui_state(self, force_hovered=None):
        is_hovered = force_hovered if force_hovered is not None else self.is_cursor_inside()
        
        if self.mode == 'FREE':
            if self.zikr_label.text() != self.zikr:
                self.zikr_label.setText(self.zikr)
                font_size = self.get_dynamic_font_size(self.zikr, 18)
                self.zikr_label.setFont(self.get_arabic_font(font_size, True))
                
            self.benefit_label.setVisible(False)
            self.count_label.setText(str(self.count))
            self.count_label.setStyleSheet("color: #4CAF50;")
            self.count_label.setVisible(True)
            
            self.back_btn.setVisible(True)
            self.morning_btn.setVisible(True)
            self.night_btn.setVisible(True)
            self.reset_btn.setVisible(True)
            self.exit_btn.setVisible(False)
            self.next_btn.setVisible(True)
            
            base_width = 350 if is_hovered else 250
            zikr_len = len(self.zikr)
            if zikr_len > 100:
                target_width = base_width + 120
            elif zikr_len > 50:
                target_width = base_width + 70
            else:
                target_width = base_width
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index < len(session_data):
                item = session_data[self.session_index]
                text = item.get("text", "")
                
                # Only update text and font if the zikr has actually changed
                if self.zikr_label.text() != text:
                    self.zikr_label.setText(text)
                    font_size = self.get_dynamic_font_size(text, 16)
                    self.zikr_label.setFont(self.get_arabic_font(font_size, True))
                
                benefit = item.get("benefit", "")
                if benefit and is_hovered:
                    if self.benefit_label.text() != benefit:
                        self.benefit_label.setText(benefit)
                        benefit_size = self.get_dynamic_font_size(benefit, 14)
                        self.benefit_label.setFont(self.get_arabic_font(benefit_size, False))
                    self.benefit_label.setVisible(True)
                else:
                    self.benefit_label.setVisible(False)
                    
                target = item.get("target_count", 1)
                self.count_label.setText(f"{self.session_count} / {target}")
                self.count_label.setStyleSheet("color: #2196F3;")
                if target == 1:
                    self.count_label.setVisible(False)
                else:
                    self.count_label.setVisible(True)
            else:
                self.finish_session()
                return

            self.back_btn.setVisible(True)
            self.morning_btn.setVisible(False)
            self.night_btn.setVisible(False)
            self.reset_btn.setVisible(False)
            self.exit_btn.setVisible(True)
            self.next_btn.setVisible(True)
            
            base_width = 500
            text_len = len(text)
            if text_len > 250:
                target_width = base_width + 150
            elif text_len > 150:
                target_width = base_width + 80
            else:
                target_width = base_width
            
        # Calculate width available for labels inside the container (accounting for container and main margins)
        label_width = target_width - 60
        
        # Apply the constrained width to the container and labels
        self.container.setFixedWidth(target_width - 30)
        self.zikr_label.setFixedWidth(label_width)
        self.benefit_label.setFixedWidth(label_width)
        
        # Calculate heights of all visible elements inside self.container
        container_content_height = 0
        
        # 1. zikr_label (always visible)
        zikr_h = self.zikr_label.heightForWidth(label_width)
        if zikr_h <= 0:
            zikr_h = self.zikr_label.sizeHint().height()
        container_content_height += zikr_h
        
        # 2. benefit_label (if visible)
        if self.benefit_label.isVisible() and self.benefit_label.text():
            benefit_h = self.benefit_label.heightForWidth(label_width)
            if benefit_h <= 0:
                benefit_h = self.benefit_label.sizeHint().height()
            container_content_height += 10 + benefit_h
            
        # 3. count_label (if visible)
        if self.count_label.isVisible() and self.count_label.text():
            container_content_height += 10 + self.count_label.sizeHint().height()
            
        # 4. options_container (if visible)
        if self.options_container.isVisible():
            container_content_height += 10 + self.options_container.sizeHint().height()
            
        # Add container layout top/bottom margins (15 + 15 = 30)
        hint_height = container_content_height + 30
        
        # Calculate target height (content height + main layout margins + safety padding for custom fonts)
        target_height = hint_height + 45
        
        # Enforce minimum heights for visual consistency
        if self.mode == 'FREE':
            min_height = 190 if is_hovered else 150
        else:
            min_height = 250 if is_hovered else 210
            
        target_height = max(min_height, target_height)
        self.apply_geometry(target_width, target_height)

    def apply_geometry(self, target_width, target_height):
        screen = self.screen().availableGeometry()
        x = screen.width() - target_width - 30
        y = screen.height() - target_height - 40
        
        target_rect = QRect(x, y, target_width, target_height)
        
        if self.isVisible() and self.geometry() != target_rect:
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(target_rect)
            self.anim.start()
        else:
            self.setGeometry(target_rect)

    def start_session(self, mode):
        if not self.db.get(mode.lower()):
            print(f"No data for {mode}")
            return
        self.mode = mode
        self.session_index = 0
        self.session_count = 0
        self.hide_timer.start()
        # Force text update and scroll reset by clearing labels first
        self.zikr_label.setText("")
        self.benefit_label.setText("")
        self.update_ui_state()

    def finish_session(self):
        if self.mode == 'MORNING':
            self.stats["morning_sessions_completed"] += 1
            self.log_history_event("morning_sessions")
        elif self.mode == 'NIGHT':
            self.stats["night_sessions_completed"] += 1
            self.log_history_event("night_sessions")
        self.save_config()
        self.exit_session()

    def exit_session(self):
        self.mode = 'FREE'
        self.hide_timer.start()
        # Force update by clearing text
        self.zikr_label.setText("")
        self.update_ui_state()

    def increment_count(self):
        if self.mode == 'FREE':
            self.count += 1
            self.stats["total_free_clicks"] += 1
            self.log_history_event("free_clicks")
            self.count_label.setText(str(self.count))
            self.save_config()
            self.show_overlay()
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index < len(session_data):
                target = session_data[self.session_index].get("target_count", 1)
                self.session_count += 1
                
                if self.session_count >= target:
                    self.session_index += 1
                    self.session_count = 0
                    self.update_ui_state()
                else:
                    # Index didn't change! Only update the count label. Very fast, no lag!
                    self.count_label.setText(f"{self.session_count} / {target}")
                    
                self.show_overlay()

    def reset_count(self):
        if self.mode == 'FREE':
            self.count = 0
            self.count_label.setText(str(self.count))
            self.save_config()
        
    def change_zikr(self, index_delta):
        if self.mode != 'FREE':
            return
            
        if not self.azkar_list:
            return
        self.zikr_index = (self.zikr_index + index_delta) % len(self.azkar_list)
        self.zikr = self.azkar_list[self.zikr_index]
        self.update_ui_state()
        self.save_config()

    def log_history_event(self, event_type):
        from datetime import date
        today = date.today().isoformat()
        if "history" not in self.stats:
            self.stats["history"] = {}
        if today not in self.stats["history"]:
            self.stats["history"][today] = {
                "free_clicks": 0,
                "morning_sessions": 0,
                "night_sessions": 0
            }
        self.stats["history"][today][event_type] += 1

    def on_fade_finished(self):
        if self.opacity_effect.opacity() == 0.0:
            self.hide()
            self.options_container.setVisible(False)
            self.update_ui_state()

    def show_overlay(self):
        self.hide_timer.start()
        if self.fade_anim.state() == QPropertyAnimation.State.Running and self.fade_anim.endValue() == 1.0:
            return
        if not self.isVisible():
            self.opacity_effect.setOpacity(0.0)
            self.show()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
    def hide_overlay(self):
        if not self.is_cursor_inside():
            if self.fade_anim.state() == QPropertyAnimation.State.Running and self.fade_anim.endValue() == 0.0:
                return
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def enterEvent(self, event):
        self.hide_timer.stop()
        self.options_container.setVisible(True)
        self.update_ui_state()
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_cursor_inside():
            self.options_container.setVisible(False)
            self.hide_timer.start()
            self.update_ui_state()
        super().leaveEvent(event)
        
    def wheelEvent(self, event):
        if self.is_cursor_inside():
            if event.angleDelta().y() > 0:
                self.change_zikr(-1)
            elif event.angleDelta().y() < 0:
                self.change_zikr(1)
        super().wheelEvent(event)

    def prev_zikr(self):
        if self.mode == 'FREE':
            self.change_zikr(-1)
        else:
            if self.session_index > 0:
                self.session_index -= 1
                self.session_count = 0
                self.zikr_label.setText("")
                self.benefit_label.setText("")
                self.update_ui_state()
                self.show_overlay()

    def next_zikr(self):
        if self.mode == 'FREE':
            self.change_zikr(1)
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index < len(session_data):
                self.session_index += 1
                self.session_count = 0
                self.zikr_label.setText("")
                self.benefit_label.setText("")
                self.update_ui_state()
                self.show_overlay()
