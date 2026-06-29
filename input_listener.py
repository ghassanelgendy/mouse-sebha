from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse, keyboard
import json
import os

from config_path import CONFIG_PATH

class InputSignals(QObject):
    triggered = pyqtSignal()

class InputListener:
    def __init__(self):
        self.signals = InputSignals()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.trigger_mouse = "Button.x2"
        self.trigger_keyboard = ""
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.trigger_mouse = data.get("trigger_mouse", "Button.x2")
                    self.trigger_keyboard = data.get("trigger_keyboard", "")
            except Exception as e:
                print("Error loading config for listener:", e)

    def reload(self):
        self.load_config()

    def on_click(self, x, y, button, pressed):
        if pressed:
            if str(button) == self.trigger_mouse:
                self.signals.triggered.emit()

    def on_press(self, key):
        # Determine string representation of key
        try:
            k = key.char
            if k is None:
                k = str(key)
        except AttributeError:
            k = str(key)
            
        if self.trigger_keyboard and (k == self.trigger_keyboard or str(key) == self.trigger_keyboard):
            self.signals.triggered.emit()

    def start(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()

    def stop(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
