<div align="center">

# 📿 Mouse Sebha

</div>
<p align="center">
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-Windows-Setup.exe">
    <img src="https://img.shields.io/badge/Download-Windows-blue?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" />
  </a>
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-Linux.deb">
    <img src="https://img.shields.io/badge/Download-Ubuntu%20%28.deb%29-orange?style=for-the-badge&logo=ubuntu&logoColor=white" alt="Download for Ubuntu (.deb)" />
  </a>
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-Linux">
    <img src="https://img.shields.io/badge/Download-Linux-orange?style=for-the-badge&logo=linux&logoColor=white" alt="Download for Linux" />
  </a>
  <a href="https://github.com/ghassanelgendy/mouse-sebha/releases/latest/download/Sebha-macOS">
    <img src="https://img.shields.io/badge/Download-macOS-black?style=for-the-badge&logo=apple&logoColor=white" alt="Download for macOS" />
  </a>
</p>

---

# النسخة العربية

برنامج يعمل في الخلفيه خفيف ومبتكر لأنظمة التشغيل (ويندوز، لينكس، وماك) يعمل كسبحة ذكية ورفيق للأذكار اليومية أثناء استخدامك للحاسوب.
تم تصميمه ليعمل بالكامل في الخلفية دون التسبب في أي فوضى بشريط المهام. يقوم البرنامج بإظهار واجهة شفافة حديثة وأنيقة في الزاوية السفلية اليمنى من الشاشة وتستجيب تلقائياً لضغطات الفأرة أو لوحة المفاتيح التي تحددها لزيادة العداد.

---

## ✨ المميزات

- **📺 واجهة زجاجية أو إشعارات نظام أوبونتو الأصلية**: الاختيار بين الواجهة الشفافة العائمة (Overlay)، أو إشعارات سطح المكتب الأصلية لنظام أوبونتو (Native Desktop Notifications)، أو كلاهما معاً.
- **⚡ تشغيل مزدوج**: ربط أي زر جانبي للفأرة و/أو مفتاح بلوحة المفاتيح في نفس الوقت ليعمل كزر للتسبيح.
- **☀️/🌙 جلسات الأذكار**: قاعدة بيانات متكاملة لأذكار الصباح وأذكار المساء.
  - يعرض كل ذكر، وفضله/مصدره، والعدد المطلوب (مثل `1/3`).
  - ضبط تلقائي للأبعاد (العرض والارتفاع) لتناسب الآيات الطويلة (مثل آية الكرسي) دون قص النص.
- **🎯 تفاعل ذكي**:
  - يختفي تلقائياً بعد 5 ثوانٍ من عدم النشاط.
  - يظهر شريط التحكم عند تمرير مؤشر الفأرة لبدء جلسة الأذكار، إعادة تعيين العداد، أو إنهاء الجلسة الحالية.
  - إمكانية التمرير بعجلة الفأرة لتغيير الأذكار في الوضع الحر.
- **⚙️ الإعدادات وشريط المهام**:
  - انقر بزر الفأرة الأيمن على أيقونة شريط المهام المخصصة لتكوين المفاتيح أو عرض الإحصائيات.
  - **الضغط للتعيين**: تعيين أزرار/مفاتيح جديدة بسهولة عبر قارئ الإدخال المدمج (أو اضغط `Esc` لإلغاء وتفريغ الزر).
  - **التشغيل التلقائي مع الويندوز**: تفعيل خيار التشغيل عند بدء تشغيل النظام مباشرة من الإعدادات.
  - **إحصائيات مدى الحياة**: تتبع إجمالي التسبيحات الحرة وجلسات الصباح والمساء المكتملة.
  - **التحديث التلقائي**: جلب التحديثات الجديدة وتثبيتها تلقائياً من المستودع مباشرة.
- **🎨 خطوط عربية مميزة**: استخدام خط مخصص لإظهار الخط العربي بجمالية، مع إبقاء الأرقام والنصوص الإنجليزية بخط النظام الافتراضي لسهولة القراءة.

---

## 🛠️ التثبيت والتشغيل

### 🐧 التثبيت على أوبونتو / لينكس (Ubuntu / Debian / Linux)

