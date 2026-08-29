import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QCursor

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class AthkarOptionButton(QPushButton):
    def __init__(self, icon_str, title_str, subtitle_str, color_accent="#4CAF50", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(72)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)
        layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        
        # Icon label
        self.icon_label = QLabel(icon_str, self)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 22))
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedWidth(40)
        
        # Text container
        text_container = QVBoxLayout()
        text_container.setSpacing(3)
        text_container.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        self.title_label = QLabel(title_str, self)
        self.title_label.setFont(QFont("Cairo", 13, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.subtitle_label = QLabel(subtitle_str, self)
        self.subtitle_label.setFont(QFont("Cairo", 10))
        self.subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.65); background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        text_container.addWidget(self.title_label)
        text_container.addWidget(self.subtitle_label)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_container)
        layout.addStretch()
        
        self.color_accent = color_accent
        self.setStyleSheet(f"""
            AthkarOptionButton {{
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 14px;
                text-align: right;
            }}
            AthkarOptionButton:hover {{
                background-color: rgba(255, 255, 255, 0.14);
                border: 1px solid {self.color_accent};
            }}
            AthkarOptionButton:pressed {{
                background-color: rgba(255, 255, 255, 0.22);
            }}
        """)

    def set_font_family(self, font_family):
        if font_family:
            self.title_label.setFont(QFont(font_family, 13, QFont.Weight.Bold))
            self.subtitle_label.setFont(QFont(font_family, 10))

class AthkarSelectionModal(QDialog):
    mode_selected = pyqtSignal(str)

    def __init__(self, font_family="Cairo", parent=None):
        super().__init__(parent)
        self.font_family = font_family
        self.initUI()

    def initUI(self):
        self.setWindowTitle("اختيار الورد")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 390)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Outer layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Card container with dark background
        self.container = QFrame(self)
        self.container.setObjectName("modalCard")
        self.container.setStyleSheet("""
            #modalCard {
                background-color: rgba(26, 26, 30, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 20px;
            }
        """)

        # Drop shadow for aesthetic depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.container)
        card_layout.setContentsMargins(22, 18, 22, 22)
        card_layout.setSpacing(12)

        # Header bar (Title + Close button)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 4)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)

        self.title_lbl = QLabel("اختر نوع الورد", self.container)
        self.title_lbl.setFont(QFont(self.font_family, 15, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        
        self.subtitle_lbl = QLabel("اختر الورد الذي ترغب في متابعته الآن:", self.container)
        self.subtitle_lbl.setFont(QFont(self.font_family, 10))
        self.subtitle_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.65); background: transparent;")

        header_text_layout.addWidget(self.title_lbl)
        header_text_layout.addWidget(self.subtitle_lbl)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        # Close button
        self.close_btn = QPushButton("✕", self.container)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.75);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 70, 70, 0.6);
                color: white;
                border: 1px solid rgba(255, 70, 70, 0.8);
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.close_btn)

        card_layout.addLayout(header_layout)

        # Separator line
        sep = QFrame(self.container)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); max-height: 1px;")
        card_layout.addWidget(sep)
        card_layout.addSpacing(4)

        # 1. Morning Athkar button
        self.morning_btn = AthkarOptionButton(
            icon_str="☀️",
            title_str="أذكار الصباح",
            subtitle_str="ورد الصباح والتحصينات اليومية",
            color_accent="#FFB74D",
            parent=self.container
        )
        self.morning_btn.set_font_family(self.font_family)
        self.morning_btn.clicked.connect(lambda: self.select_mode("MORNING"))
        card_layout.addWidget(self.morning_btn)

        # 2. Evening Athkar button
        self.night_btn = AthkarOptionButton(
            icon_str="🌙",
            title_str="أذكار المساء",
            subtitle_str="ورد المساء وحفظ الليل",
            color_accent="#64B5F6",
            parent=self.container
        )
        self.night_btn.set_font_family(self.font_family)
        self.night_btn.clicked.connect(lambda: self.select_mode("NIGHT"))
        card_layout.addWidget(self.night_btn)

        # 3. Free Mode button
        self.free_btn = AthkarOptionButton(
            icon_str="📿",
            title_str="الوضع الحر (تسبيح)",
            subtitle_str="تسبيح وذكر مفتوح مع العداد",
            color_accent="#81C784",
            parent=self.container
        )
        self.free_btn.set_font_family(self.font_family)
        self.free_btn.clicked.connect(lambda: self.select_mode("FREE"))
        card_layout.addWidget(self.free_btn)

        main_layout.addWidget(self.container)

    def select_mode(self, mode: str):
        self.mode_selected.emit(mode)
        self.accept()

    def show_centered(self):
        # Position modal in the center of the active screen
        try:
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
            if screen:
                geo = screen.geometry()
                x = geo.x() + (geo.width() - self.width()) // 2
                y = geo.y() + (geo.height() - self.height()) // 2
                self.move(x, y)
        except Exception:
            pass
            
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key in (Qt.Key.Key_1, Qt.Key.Key_M):
            self.select_mode("MORNING")
        elif key in (Qt.Key.Key_2, Qt.Key.Key_N, Qt.Key.Key_E):
            self.select_mode("NIGHT")
        elif key in (Qt.Key.Key_3, Qt.Key.Key_F):
            self.select_mode("FREE")
        else:
            super().keyPressEvent(event)
