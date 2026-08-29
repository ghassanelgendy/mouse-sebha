import os
import sys
import shutil
import subprocess
import re
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtDBus import QDBusConnection

NOTIFICATION_REPLACE_ID = 42100

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

# Unified tracking set and ID to guarantee replacing older notifications and ignoring other apps
_sent_notification_ids = {NOTIFICATION_REPLACE_ID}
_last_notification_id = 0

class NotificationListener(QObject):
    notification_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False

    @pyqtSlot(int, str)
    def handle_action(self, nid, action_key):
        if int(nid) in _sent_notification_ids or (int(nid) == _last_notification_id and _last_notification_id > 0):
            self.notification_clicked.emit()

_global_listener = None

def get_notification_listener() -> NotificationListener:
    global _global_listener
    if _global_listener is None:
        _global_listener = NotificationListener()
    return _global_listener

_dbus_bus = None
_dbus_iface = None
_dbus_listener_active = False

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    _dbus_bus = dbus.SessionBus()
    _notify_obj = _dbus_bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
    _dbus_iface = dbus.Interface(_notify_obj, "org.freedesktop.Notifications")
    
    def _on_dbus_action_invoked(nid, action_key):
        if int(nid) in _sent_notification_ids or (int(nid) == _last_notification_id and _last_notification_id > 0):
            listener = get_notification_listener()
            listener.notification_clicked.emit()

    _dbus_bus.add_signal_receiver(
        _on_dbus_action_invoked,
        signal_name="ActionInvoked",
        dbus_interface="org.freedesktop.Notifications",
        path="/org/freedesktop/Notifications"
    )
    _dbus_listener_active = True
except Exception as e:
    _dbus_iface = None
    _dbus_bus = None

# If native dbus-python listener wasn't registered, fallback to QtDBus
if not _dbus_listener_active:
    try:
        _qbus = QDBusConnection.sessionBus()
        if _qbus.isConnected():
            listener = get_notification_listener()
            _qbus.connect(
                "",
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications",
                "ActionInvoked",
                listener.handle_action
            )
    except Exception:
        pass

# Libnotify setup
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

def is_notify_send_available():
    return sys.platform.startswith("linux") and shutil.which("notify-send") is not None

def close_current_notification():
    global _last_notification_id, _dbus_iface
    if _dbus_iface is not None and _last_notification_id > 0:
        try:
            import dbus
            _dbus_iface.CloseNotification(dbus.UInt32(_last_notification_id))
        except Exception:
            pass

