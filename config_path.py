import os
import sys
import json
from PyQt6.QtCore import QStandardPaths

def _get_config_path():
    try:
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if not app_data_dir or app_data_dir == ".":
            app_data_dir = os.path.expanduser("~/.config/Sebha")
        elif "sebha" not in app_data_dir.lower():
            app_data_dir = os.path.join(app_data_dir, "Sebha")
    except Exception:
        app_data_dir = os.path.expanduser("~/.config/Sebha")

    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception:
        app_data_dir = os.path.expanduser("~/.sebha")
        try:
            os.makedirs(app_data_dir, exist_ok=True)
        except Exception:
            app_data_dir = "."

    return os.path.join(app_data_dir, "config.json")

CONFIG_PATH = _get_config_path()

# Default config dictionary
DEFAULT_CONFIG = {
    "count": 0,
    "zikr": "سبحان الله",
    "azkar_list": [
        "سبحان الله",
        "الحمد لله",
        "لا إله إلا الله",
        "الله أكبر",
        "لا حول ولا قوة إلا بالله",
        "أستغفر الله"
    ],
    "trigger_mouse": "Button.x2",
    "trigger_keyboard": "",
    "auto_update": True,
    "show_tray_icon": True,
    "hadith_reminder_enabled": True,
    "hadith_reminder_interval": 30,
    "font_family": "Default",
    "overlay_position": "Bottom-Right",
    "stats": {
        "total_free_clicks": 0,
        "morning_sessions_completed": 0,
        "night_sessions_completed": 0,
        "history": {}
    }
}

# If the config file does not exist, migrate or create default
if not os.path.exists(CONFIG_PATH):
    local_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(local_config) and local_config != CONFIG_PATH:
        try:
            import shutil
            shutil.copy2(local_config, CONFIG_PATH)
            print("Migrated local config to AppData")
        except Exception as e:
            print("Error migrating config:", e)
            
    # If still doesn't exist, create default
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
            print("Created default config in AppData")
        except Exception as e:
            print("Error creating default config:", e)
