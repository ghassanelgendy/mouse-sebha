import os
import json
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QColor, QPalette, QFont, QFontDatabase

from config_path import CONFIG_PATH
import notification_manager

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("db.json")

class HoverAreaWidget(QWidget):
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        # Draw completely transparent but hit-test opaque color (1/255 alpha)
        # Using native painting ensures it composites perfectly and remains 100% transparent
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

class SebhaOverlay(QWidget):
    open_settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self._overlay_opacity = 1.0
        self.is_mouse_hovered = False

        # Ensure fonts directory exists and download/migrate fonts
        self.ensure_fonts_dir_setup()
        
        # Load all fonts in assets/fonts/
        self.loaded_font_families = []
        fonts_dir = resource_path("assets/fonts")
        if os.path.exists(fonts_dir):
            for filename in os.listdir(fonts_dir):
                if filename.lower().endswith((".ttf", ".otf")):
                    path = os.path.join(fonts_dir, filename)
                    font_id = QFontDatabase.addApplicationFont(path)
                    if font_id != -1:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        if families:
                            self.loaded_font_families.append(families[0])
                            
        self.font_family = ""
        self.overlay_position = "Bottom-Right"
        self.display_mode = "overlay"
            
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

        self.is_bg_light = False

        self.initUI()

        # Setup persistent opacity animation on custom property for universal Wayland/X11 support
        self.fade_anim = QPropertyAnimation(self, b"overlay_opacity")
        self.fade_anim.setDuration(200)
        self.fade_anim.finished.connect(self.on_fade_finished)
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide_overlay)
        self.hide_timer.setInterval(5000)
        
        self.hover_timer = QTimer(self)
        self.hover_timer.setInterval(100)
        self.hover_timer.timeout.connect(self.check_hover_zones)

        # Detect initial background brightness
        self.detect_background_brightness()

        # Warm up styles, layouts, and fonts to prevent lag on first hover
        self.warm_up()

    def get_overlay_opacity(self):
        return getattr(self, "_overlay_opacity", 1.0)
        
    def set_overlay_opacity(self, val):
        self._overlay_opacity = val
        self.apply_opacity_to_widgets(val)
        
    overlay_opacity = pyqtProperty(float, get_overlay_opacity, set_overlay_opacity)

    def apply_opacity_to_widgets(self, val):
        bg_alpha = int(200 * val)
        text_alpha = int(255 * val)
        subtext_alpha = int(170 * val)
        
        if hasattr(self, 'container'):
            self.container.setStyleSheet(f"""
                #glassyContainer {{
                    background-color: rgba(30, 30, 30, {bg_alpha});
                    border-radius: 15px;
                }}
            """)
        if hasattr(self, 'zikr_label'):
            self.zikr_label.setStyleSheet(f"color: rgba(255, 255, 255, {text_alpha}); background: transparent;")
        if hasattr(self, 'benefit_label'):
            self.benefit_label.setStyleSheet(f"color: rgba(170, 170, 170, {subtext_alpha}); background: transparent;")
        if hasattr(self, 'count_label'):
            if self.count_label.text() == "حديث شريف":
                self.count_label.setStyleSheet(f"color: rgba(255, 152, 0, {text_alpha}); background: transparent;")
            elif "/" in self.count_label.text():
                self.count_label.setStyleSheet(f"color: rgba(33, 150, 243, {text_alpha}); background: transparent;")
            else:
                self.count_label.setStyleSheet(f"color: rgba(76, 175, 80, {text_alpha}); background: transparent;")
        if hasattr(self, 'upper_widget'):
            self.update_button_styles()

    def ensure_fonts_dir_setup(self):
        fonts_dir = resource_path("assets/fonts")
        os.makedirs(fonts_dir, exist_ok=True)
        
        # Migrate font.ttf if it exists in assets/
        old_font_path = resource_path("assets/font.ttf")
        new_font_path = os.path.join(fonts_dir, "font.ttf")
        if os.path.exists(old_font_path) and not os.path.exists(new_font_path):
            try:
                import shutil
                shutil.move(old_font_path, new_font_path)
                print("Migrated default font to assets/fonts/")
            except Exception as e:
                print("Failed to move default font:", e)
                
        # Migrate cairo.ttf if it exists in assets/
        old_cairo_path = resource_path("assets/cairo.ttf")
        new_cairo_path = os.path.join(fonts_dir, "cairo.ttf")
        if os.path.exists(old_cairo_path) and not os.path.exists(new_cairo_path):
            try:
                import shutil
                shutil.move(old_cairo_path, new_cairo_path)
                print("Migrated Cairo font to assets/fonts/")
            except Exception as e:
                print("Failed to move Cairo font:", e)
                
        # If cairo.ttf is missing, download it to assets/fonts/cairo.ttf
        if not os.path.exists(new_cairo_path):
            self.download_cairo_font()

    def download_cairo_font(self):
        fonts_dir = resource_path("assets/fonts")
        os.makedirs(fonts_dir, exist_ok=True)
        cairo_path = os.path.join(fonts_dir, "cairo.ttf")
        if not os.path.exists(cairo_path):
            import urllib.request
            try:
                url = "https://raw.githubusercontent.com/google/fonts/main/ofl/cairo/Cairo%5Bslnt%2Cwght%5D.ttf"
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req) as response, open(cairo_path, 'wb') as out_file:
                    out_file.write(response.read())
                print("Downloaded Cairo font successfully.")
            except Exception as e:
                print("Failed to download Cairo font:", e)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.count = data.get("count", 0)
                    self.zikr = data.get("zikr", "سبحان الله")
                    self.azkar_list = data.get("azkar_list", ["سبحان الله"])
                    self.font_family = data.get("font_family", "Default")
                    self.overlay_position = data.get("overlay_position", "Bottom-Right")
                    self.display_mode = data.get("display_mode", "overlay")
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
                if hasattr(self, "zikr_label"):
                    self.update_ui_state()
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
                    "font_family": self.font_family,
                    "overlay_position": self.overlay_position,
                    "display_mode": getattr(self, "display_mode", "overlay"),
                    "stats": self.stats
                })
                json.dump(current_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Error saving config:", e)

    def get_current_arabic_font_family(self):
        if hasattr(self, 'font_family') and self.font_family and self.font_family != "Default":
            if self.font_family in self.loaded_font_families:
                return self.font_family
        if hasattr(self, 'loaded_font_families') and self.loaded_font_families:
            if "Cairo" in self.loaded_font_families:
                return "Cairo"
            return self.loaded_font_families[0]
        return "Segoe UI"

    def get_arabic_font(self, size, bold=False):
        font = QFont(self.get_current_arabic_font_family(), size)
        font.setBold(bold)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferOutline | QFont.StyleStrategy.PreferQuality)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        return font
        
    def get_english_font(self, size, bold=False):
        font = QFont("Segoe UI", size)
        font.setBold(bold)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferOutline | QFont.StyleStrategy.PreferQuality)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
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
        self.main_layout.setSpacing(10)

        # Upper widget for options
        self.upper_widget = HoverAreaWidget(self)
        self.upper_widget.setFixedHeight(40)
        upper_layout = QHBoxLayout(self.upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.setSpacing(0)
        upper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.trigger_circle = QPushButton("⚙️", self.upper_widget)
        self.trigger_circle.setFont(self.get_english_font(12))
        self.trigger_circle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.trigger_circle.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 30, 30, 180);
                color: white;
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        upper_layout.addWidget(self.trigger_circle)
        
        self.options_container = QWidget(self.upper_widget)
        options_layout = QHBoxLayout(self.options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)
        options_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upper_layout.addWidget(self.options_container)

        self.main_layout.addWidget(self.upper_widget)

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
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)

        self.zikr_label = QLabel(self.zikr)
        self.zikr_label.setFont(self.get_arabic_font(18, True)) # Slightly larger for Arabic
        self.zikr_label.setStyleSheet("color: white;")
        self.zikr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zikr_label.setWordWrap(True)
        self.zikr_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.zikr_label.mouseDoubleClickEvent = self.copy_zikr_to_clipboard
        
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
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFont(self.get_english_font(12, True))
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(self.btn_style)
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

        self.hide_btn = QPushButton("👁️")
        self.hide_btn.setFont(self.get_english_font(12, True))
        self.hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide_btn.setStyleSheet(self.btn_style)
        self.hide_btn.clicked.connect(self.hide_overlay_instantly)

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

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFont(self.get_english_font(12, True))
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet(self.btn_style)
        self.settings_btn.clicked.connect(self.open_settings_requested.emit)

        self.trigger_circle.clicked.connect(self.open_settings_requested.emit)

        self.hadith_btn = QPushButton("📖")
        self.hadith_btn.setFont(self.get_arabic_font(12, True))
        self.hadith_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hadith_btn.setStyleSheet(self.btn_style)
        self.hadith_btn.clicked.connect(lambda: self.start_session('HADITH'))

        options_layout.addWidget(self.back_btn)
        options_layout.addWidget(self.morning_btn)
        options_layout.addWidget(self.night_btn)
        options_layout.addWidget(self.hadith_btn)
        options_layout.addWidget(self.reset_btn)
        options_layout.addWidget(self.settings_btn)
        options_layout.addWidget(self.exit_btn)
        options_layout.addWidget(self.hide_btn)
        options_layout.addWidget(self.next_btn)
        self.trigger_circle.setVisible(False)
        self.options_container.setVisible(False)

        container_layout.addWidget(self.zikr_label)
        container_layout.addWidget(self.benefit_label)
        container_layout.addWidget(self.count_label)
        
        self.main_layout.addWidget(self.container)
        self.update_ui_state()

    def is_cursor_inside(self):
        if not self.isVisible():
            return False
        return getattr(self, "is_mouse_hovered", False) or self.underMouse()

    def warm_up(self):
        # Force compilation of styles, layout generation, and font rasterization
        self.show_options_bar()
        self.update_ui_state()
        self.hide_options_bar()

    def update_ui_state(self, animate=True):
        is_hovered = self.is_cursor_inside()
        
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
            self.hide_btn.setVisible(True)
            
            target_width = 400
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index < len(session_data):
                item = session_data[self.session_index]
                text = item.get("text", "")
                
                # We always calculate the zikr font size so we can base the benefit size on it
                font_size = self.get_dynamic_font_size(text, 16)
                if self.zikr_label.text() != text:
                    self.zikr_label.setText(text)
                self.zikr_label.setFont(self.get_arabic_font(font_size, True))
                
                benefit = item.get("benefit", "")
                if benefit and is_hovered:
                    if self.benefit_label.text() != benefit:
                        self.benefit_label.setText(benefit)
                    benefit_size = font_size - 4
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
            self.hide_btn.setVisible(True)
            
            target_width = 500
            
        # Calculate width available for labels inside the container (accounting for container and main margins)
        label_width = target_width - 60
        
        # Apply the constrained width to the container and labels
        self.container.setFixedWidth(target_width - 30)
        self.upper_widget.setFixedWidth(target_width - 30)
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
            
        # Add container layout top/bottom margins (15 + 15 = 30)
        hint_height = container_content_height + 30
        
        # Calculate target height (content height + upper_widget height 40 + layout spacing 10 + main margins 30)
        target_height = hint_height + 80
        
        # Enforce minimum heights for visual consistency
        if self.mode == 'FREE':
            min_height = 160
        else:
            min_height = 220
            
        target_height = max(min_height, target_height)
        self.apply_geometry(target_width, target_height, animate=animate)

    def get_active_screen(self):
        try:
            from pynput.mouse import Controller
            mx, my = Controller().position
            m_point = QPoint(int(mx), int(my))
            
            # Check bounding box of all screens in logical space
            for s in QApplication.screens():
                if s.geometry().contains(m_point):
                    return s

            # Check screenAt
            screen = QApplication.screenAt(m_point)
            if screen:
                return screen
                    
            # Nearest screen center distance fallback
            best_screen = None
            min_dist = float('inf')
            for s in QApplication.screens():
                g = s.geometry()
                cx = g.x() + g.width() // 2
                cy = g.y() + g.height() // 2
                dist = (mx - cx) ** 2 + (my - cy) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best_screen = s
            if best_screen:
                return best_screen
        except Exception:
            pass
            
        try:
            cpos = self.cursor().pos()
            if cpos != QPoint(0, 0):
                screen = QApplication.screenAt(cpos)
                if screen:
                    return screen
        except Exception:
            pass
            
        return self.screen() or QApplication.primaryScreen()

    def apply_geometry(self, target_width, target_height, animate=True):
        screen_obj = self.get_active_screen()
        screen = screen_obj.availableGeometry()
        pos_setting = getattr(self, "overlay_position", "Bottom-Right")
        
        if pos_setting == "Top-Left":
            x = screen.x() + 30
            y = screen.y() + 40
        elif pos_setting == "Top-Center":
            x = screen.x() + (screen.width() - target_width) // 2
            y = screen.y() + 40
        elif pos_setting == "Top-Right":
            x = screen.x() + screen.width() - target_width - 30
            y = screen.y() + 40
        elif pos_setting == "Bottom-Left":
            x = screen.x() + 30
            y = screen.y() + screen.height() - target_height - 40
        elif pos_setting == "Bottom-Center":
            x = screen.x() + (screen.width() - target_width) // 2
            y = screen.y() + screen.height() - target_height - 40
        else: # Bottom-Right (default)
            x = screen.x() + screen.width() - target_width - 30
            y = screen.y() + screen.height() - target_height - 40
            
        target_rect = QRect(x, y, target_width, target_height)
        
        if self.windowHandle():
            self.windowHandle().setScreen(screen_obj)

        if self.geometry() != target_rect:
            self.detect_background_brightness(x, y, target_width, target_height)
            
        if animate and self.isVisible() and self.geometry() != target_rect:
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(target_rect)
            self.anim.start()
        else:
            self.setGeometry(target_rect)

    def toggle_session(self, mode):
        """Toggle session: switch to requested mode, or exit to FREE if already active."""
        if self.mode == mode:
            self.exit_session()
        else:
            self.start_session(mode)

    def start_session(self, mode):
        session_data = self.db.get(mode.lower(), [])
        if not session_data:
            print(f"No data for {mode}")
            return
            
        show_overlay_ui = getattr(self, "display_mode", "overlay") in ("overlay", "both")
        send_native_notify = getattr(self, "display_mode", "overlay") in ("notification", "both")
            
        def perform_change():
            self.mode = mode
            self.session_index = 0
            self.session_count = 0
            self.zikr_label.setText("")
            self.benefit_label.setText("")
            if show_overlay_ui:
                self.show_overlay()
            
        if show_overlay_ui:
            self.transition_to_zikr(perform_change)
        else:
            self.mode = mode
            self.session_index = 0
            self.session_count = 0
            
        if send_native_notify and session_data:
            first_item = session_data[0]
            notification_manager.notify_count(
                zikr=first_item.get("text", ""),
                count=0,
                target=first_item.get("target_count", 1),
                benefit=first_item.get("benefit", ""),
                mode=mode
            )

    def finish_session(self):
        send_native_notify = getattr(self, "display_mode", "overlay") in ("notification", "both")
        if send_native_notify:
            notification_manager.notify_session_completed(self.mode)
            
        if self.mode == 'MORNING':
            self.stats["morning_sessions_completed"] += 1
            self.log_history_event("morning_sessions")
        elif self.mode == 'NIGHT':
            self.stats["night_sessions_completed"] += 1
            self.log_history_event("night_sessions")
        self.save_config()
        self.exit_session()

    def exit_session(self):
        show_overlay_ui = getattr(self, "display_mode", "overlay") in ("overlay", "both")
        send_native_notify = getattr(self, "display_mode", "overlay") in ("notification", "both")
        
        self.mode = 'FREE'
        self.session_index = 0
        self.session_count = 0
        
        if send_native_notify:
            notification_manager.notify_count(
                zikr=self.zikr,
                count=self.count,
                mode='FREE'
            )
            
        if show_overlay_ui:
            def perform_change():
                self.zikr_label.setText("")
                self.benefit_label.setText("")
                self.show_overlay()
            self.transition_to_zikr(perform_change)

    def show_hadith_notification(self, hadith_item=None):
        if not hadith_item:
            hadiths = self.db.get("hadith", [])
            if not hadiths:
                return
            import random
            hadith_item = random.choice(hadiths[:min(100, len(hadiths))])

        show_overlay_ui = getattr(self, "display_mode", "overlay") in ("overlay", "both")
        send_native_notify = getattr(self, "display_mode", "overlay") in ("notification", "both")

        if send_native_notify:
            notification_manager.notify_hadith(
                text=hadith_item.get("text", ""),
                benefit=hadith_item.get("benefit", "")
            )

        if show_overlay_ui:
            def perform_change():
                text = hadith_item.get("text", "")
                benefit = hadith_item.get("benefit", "")
                
                font_size = self.get_dynamic_font_size(text, 16)
                self.zikr_label.setText(text)
                self.zikr_label.setFont(self.get_arabic_font(font_size, True))
                
                if benefit:
                    self.benefit_label.setText(f"📖 {benefit}")
                    self.benefit_label.setFont(self.get_arabic_font(max(12, font_size - 4), False))
                    self.benefit_label.setVisible(True)
                else:
                    self.benefit_label.setVisible(False)
                    
                self.count_label.setText("حديث شريف")
                self.count_label.setStyleSheet("color: #FF9800;")
                self.count_label.setVisible(True)
                
                self.show_overlay()

            self.transition_to_zikr(perform_change)

    def is_overlay_hidden(self):
        return (not self.isVisible() or 
                self.overlay_opacity <= 0.01 or 
                (self.fade_anim.state() == QPropertyAnimation.State.Running and self.fade_anim.endValue() == 0.0))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.increment_count()
            event.accept()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        show_action = menu.addAction("إخفاء الواجهة (Hide Overlay)" if self.isVisible() and self.overlay_opacity > 0.1 else "إظهار الواجهة (Show Overlay)")
        show_action.triggered.connect(lambda: self.hide_overlay_instantly() if self.isVisible() and self.overlay_opacity > 0.1 else self.show_overlay())
        
        menu.addSeparator()
        
        morning_action = menu.addAction("أذكار الصباح")
        morning_action.setCheckable(True)
        morning_action.setChecked(self.mode == 'MORNING')
        morning_action.triggered.connect(lambda: self.toggle_session('MORNING'))
        
        night_action = menu.addAction("أذكار المساء")
        night_action.setCheckable(True)
        night_action.setChecked(self.mode == 'NIGHT')
        night_action.triggered.connect(lambda: self.toggle_session('NIGHT'))
        
        free_action = menu.addAction("الوضع الحر")
        free_action.setCheckable(True)
        free_action.setChecked(self.mode == 'FREE')
        free_action.triggered.connect(self.exit_session)
        
        hadith_action = menu.addAction("حديث شريف")
        hadith_action.triggered.connect(lambda: self.show_hadith_notification())
        
        menu.addSeparator()
        
        reset_action = menu.addAction("إعادة تعيين العداد (Reset Counter)")
        reset_action.triggered.connect(self.reset_count)
        
        settings_action = menu.addAction("الإعدادات (Settings)")
        settings_action.triggered.connect(self.open_settings_requested.emit)
        
        menu.exec(event.globalPos())

    def increment_count(self):
        show_overlay_ui = getattr(self, "display_mode", "overlay") in ("overlay", "both")
        send_native_notify = getattr(self, "display_mode", "overlay") in ("notification", "both")

        if show_overlay_ui and self.is_overlay_hidden():
            self.show_overlay()
            if self.mode != 'FREE':
                return

        if self.mode == 'FREE':
            self.count += 1
            self.stats["total_free_clicks"] += 1
            self.log_history_event("free_clicks")
            self.save_config()
            
            if send_native_notify:
                notification_manager.notify_count(
                    zikr=self.zikr,
                    count=self.count,
                    mode='FREE'
                )
                
            if show_overlay_ui:
                self.count_label.setText(str(self.count))
                self.show_overlay()
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index < len(session_data):
                item = session_data[self.session_index]
                target = item.get("target_count", 1)
                self.session_count += 1
                
                if self.session_count >= target:
                    if self.session_index + 1 >= len(session_data):
                        self.finish_session()
                    else:
                        self.session_index += 1
                        self.session_count = 0
                        next_item = session_data[self.session_index]
                        
                        if send_native_notify:
                            notification_manager.notify_count(
                                zikr=next_item.get("text", ""),
                                count=0,
                                target=next_item.get("target_count", 1),
                                benefit=next_item.get("benefit", ""),
                                mode=self.mode
                            )
                            
                        if show_overlay_ui:
                            def perform_change():
                                self.zikr_label.setText("")
                                self.benefit_label.setText("")
                                self.show_overlay()
                            self.transition_to_zikr(perform_change)
                else:
                    if send_native_notify:
                        notification_manager.notify_count(
                            zikr=item.get("text", ""),
                            count=self.session_count,
                            target=target,
                            benefit=item.get("benefit", ""),
                            mode=self.mode
                        )
                    if show_overlay_ui:
                        self.count_label.setText(f"{self.session_count} / {target}")
                        self.show_overlay()

    def reset_count(self):
        if self.mode == 'FREE':
            self.count = 0
            self.count_label.setText(str(self.count))
            self.save_config()
            if getattr(self, "display_mode", "overlay") in ("notification", "both"):
                notification_manager.notify_count(
                    zikr=self.zikr,
                    count=self.count,
                    mode='FREE'
                )
        
    def copy_zikr_to_clipboard(self, event):
        text = self.zikr_label.text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            # Show a brief green flash feedback
            self.zikr_label.setStyleSheet("color: #4CAF50;") # Green
            QTimer.singleShot(800, lambda: self.zikr_label.setStyleSheet("color: white;"))
        
    def transition_to_zikr(self, update_func):
        self.pending_transition_func = update_func
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.overlay_opacity)
        self.fade_anim.setEndValue(0.1)
        self.fade_anim.setDuration(120)
        self.fade_anim.start()

    def change_zikr(self, index_delta):
        if self.mode != 'FREE' or not self.azkar_list:
            return
            
        def perform_change():
            self.zikr_index = (self.zikr_index + index_delta) % len(self.azkar_list)
            self.zikr = self.azkar_list[self.zikr_index]
            self.save_config()
            if getattr(self, "display_mode", "overlay") in ("notification", "both"):
                notification_manager.notify_count(
                    zikr=self.zikr,
                    count=self.count,
                    mode='FREE'
                )
            
        if getattr(self, "display_mode", "overlay") in ("overlay", "both"):
            self.transition_to_zikr(perform_change)
        else:
            perform_change()

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
        end_val = self.fade_anim.endValue()
        
        if getattr(self, "pending_transition_func", None) is not None:
            func = self.pending_transition_func
            self.pending_transition_func = None
            func()
            self.update_ui_state()
            self.fade_anim.setStartValue(0.1)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.setDuration(180)
            self.fade_anim.start()
            return

        if end_val == 0.0:
            self.set_overlay_opacity(0.0)
            self.hide()
            self.hide_options_bar()
        elif end_val == 1.0:
            self.set_overlay_opacity(1.0)

    def update_hide_timer_interval(self):
        text = self.zikr_label.text()
        char_count = len(text) if text else 0
        # Disappear according to character length: min 4.5s, scaling up to 20s for long texts
        interval = max(4500, min(20000, 4500 + char_count * 40))
        self.hide_timer.setInterval(interval)

    def show_overlay(self):
        self.update_ui_state(animate=False)
        self.update_hide_timer_interval()
        self.hide_timer.start()
        if self.fade_anim.state() == QPropertyAnimation.State.Running and self.fade_anim.endValue() == 1.0:
            return
            
        # Detect background brightness before making it visible
        if not self.isVisible() or self.overlay_opacity < 0.1:
            self.detect_background_brightness()

        if not self.isVisible():
            self.set_overlay_opacity(0.0)
            self.show()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.overlay_opacity)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
    def hide_overlay(self):
        if not self.is_cursor_inside():
            if self.fade_anim.state() == QPropertyAnimation.State.Running and self.fade_anim.endValue() == 0.0:
                return
            self.hide_timer.stop()
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.overlay_opacity)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()
        else:
            # If mouse is actually inside, defer hiding
            self.hide_timer.start()

    def hide_overlay_instantly(self):
        self.hide_timer.stop()
        self.hover_timer.stop()
        self.fade_anim.stop()
        self.set_overlay_opacity(0.0)
        self.hide()
        self.hide_options_bar()

    def check_hover_zones(self):
        pos = self.mapFromGlobal(self.cursor().pos())
        if self.rect().contains(pos):
            # container starts at y=65 (top margin 15 + upper_widget 40 + spacing 10)
            if pos.y() < 65:
                self.show_options_bar()
            else:
                self.hide_options_bar()
        else:
            self.hover_timer.stop()
            self.hide_options_bar()
            if not self.is_overlay_hidden():
                self.hide_timer.start()

    def show_options_bar(self):
        self.trigger_circle.setVisible(False)
        self.options_container.setVisible(True)

    def hide_options_bar(self):
        self.options_container.setVisible(False)
        if self.is_cursor_inside():
            self.trigger_circle.setVisible(True)
        else:
            self.trigger_circle.setVisible(False)

    def enterEvent(self, event):
        self.is_mouse_hovered = True
        self.hide_timer.stop()
        self.hover_timer.start()
        self.check_hover_zones()
        self.fade_anim.stop()
        self.set_overlay_opacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_mouse_hovered = False
        self.hover_timer.stop()
        self.hide_options_bar()
        self.update_hide_timer_interval()
        self.hide_timer.start()
        super().leaveEvent(event)

    def showEvent(self, event):
        self.update_ui_state(animate=False)
        super().showEvent(event)
        
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
                session_data = self.db.get(self.mode.lower(), [])
                curr_item = session_data[self.session_index] if self.session_index < len(session_data) else None
                if getattr(self, "display_mode", "overlay") in ("notification", "both") and curr_item:
                    notification_manager.notify_count(
                        zikr=curr_item.get("text", ""),
                        count=0,
                        target=curr_item.get("target_count", 1),
                        benefit=curr_item.get("benefit", ""),
                        mode=self.mode
                    )
                if getattr(self, "display_mode", "overlay") in ("overlay", "both"):
                    def perform_change():
                        self.zikr_label.setText("")
                        self.benefit_label.setText("")
                        self.show_overlay()
                    self.transition_to_zikr(perform_change)

    def next_zikr(self):
        if self.mode == 'FREE':
            self.change_zikr(1)
        else:
            session_data = self.db.get(self.mode.lower(), [])
            if self.session_index + 1 < len(session_data):
                self.session_index += 1
                self.session_count = 0
                curr_item = session_data[self.session_index]
                if getattr(self, "display_mode", "overlay") in ("notification", "both"):
                    notification_manager.notify_count(
                        zikr=curr_item.get("text", ""),
                        count=0,
                        target=curr_item.get("target_count", 1),
                        benefit=curr_item.get("benefit", ""),
                        mode=self.mode
                    )
                if getattr(self, "display_mode", "overlay") in ("overlay", "both"):
                    def perform_change():
                        self.zikr_label.setText("")
                        self.benefit_label.setText("")
                        self.show_overlay()
                    self.transition_to_zikr(perform_change)
            elif self.session_index + 1 >= len(session_data):
                self.finish_session()

    def detect_background_brightness(self, x=None, y=None, width=None, height=None):
        if x is not None and y is not None and width is not None and height is not None:
            target_width = width
            target_height = height
            target_x = x
            target_y = y
        else:
            target_rect = self.geometry()
            target_width = target_rect.width()
            target_height = target_rect.height()
            target_x = target_rect.x()
            target_y = target_rect.y()
            if target_width <= 0 or target_height <= 0:
                target_width = 400 if self.mode == 'FREE' else 500
                target_height = 160 if self.mode == 'FREE' else 220
                
        # Grab background only for the self.upper_widget area (which holds the buttons)
        grab_x = target_x + 15
        grab_y = target_y + 15
        grab_width = max(10, target_width - 30)
        grab_height = 40
        
        screen_obj = self.get_active_screen()
            
        was_visible = self.isVisible()
        current_opacity = self.overlay_opacity
        if was_visible:
            self.set_overlay_opacity(0.0)
            QApplication.processEvents()
            
        pixmap = screen_obj.grabWindow(0, grab_x, grab_y, grab_width, grab_height)
        
        if was_visible:
            self.set_overlay_opacity(current_opacity)
            
        if not pixmap.isNull():
            scaled_img = pixmap.toImage().scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            color = scaled_img.pixelColor(0, 0)
            brightness = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
            self.is_bg_light = brightness > 150
        else:
            self.is_bg_light = False
            
        self.update_button_styles()

    def update_button_styles(self):
        is_light = getattr(self, "is_bg_light", False)
        
        if is_light:
            bg_color = "rgba(20, 20, 20, 200)"
            hover_bg_color = "rgba(50, 50, 50, 220)"
            border_color = "rgba(255, 255, 255, 30)"
            text_color = "white"
            
            exit_bg = "rgba(180, 40, 40, 200)"
            exit_hover = "rgba(210, 60, 60, 220)"
        else:
            bg_color = "rgba(255, 255, 255, 40)"
            hover_bg_color = "rgba(255, 255, 255, 80)"
            border_color = "rgba(255, 255, 255, 20)"
            text_color = "white"
            
            exit_bg = "rgba(255, 80, 80, 80)"
            exit_hover = "rgba(255, 80, 80, 120)"
            
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
                font-weight: bold;
                border: 1px solid {border_color};
            }}
            QPushButton:hover {{
                background-color: {hover_bg_color};
            }}
        """
        
        trigger_border = "rgba(255, 255, 255, 30)"
        trigger_style = f"""
            QPushButton {{
                background-color: {bg_color if is_light else "rgba(30, 30, 30, 180)"};
                color: {text_color};
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
                border: 1px solid {trigger_border};
            }}
            QPushButton:hover {{
                background-color: {hover_bg_color if is_light else "rgba(255, 255, 255, 40)"};
                border: 1px solid rgba(255, 255, 255, 60);
            }}
        """
        
        exit_style = f"""
            QPushButton {{
                background-color: {exit_bg};
                color: {text_color};
                border-radius: 17px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0px;
                font-weight: bold;
                border: 1px solid {border_color};
            }}
            QPushButton:hover {{
                background-color: {exit_hover};
            }}
        """
        
        self.trigger_circle.setStyleSheet(trigger_style)
        self.back_btn.setStyleSheet(style)
        self.morning_btn.setStyleSheet(style)
        self.night_btn.setStyleSheet(style)
        self.reset_btn.setStyleSheet(style)
        self.hide_btn.setStyleSheet(style)
        self.next_btn.setStyleSheet(style)
        self.exit_btn.setStyleSheet(exit_style)
