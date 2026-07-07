import os
import sys

def configure_startup():
    if sys.platform != "win32":
        print("Startup configuration is only supported on Windows.")
        return

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
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            cmd = f'"{exe_path}"'
        else:
            pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.pyw')
            cmd = f'"{pythonw_exe}" "{script_path}"'
            
        winreg.SetValueEx(key, "Sebha", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("Successfully registered Sebha in Windows Startup registry.")
        print(f"Command registered: {cmd}")
        print("The app will now start automatically in the background when you log in.")
    except Exception as e:
        print(f"Error registering startup: {e}")

if __name__ == '__main__':
    configure_startup()
