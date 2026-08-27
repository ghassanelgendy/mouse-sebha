import os
import sys
import shutil
import subprocess
import re

NOTIFICATION_REPLACE_ID_COUNT = 42100
NOTIFICATION_REPLACE_ID_HADITH = 42101
NOTIFICATION_REPLACE_ID_GENERAL = 42102

RLM = "\u200F"  # Unicode Right-to-Left Mark (forces RTL text layout in notifications)

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u27BF\u2300-\u23FF\u2B00-\u2BFF\u200D\uFE0F]+"
)

def _strip_emojis(text: str) -> str:
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", text)
    return re.sub(r" +", " ", cleaned).strip()

def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = _strip_emojis(text)
    # Remove any accidental empty parentheses '()' or '( )' or '[]'
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\[\s*\]', '', cleaned)
    return re.sub(r" +", " ", cleaned).strip()

def _to_rtl(text: str) -> str:
    """
    Ensures every line in a string starts with a Right-to-Left Mark (RLM),
    forcing notification daemons and text layout engines to render strictly RTL.
    """
    if not text:
        return ""
    lines = text.split("\n")
    rtl_lines = []
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            if not cleaned.startswith(RLM):
                cleaned = f"{RLM}{cleaned}"
            rtl_lines.append(cleaned)
        else:
            rtl_lines.append("")
    return "\n".join(rtl_lines)

def _to_int(val, default=None):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

# Try initializing libnotify (GIR Notify)
_libnotify_available = False
_Notify = None
_GLib = None

try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify, GLib
    Notify.init("Sebha")
    _Notify = Notify
    _GLib = GLib
    _libnotify_available = True
except Exception:
    _libnotify_available = False

# Try initializing D-Bus direct fallback
_dbus_iface = None
if not _libnotify_available:
    try:
        import dbus
        bus = dbus.SessionBus()
        notify_obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        _dbus_iface = dbus.Interface(notify_obj, "org.freedesktop.Notifications")
    except Exception:
        _dbus_iface = None

_last_count_nid = 0
_last_hadith_nid = 0
_last_general_nid = 0

def is_notify_send_available():
    return sys.platform.startswith("linux") and shutil.which("notify-send") is not None

def notify_count(zikr: str, count: int, target: int = None, benefit: str = "", mode: str = "FREE", tray_icon = None):
    """
    Sends or updates a clean native desktop notification for Dhikr counter.
    Instantly replaces any previous notification on double-click / rapid clicks.
    RTL layout, no icons, no emojis.
    """
    global _last_count_nid

    mode_str = (mode or "FREE").upper()
    t_val = _to_int(target)
    c_val = _to_int(count, 0)

    if mode_str in ("MORNING", "NIGHT"):
        base_title = "أذكار الصباح" if mode_str == "MORNING" else "أذكار المساء"
        if t_val is not None and t_val > 1:
            title = f"{base_title} - {c_val}/{t_val}"
        else:
            title = base_title
        body_lines = [_clean_text(zikr)]
    else:
        title = _clean_text(zikr) if zikr else "سبحان الله"
        if t_val is not None and t_val > 1:
            body_lines = [f"العدد: {c_val} / {t_val}"]
        elif t_val == 1:
            body_lines = []  # For thikrs with 1 count only, do not show counter
        else:
            body_lines = [f"العدد: {c_val}"]

    title = _to_rtl(title)
    body = _to_rtl("\n".join(body_lines))

    # 1. notify-send CLI (Most reliable and responsive on Linux desktops)
    if is_notify_send_available():
        cmd = [
            "notify-send",
            "-a", "Sebha",
            "-t", "2500",
            "-u", "normal",
            "-h", "string:synchronous:sebha-counter",
        ]
        if t_val is not None and t_val > 1:
            progress = max(0, min(100, int((c_val / t_val) * 100)))
            cmd.extend(["-h", f"int:value:{progress}"])
        cmd.extend([title, body])
        
        try:
            subprocess.Popen(cmd)
            return
        except Exception as e:
            print("Error executing notify-send:", e)

    # 2. Native libnotify fallback
    if _libnotify_available:
        try:
            notif = _Notify.Notification.new(title, body, "")
            notif.set_hint("transient", _GLib.Variant("b", True))
            notif.set_hint("x-canonical-private-synchronous", _GLib.Variant("s", "sebha-counter"))
            notif.set_hint("synchronous", _GLib.Variant("s", "sebha-counter"))

            if t_val is not None and t_val > 1:
                progress = max(0, min(100, int((c_val / t_val) * 100)))
                notif.set_hint("value", _GLib.Variant("i", progress))

            notif.set_timeout(2500)
            notif.show()
            return
        except Exception as e:
            print("Error executing libnotify:", e)

    # 3. Direct D-Bus fallback
    if _dbus_iface is not None:
        try:
            import dbus
            hints = {
                "transient": dbus.Boolean(True),
                "x-canonical-private-synchronous": dbus.String("sebha-counter"),
                "synchronous": dbus.String("sebha-counter")
            }
            if t_val is not None and t_val > 1:
                hints["value"] = dbus.Int32(max(0, min(100, int((c_val / t_val) * 100))))

            _last_count_nid = _dbus_iface.Notify(
                "Sebha",
                _last_count_nid,
                "",  # no icon
                title,
                body,
                [],
                hints,
                2500
            )
            return
        except Exception:
            pass

    # 4. Tray icon fallback
    if tray_icon and hasattr(tray_icon, "showMessage") and tray_icon.isSystemTrayAvailable():
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            tray_icon.showMessage(title, body, QSystemTrayIcon.Icon.NoIcon, 2500)
        except Exception:
            pass

