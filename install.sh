#!/bin/bash

set -e

echo "=== Installing KToys ==="

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed in the system." >&2
    exit 1
fi

INSTALL_DIR="$HOME/.local/share/ktoys"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Stopping any running KToys or old Color Picker processes..."
pkill -f ktoys || true
pkill -f color-picker-kde || true
pkill -f main.py || true

echo "1. Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

echo "2. Copying application files..."
rm -rf "$INSTALL_DIR/ktoys"
cp -r ktoys "$INSTALL_DIR/"
cp main.py "$INSTALL_DIR/main.py"
chmod +x "$INSTALL_DIR/main.py"
cp ktoys.desktop "$INSTALL_DIR/ktoys.desktop"

echo "3. Creating Python virtual environment (venv)..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    if ! python3 -m venv "$INSTALL_DIR/venv"; then
        echo "Error: Failed to create virtual environment." >&2
        echo "Make sure python3-venv package is installed (e.g. sudo apt install python3-venv or sudo dnf install python3-virtualenv)." >&2
        exit 1
    fi
fi

echo "4. Installing dependencies (PySide6) in venv..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install PySide6

echo "5. Configuring .desktop file..."
DESKTOP_FILE="$DESKTOP_DIR/ktoys.desktop"
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"
MAIN_SCRIPT="$INSTALL_DIR/main.py"

DEFAULT_SHORTCUT="Meta+Shift+C"
SETTINGS_FILE="$HOME/.config/ktoys/ColorPicker.conf"
if [ -f "$SETTINGS_FILE" ]; then
    SAVED_SHORTCUT=$(grep -i '^shortcut=' "$SETTINGS_FILE" | cut -d'=' -f2 | tr -d '\r\n')
    if [ -n "$SAVED_SHORTCUT" ]; then
        DEFAULT_SHORTCUT="$SAVED_SHORTCUT"
        echo "Detected previously set shortcut: $DEFAULT_SHORTCUT"
    fi
fi

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=KToys
Comment=Utility suite for KDE
Exec=$BIN_DIR/ktoys
Icon=preferences-desktop-accessories
Terminal=false
Categories=Utility;
Actions=ColorPicker;

[Desktop Action ColorPicker]
Name=KColorPicker
Exec=$BIN_DIR/ktoys --module color_picker
Icon=color-picker
X-KDE-Shortcuts=$DEFAULT_SHORTCUT
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

echo "6. Creating launcher in ~/.local/bin..."
cat <<EOF > "$BIN_DIR/ktoys"
#!/bin/bash
exec "$VENV_PYTHON" "$MAIN_SCRIPT" "\$@"
EOF
chmod +x "$BIN_DIR/ktoys"

rm -f "$DESKTOP_DIR/color-picker-kde.desktop"
rm -f "$BIN_DIR/color-picker-kde"

for cmd in "kbuildsycoca6" "kbuildsycoca5"; do
    if command -v "$cmd" &> /dev/null; then
        echo "Refreshing KDE system configuration cache with $cmd..."
        "$cmd" --noincremental &> /dev/null || true
        break
    fi
done

echo "Starting KToys launcher in the background..."
nohup "$BIN_DIR/ktoys" > /dev/null 2>&1 &

echo "=== Installation completed successfully ==="
echo "Program was installed in: $INSTALL_DIR"
echo "Application source code (editable) is located in: $INSTALL_DIR/ktoys/"
echo "KDE activation shortcut (current: $DEFAULT_SHORTCUT) has been registered."
echo "Terminal launcher shortcut: $BIN_DIR/ktoys"
echo ""
echo "For the keyboard shortcut to start working, the KDE Plasma system must read the new shortcut from the .desktop file."
echo "This usually happens automatically, but in some cases a relogin might be required."
