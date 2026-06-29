import sys
import os
import shutil
import argparse
import getpass
import subprocess
from PySide6.QtCore import Qt, Signal, QSize, QSettings, QPoint, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QIcon, QPalette, QCursor, QAction, QBrush, QPainter
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QFrame,
    QToolButton,
    QSystemTrayIcon,
    QMenu,
    QAbstractButton,
    QGraphicsOpacityEffect,
    QDialog,
    QTabWidget,
    QCheckBox,
    QPushButton,
    QMessageBox,
)
from ktoys.modules import REGISTRY


def update_desktop_file(group_name: str, key: str, value: str):
    home = os.path.expanduser("~")
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [
        os.path.join(home, ".local/share/applications/ktoys.desktop"),
        os.path.join(proj_root, "ktoys.desktop")
    ]
    
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            current_group = None
            key_updated = False
            in_target_group = False
            
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                if stripped.startswith("[") and stripped.endswith("]"):
                    if in_target_group and not key_updated:
                        if value:
                            new_lines.append(f"{key}={value}\n")
                        key_updated = True
                    current_group = stripped
                    in_target_group = (current_group == group_name)
                    new_lines.append(line)
                    i += 1
                    continue
                
                if in_target_group and stripped.split("=")[0].strip() == key:
                    if value:
                        new_lines.append(f"{key}={value}\n")
                    key_updated = True
                    i += 1
                    continue
                
                new_lines.append(line)
                i += 1
                
            if in_target_group and not key_updated and value:
                new_lines.append(f"{key}={value}\n")
                
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Error updating desktop file {path}: {e}")
            
    for cmd in ["kbuildsycoca6", "kbuildsycoca5"]:
        if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
            try:
                subprocess.run([cmd, "--noincremental"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            break


def toggle_autostart(enabled: bool):
    home = os.path.expanduser("~")
    autostart_dir = os.path.join(home, ".config", "autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    autostart_file = os.path.join(autostart_dir, "ktoys.desktop")
    
    desktop_src = os.path.join(home, ".local/share/applications/ktoys.desktop")
    if not os.path.exists(desktop_src):
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        desktop_src = os.path.join(proj_root, "ktoys.desktop")
        
    if enabled:
        if os.path.exists(desktop_src):
            try:
                shutil.copy2(desktop_src, autostart_file)
                with open(autostart_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for idx, line in enumerate(lines):
                    if line.strip().startswith("Exec=") and not line.strip().endswith("--background"):
                        lines[idx] = line.strip() + " --background\n"
                        break
                with open(autostart_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            except Exception as e:
                print(f"Error setting autostart: {e}")
    else:
        if os.path.exists(autostart_file):
            try:
                os.remove(autostart_file)
            except Exception as e:
                print(f"Error removing autostart: {e}")


class LauncherSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("KToys Settings")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setModal(True)
        self.setFixedSize(320, 240)

        self.tabs = QTabWidget()

        self.general_tab = QWidget()
        gen_layout = QVBoxLayout(self.general_tab)
        gen_layout.setContentsMargins(12, 12, 12, 12)
        gen_layout.setSpacing(12)

        gen_title = QLabel("General Behavior:")
        gen_title.setStyleSheet("font-weight: bold;")
        gen_layout.addWidget(gen_title)

        self.cb_autostart = QCheckBox("Start KToys on system login")
        self.cb_show_tray = QCheckBox("Show icon in system tray")
        self.cb_close_tray = QCheckBox("Minimize launcher to tray on close")

        self.cb_autostart.setChecked(self.settings.value("autostart", False, type=bool))
        self.cb_show_tray.setChecked(self.settings.value("show_tray", True, type=bool))
        self.cb_close_tray.setChecked(self.settings.value("minimize_to_tray", True, type=bool))

        self.cb_show_tray.toggled.connect(self.cb_close_tray.setEnabled)
        self.cb_close_tray.setEnabled(self.cb_show_tray.isChecked())

        gen_layout.addWidget(self.cb_autostart)
        gen_layout.addWidget(self.cb_show_tray)
        gen_layout.addWidget(self.cb_close_tray)
        gen_layout.addStretch()

        self.about_tab = QWidget()
        about_layout = QVBoxLayout(self.about_tab)
        about_layout.setContentsMargins(12, 12, 12, 12)
        about_layout.setSpacing(6)

        app_title = QLabel("KToys")
        app_title.setStyleSheet("font-size: 11pt; font-weight: bold; color: palette(window-text);")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_desc = QLabel("Utility suite for KDE Plasma desktop environment.")
        app_desc.setWordWrap(True)
        app_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_desc.setStyleSheet("font-size: 9pt;")

        author_label = QLabel("<b>Author:</b> Igor Stefaniak<br><b>Version:</b> 1.0.0<br><b>License:</b> MIT")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_label.setStyleSheet("font-size: 9pt;")

        about_layout.addSpacing(6)
        about_layout.addWidget(app_title)
        about_layout.addWidget(app_desc)
        about_layout.addSpacing(6)
        about_layout.addWidget(author_label)
        about_layout.addStretch()

        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.about_tab, "About")

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Save")
        self.ok_button.clicked.connect(self.save_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)

        if parent:
            self.setStyleSheet(parent.styleSheet())

    def save_and_accept(self):
        autostart_changed = self.cb_autostart.isChecked() != self.settings.value("autostart", False, type=bool)
        
        self.settings.setValue("autostart", self.cb_autostart.isChecked())
        self.settings.setValue("minimize_to_tray", self.cb_close_tray.isChecked())
        self.settings.setValue("show_tray", self.cb_show_tray.isChecked())

        if autostart_changed:
            toggle_autostart(self.cb_autostart.isChecked())

        self.accept()


class QToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(38, 20)
        self._thumb_position = 2.0
        self.animation = QPropertyAnimation(self, b"thumb_position")
        self.animation.setDuration(120)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @Property(float)
    def thumb_position(self) -> float:
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos: float):
        self._thumb_position = pos
        self.update()

    def nextCheckState(self):
        super().nextCheckState()
        self.animate(self.isChecked())

    def setChecked(self, checked: bool):
        was_checked = self.isChecked()
        super().setChecked(checked)
        if was_checked != checked:
            self._thumb_position = 20.0 if checked else 2.0
            self.update()

    def animate(self, checked: bool):
        start = self._thumb_position
        end = 20.0 if checked else 2.0
        self.animation.stop()
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = None
        p = self.parent()
        while p:
            if hasattr(p, "highlight_hex"):
                track_color = QColor(p.highlight_hex)
                break
            p = p.parent()
            
        if not track_color:
            track_color = QApplication.palette().color(QPalette.ColorRole.Highlight)
            
        track_color = track_color if self.isChecked() else QColor("#555555")
        
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        thumb_color = QColor("#ffffff")
        painter.setBrush(QBrush(thumb_color))
        thumb_diameter = self.height() - 4
        painter.drawEllipse(self._thumb_position, 2, thumb_diameter, thumb_diameter)


class ModuleCard(QFrame):
    clicked = Signal(str)
    settings_requested = Signal(str)
    status_changed = Signal(str, bool)

    def __init__(self, module_id, name, desc, icon_name, has_settings=False, is_enabled=True):
        super().__init__()
        self.module_id = module_id
        self.is_active = is_enabled
        self.setObjectName("ModuleCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("CardContent")
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self.icon_label = QLabel()
        icon = QIcon.fromTheme(icon_name, QIcon.fromTheme("applications-other"))
        self.icon_label.setPixmap(icon.pixmap(32, 32))
        self.icon_label.setFixedSize(32, 32)
        content_layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ModuleName")
        
        self.desc_label = QLabel(desc)
        self.desc_label.setObjectName("ModuleDesc")
        self.desc_label.setWordWrap(True)
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.desc_label)
        content_layout.addLayout(text_layout, 1)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.content_widget.setGraphicsEffect(self.opacity_effect)
        layout.addWidget(self.content_widget, 1)

        self.switch_widget = QToggleSwitch()
        self.switch_widget.setChecked(is_enabled)
        self.switch_widget.toggled.connect(lambda checked: self.status_changed.emit(self.module_id, checked))
        self.switch_widget.toggled.connect(self.set_active_state)
        layout.addWidget(self.switch_widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.settings_btn = None
        if has_settings:
            self.settings_btn = QToolButton()
            self.settings_btn.setIcon(QIcon.fromTheme("settings-configure", QIcon.fromTheme("preferences-system")))
            self.settings_btn.setIconSize(QSize(16, 16))
            self.settings_btn.setFixedSize(24, 24)
            self.settings_btn.setObjectName("SettingsButton")
            self.settings_btn.setToolTip("Settings")
            self.settings_btn.clicked.connect(lambda: self.settings_requested.emit(self.module_id))
            buttons_layout.addWidget(self.settings_btn)

        self.launch_btn = QToolButton()
        self.launch_btn.setIcon(QIcon.fromTheme("go-next", QIcon.fromTheme("media-playback-start")))
        self.launch_btn.setIconSize(QSize(16, 16))
        self.launch_btn.setFixedSize(24, 24)
        self.launch_btn.setObjectName("LaunchButton")
        self.launch_btn.setToolTip("Launch")
        self.launch_btn.clicked.connect(lambda: self.clicked.emit(self.module_id))
        buttons_layout.addWidget(self.launch_btn)

        layout.addLayout(buttons_layout)

        self.set_active_state(is_enabled)

    def set_active_state(self, active: bool):
        self.is_active = active
        self.opacity_effect.setOpacity(1.0 if active else 0.45)
        self.launch_btn.setEnabled(active)
        if self.settings_btn:
            self.settings_btn.setEnabled(active)
            
        if active:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_active:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(event)


class KToysLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ktoys", "Launcher")
        
        self.setWindowTitle("KToys")
        self.setWindowIcon(QIcon.fromTheme("preferences-desktop-accessories", QIcon.fromTheme("applications-other")))
        self.setMinimumSize(460, 480)
        self.resize(460, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        palette = self.palette()
        self.highlight_hex = palette.color(QPalette.ColorRole.Highlight).name()
        window_text_color = palette.color(QPalette.ColorRole.WindowText)
        self.window_text_rgba = f"rgba({window_text_color.red()}, {window_text_color.green()}, {window_text_color.blue()}, 0.75)"

        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(QIcon.fromTheme("settings-configure", QIcon.fromTheme("preferences-system")))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setObjectName("LauncherSettingsButton")
        self.settings_btn.setToolTip("KToys Settings")
        self.settings_btn.clicked.connect(self.show_settings)

        title_label = QLabel("KToys")
        title_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: palette(window-text); background: transparent;")
        
        desc_label = QLabel("A collection of utility tools and modules for KDE.")
        desc_label.setStyleSheet(f"font-size: 10pt; color: {self.window_text_rgba}; background: transparent;")

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(desc_label)
        
        header_row.addLayout(header_text_layout, 1)
        header_row.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(header_row)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search tools...")
        self.search_input.textChanged.connect(self.filter_modules)
        main_layout.addWidget(self.search_input)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setObjectName("ModulesScroll")
        
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)

        self.cards = []
        for mod_id, mod in REGISTRY.items():
            is_enabled = self.settings.value(f"modules/{mod_id}/enabled", True, type=bool)
            card = ModuleCard(mod_id, mod.get_name(), mod.get_description(), mod.get_icon(), has_settings=mod.has_settings(), is_enabled=is_enabled)
            card.clicked.connect(self.run_module)
            card.settings_requested.connect(self.show_module_settings)
            card.status_changed.connect(self.toggle_module)
            self.scroll_layout.addWidget(card)
            self.cards.append(card)

        self.no_results = QLabel("No utility tools match your search.")
        self.no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results.setStyleSheet("font-size: 10pt; color: palette(mid); margin-top: 20px;")
        self.no_results.setVisible(False)
        self.scroll_layout.addWidget(self.no_results)
        
        self.scroll_layout.addStretch(1)
        self.scroll.setWidget(scroll_content)
        main_layout.addWidget(self.scroll, 1)

        self.apply_style()
        self.setup_tray_icon()



    def apply_style(self):
        palette = self.palette()
        window_text_color = palette.color(QPalette.ColorRole.WindowText)
        desc_text_rgba = f"rgba({window_text_color.red()}, {window_text_color.green()}, {window_text_color.blue()}, 0.7)"
        
        self.setStyleSheet(
            f"""
            KToysLauncher {{
                background-color: palette(window);
                color: palette(window-text);
            }}
            QLabel {{
                background: transparent;
            }}
            QLineEdit#SearchInput {{
                background-color: palette(base);
                border: 1px solid palette(midlight);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10.5pt;
                color: palette(text);
            }}
            QLineEdit#SearchInput:focus {{
                border: 1px solid {self.highlight_hex};
            }}
            QScrollArea#ModulesScroll {{
                background: transparent;
            }}
            QScrollArea#ModulesScroll > QWidget > QWidget {{
                background: transparent;
            }}
            QFrame#ModuleCard {{
                background-color: palette(base);
                border: 1px solid palette(midlight);
                border-radius: 8px;
            }}
            QFrame#ModuleCard:hover {{
                background-color: palette(alternate-base);
                border-color: {self.highlight_hex};
            }}
            QFrame#ModuleCard QLabel {{
                background-color: transparent;
                background: transparent;
            }}
            QLabel#ModuleName {{
                color: palette(text);
                font-weight: bold;
                font-size: 11pt;
            }}
            QLabel#ModuleDesc {{
                color: {desc_text_rgba};
                font-size: 9pt;
            }}
            QToolButton#LaunchButton, QToolButton#SettingsButton, QToolButton#LauncherSettingsButton {{
                border: none;
                background-color: transparent;
                padding: 4px;
                border-radius: 4px;
            }}
            QToolButton#LaunchButton:hover, QToolButton#SettingsButton:hover, QToolButton#LauncherSettingsButton:hover {{
                background-color: palette(alternate-base);
            }}
            """
        )

    def filter_modules(self, query):
        query = query.lower()
        visible_count = 0
        for card in self.cards:
            match = query in card.name_label.text().lower() or query in card.desc_label.text().lower()
            card.setVisible(match)
            if match:
                visible_count += 1
        
        self.no_results.setVisible(visible_count == 0)

    def run_module(self, module_id, action=None):
        is_enabled = self.settings.value(f"modules/{module_id}/enabled", True, type=bool)
        if not is_enabled:
            return

        if module_id in REGISTRY:
            module = REGISTRY[module_id]
            module.launch(trigger_action=action)

    def show_module_settings(self, module_id):
        is_enabled = self.settings.value(f"modules/{module_id}/enabled", True, type=bool)
        if not is_enabled:
            return

        if module_id in REGISTRY:
            module = REGISTRY[module_id]
            module.show_settings(self)

    def toggle_module(self, module_id, enabled):
        self.settings.setValue(f"modules/{module_id}/enabled", enabled)
        self.rebuild_tray_menu()

    def show_settings(self):
        dialog = LauncherSettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.setup_tray_icon()

    def setup_tray_icon(self):
        show_tray = self.settings.value("show_tray", True, type=bool)
        if show_tray:
            if not hasattr(self, "tray_icon"):
                self.tray_icon = QSystemTrayIcon(self)
                self.tray_icon.setIcon(QIcon.fromTheme("preferences-desktop-accessories", QIcon.fromTheme("applications-other")))
                self.tray_menu = QMenu(self)
                self.tray_icon.setContextMenu(self.tray_menu)
                self.tray_icon.activated.connect(self.on_tray_activated)
            self.rebuild_tray_menu()
            self.tray_icon.show()
        else:
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()

    def rebuild_tray_menu(self):
        if not hasattr(self, "tray_menu"):
            return
            
        self.tray_menu.clear()
        
        show_action = self.tray_menu.addAction("Show Launcher")
        show_action.triggered.connect(self.show_and_activate)
        
        modules_menu = self.tray_menu.addMenu("Launch Module")
        modules_menu.setIcon(QIcon.fromTheme("run-build"))
        
        for mod_id, mod in REGISTRY.items():
            is_enabled = self.settings.value(f"modules/{mod_id}/enabled", True, type=bool)
            if is_enabled:
                action = modules_menu.addAction(mod.get_name())
                action.setIcon(QIcon.fromTheme(mod.get_icon()))
                action.triggered.connect(lambda checked=False, m_id=mod_id: self.run_module(m_id))
                
        settings_action = self.tray_menu.addAction("Settings")
        settings_action.setIcon(QIcon.fromTheme("settings-configure", QIcon.fromTheme("preferences-system")))
        settings_action.triggered.connect(self.show_settings)
        
        self.tray_menu.addSeparator()
        
        quit_action = self.tray_menu.addAction("Quit")
        quit_action.setIcon(QIcon.fromTheme("application-exit"))
        quit_action.triggered.connect(QApplication.quit)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()

    def show_and_activate(self):
        self.show()
        if self.isMaximized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        minimize_to_tray = self.settings.value("minimize_to_tray", True, type=bool)
        show_tray = self.settings.value("show_tray", True, type=bool)
        
        if minimize_to_tray and show_tray:
            event.ignore()
            self.hide()
            return

        color_picker = REGISTRY.get("color_picker")
        if color_picker and color_picker.window and (color_picker.window.isVisible() or (hasattr(color_picker.window, "tray_icon") and color_picker.window.tray_icon.isVisible())):
            event.ignore()
            self.hide()
        else:
            QApplication.quit()


def main():
    parser = argparse.ArgumentParser(description="KToys - KDE Utility Suite")
    parser.add_argument("--module", type=str, help="Module ID to run")
    parser.add_argument("--action", type=str, help="Action to invoke in the module")
    parser.add_argument("--no-pick", action="store_true", help="Prevent color picker from screen picking on launch")
    parser.add_argument("--background", action="store_true", help="Start KToys in the background (system tray)")
    args, unknown = parser.parse_known_args()

    if args.module:
        from PySide6.QtCore import QSettings
        settings = QSettings("ktoys", "Launcher")
        is_enabled = settings.value(f"modules/{args.module}/enabled", True, type=bool)
        if not is_enabled:
            print(f"Module '{args.module}' is disabled in KToys.")
            sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("KToys")
    app.setDesktopFileName("ktoys")
    app.setQuitOnLastWindowClosed(False)

    socket_name = f"ktoys_socket_{getpass.getuser()}"

    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(200):
        if args.background:
            socket.disconnectFromServer()
            return
            
        cmd = "show_launcher"
        if args.module:
            action = args.action or ""
            if args.module == "color_picker" and not args.action and not args.no_pick:
                action = "pick"
            cmd = f"run:{args.module}:{action}"
            
        socket.write(cmd.encode("utf-8"))
        socket.waitForBytesWritten(200)
        socket.disconnectFromServer()
        return

    QLocalServer.removeServer(socket_name)
    server = QLocalServer()
    if not server.listen(socket_name):
        print("KToys Local Server Error:", server.errorString())

    launcher = KToysLauncher()

    def handle_incoming_connection():
        client_socket = server.nextPendingConnection()
        if client_socket:
            if client_socket.waitForReadyRead(200):
                data = client_socket.readAll().data().decode("utf-8")
                if data.startswith("run:"):
                    parts = data.split(":")
                    mod_id = parts[1]
                    action = parts[2] if len(parts) > 2 and parts[2] else None
                    launcher.run_module(mod_id, action)
                elif data == "show_launcher":
                    launcher.show_and_activate()
            client_socket.disconnectFromServer()

    server.newConnection.connect(handle_incoming_connection)
    app.server = server

    if args.module:
        action = args.action
        if args.module == "color_picker" and not action and not args.no_pick:
            action = "pick"
        launcher.run_module(args.module, action)
    elif args.background:
        pass
    else:
        launcher.show_and_activate()

    exit_code = app.exec()
    server.close()
    QLocalServer.removeServer(socket_name)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