def notify_hadith(text: str, benefit: str = "", tray_icon = None):
    """
    Sends a clean native desktop notification for a Hadith reminder.
    RTL layout, no icons, no emojis.
    """
    global _last_hadith_nid

    title = _to_rtl("حديث شريف")
    body_text = _clean_text(text)
    clean_benefit = _clean_text(benefit)
    if clean_benefit:
        body_text += f"\n\n({clean_benefit})"
    body = _to_rtl(body_text)

    # 1. notify-send CLI
    if is_notify_send_available():
        cmd = [
            "notify-send",
            "-a", "Sebha",
            "-t", "8000",
            "-u", "normal",
            "-h", "string:synchronous:sebha-hadith",
            title,
            body
        ]
        try:
            subprocess.Popen(cmd)
            return
        except Exception as e:
            print("Error executing notify-send for hadith:", e)

    # 2. Native libnotify
    if _libnotify_available:
        try:
            notif = _Notify.Notification.new(title, body, "")
            notif.set_hint("x-canonical-private-synchronous", _GLib.Variant("s", "sebha-hadith"))
            notif.set_hint("synchronous", _GLib.Variant("s", "sebha-hadith"))
            notif.set_timeout(8000)
            notif.show()
            return
        except Exception:
            pass

    # 3. Direct D-Bus fallback
    if _dbus_iface is not None:
        try:
            import dbus
            _last_hadith_nid = _dbus_iface.Notify(
                "Sebha",
                _last_hadith_nid,
                "",  # no icon
                title,
                body,
                [],
                {
                    "x-canonical-private-synchronous": dbus.String("sebha-hadith"),
                    "synchronous": dbus.String("sebha-hadith")
                },
                8000
            )
            return
        except Exception:
            pass

    # 4. Tray icon fallback
    if tray_icon and hasattr(tray_icon, "showMessage") and tray_icon.isSystemTrayAvailable():
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            tray_icon.showMessage(title, body, QSystemTrayIcon.Icon.NoIcon, 8000)
        except Exception:
            pass

def notify_session_completed(mode: str = "MORNING", tray_icon = None):
    """
    Sends a clean notification when an entire Athkar session is completed.
    RTL layout, no icons, no emojis.
    """
    global _last_general_nid

    mode_str = (mode or "MORNING").upper()
    title = _to_rtl("تقبل الله طاعتكم")
    if mode_str == "MORNING":
        body = _to_rtl("تم إتمام أذكار الصباح بنجاح")
    elif mode_str == "NIGHT":
        body = _to_rtl("تم إتمام أذكار المساء بنجاح")
    else:
        body = _to_rtl("تم إتمام الورد بنجاح")

    # 1. notify-send CLI
    if is_notify_send_available():
        cmd = [
            "notify-send",
            "-a", "Sebha",
            "-t", "5000",
            "-u", "normal",
            title,
            body
        ]
        try:
            subprocess.Popen(cmd)
            return
        except Exception as e:
            print("Error executing notify-send for session completion:", e)

    # 2. Native libnotify
    if _libnotify_available:
        try:
            notif = _Notify.Notification.new(title, body, "")
            notif.set_timeout(5000)
            notif.show()
            return
        except Exception:
            pass

    # 3. Direct D-Bus fallback
    if _dbus_iface is not None:
        try:
            _last_general_nid = _dbus_iface.Notify(
                "Sebha",
                _last_general_nid,
                "",  # no icon
                title,
                body,
                [],
                {},
                5000
            )
            return
        except Exception:
            pass

    # 4. Tray icon fallback
    if tray_icon and hasattr(tray_icon, "showMessage") and tray_icon.isSystemTrayAvailable():
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            tray_icon.showMessage(title, body, QSystemTrayIcon.Icon.NoIcon, 5000)
        except Exception:
            pass
