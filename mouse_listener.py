from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse

class MouseSignals(QObject):
    forward_clicked = pyqtSignal()

class MouseListener:
    def __init__(self):
        self.signals = MouseSignals()
        self.listener = None

    def on_click(self, x, y, button, pressed):
        if pressed and button in (mouse.Button.x1, mouse.Button.x2):
            self.signals.forward_clicked.emit()

    def start(self):
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
