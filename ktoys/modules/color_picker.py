import sys
import os
import subprocess
from PySide6.QtCore import Qt, QObject, Signal, Slot, QSize, QSettings, QPoint, QRect
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QBrush, QPainterPath, QFont, QMouseEvent, QKeyEvent, QWheelEvent, QCursor, QPalette, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QFrame,
    QMessageBox,
    QColorDialog,
    QDialog,
    QTabWidget,
    QCheckBox,
    QKeySequenceEdit,
    QSystemTrayIcon,
    QMenu,
)
from ktoys.modules.base import BaseModule


class CustomColorPicker(QWidget):
    color_selected = Signal(int, int, int)
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.BypassWindowManagerHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.geom = screen.geometry()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
        self.setGeometry(self.geom)
        self.ratio = screen.devicePixelRatio()
        
        self.screenshot = screen.grabWindow(
            0, 0, 0, self.geom.width(), self.geom.height()
        )
        self.screenshot.setDevicePixelRatio(self.ratio)
        self.image = self.screenshot.toImage()
        
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.zoom_factor = 12
        self.mouse_pos = self.mapFromGlobal(QCursor.pos())
        self.phys_x = int(self.mouse_pos.x() * self.ratio)
        self.phys_y = int(self.mouse_pos.y() * self.ratio)

    def closeEvent(self, event):
        try:
            self.releaseKeyboard()
        except:
            pass
        super().closeEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_pos = event.position().toPoint()
        self.phys_x = int(self.mouse_pos.x() * self.ratio)
        self.phys_y = int(self.mouse_pos.y() * self.ratio)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self.geom.contains(QCursor.pos()):
            try:
                self.grabKeyboard()
                self.setFocus()
            except:
                pass

    def leaveEvent(self, event):
        self.mouse_pos = QPoint(-9999, -9999)
        self.phys_x = -9999
        self.phys_y = -9999
        try:
            self.releaseKeyboard()
        except:
            pass
        self.update()

    def enterEvent(self, event):
        self.mouse_pos = self.mapFromGlobal(QCursor.pos())
        self.phys_x = int(self.mouse_pos.x() * self.ratio)
        self.phys_y = int(self.mouse_pos.y() * self.ratio)
        try:
            self.grabKeyboard()
            self.setFocus()
        except:
            pass
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if 0 <= self.phys_x < self.image.width() and 0 <= self.phys_y < self.image.height():
                color = QColor(self.image.pixel(self.phys_x, self.phys_y))
                self.color_selected.emit(color.red(), color.green(), color.blue())
            else:
                self.cancelled.emit()
            self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancelled.emit()
            self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if 0 <= self.phys_x < self.image.width() and 0 <= self.phys_y < self.image.height():
                color = QColor(self.image.pixel(self.phys_x, self.phys_y))
                self.color_selected.emit(color.red(), color.green(), color.blue())
            else:
                self.cancelled.emit()
            self.close()
        elif event.key() == Qt.Key.Key_Left:
            self.phys_x = max(0, self.phys_x - 1)
            self.mouse_pos = QPoint(int(self.phys_x / self.ratio), int(self.phys_y / self.ratio))
            self.update()
        elif event.key() == Qt.Key.Key_Right:
            self.phys_x = min(self.image.width() - 1, self.phys_x + 1)
            self.mouse_pos = QPoint(int(self.phys_x / self.ratio), int(self.phys_y / self.ratio))
            self.update()
        elif event.key() == Qt.Key.Key_Up:
            self.phys_y = max(0, self.phys_y - 1)
            self.mouse_pos = QPoint(int(self.phys_x / self.ratio), int(self.phys_y / self.ratio))
            self.update()
        elif event.key() == Qt.Key.Key_Down:
            self.phys_y = min(self.image.height() - 1, self.phys_y + 1)
            self.mouse_pos = QPoint(int(self.phys_x / self.ratio), int(self.phys_y / self.ratio))
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor = min(30, self.zoom_factor + 2)
        elif delta < 0:
            self.zoom_factor = max(4, self.zoom_factor - 2)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.drawPixmap(0, 0, self.screenshot)
        
        if not self.rect().contains(self.mouse_pos):
            return
            
        phys_x = self.phys_x
        phys_y = self.phys_y
        
        if 0 <= phys_x < self.image.width() and 0 <= phys_y < self.image.height():
            hover_color = QColor(self.image.pixel(phys_x, phys_y))
        else:
            hover_color = QColor(0, 0, 0)
            
        palette = self.palette()
        bg_color = palette.color(QPalette.ColorRole.Window)
        bubble_bg = QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 230)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        border_color = palette.color(QPalette.ColorRole.Mid)
        accent_color = palette.color(QPalette.ColorRole.Highlight)

        loupe_radius = 70
        loupe_diameter = loupe_radius * 2
        
        cols = loupe_diameter // self.zoom_factor
        if cols % 2 == 0:
            cols += 1
        rows = cols
        
        grid_width = cols * self.zoom_factor
        grid_height = rows * self.zoom_factor
        
        offset_x = (loupe_diameter - grid_width) / 2
        offset_y = (loupe_diameter - grid_height) / 2
        
        clip_path = QPainterPath()
        clip_path.addEllipse(self.mouse_pos.x() - loupe_radius, self.mouse_pos.y() - loupe_radius, loupe_diameter, loupe_diameter)
        
        painter.save()
        painter.setClipPath(clip_path)
        painter.fillRect(self.mouse_pos.x() - loupe_radius, self.mouse_pos.y() - loupe_radius, loupe_diameter, loupe_diameter, QColor(20, 20, 20))
        
        start_x = phys_x - cols // 2
        start_y = phys_y - rows // 2
        
        for r in range(rows):
            for c in range(cols):
                px = start_x + c
                py = start_y + r
                if 0 <= px < self.image.width() and 0 <= py < self.image.height():
                    color = QColor(self.image.pixel(px, py))
                else:
                    color = QColor(0, 0, 0)
                
                rect_x = self.mouse_pos.x() - loupe_radius + offset_x + c * self.zoom_factor
                rect_y = self.mouse_pos.y() - loupe_radius + offset_y + r * self.zoom_factor
                painter.fillRect(rect_x, rect_y, self.zoom_factor, self.zoom_factor, color)
                
        if self.zoom_factor >= 8:
            grid_pen = QPen(QColor(128, 128, 128, 80), 1)
            painter.setPen(grid_pen)
            
            for c in range(cols + 1):
                lx = self.mouse_pos.x() - loupe_radius + offset_x + c * self.zoom_factor
                painter.drawLine(lx, self.mouse_pos.y() - loupe_radius, lx, self.mouse_pos.y() + loupe_radius)
            for r in range(rows + 1):
                ly = self.mouse_pos.y() - loupe_radius + offset_y + r * self.zoom_factor
                painter.drawLine(self.mouse_pos.x() - loupe_radius, ly, self.mouse_pos.x() + loupe_radius, ly)
                
        center_x = self.mouse_pos.x() - loupe_radius + offset_x + (cols // 2) * self.zoom_factor
        center_y = self.mouse_pos.y() - loupe_radius + offset_y + (rows // 2) * self.zoom_factor
        
        brightness = hover_color.red() * 0.299 + hover_color.green() * 0.587 + hover_color.blue() * 0.114
        center_border = Qt.GlobalColor.white if brightness < 128 else Qt.GlobalColor.black
        
        painter.setPen(QPen(center_border, 1))
        painter.drawRect(center_x, center_y, self.zoom_factor, self.zoom_factor)
        
        painter.restore()
        
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
        painter.drawEllipse(self.mouse_pos.x() - loupe_radius - 1, self.mouse_pos.y() - loupe_radius - 1, loupe_diameter + 2, loupe_diameter + 2)
        
        magnifier_color = text_color
        painter.setPen(QPen(magnifier_color, 3))
        painter.drawEllipse(self.mouse_pos.x() - loupe_radius, self.mouse_pos.y() - loupe_radius, loupe_diameter, loupe_diameter)
        
        inner_contrast = QColor(255, 255, 255, 120) if magnifier_color.lightnessF() < 0.6 else QColor(0, 0, 0, 80)
        painter.setPen(QPen(inner_contrast, 1))
        painter.drawEllipse(self.mouse_pos.x() - loupe_radius + 2, self.mouse_pos.y() - loupe_radius + 2, loupe_diameter - 4, loupe_diameter - 4)
        
        info_w, info_h = 130, 44
        info_x = self.mouse_pos.x() - info_w // 2
        info_y = self.mouse_pos.y() + loupe_radius + 10
        
        if info_y + info_h > self.geom.height():
            info_y = self.mouse_pos.y() - loupe_radius - info_h - 10
            
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bubble_bg))
        painter.drawRoundedRect(info_x, info_y, info_w, info_h, 4, 4)
        
        font = self.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        hex_str = hover_color.name(QColor.NameFormat.HexRgb).upper()
        rgb_str = f"{hover_color.red()},{hover_color.green()},{hover_color.blue()}"
        
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(hover_color))
        painter.drawRect(info_x + 8, info_y + 8, 14, 28)
        
        painter.setPen(QPen(text_color))
        painter.drawText(info_x + 30, info_y + 20, hex_str)
        
        font.setBold(False)
        font.setPointSize(7)
        painter.setFont(font)
        painter.drawText(info_x + 30, info_y + 32, rgb_str)


