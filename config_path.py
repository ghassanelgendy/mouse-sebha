import os
from PyQt6.QtCore import QStandardPaths

# AppConfigLocation points to AppData/Local/Sebha on Windows, ~/.config/Sebha on Linux, etc.
app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
if not os.path.exists(app_data_dir):
    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception as e:
        print("Error creating app data directory:", e)

CONFIG_PATH = os.path.join(app_data_dir, "config.json")

# Migration check: if AppData config doesn't exist but local config does, copy it
local_config = "config.json"
if not os.path.exists(CONFIG_PATH) and os.path.exists(local_config):
    try:
        import shutil
        shutil.copy2(local_config, CONFIG_PATH)
        print("Migrated local config to AppData")
    except Exception as e:
        print("Error migrating config:", e)
