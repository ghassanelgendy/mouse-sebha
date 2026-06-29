import os
import sys
import subprocess

def create_startup_shortcut():
    startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
    shortcut_path = os.path.join(startup_dir, 'Sebha.lnk')
    
    pythonw_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    script_path = os.path.abspath('main.pyw')
    working_dir = os.path.abspath('.')

    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{pythonw_exe}"
$Shortcut.Arguments = '"{script_path}"'
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Save()
'''

    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print(f"Startup shortcut created successfully at:\\n{shortcut_path}")
        print("The app will now start automatically in the background when you turn on your PC.")
    except Exception as e:
        print(f"Error creating shortcut: {e}")

if __name__ == '__main__':
    create_startup_shortcut()