class ColorDot(QPushButton):
    selected = Signal(QColor)

    def __init__(self, color: str):
        super().__init__()

        self.color = QColor(color)
        self.active = False

        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.clicked.connect(lambda: self.selected.emit(self.color))

    def set_active(self, active: bool):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(3, 3, -3, -3)

        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)

        if self.active:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#8a8a8a"), 2))
            painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))


class CopyRow(QFrame):
    copy_requested = Signal(str)

    def __init__(self, name: str):
        super().__init__()

        self.setObjectName("CopyRow")

        self.name_label = QLabel(name)
        self.name_label.setObjectName("NameLabel")
        self.name_label.setFixedWidth(44)
        self.name_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("")
        self.value_label.setObjectName("ValueLabel")
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.copy_button = QToolButton()
        self.copy_button.setObjectName("CopyButton")
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_button.setIconSize(QSize(16, 16))
        self.copy_button.setToolTip("Copy")
        self.copy_button.clicked.connect(self.copy)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)
        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(self.copy_button)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def value(self):
        return self.value_label.text()

    def copy(self):
        self.copy_requested.emit(self.value())


class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setModal(True)
        self.setFixedSize(320, 395)

        self.tabs = QTabWidget()

        self.formats_tab = QWidget()
        formats_layout = QVBoxLayout(self.formats_tab)
        formats_layout.setContentsMargins(12, 12, 12, 12)
        formats_layout.setSpacing(8)

        formats_label = QLabel("Choose visible save formats:")
        formats_label.setStyleSheet("font-weight: bold;")
        formats_layout.addWidget(formats_label)

        self.cb_hex = QCheckBox("HEX")
        self.cb_include_hash = QCheckBox("Add '#' symbol before HEX")
        self.cb_include_hash.setStyleSheet("margin-left: 15px;")
        self.cb_hex.toggled.connect(self.cb_include_hash.setEnabled)
        self.cb_rgb = QCheckBox("RGB")
        self.cb_include_rgb_prefix = QCheckBox("Add 'rgb()'")
        self.cb_include_rgb_prefix.setStyleSheet("margin-left: 15px;")
        self.cb_rgb.toggled.connect(self.cb_include_rgb_prefix.setEnabled)

        self.cb_hsl = QCheckBox("HSL")
        self.cb_include_hsl_prefix = QCheckBox("Add 'hsl()'")
        self.cb_include_hsl_prefix.setStyleSheet("margin-left: 15px;")
        self.cb_hsl.toggled.connect(self.cb_include_hsl_prefix.setEnabled)
        self.cb_hsv = QCheckBox("HSV")
        self.cb_include_hsv_prefix = QCheckBox("Add 'hsv()'")
        self.cb_include_hsv_prefix.setStyleSheet("margin-left: 15px;")
        self.cb_hsv.toggled.connect(self.cb_include_hsv_prefix.setEnabled)
        self.cb_hex.setChecked(self.settings.value("show_hex", True, type=bool))
        self.cb_include_hash.setChecked(self.settings.value("include_hash", False, type=bool))
        self.cb_include_hash.setEnabled(self.cb_hex.isChecked())

        self.cb_rgb.setChecked(self.settings.value("show_rgb", True, type=bool))
        self.cb_include_rgb_prefix.setChecked(self.settings.value("include_rgb_prefix", True, type=bool))
        self.cb_include_rgb_prefix.setEnabled(self.cb_rgb.isChecked())

        self.cb_hsl.setChecked(self.settings.value("show_hsl", True, type=bool))
        self.cb_include_hsl_prefix.setChecked(self.settings.value("include_hsl_prefix", True, type=bool))
        self.cb_include_hsl_prefix.setEnabled(self.cb_hsl.isChecked())

        self.cb_hsv.setChecked(self.settings.value("show_hsv", True, type=bool))
        self.cb_include_hsv_prefix.setChecked(self.settings.value("include_hsv_prefix", True, type=bool))
        self.cb_include_hsv_prefix.setEnabled(self.cb_hsv.isChecked())

        formats_layout.addWidget(self.cb_hex)
        formats_layout.addWidget(self.cb_include_hash)
        formats_layout.addWidget(self.cb_rgb)
        formats_layout.addWidget(self.cb_include_rgb_prefix)
        formats_layout.addWidget(self.cb_hsl)
        formats_layout.addWidget(self.cb_include_hsl_prefix)
        formats_layout.addWidget(self.cb_hsv)
        formats_layout.addWidget(self.cb_include_hsv_prefix)
        formats_layout.addStretch()

        self.shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(self.shortcuts_tab)
        shortcuts_layout.setContentsMargins(12, 12, 12, 12)
        shortcuts_layout.setSpacing(10)

        shortcuts_label = QLabel("Global activation shortcut (KDE):")
        shortcuts_label.setStyleSheet("font-weight: bold;")
        shortcuts_layout.addWidget(shortcuts_label)

        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.keySequenceChanged.connect(self.on_key_sequence_changed)
        shortcuts_layout.addWidget(self.shortcut_edit)

        current_shortcut = self.settings.value("shortcut", "Meta+Shift+C", type=str)
        self.shortcut_edit.setKeySequence(QKeySequence(current_shortcut))

        shortcuts_desc = QLabel(
            "Set a keyboard shortcut to invoke the program window.\n"
            "This shortcut will be saved in the application's .desktop file and "
            "registered by the KDE Plasma system."
        )
        shortcuts_desc.setWordWrap(True)
        shortcuts_desc.setStyleSheet("font-size: 8.5pt; color: palette(window-text);")
        shortcuts_layout.addWidget(shortcuts_desc)
        shortcuts_layout.addStretch()

        self.about_tab = QWidget()
        about_layout = QVBoxLayout(self.about_tab)
        about_layout.setContentsMargins(12, 12, 12, 12)
        about_layout.setSpacing(6)

        app_title = QLabel("KColorPicker")
        app_title.setStyleSheet("font-size: 11pt; font-weight: bold; color: palette(window-text);")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_desc = QLabel("Color picking and management tool compatible with Kvantum and KDE.")
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

        self.tabs.addTab(self.formats_tab, "Formats")
        self.tabs.addTab(self.shortcuts_tab, "Shortcut")
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

    def on_key_sequence_changed(self, sequence):
        if sequence.count() > 1:
            first_key_str = sequence.toString().split(",")[0].strip()
            self.shortcut_edit.blockSignals(True)
            self.shortcut_edit.setKeySequence(QKeySequence(first_key_str))
            self.shortcut_edit.blockSignals(False)

    def save_and_accept(self):
        if not (self.cb_hex.isChecked() or self.cb_rgb.isChecked() or 
                self.cb_hsl.isChecked() or self.cb_hsv.isChecked()):
            QMessageBox.warning(self, "Error", "You must select at least one color format!")
            return

        self.settings.setValue("show_hex", self.cb_hex.isChecked())
        self.settings.setValue("show_rgb", self.cb_rgb.isChecked())
        self.settings.setValue("show_hsl", self.cb_hsl.isChecked())
        self.settings.setValue("show_hsv", self.cb_hsv.isChecked())
        self.settings.setValue("include_hash", self.cb_include_hash.isChecked())
        self.settings.setValue("include_rgb_prefix", self.cb_include_rgb_prefix.isChecked())
        self.settings.setValue("include_hsl_prefix", self.cb_include_hsl_prefix.isChecked())
        self.settings.setValue("include_hsv_prefix", self.cb_include_hsv_prefix.isChecked())

        new_shortcut = self.shortcut_edit.keySequence().toString().split(",")[0].strip()
        old_shortcut = self.settings.value("shortcut", "Meta+Shift+C", type=str)
        if new_shortcut != old_shortcut:
            self.settings.setValue("shortcut", new_shortcut)
            update_desktop_shortcut(new_shortcut)

        self.accept()


