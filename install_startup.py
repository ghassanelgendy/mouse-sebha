import os
import sys

def configure_startup(enable=True):
    if sys.platform == "win32":
        # Clean up old shortcut if it exists to avoid duplicate launches
        try:
            startup_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_dir, 'Sebha.lnk')
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print("Removed old Startup folder shortcut.")
        except Exception as e:
            print(f"Note: Could not check/remove old shortcut: {e}")

        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enable:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                    cmd = f'"{exe_path}"'
                else:
                    pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                    if not os.path.exists(pythonw_exe):
                        pythonw_exe = sys.executable
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.pyw')
                    cmd = f'"{pythonw_exe}" "{script_path}"'
                winreg.SetValueEx(key, "Sebha", 0, winreg.REG_SZ, cmd)
                print("Successfully registered Sebha in Windows Startup registry.")
                print(f"Command registered: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, "Sebha")
                    print("Removed Sebha from Windows Startup registry.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error configuring Windows startup: {e}")

    elif sys.platform.startswith("linux"):
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = os.path.join(autostart_dir, "sebha.desktop")
        
        if enable:
            try:
                os.makedirs(autostart_dir, exist_ok=True)
                if getattr(sys, 'frozen', False):
                    exec_cmd = f'"{sys.executable}"'
                else:
                    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.pyw"))
                    exec_cmd = f'"{sys.executable}" "{script_path}"'
                    
                content = f"""[Desktop Entry]
Type=Application
Name=Sebha
Comment=Mouse Sebha Athkar Overlay
Exec={exec_cmd}
Icon=sebha
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(content)
                os.chmod(desktop_file, 0o755)
                print(f"Successfully configured Linux autostart: {desktop_file}")
            except Exception as e:
                print(f"Error configuring Linux autostart: {e}")
        else:
            if os.path.exists(desktop_file):
                try:
                    os.remove(desktop_file)
                    print(f"Removed Linux autostart file: {desktop_file}")
                except Exception as e:
                    print(f"Error removing Linux autostart: {e}")
    else:
        print(f"Startup configuration is not supported on platform: {sys.platform}")

if __name__ == '__main__':
    configure_startup(enable=True)

