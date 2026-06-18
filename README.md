# KDE Color Picker

A PySide6-based color picker for KDE Plasma.

## Features

- **Screen Magnifier:** Select pixels with zoom.
- **Controls:**
  - `Mouse Move` to target.
  - `Scroll Wheel` to adjust zoom.
  - `Arrow Keys` for pixel-by-pixel movement.
  - `Left Click` / `Enter` / `Space` to select color (auto-copies to clipboard).
  - `Right Click` / `Escape` to cancel.
- **History & Formats:**
  - Supports HEX, RGB, HSL, and HSV.
  - Keeps history of the last 8 colors.
  - Customizable color formats and prefixes.
- **KDE Integration:**
  - Runs in system tray.
  - Global activation shortcut (`Meta+Shift+C` by default, configurable).
  - Single instance enforcement (new launches trigger the picker in the active instance).

## Prerequisites

Python 3 and `venv` are required.

- **Ubuntu/Debian:** `sudo apt install python3 python3-venv`
- **Fedora:** `sudo dnf install python3 python3-virtualenv`
- **Arch/Manjaro:** `sudo pacman -S python`

## Installation

Run the installer:

```bash
./install.sh
```

The installer:
1. Copies files to `~/.local/share/color-picker-kde/`.
2. Sets up a virtual environment and installs `PySide6`.
3. Adds launcher to `~/.local/bin/color-picker-kde`.
4. Registers `color-picker-kde.desktop` in `~/.local/share/applications/` with default shortcut `Meta+Shift+C`.

## Usage

- **Start:** Run `color-picker-kde` or use the global shortcut `Meta+Shift+C`.
- **System Tray:** Right-click tray icon to open settings or exit.
