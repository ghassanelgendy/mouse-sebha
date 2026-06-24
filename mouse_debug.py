from pynput import mouse
import time

def on_click(x, y, button, pressed):
    if pressed:
        with open("mouse_debug.log", "a") as f:
            f.write(f"Clicked button: {button}\n")

with open("mouse_debug.log", "w") as f:
    f.write("Starting mouse debug...\n")

listener = mouse.Listener(on_click=on_click)
listener.start()

try:
    time.sleep(60)
finally:
    listener.stop()
