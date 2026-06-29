# KToys

A PySide6-based utility suite and launcher for the KDE Plasma desktop environment.

## Features

### KToys Launcher
- Searchable dashboard of custom utilities.
- Quick system tray integration.
- Custom module activation and toggles.

### KColorPicker Module
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

### KDE Integration
- System Tray support with minimize-to-tray.
- Global activation shortcuts (e.g. `Meta+Shift+C` for KColorPicker, configurable in KColorPicker settings).
- Single-instance enforcement using local sockets.

## Prerequisites

Python 3 and `venv` are required.

- **Ubuntu/Debian:** `sudo apt install python3 python3-venv`
- **Fedora:** `sudo dnf install python3`
- **Arch/Manjaro:** `sudo pacman -S python`

## Installation

Run the installer:

```bash
./install.sh
```

The installer:
1. Copies files to `~/.local/share/ktoys/`.
2. Sets up a virtual environment and installs `PySide6`.
3. Adds the launcher to `~/.local/bin/ktoys`.
4. Registers `ktoys.desktop` in `~/.local/share/applications/`.

## Usage

- **Start Launcher:** Run `ktoys` or start KToys from your application menu.
- **Start Color Picker directly:** Run `ktoys --module color_picker` or use the global shortcut `Meta+Shift+C`.
- **System Tray:** Use the system tray icon to launch modules, open settings, or exit.
