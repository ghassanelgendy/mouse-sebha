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

    def _match_mouse(self, button):
        if not self.trigger_mouse:
            return False
        
        target = str(self.trigger_mouse).strip("'\"").lower()
        sb = str(button).strip("'\"").lower()
        
        if sb == target or str(button).lower() == target:
            return True
            
        if hasattr(button, 'name') and button.name:
            bn = str(button.name).lower()
            if bn == target or f"button.{bn}" == target:
                return True
                
        return False

    def on_click(self, x, y, button, pressed):
        if pressed and self._match_mouse(button):
            self.signals.triggered.emit()

    def _match_key(self, key):
        if not self.trigger_keyboard:
            return False
        
        target = str(self.trigger_keyboard).strip("'\"").lower()
        
        # Check string representation (e.g. "key.f2", "key.space", "a")
        sk = str(key).strip("'\"").lower()
        if sk == target or str(key).lower() == target:
            return True
            
        # Check key.name attribute if available (e.g. 'f2', 'space', 'esc')
        if hasattr(key, 'name') and key.name:
            kn = str(key.name).lower()
            if kn == target or f"key.{kn}" == target:
                return True
                
        # Check key.char attribute if available (e.g. 'a', 'b', '1')
        try:
            if key.char and str(key.char).lower() == target:
                return True
        except AttributeError:
            pass
            
        # Space key matching
        if target in ("space", "key.space", " ") and (sk in ("space", "key.space") or getattr(key, 'char', None) == ' '):
            return True
            
        return False

    def on_press(self, key):
        if self._match_key(key):
            self.signals.triggered.emit()

    def start(self):
        try:
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.mouse_listener.start()
        except Exception as e:
            print("Warning: Could not start mouse listener:", e)
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
            self.keyboard_listener.start()
        except Exception as e:
            print("Warning: Could not start keyboard listener:", e)

    def stop(self):
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass
