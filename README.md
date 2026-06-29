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

# 🇸🇦 النسخة العربية (Arabic Version)

برنامج خلفي خفيف وجميل ومبتكر لأنظمة التشغيل (ويندوز، لينكس، وماك) يعمل كسبحة ذكية ورفيق للأذكار اليومية أثناء استخدامك للحاسوب.
تم تصميمه ليعمل بالكامل في الخلفية دون التسبب في أي فوضى بشريط المهام. يقوم البرنامج بإظهار واجهة شفافة حديثة وأنيقة في الزاوية السفلية اليمنى من الشاشة وتستجيب تلقائياً لضغطات الفأرة أو لوحة المفاتيح التي تحددها لزيادة العداد.

---

## ✨ المميزات

- **📺 واجهة زجاجية حديثة**: تصميم واجهة مستخدم شفافة خالية من الإطارات وتأثير زجاجي راقٍ.
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

### المتطلبات الأساسية
تأكد من تثبيت بايثون 3.10 أو أحدث على جهازك.

### 1. تثبيت المكتبات المطلوبة
قم بنسخ المستودع، وانتقل إلى المجلد، ثم قم بتثبيت الحزم المطلوبة:
```bash
pip install -r requirements.txt
```

### 2. تشغيل التطبيق
ابدأ العملية في الخلفية:
```bash
pythonw main.pyw
```
*(استخدام `pythonw` يجعل البرنامج يعمل كعملية خلفية دون ظهور نافذة سطر الأوامر).*

---

## ⚙️ الإعدادات والتخصيص

- **مفاتيح التسبيح**: انقر على زر `Assign` بجانب خيارات الفأرة/لوحة المفاتيح في الإعدادات، ثم اضغط على الزر المطلوب. اضغط على مفتاح `Esc` لتفريغ وإلغاء الزر.
- **قاعدة بيانات الأذكار**: يمكنك تخصيص الأذكار وأعدادها وفضائلها عن طريق تعديل ملف `db.json`.
- **نسخ احتياطي للإعدادات**: يتم حفظ المفاتيح والإحصائيات المخصصة في ملف `config.json`.

---

# 🇬🇧 English Version (النسخة الإنجليزية)

A lightweight, beautiful, and unobtrusive background application for Windows, Linux, and macOS that functions as a smart Sebha and Athkar companion.
Designed to stay completely out of your way as a background process (no taskbar clutter), it overlays a modern, glassy, and semi-transparent counter in the bottom-right corner of your screen that responds to mouse and keyboard hotkeys.

---

## ✨ Features

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

## 🛠️ Installation & Setup

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

## ⚙️ Configuration & Customization

- **Triggers**: Click the `Assign` button next to Mouse/Keyboard options in Settings, then press your desired button. Press `Esc` to clear the trigger.
- **Athkar Database**: You can customize the Athkar, their target counts, and benefits by modifying the `db.json` file.
- **Config Backup**: Custom keybindings and stats are persisted in `config.json`.

---

## 📜 License | الترخيص
This project is open-source and free to use. Enjoy and remember to keep your tongue moist with the remembrance of Allah.