class ColorPicker(QWidget):
    def __init__(self, pick_on_start: bool = True):
        super().__init__()
        self.pick_on_start = pick_on_start

        self.setWindowTitle("KColorPicker")
        self.setWindowIcon(QIcon.fromTheme("color-picker", QIcon.fromTheme("applications-graphics")))
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.resize(360, 270)
        self.setMinimumSize(360, 270)
        self.setMaximumSize(360, 270)

        self.settings = QSettings("ktoys", "ColorPicker")
        default_history = []
        self.history = self.settings.value("history", default_history)
        if not isinstance(self.history, list):
            self.history = default_history
        self.history = list(self.history)[:8]

        if self.history:
            self.current_color = QColor(self.history[0])
        else:
            self.current_color = QColor("#cbb6ac")
        self.color_dots = []

        self.preview_bar = QLabel()
        self.preview_bar.setObjectName("PreviewBar")
        self.preview_bar.setFixedWidth(22)

        self.hex_row = CopyRow("HEX")
        self.rgb_row = CopyRow("RGB")
        self.hsl_row = CopyRow("HSL")
        self.hsv_row = CopyRow("HSV")

        for row in [self.hex_row, self.rgb_row, self.hsl_row, self.hsv_row]:
            row.copy_requested.connect(self.copy_to_clipboard)

        rows_layout = QVBoxLayout()
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(10)
        rows_layout.addWidget(self.hex_row)
        rows_layout.addWidget(self.rgb_row)
        rows_layout.addWidget(self.hsl_row)
        rows_layout.addWidget(self.hsv_row)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(14, 14, 14, 20)
        content_layout.setSpacing(12)
        content_layout.addWidget(self.preview_bar)
        content_layout.addLayout(rows_layout, 1)

        self.pick_button = QToolButton()
        self.pick_button.setIcon(QIcon.fromTheme("color-picker"))
        self.pick_button.setIconSize(QSize(18, 18))
        self.pick_button.setFixedSize(28, 28)
        self.pick_button.setToolTip("Pick color")
        self.pick_button.setObjectName("PickButton")
        self.pick_button.clicked.connect(self.pick_from_screen)

        self.palette_button = QToolButton()
        self.palette_button.setIcon(QIcon.fromTheme("applications-graphics"))
        self.palette_button.setIconSize(QSize(18, 18))
        self.palette_button.setFixedSize(28, 28)
        self.palette_button.setToolTip("Choose from palette")
        self.palette_button.clicked.connect(self.pick_from_palette)

        bottom_bar = QFrame()
        bottom_bar.setObjectName("BottomBar")

        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 6, 12, 6)
        bottom_layout.setSpacing(6)
        bottom_layout.addWidget(self.pick_button)

        for _ in range(8):
            dot = ColorDot("#ffffff")
            dot.selected.connect(self.set_color)
            self.color_dots.append(dot)
            bottom_layout.addWidget(dot)

        bottom_layout.addStretch(1)
        bottom_layout.addSpacing(6)
        bottom_layout.addWidget(self.palette_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(content_layout, 1)
        main_layout.addWidget(bottom_bar)

        self.apply_style()
        self.update_dots()
        self.set_color(self.current_color)

        self.update_row_visibility()

        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            if self.isMaximized():
                self.showNormal()
            visible_count = sum([
                self.settings.value("show_hex", True, type=bool),
                self.settings.value("show_rgb", True, type=bool),
                self.settings.value("show_hsl", True, type=bool),
                self.settings.value("show_hsv", True, type=bool)
            ])
            new_height = 270 - (4 - visible_count) * 50
            self.setMinimumSize(360, new_height)
            self.setMaximumSize(360, new_height)
            self.resize(360, new_height)
        else:
            move_to_bottom_center(self)

        self.setup_tray_icon()

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def apply_style(self):
        self.setStyleSheet(
            """
            QWidget {
                background: palette(window);
                color: palette(window-text);
                font-size: 10pt;
            }

            QFrame#TitleBar {
                background: palette(window);
                border-bottom: 1px solid palette(midlight);
            }

            QLabel#TitleLabel {
                font-size: 9pt;
                font-weight: 500;
            }

            QLabel#PreviewBar {
                border-radius: 3px;
                border: 1px solid palette(midlight);
            }

            QFrame#CopyRow {
                background-color: palette(base);
                border: 1px solid palette(midlight);
                border-radius: 4px;
                min-height: 40px;
                max-height: 40px;
            }

            QLabel#NameLabel {
                color: palette(window-text);
                background-color: palette(window);
                border-radius: 4px;
                font-size: 8pt;
                font-weight: bold;
                min-height: 20px;
                max-height: 20px;
            }

            QLabel#ValueLabel {
                background-color: transparent;
                color: palette(text);
                font-size: 9pt;
            }

            QToolButton#CopyButton {
                border: none;
                padding: 4px;
            }

            QToolButton#CopyButton:hover {
                background: palette(alternate-base);
                border-radius: 4px;
            }

            QFrame#BottomBar {
                background: palette(window);
                border-top: 1px solid palette(midlight);
            }

            QToolButton {
                border: none;
                padding: 5px;
                border-radius: 4px;
            }

            QToolButton:hover {
                background: palette(alternate-base);
            }
            """
        )

    def set_color(self, color: QColor):
        self.current_color = QColor(color)

        r = self.current_color.red()
        g = self.current_color.green()
        b = self.current_color.blue()

        hsl_h = max(0, self.current_color.hslHue())
        hsl_s = round(self.current_color.hslSaturationF() * 100)
        hsl_l = round(self.current_color.lightnessF() * 100)

        hsv_h = max(0, self.current_color.hsvHue())
        hsv_s = round(self.current_color.hsvSaturationF() * 100)
        hsv_v = round(self.current_color.valueF() * 100)

        include_hash = self.settings.value("include_hash", False, type=bool)
        hex_value = self.current_color.name(QColor.NameFormat.HexRgb)
        if not include_hash:
            hex_value = hex_value.replace("#", "")

        include_rgb_prefix = self.settings.value("include_rgb_prefix", True, type=bool)
        include_hsl_prefix = self.settings.value("include_hsl_prefix", True, type=bool)
        include_hsv_prefix = self.settings.value("include_hsv_prefix", True, type=bool)

        rgb_val = f"rgb({r}, {g}, {b})" if include_rgb_prefix else f"{r}, {g}, {b}"
        hsl_val = f"hsl({hsl_h}, {hsl_s}%, {hsl_l}%)" if include_hsl_prefix else f"{hsl_h}, {hsl_s}%, {hsl_l}%"
        hsv_val = f"hsv({hsv_h}, {hsv_s}%, {hsv_v}%)" if include_hsv_prefix else f"{hsv_h}, {hsv_s}%, {hsv_v}%"

        self.hex_row.set_value(hex_value)
        self.rgb_row.set_value(rgb_val)
        self.hsl_row.set_value(hsl_val)
        self.hsv_row.set_value(hsv_val)

        self.preview_bar.setStyleSheet(
            f"""
            QLabel#PreviewBar {{
                background-color: {self.current_color.name()};
                border-radius: 3px;
                border: 1px solid palette(midlight);
            }}
            """
        )

        current_hex = self.current_color.name(QColor.NameFormat.HexRgb).lower()

        for dot in self.color_dots:
            dot.set_active(dot.color.name(QColor.NameFormat.HexRgb).lower() == current_hex)

    def pick_from_palette(self):
        color = QColorDialog.getColor(self.current_color, self, "Choose color")

        if color.isValid():
            self.set_color(color)
            self.add_to_history(color)

    def add_to_history(self, color: QColor):
        hex_color = color.name(QColor.NameFormat.HexRgb).lower()
        if hex_color in self.history:
            self.history.remove(hex_color)
        self.history.insert(0, hex_color)
        self.history = self.history[:8]
        self.settings.setValue("history", self.history)
        self.update_dots()

    def update_dots(self):
        for i, dot in enumerate(self.color_dots):
            if i < len(self.history):
                dot.color = QColor(self.history[i])
                dot.setEnabled(True)
                dot.setVisible(True)
                dot.update()
            else:
                dot.setEnabled(False)
                dot.setVisible(False)

    def pick_from_screen(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.hide()
        
        self.picker_windows = []
        
        def on_selected(r, g, b):
            self.on_screen_color(r, g, b)
            self.cleanup_pickers()

        def on_cancelled():
            self.on_screen_cancel()
            self.cleanup_pickers()

        for screen in QApplication.screens():
            w = CustomColorPicker(screen)
            w.color_selected.connect(on_selected)
            w.cancelled.connect(on_cancelled)
            self.picker_windows.append(w)
            w.show()

    def cleanup_pickers(self):
        for w in self.picker_windows:
            w.close()
        self.picker_windows.clear()

    def on_screen_cancel(self):
        self.show_and_activate()

    def on_screen_color(self, r: int, g: int, b: int):
        self.pick_button.setEnabled(True)
        color = QColor(r, g, b)
        self.set_color(color)
        self.add_to_history(color)
        
        include_hash = self.settings.value("include_hash", False, type=bool)
        hex_value = color.name(QColor.NameFormat.HexRgb)
        if not include_hash:
            hex_value = hex_value.replace("#", "")
        self.copy_to_clipboard(hex_value)
        
        self.show_and_activate()

    def on_screen_error(self, message: str):
        self.pick_button.setEnabled(True)
        self.show_and_activate()

        QMessageBox.warning(
            self,
            "Error",
            f"Failed to pick color:\n{message}",
        )


    def update_row_visibility(self):
        show_hex = self.settings.value("show_hex", True, type=bool)
        show_rgb = self.settings.value("show_rgb", True, type=bool)
        show_hsl = self.settings.value("show_hsl", True, type=bool)
        show_hsv = self.settings.value("show_hsv", True, type=bool)

        self.hex_row.setVisible(show_hex)
        self.rgb_row.setVisible(show_rgb)
        self.hsl_row.setVisible(show_hsl)
        self.hsv_row.setVisible(show_hsv)

        visible_count = sum([show_hex, show_rgb, show_hsl, show_hsv])
        new_height = 270 - (4 - visible_count) * 50

        self.setMinimumSize(360, new_height)
        self.setMaximumSize(360, new_height)

        if self.isVisible():
            old_geom = self.geometry()
            new_y = old_geom.y() + old_geom.height() - new_height
            self.resize(360, new_height)
            self.move(old_geom.x(), new_y)
        else:
            self.resize(360, new_height)

    def copy_to_clipboard(self, text: str):
        QApplication.clipboard().setText(text)

    def show_and_activate(self):
        self.show()
        if self.isMaximized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_row_visibility()
            self.set_color(self.current_color)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("color-picker", QIcon.fromTheme("applications-graphics")))
        
        self.tray_menu = QMenu(self)
        
        pick_action = self.tray_menu.addAction("Pick color")
        pick_action.setIcon(QIcon.fromTheme("color-picker"))
        pick_action.triggered.connect(self.pick_from_screen)
        
        show_action = self.tray_menu.addAction("Show window")
        show_action.triggered.connect(self.show_and_activate)
        
        settings_action = self.tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        
        self.tray_menu.addSeparator()
        
        quit_action = self.tray_menu.addAction("Quit")
        quit_action.setIcon(QIcon.fromTheme("application-exit"))
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()


def move_to_bottom_center(window: QWidget):
    screen = QApplication.primaryScreen()
    if not screen:
        return

    geometry = screen.availableGeometry()

    x = geometry.x() + int((geometry.width() - window.width()) / 2)
    y = geometry.y() + geometry.height() - window.height() - 32

    window.move(x, y)


def update_desktop_shortcut(shortcut_str: str):
    from ktoys.launcher import update_desktop_file
    update_desktop_file("[Desktop Action ColorPicker]", "X-KDE-Shortcuts", shortcut_str)


class ColorPickerModule(BaseModule):
    def get_id(self) -> str:
        return "color_picker"

    def get_name(self) -> str:
        return "KColorPicker"

    def get_icon(self) -> str:
        return "color-picker"

    def get_description(self) -> str:
        return "Screen color picker and palette selector for KDE."

    def launch(self, parent=None, trigger_action=None) -> QWidget:
        if self.window is None:
            self.window = ColorPicker(pick_on_start=False)
        
        if trigger_action == "pick":
            self.window.pick_from_screen()
        else:
            self.window.show_and_activate()
            
        return self.window

    def has_settings(self) -> bool:
        return True

    def show_settings(self, parent=None):
        settings = QSettings("ktoys", "ColorPicker")
        dialog = SettingsDialog(parent, settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self.window is not None:
                self.window.update_row_visibility()
                self.window.set_color(self.window.current_color)
