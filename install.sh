#!/bin/bash
set -e

echo "========================================="
echo "   Mouse Sebha - Linux Installer"
echo "========================================="

# User directories
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to run sudo if available without hanging
run_sudo_apt() {
    if command -v sudo &> /dev/null; then
        sudo -n true 2>/dev/null && sudo "$@" || true
    elif [ "$(id -u)" -eq 0 ]; then
        "$@" || true
    fi
}

# Check system Qt & XCB dependencies on Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    if ! ldconfig -p 2>/dev/null | grep -q "libxcb-cursor.so.0"; then
        echo "[+] Attempting to install system Qt & XCB dependencies..."
        run_sudo_apt apt-get update -qq
        run_sudo_apt apt-get install -y -qq libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libgl1
    fi
fi

# Check if running in source repository with python code
EXE_SRC=""
if [ -f "$SCRIPT_DIR/main.pyw" ]; then
    echo "[+] Found Python source repository at $SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/dist/Sebha-Linux" ]; then
    EXE_SRC="$SCRIPT_DIR/dist/Sebha-Linux"
elif [ -f "$SCRIPT_DIR/Sebha-Linux" ]; then
    EXE_SRC="$SCRIPT_DIR/Sebha-Linux"
fi

if [ -n "$EXE_SRC" ]; then
    echo "[+] Found binary executable: $EXE_SRC"
    echo "[+] Copying binary to $INSTALL_DIR/sebha..."
    cp "$EXE_SRC" "$INSTALL_DIR/sebha"
    chmod +x "$INSTALL_DIR/sebha"
    EXEC_CMD="$INSTALL_DIR/sebha"
else
    echo "[!] Sebha-Linux binary executable not found in current folder or Downloads."
    echo "[+] Setting up Python environment..."
    
    if command -v python3 &> /dev/null; then
        # Check if pip is available
        if ! python3 -m pip --version &> /dev/null; then
            echo "[+] Attempting to install python3-pip..."
            run_sudo_apt apt-get install -y python3-pip python3-venv
        fi
        
        echo "[+] Installing required Python packages..."
        python3 -m pip install --break-system-packages -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" || true
        
        # Create launcher script wrapper
        WRAPPER_PATH="$INSTALL_DIR/sebha"
        cat << EOF > "$WRAPPER_PATH"
#!/bin/bash
export QT_QPA_PLATFORM="wayland;xcb"
cd "$SCRIPT_DIR"
exec python3 "$SCRIPT_DIR/main.pyw" "\$@"
EOF
        chmod +x "$WRAPPER_PATH"
        EXEC_CMD="$WRAPPER_PATH"
    else
        echo "[!] Error: Neither Sebha-Linux binary nor python3 found!"
        exit 1
    fi
fi

# Copy icon if present
if [ -f "$SCRIPT_DIR/assets/logo.png" ]; then
    echo "[+] Installing app icon..."
    cp "$SCRIPT_DIR/assets/logo.png" "$ICON_DIR/sebha.png"
fi

# Create desktop launcher file
DESKTOP_FILE="$DESKTOP_DIR/sebha.desktop"
echo "[+] Creating desktop shortcut at $DESKTOP_FILE..."
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=Sebha
Comment=Mouse Sebha - Athkar Companion Overlay
Exec=$EXEC_CMD
Icon=sebha
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$DESKTOP_FILE"

# Make sure ~/.local/bin is in PATH output note
echo ""
echo "========================================="
echo "   Installation Completed Successfully!"
echo "========================================="
echo "You can now launch 'Sebha' from your Applications Menu."
echo "Or run in terminal: $EXEC_CMD"