#### الخيار 1: التثبيت عبر حزمة Debian المباشرة (الأسهل لأوبونتو)
1. قم بتحميل الملف `Sebha-Linux.deb` من قائمة [الإصدارات (Releases)](https://github.com/ghassanelgendy/mouse-sebha/releases).
2. انقر مزدوجاً على الملف لتثبيته مباشرة، أو نفذ الأمر التالي في الطرفية (Terminal):
   ```bash
   sudo apt install ./Sebha-Linux.deb
   ```
3. ستظهر السبحة في قائمة التطبيقات (Applications Menu) مع الأيقونة وتعمل كأي تطبيق عادي.

#### الخيار 2: استخدام ملف التنفيذ والسكربت المدمج
إذا قمت بتحميل الملف التنفيذي المباشر `Sebha-Linux`:
```bash
chmod +x Sebha-Linux
./install.sh
```
أو تشغيله المباشر: `./Sebha-Linux`

#### الخيار 3: التشغيل والتثبيت من المصدر (Python Source / Repository)
1. تثبيت بايثون ومكتبات النظام الحزمية المطلوبة:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libgl1
   ```
2. التثبيت التلقائي وإنشاء اختصار التطبيق في قائمة البرامج:
   ```bash
   bash install.sh
   ```
   أو تشغيل التطبيق مباشرة: `python3 main.pyw`

### 💻 التثبيت على ويندوز (Windows)
حمل ملف التثبيت المباشر `Sebha-Windows-Setup.exe` وانقر عليه للتثبيت الفوري.

---

## ⚙️ الإعدادات والتخصيص

- **مفاتيح التسبيح**: انقر على زر `Assign` بجانب خيارات الفأرة/لوحة المفاتيح في الإعدادات، ثم اضغط على الزر المطلوب. اضغط على مفتاح `Esc` لتفريغ وإلغاء الزر.
- **قاعدة بيانات الأذكار**: يمكنك تخصيص الأذكار وأعدادها وفضائلها عن طريق تعديل ملف `db.json`.
- **نسخ احتياطي للإعدادات**: يتم حفظ المفاتيح والإحصائيات المخصصة في ملف `config.json`.

---

# English Version 

A lightweight, beautiful, and unobtrusive background application for Windows, Linux, and macOS that functions as a smart Sebha and Athkar companion.
Designed to stay completely out of your way as a background process (no taskbar clutter), it overlays a modern, glassy, and semi-transparent counter in the bottom-right corner of your screen that responds to mouse and keyboard hotkeys.

---

## ✨ Features

- **📺 Modern Glassy Overlay & Native Ubuntu Notifications**: Choose between the floating glassy overlay, native Ubuntu desktop notifications (`notify-send`), or both simultaneously.
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

## 🛠️ Installation & Setup

### 🐧 Installing on Ubuntu / Debian / Linux

#### Option 1: Debian Package (.deb) - Recommended for Ubuntu
1. Download `Sebha-Linux.deb` from the [Releases](https://github.com/ghassanelgendy/mouse-sebha/releases) page.
2. Double-click the file to install via Ubuntu Software / App Center, or run in Terminal:
   ```bash
   sudo apt install ./Sebha-Linux.deb
   ```
3. Launch `Sebha` directly from your Applications menu.

#### Option 2: Standalone Executable Binary
If you downloaded `Sebha-Linux` executable:
1. Grant execution permissions:
   ```bash
   chmod +x Sebha-Linux
   ```
2. Run the interactive installer script to set up application menu shortcuts:
   ```bash
   ./install.sh
   ```
   Or run the binary directly: `./Sebha-Linux`

#### Option 3: Run / Install from Python Source Repository
1. Install Python 3 and system Qt/XCB dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libgl1
   ```
2. Run installer script to install Python dependencies and set up the Application Menu desktop shortcut:
   ```bash
   bash install.sh
   ```
   Or launch directly using python:
   ```bash
   python3 main.pyw
   ```

### 💻 Installing on Windows
Download `Sebha-Windows-Setup.exe` from Releases and run the setup wizard.

---

## ⚙️ Configuration & Customization

- **Triggers**: Click the `Assign` button next to Mouse/Keyboard options in Settings, then press your desired button. Press `Esc` to clear the trigger.
- **Athkar Database**: You can customize the Athkar, their target counts, and benefits by modifying the `db.json` file.
- **Config Backup**: Custom keybindings and stats are persisted in `config.json`.

---

## 📜 License | الترخيص
This project is open-source and free to use. Enjoy and remember to keep your tongue moist with the remembrance of Allah.
