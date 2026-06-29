# 📿 سبحة الفأرة | Mouse Sebha

<p align="center">
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-Windows.exe">
    <img src="https://img.shields.io/badge/تحميل-Windows-blue?style=for-the-badge&logo=windows&logoColor=white" alt="تحميل لنظام ويندوز" />
  </a>
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-Linux">
    <img src="https://img.shields.io/badge/تحميل-Linux-orange?style=for-the-badge&logo=linux&logoColor=white" alt="تحميل لنظام لينكس" />
  </a>
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-macOS">
    <img src="https://img.shields.io/badge/تحميل-macOS-black?style=for-the-badge&logo=apple&logoColor=white" alt="تحميل لنظام ماك" />
  </a>
</p>

---

## 🌟 نبذة عن البرنامج (باللغة العربية)

برنامج خلفي خفيف وجميل ومبتكر لأنظمة التشغيل (ويندوز، لينكس، وماك) يعمل كسبحة ذكية ورفيق للأذكار اليومية أثناء استخدامك للحاسوب.
تم تصميمه ليعمل بالكامل في الخلفية دون التسبب في أي فوضى بشريط المهام. يقوم البرنامج بإظهار واجهة شفافة حديثة وأنيقة في الزاوية السفلية اليمنى من الشاشة وتستجيب تلقائياً لضغطات الفأرة أو لوحة المفاتيح التي تحددها لزيادة العداد.

---

## 🌟 About the Program (English Translation)

A lightweight, beautiful, and unobtrusive background application for Windows, Linux, and macOS that functions as a smart Sebha and Athkar companion. 
Designed to stay completely out of your way as a background process (no taskbar clutter), it overlays a modern, glassy, and semi-transparent counter in the bottom-right corner of your screen that responds to mouse and keyboard hotkeys.

---

## ✨ Features | المميزات

- **📺 Modern Glassy Overlay**: Semi-transparent, frameless, and premium glassmorphic UI.
- **⚡ Dual Triggers**: Bind any mouse side button (e.g., FWD / XButton2) and/or keyboard key simultaneously as your click counter.
- **☀️/🌙 Athkar Sessions**: Fully integrated Morning (**أذكار الصباح**) and Night (**أذكار المساء**) Athkar database.
  - Displays each zikr, its benefit/source, and its target counter (e.g., `1/3`).
  - Auto-height and width adjustment smoothly expands the box to fit long verses (like Ayat al-Kursi) without clipping.
- **🎯 Smart Interaction**:
  - Automatically hides after 5 seconds of inactivity.
  - Hovering reveals the control panel to start Morning/Night sessions, reset counters, or exit current sessions.
  - Scrolling your mouse wheel over the overlay lets you cycle through different free-mode zikrs.
- **⚙️ Settings & System Tray Control**:
  - Right-click the custom tray icon to configure triggers or view statistics.
  - **Press to Assign**: Dynamically binds new keys/buttons safely using a PyQt event listener bridge (or clear them with `Esc`).
  - **Windows Startup Integration**: Toggle "Run at Windows Startup" directly from settings.
  - **Lifetime Stats**: Tracks your total free clicks, morning sessions, and night sessions completed.
  - **Auto-Update**: Pulls updates automatically from the repository directly.
- **🎨 Premium Typography**: Uses your custom `@font.ttf` for beautiful Arabic calligraphy, while keeping English text and counters in a clean system font (`Segoe UI`) for maximum readability.

---

## 🛠️ Installation & Setup | التثبيت والتشغيل

### Prerequisites
Make sure you have Python 3.10+ installed on your system.

### 1. Install Dependencies
Clone this repository, navigate to the folder, and install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the background process:
```bash
pythonw main.pyw
```
*(Using `pythonw` runs it as a background task, keeping your command prompt free and avoiding a command window popup).*

---

## ⚙️ Configuration & Customization | الإعدادات والتخصيص

- **Triggers**: Click the `Assign` button next to Mouse/Keyboard options in Settings, then press your desired button. Press `Esc` to clear the trigger.
- **Athkar Database**: You can customize the Athkar, their target counts, and benefits by modifying the `db.json` file.
- **Config Backup**: Custom keybindings and stats are persisted in `config.json`.

---

## 📜 License | الترخيص
This project is open-source and free to use. Enjoy and remember to keep your tongue moist with the remembrance of Allah.
