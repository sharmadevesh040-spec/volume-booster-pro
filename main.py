"""
Volume Booster Pro - Application Entry Point
Native Windows Desktop Application for System-Wide Audio Amplification & DSP Equalization.
"""

import os
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from app.config import ConfigManager, APP_DISPLAY_NAME
from app.apo_engine import EqualizerApoEngine
from app.ui.main_window import MainWindow


def setup_windows_environment():
    """Configure Windows DPI awareness and Taskbar AppUserModelID."""
    try:
        # Windows AppUserModelID for taskbar icon grouping
        app_id = "Antigravity.VolumeBoosterPro.2.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    try:
        # Per-Monitor High DPI awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        # Windows COM initialization for Core Audio
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass


def main():
    """Main application routine."""
    setup_windows_environment()

    # Enable High DPI scaling in Qt
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setQuitOnLastWindowClosed(False)

    icon_path = os.path.abspath("assets/icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Initialize configuration and engine
    config = ConfigManager()
    apo = EqualizerApoEngine()

    # Create main window
    window = MainWindow(config, apo)

    # Check CLI arguments
    start_minimized = "--minimized" in sys.argv or "-m" in sys.argv
    if not start_minimized:
        window.show()
    else:
        window.hide()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
