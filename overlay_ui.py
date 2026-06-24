import os
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QPalette, QFont, QFontDatabase

CONFIG_PATH = "config.json"
DB_PATH = "db.json"

class SebhaOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Load Arabic Font specifically for Arabic text
        self.arabic_font_family = "Segoe UI" # fallback
        font_id = QFontDatabase.addApplicationFont("font.ttf")
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

        self.initUI()
        
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide_overlay)
        self.hide_timer.setInterval(5000)

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
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.zikr_label = QLabel(self.zikr)
        self.zikr_label.setFont(self.get_arabic_font(18, True)) # Slightly larger for Arabic
        self.zikr_label.setStyleSheet("color: white;")
        self.zikr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zikr_label.setWordWrap(True)
        
        self.benefit_label = QLabel("")
        self.benefit_label.setFont(self.get_arabic_font(14, False))
        self.benefit_label.setStyleSheet("color: #AAAAAA;")
        self.benefit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.benefit_label.setWordWrap(True)
        self.benefit_label.setVisible(False)
        
        self.count_label = QLabel(str(self.count))
        self.count_label.setFont(self.get_english_font(36, True)) # Use English/Numbers font
        self.count_label.setStyleSheet("color: #4CAF50;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.options_container = QWidget()
        options_layout = QHBoxLayout(self.options_container)
        options_layout.setContentsMargins(0, 10, 0, 0)
        options_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 40);
                color: white;
                border-radius: 5px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 80);
            }
        """
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFont(self.get_english_font(11, True))
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(self.btn_style.replace("40", "80").replace("255, 255, 255", "255, 80, 80"))
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reset_btn.clicked.connect(self.reset_count)
        
        self.morning_btn = QPushButton("☀️ أذكار الصباح")
        self.morning_btn.setFont(self.get_arabic_font(11, True))
        self.morning_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.morning_btn.setStyleSheet(self.btn_style)
        self.morning_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.morning_btn.clicked.connect(lambda: self.start_session('MORNING'))
        
        self.night_btn = QPushButton("🌙 أذكار المساء")
        self.night_btn.setFont(self.get_arabic_font(11, True))
        self.night_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.night_btn.setStyleSheet(self.btn_style)
        self.night_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.night_btn.clicked.connect(lambda: self.start_session('NIGHT'))

        self.exit_btn = QPushButton("Exit Session")
        self.exit_btn.setFont(self.get_english_font(11, True))
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.setStyleSheet(self.btn_style.replace("40", "80").replace("255, 255, 255", "255, 80, 80"))
        self.exit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.exit_btn.clicked.connect(self.exit_session)
        self.exit_btn.setVisible(False)

        options_layout.addWidget(self.morning_btn)
        options_layout.addWidget(self.night_btn)
        options_layout.addWidget(self.reset_btn)
        options_layout.addWidget(self.exit_btn)
        
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

    def update_ui_state(self):
        is_hovered = self.is_cursor_inside()
        
        if self.mode == 'FREE':
            if self.zikr_label.text() != self.zikr:
                self.zikr_label.setText(self.zikr)
                font_size = self.get_dynamic_font_size(self.zikr, 18)
                self.zikr_label.setFont(self.get_arabic_font(font_size, True))
                
            self.benefit_label.setVisible(False)
            self.count_label.setText(str(self.count))
            self.count_label.setStyleSheet("color: #4CAF50;")
            
            self.morning_btn.setVisible(True)
            self.night_btn.setVisible(True)
            self.reset_btn.setVisible(True)
            self.exit_btn.setVisible(False)
            
            target_width = 350 if is_hovered else 250
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
                if benefit:
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
            else:
                self.finish_session()
                return

            self.morning_btn.setVisible(False)
            self.night_btn.setVisible(False)
            self.reset_btn.setVisible(False)
            self.exit_btn.setVisible(True)
            
            target_width = 500
            
        # Temporarily restrict container width so layout computes proper height-for-width word wrap
        self.container.setFixedWidth(target_width - 30)
        self.container.layout().activate()
        hint_height = self.container.layout().sizeHint().height()
        
        # Calculate target height (content height + main layout margins)
        target_height = hint_height + 30
        
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
        
        from PyQt6.QtCore import QRect, QPropertyAnimation, QEasingCurve
        target_rect = QRect(x, y, target_width, target_height)
        
        if self.isVisible() and self.geometry() != target_rect:
            self.anim = QPropertyAnimation(self, b"geometry")
            self.anim.setDuration(250)
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(target_rect)
            self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
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
        self.hide_timer.stop()
        # Force text update and scroll reset by clearing labels first
        self.zikr_label.setText("")
        self.benefit_label.setText("")
        self.update_ui_state()

    def finish_session(self):
        if self.mode == 'MORNING':
            self.stats["morning_sessions_completed"] += 1
        elif self.mode == 'NIGHT':
            self.stats["night_sessions_completed"] += 1
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

    def show_overlay(self):
        self.show()
        if self.mode == 'FREE':
            self.hide_timer.start()
        else:
            self.hide_timer.stop()
        
    def hide_overlay(self):
        if self.mode != 'FREE':
            return
            
        if not self.is_cursor_inside():
            self.hide()
            self.options_container.setVisible(False)
            self.update_ui_state()

    def enterEvent(self, event):
        self.hide_timer.stop()
        self.options_container.setVisible(True)
        self.update_ui_state()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_cursor_inside():
            self.options_container.setVisible(False)
            if self.mode == 'FREE':
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
