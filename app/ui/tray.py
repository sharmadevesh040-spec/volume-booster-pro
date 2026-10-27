"""
Volume Booster Pro - System Tray Icon and Context Menu
Enables seamless background running, quick preset switching, and minimize-to-tray.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, QObject


class TrayManager(QObject):
    """Manages the Windows notification area system tray icon."""

    restore_requested = Signal()
    bypass_toggled = Signal(bool)
    preset_selected = Signal(str)
    volume_selected = Signal(int)
    exit_requested = Signal()

    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon(self.icon, parent)
        self.tray.setToolTip("Volume Booster Pro - Windows System Audio Enhancer")

        self._create_menu()
        self.tray.activated.connect(self._on_tray_activated)

    def _create_menu(self):
        self.menu = QMenu()

        # Header Title
        title_action = QAction("⚡ Volume Booster Pro", self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        self.menu.addSeparator()

        # Show / Restore Action
        self.show_action = QAction("Open Window", self.menu)
        self.show_action.triggered.connect(self.restore_requested.emit)
        self.menu.addAction(self.show_action)

        # Master Bypass Action
        self.bypass_action = QAction("Master Bypass (Disable)", self.menu)
        self.bypass_action.setCheckable(True)
        self.bypass_action.toggled.connect(self.bypass_toggled.emit)
        self.menu.addAction(self.bypass_action)
        self.menu.addSeparator()

        # Presets Submenu
        presets_menu = self.menu.addMenu("Presets")
        self.preset_actions = {}
        preset_names = [
            ("balanced", "Balanced (125%)"),
            ("movie", "Movie (150%)"),
            ("bass_boost", "Bass Boost (140%)"),
            ("voice", "Voice Clarity (160%)"),
            ("normal", "Normal (100%)")
        ]
        for key, label in preset_names:
            act = QAction(label, presets_menu)
            act.triggered.connect(lambda checked=False, k=key: self.preset_selected.emit(k))
            presets_menu.addAction(act)
            self.preset_actions[key] = act

        # Volume Quick Jumps Submenu
        vol_menu = self.menu.addMenu("Quick Amplification")
        for vol in [100, 125, 150, 200, 300]:
            act = QAction(f"{vol}%", vol_menu)
            act.triggered.connect(lambda checked=False, v=vol: self.volume_selected.emit(v))
            vol_menu.addAction(act)

        self.menu.addSeparator()

        # Exit Action
        self.exit_action = QAction("Exit", self.menu)
        self.exit_action.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(self.exit_action)

        self.tray.setContextMenu(self.menu)

    def show(self):
        """Display the tray icon."""
        self.tray.show()

    def hide(self):
        """Hide the tray icon."""
        self.tray.hide()

    def set_bypassed(self, bypassed: bool):
        """Update bypass checkmark state."""
        self.bypass_action.setChecked(bypassed)

    def show_message(self, title: str, message: str):
        """Display a system tray balloon notification."""
        self.tray.showMessage(title, message, self.icon, 3000)

    def _on_tray_activated(self, reason):
        """Handle tray clicks."""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_requested.emit()
