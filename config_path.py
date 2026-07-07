import os
import json
from PyQt6.QtCore import QStandardPaths

# AppConfigLocation points to AppData/Local/Sebha on Windows, ~/.config/Sebha on Linux, etc.
app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
if not os.path.exists(app_data_dir):
    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception as e:
        print("Error creating app data directory:", e)

CONFIG_PATH = os.path.join(app_data_dir, "config.json")

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
    "font_family": "Default",
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
    if os.path.exists(local_config):
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