def _send_desktop_notification(title: str, body: str, timeout_ms: int = 4000, progress: int = None, tray_icon = None):
    global _last_notification_id, _dbus_iface, _sent_notification_ids

    # Ensure notification listener is initialized
    get_notification_listener()

    # 1. Direct D-Bus (Fastest, zero process overhead, native unicast action & replacement support)
    if _dbus_iface is not None:
        try:
            import dbus
            hints = {
                "transient": dbus.Boolean(True),
                "synchronous": dbus.String("sebha-notification"),
                "x-canonical-private-synchronous": dbus.String("sebha-notification"),
                "urgency": dbus.Byte(1)
            }
            if progress is not None:
                hints["value"] = dbus.Int32(max(0, min(100, int(progress))))

            # 'default' enables clicking the notification banner/menu item directly,
            # 'choose_athkar' shows an explicit interactive button in GNOME/KDE
            actions = dbus.Array(["default", "اختيار الورد", "choose_athkar", "📿 اختيار الورد"], signature="s")
            replaces_id = dbus.UInt32(_last_notification_id if _last_notification_id > 0 else 0)

            nid = _dbus_iface.Notify(
                "Sebha",
                replaces_id,
                "",  # no icon
                title,
                body,
                actions,
                hints,
                dbus.Int32(timeout_ms)
            )
            _last_notification_id = int(nid)
            _sent_notification_ids.add(int(nid))
            if len(_sent_notification_ids) > 50:
                _sent_notification_ids.clear()
                _sent_notification_ids.add(NOTIFICATION_REPLACE_ID)
                _sent_notification_ids.add(int(nid))
            return
        except Exception as e:
            print("Error executing direct D-Bus Notify:", e)

    # 2. notify-send CLI with replacement ID
    if is_notify_send_available():
        replace_id_arg = str(_last_notification_id if _last_notification_id > 0 else NOTIFICATION_REPLACE_ID)
        cmd = [
            "notify-send",
            "-a", "Sebha",
            "-r", replace_id_arg,
            "-t", str(timeout_ms),
            "-u", "normal",
            "-h", "string:synchronous:sebha-notification",
            "-h", "string:x-canonical-private-synchronous:sebha-notification"
        ]
        if progress is not None:
            cmd.extend(["-h", f"int:value:{int(progress)}"])
        cmd.extend([title, body])

        try:
            subprocess.Popen(cmd)
            _last_notification_id = NOTIFICATION_REPLACE_ID
            _sent_notification_ids.add(NOTIFICATION_REPLACE_ID)
            return
        except Exception as e:
            print("Error executing notify-send:", e)

    # 3. Native libnotify fallback
    if _libnotify_available:
        try:
            notif = _Notify.Notification.new(title, body, "")
            notif.set_hint("transient", _GLib.Variant("b", True))
            notif.set_hint("x-canonical-private-synchronous", _GLib.Variant("s", "sebha-notification"))
            notif.set_hint("synchronous", _GLib.Variant("s", "sebha-notification"))
            if _last_notification_id > 0:
                notif.set_hint("replaces-id", _GLib.Variant("u", _last_notification_id))

            if progress is not None:
                notif.set_hint("value", _GLib.Variant("i", int(progress)))

            def _on_libnotify_action(n, action, user_data=None):
                listener = get_notification_listener()
                listener.notification_clicked.emit()

            notif.add_action("default", "اختيار الورد", _on_libnotify_action)
            notif.add_action("choose_athkar", "📿 اختيار الورد", _on_libnotify_action)

            notif.set_timeout(timeout_ms)
            notif.show()
            return
        except Exception as e:
            print("Error executing libnotify:", e)

    # 4. Tray icon fallback (Windows / environments without native notification server)
    if tray_icon and hasattr(tray_icon, "showMessage") and tray_icon.isSystemTrayAvailable():
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            tray_icon.showMessage(title, body, QSystemTrayIcon.Icon.NoIcon, timeout_ms)
        except Exception:
            pass

def notify_count(zikr: str, count: int, target: int = None, benefit: str = "", mode: str = "FREE", tray_icon = None):
    """
    Sends or updates a clean native desktop notification for Dhikr counter.
    Instantly replaces/erases any previous notification in the notifications menu.
    RTL layout, no icons, no emojis.
    """
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
            body_lines = []
        else:
            body_lines = [f"العدد: {c_val}"]

    title = _to_rtl(title)
    body = _to_rtl("\n".join(body_lines))

    progress = None
    if t_val is not None and t_val > 1:
        progress = max(0, min(100, int((c_val / t_val) * 100)))

    _send_desktop_notification(title, body, timeout_ms=3000, progress=progress, tray_icon=tray_icon)

def notify_hadith(text: str, benefit: str = "", tray_icon = None):
    """
    Sends a clean native desktop notification for a Hadith reminder.
    Replaces/erases older notifications in the menu.
    """
    title = _to_rtl("حديث شريف")
    body_text = _clean_text(text)
    clean_benefit = _clean_text(benefit)
    if clean_benefit:
        body_text += f"\n\n({clean_benefit})"
    body = _to_rtl(body_text)

    _send_desktop_notification(title, body, timeout_ms=8000, tray_icon=tray_icon)

def notify_session_completed(mode: str = "MORNING", tray_icon = None):
    """
    Sends a clean notification when an entire Athkar session is completed.
    Replaces/erases older notifications in the menu.
    """
    mode_str = (mode or "MORNING").upper()
    title = _to_rtl("تقبل الله طاعتكم")
    if mode_str == "MORNING":
        body = _to_rtl("تم إتمام أذكار الصباح بنجاح")
    elif mode_str == "NIGHT":
        body = _to_rtl("تم إتمام أذكار المساء بنجاح")
    else:
        body = _to_rtl("تم إتمام الورد بنجاح")

    _send_desktop_notification(title, body, timeout_ms=5000, tray_icon=tray_icon)
