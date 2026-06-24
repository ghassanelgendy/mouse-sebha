# 📿 Mouse Sebha (سبحة الفأرة)

A lightweight, beautiful, and unobtrusive background application for Windows that functions as a smart Sebha and Athkar companion. Designed to stay completely out of your way as a background process (no taskbar clutter), it overlays a modern, glassy, and semi-transparent counter in the bottom-right corner of your screen that responds to mouse and keyboard hotkeys.

---

## ✨ Features

- **📺 Modern Glassy Overlay**: Semi-transparent, frameless, and premium glassmorphic UI.
- **⚡ Dual Triggers**: Bind any mouse side button (e.g., FWD / XButton2) and/or keyboard key simultaneously as your click counter.
- **☀️/🌙 Athkar Sessions**: Fully integrated Morning (**أذكار الصباح**) and Night (**أذكار المساء**) Athkar database.
  - Displays each zikr, its benefit/source, and its target counter (e.g., `1/3`).
  - Auto-height adjustment smoothly expands the box to fit long verses (like Ayat al-Kursi) without using scrollbars.
- **🎯 Smart Interaction**:
  - Automatically hides after 5 seconds of inactivity.
  - Hovering reveals the control panel to start Morning/Night sessions, reset counters, or exit current sessions.
  - Scrolling your mouse wheel over the overlay lets you cycle through different free-mode zikrs.
- **⚙️ Settings & System Tray Control**:
  - Right-click the custom tray icon to configure triggers or view statistics.
  - **Press to Assign**: Dynamically binds new keys/buttons safely using a PyQt event listener bridge.
  - **Windows Startup Integration**: Toggle "Run at Windows Startup" directly from settings to start counting as soon as your PC boots.
  - **Lifetime Stats**: Tracks your total free clicks, morning sessions, and night sessions completed.
- **🎨 Premium Typography**: Uses your custom `@font.ttf` for beautiful Arabic calligraphy, while keeping English text and counters in a clean system font (`Segoe UI`) for maximum readability.

---

## 🛠️ Installation & Setup

### Prerequisites
Make sure you have Python 3.10+ installed on your Windows system.

### 1. Install Dependencies
Clone this repository, navigate to the folder, and install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the background process:
```bash
pythonw main.py
```
*(Using `pythonw` runs it as a background task, keeping your command prompt free and avoiding a command window popup).*

---

## ⚙️ Configuration & Customization

- **Triggers**: Click the `Assign` button next to Mouse/Keyboard options in Settings, then press your desired button. The listeners update dynamically in the background.
- **Athkar Database**: You can customize the Athkar, their target counts, and benefits by modifying the `db.json` file.
- **Config Backup**: Custom keybindings and stats are persisted in `config.json`.

---

## 📜 License
This project is open-source and free to use. Enjoy and remember to keep your tongue moist with the remembrance of Allah.
