#!/bin/bash

set -e

echo "=== Installing KDE Color Picker ==="

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed in the system." >&2
    exit 1
fi

INSTALL_DIR="$HOME/.local/share/color-picker-kde"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "1. Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

echo "2. Copying application files..."
cp main.py "$INSTALL_DIR/main.py"
chmod +x "$INSTALL_DIR/main.py"
cp color-picker-kde.desktop "$INSTALL_DIR/color-picker-kde.desktop"

echo "3. Creating Python virtual environment (venv)..."
if ! python3 -m venv "$INSTALL_DIR/venv"; then
    echo "Error: Failed to create virtual environment." >&2
    echo "Make sure python3-venv package is installed (e.g. sudo apt install python3-venv or sudo dnf install python3-virtualenv)." >&2
    exit 1
fi

echo "4. Installing dependencies (PySide6) in venv..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install PySide6

echo "5. Configuring .desktop file..."
DESKTOP_FILE="$DESKTOP_DIR/color-picker-kde.desktop"
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"
MAIN_SCRIPT="$INSTALL_DIR/main.py"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=Color Picker
Comment=KDE Color Picker
Exec=$VENV_PYTHON $MAIN_SCRIPT
Icon=color-picker
Terminal=false
Categories=Utility;Graphics;
StartupWMClass=color-picker-kde
EOF

DEFAULT_SHORTCUT="Meta+Shift+C"
SETTINGS_FILE="$HOME/.config/color-picker-kde/ColorPicker.conf"
if [ -f "$SETTINGS_FILE" ]; then
    SAVED_SHORTCUT=$(grep -i '^shortcut=' "$SETTINGS_FILE" | cut -d'=' -f2 | tr -d '\r\n')
    if [ -n "$SAVED_SHORTCUT" ]; then
        DEFAULT_SHORTCUT="$SAVED_SHORTCUT"
        echo "Detected previously set shortcut: $DEFAULT_SHORTCUT"
    fi
fi

echo "X-KDE-Shortcuts=$DEFAULT_SHORTCUT" >> "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"

echo "6. Creating launcher in ~/.local/bin..."
cat <<EOF > "$BIN_DIR/color-picker-kde"
#!/bin/bash
exec "$VENV_PYTHON" "$MAIN_SCRIPT" "\$@"
EOF
chmod +x "$BIN_DIR/color-picker-kde"

echo "=== Installation completed successfully ==="
echo "Program was installed in: $INSTALL_DIR"
echo "Application source code (editable) is located in: $INSTALL_DIR/main.py"
echo "KDE activation shortcut (current: $DEFAULT_SHORTCUT) has been registered."
echo "Terminal launcher shortcut: $BIN_DIR/color-picker-kde"
echo ""
echo "For the keyboard shortcut to start working, the KDE Plasma system must read the new shortcut from the .desktop file."
echo "This usually happens automatically, but in some cases a relogin might be required."
