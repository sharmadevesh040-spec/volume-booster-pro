"""
Volume Booster Pro - System Installation and First-Run Wizard
Handles automatic installation prompts, desktop/start menu shortcuts,
Windows Add/Remove Programs registration, and self-contained uninstallation.
"""

import os
import sys
import shutil
import winreg
import subprocess
from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from app.config import ConfigManager, APP_NAME, APP_DISPLAY_NAME, APP_VERSION

INSTALL_DIR = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), "Programs", APP_NAME)

def get_desktop_dir() -> str:
    """Resolve the true Windows Desktop directory (including OneDrive-redirected Desktops)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = winreg.QueryValueEx(key, "Desktop")
            return os.path.expandvars(val)
    except Exception:
        return os.path.join(os.getenv("USERPROFILE", os.path.expanduser("~")), "Desktop")

def get_start_menu_dir() -> str:
    """Resolve the true Windows Start Menu Programs directory."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = winreg.QueryValueEx(key, "Programs")
            return os.path.expandvars(val)
    except Exception:
        return os.path.join(os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming")), "Microsoft", "Windows", "Start Menu", "Programs")

DESKTOP_DIR = get_desktop_dir()
START_MENU_DIR = get_start_menu_dir()
UNINSTALL_REG_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"


def is_running_installed() -> bool:
    """Return True if the running process is located inside the official install folder."""
    try:
        current_exe = os.path.abspath(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
        common = os.path.commonpath([current_exe, INSTALL_DIR])
        return os.path.abspath(common) == os.path.abspath(INSTALL_DIR)
    except Exception:
        return False


def is_already_installed() -> bool:
    """Check if Volume Booster Pro is installed in the target location."""
    exe_target = os.path.join(INSTALL_DIR, "VolumeBoosterPro.exe")
    bat_target = os.path.join(INSTALL_DIR, "run_app.bat")
    return os.path.exists(exe_target) or os.path.exists(bat_target)


def create_windows_shortcut(target_path: str, shortcut_path: str, icon_path: Optional[str] = None, description: str = "") -> bool:
    """Create a Windows .lnk shortcut using win32com or PowerShell."""
    try:
        os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
        work_dir = os.path.dirname(target_path)
        
        # Method 1: win32com.client (Fastest, zero-process)
        try:
            import win32com.client
            ws = win32com.client.Dispatch("WScript.Shell")
            sc = ws.CreateShortcut(shortcut_path)
            sc.TargetPath = target_path
            sc.WorkingDirectory = work_dir
            sc.Description = description
            if icon_path and os.path.exists(icon_path):
                sc.IconLocation = icon_path
            sc.Save()
            return os.path.exists(shortcut_path)
        except Exception:
            pass

        # Method 2: Encoded PowerShell (guaranteed zero syntax escaping issues)
        import base64
        icon_line = f"$s.IconLocation = '{icon_path}';" if icon_path and os.path.exists(icon_path) else ""
        ps_code = f"""
        $w = New-Object -ComObject WScript.Shell
        $s = $w.CreateShortcut('{shortcut_path}')
        $s.TargetPath = '{target_path}'
        $s.WorkingDirectory = '{work_dir}'
        $s.Description = '{description}'
        {icon_line}
        $s.Save()
        """
        enc = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        return os.path.exists(shortcut_path)
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False


def register_windows_uninstaller(install_dir: str, target_exe: str, icon_path: str) -> None:
    """Register the application in Windows 'Apps & Features' (Add or Remove Programs)."""
    try:
        uninstall_bat = os.path.join(install_dir, "uninstall.bat")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Volume Booster Pro Team")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path if os.path.exists(icon_path) else target_exe)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninstall_bat}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"Failed to register uninstaller in registry: {e}")


def write_uninstaller_script(install_dir: str) -> str:
    """Create a self-deleting uninstall.bat script in the install directory."""
    uninstall_path = os.path.join(install_dir, "uninstall.bat")
    desktop_lnk = os.path.join(DESKTOP_DIR, f"{APP_DISPLAY_NAME}.lnk")
    start_lnk = os.path.join(START_MENU_DIR, f"{APP_DISPLAY_NAME}.lnk")

    content = f"""@echo off
title {APP_DISPLAY_NAME} - Uninstaller
cls
echo ==========================================================
echo        Uninstalling {APP_DISPLAY_NAME}
echo ==========================================================
echo.
echo Are you sure you want to remove {APP_DISPLAY_NAME} from this PC?
echo Press [Y] to confirm or close this window to cancel.
set /p confirm="> "
if /i not "%confirm%"=="Y" exit /b 0

echo.
echo [*] Terminating running instances...
taskkill /f /im VolumeBoosterPro.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq {APP_DISPLAY_NAME}*" 2>nul

echo [*] Removing shortcuts...
if exist "{desktop_lnk}" del /f /q "{desktop_lnk}" 2>nul
if exist "{start_lnk}" del /f /q "{start_lnk}" 2>nul

echo [*] Removing registry entries...
reg delete "HKCU\\{UNINSTALL_REG_KEY}" /f 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "{APP_NAME}" /f 2>nul

echo [*] Removing application files...
start /b "" cmd /c "timeout /t 1 /nobreak >nul & rd /s /q \\"%~dp0\\" & exit"
echo.
echo ==========================================================
echo {APP_DISPLAY_NAME} has been completely uninstalled.
echo ==========================================================
timeout /t 2 >nul
exit
"""
    try:
        with open(uninstall_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Failed to write uninstaller: {e}")
    return uninstall_path


def install_to_system(create_desktop: bool = True, create_start_menu: bool = True, start_with_windows: bool = True) -> Tuple[bool, str]:
    """
    Perform the complete installation to %LOCALAPPDATA%\\Programs\\VolumeBoosterPro.
    Returns (success, target_executable_path).
    """
    try:
        os.makedirs(INSTALL_DIR, exist_ok=True)
        is_frozen = getattr(sys, "frozen", False)

        if is_frozen:
            source_dir = os.path.dirname(sys.executable)
            target_exe = os.path.join(INSTALL_DIR, "VolumeBoosterPro.exe")
            # Copy all files from the compiled bundle
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(INSTALL_DIR, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d, ignore_errors=True)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
        else:
            # Running from source (Python)
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            dist_exe_dir = os.path.join(base_dir, "dist", "VolumeBoosterPro")

            if os.path.exists(dist_exe_dir) and os.path.exists(os.path.join(dist_exe_dir, "VolumeBoosterPro.exe")):
                # Prefer compiled binary if available
                target_exe = os.path.join(INSTALL_DIR, "VolumeBoosterPro.exe")
                for item in os.listdir(dist_exe_dir):
                    s = os.path.join(dist_exe_dir, item)
                    d = os.path.join(INSTALL_DIR, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d, ignore_errors=True)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
            else:
                # Copy Python project structure
                target_exe = os.path.join(INSTALL_DIR, "run_app.bat")
                items_to_copy = ["app", "assets", "main.py", "run_app.bat", "requirements.txt", "README.md"]
                for item in items_to_copy:
                    s = os.path.join(base_dir, item)
                    d = os.path.join(INSTALL_DIR, item)
                    if os.path.exists(s):
                        if os.path.isdir(s):
                            if os.path.exists(d):
                                shutil.rmtree(d, ignore_errors=True)
                            shutil.copytree(s, d)
                        else:
                            shutil.copy2(s, d)

        icon_path = os.path.join(INSTALL_DIR, "assets", "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(INSTALL_DIR, "assets", "icon.png")

        # Create Desktop Shortcut
        if create_desktop:
            desktop_lnk = os.path.join(DESKTOP_DIR, f"{APP_DISPLAY_NAME}.lnk")
            create_windows_shortcut(target_exe, desktop_lnk, icon_path, f"{APP_DISPLAY_NAME} Audio Enhancer")

        # Create Start Menu Shortcut
        if create_start_menu:
            start_lnk = os.path.join(START_MENU_DIR, f"{APP_DISPLAY_NAME}.lnk")
            create_windows_shortcut(target_exe, start_lnk, icon_path, f"{APP_DISPLAY_NAME} Audio Enhancer")

        # Windows Startup Registry
        if start_with_windows:
            try:
                run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{target_exe}" --minimized')
            except Exception as e:
                print(f"Failed to set startup registry: {e}")

        # Register uninstaller and script
        write_uninstaller_script(INSTALL_DIR)
        register_windows_uninstaller(INSTALL_DIR, target_exe, icon_path)

        return True, target_exe
    except Exception as e:
        print(f"Installation failed: {e}")
        return False, str(e)


class InstallPromptDialog(QDialog):
    """Modern installation wizard dialog shown to users who download the app."""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"Install {APP_DISPLAY_NAME}")
        self.setFixedSize(520, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 22, 24, 22)

        # Header with Logo
        header_layout = QHBoxLayout()
        logo_lbl = QLabel()
        logo_path = os.path.abspath("assets/icon.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            logo_lbl.setPixmap(pix.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel(f"Install {APP_DISPLAY_NAME}")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #00f0ff;")
        sub_lbl = QLabel(f"Version {APP_VERSION} • Windows Audio Enhancer & Equalizer")
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Introduction Frame
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: rgba(18, 24, 38, 0.85); border: 1px solid rgba(0, 240, 255, 0.25); "
            "border-radius: 12px; padding: 14px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        welcome_lbl = QLabel("Would you like to install Volume Booster Pro on your PC?")
        welcome_lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        card_layout.addWidget(welcome_lbl)

        features = (
            "✔ <b>One-Click Access:</b> Adds Desktop and Windows Start Menu shortcuts.<br>"
            "✔ <b>Equalizer APO Integration:</b> Amplifies Chrome, Spotify, Netflix & Games with 0 latency.<br>"
            "✔ <b>User Profile Install:</b> No administrative privileges required.<br>"
            "✔ <b>Clean Uninstallation:</b> Can be easily uninstalled from Windows Settings anytime."
        )
        features_lbl = QLabel(features)
        features_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; line-height: 1.5;")
        features_lbl.setTextFormat(Qt.RichText)
        card_layout.addWidget(features_lbl)

        layout.addWidget(card)

        # Options Checkboxes
        opts_box = QVBoxLayout()
        opts_box.setSpacing(8)

        self.cb_desktop = QCheckBox("Create Desktop shortcut")
        self.cb_desktop.setChecked(True)
        self.cb_desktop.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        opts_box.addWidget(self.cb_desktop)

        self.cb_start_menu = QCheckBox("Create Start Menu shortcut")
        self.cb_start_menu.setChecked(True)
        self.cb_start_menu.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        opts_box.addWidget(self.cb_start_menu)

        self.cb_startup = QCheckBox("Start automatically when Windows starts")
        self.cb_startup.setChecked(True)
        self.cb_startup.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        opts_box.addWidget(self.cb_startup)

        layout.addLayout(opts_box)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_portable = QPushButton("Run Portable (Don't Install)")
        self.btn_portable.setStyleSheet(
            "QPushButton { background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); "
            "color: #94a3b8; border-radius: 8px; padding: 10px 16px; font-weight: 600; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.14); color: #f1f5f9; }"
        )
        self.btn_portable.clicked.connect(self._on_run_portable)
        btn_layout.addWidget(self.btn_portable)

        self.btn_install = QPushButton("⚡ Install to PC")
        self.btn_install.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7); "
            "color: #050811; border: none; border-radius: 8px; padding: 10px 22px; font-weight: 800; font-size: 13px; } "
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #c084fc); }"
        )
        self.btn_install.clicked.connect(self._on_install_clicked)
        btn_layout.addWidget(self.btn_install)

        layout.addLayout(btn_layout)

    def _on_run_portable(self):
        """User chose not to install."""
        self.config.settings["install_prompt_dismissed"] = True
        self.config.save_settings()
        self.accept()

    def _on_install_clicked(self):
        """Perform installation."""
        self.btn_install.setEnabled(False)
        self.btn_install.setText("Installing...")

        success, target = install_to_system(
            create_desktop=self.cb_desktop.isChecked(),
            create_start_menu=self.cb_start_menu.isChecked(),
            start_with_windows=self.cb_startup.isChecked()
        )

        if success:
            QMessageBox.information(
                self,
                "Installation Complete",
                f"{APP_DISPLAY_NAME} has been successfully installed!\n\n"
                f"Location: {INSTALL_DIR}\n"
                "Shortcuts have been placed on your Desktop and Start Menu.\n\n"
                "Launching installed application..."
            )
            # Launch installed application and exit current temporary runner
            try:
                subprocess.Popen([target], cwd=INSTALL_DIR, creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0)
                sys.exit(0)
            except Exception:
                self.accept()
        else:
            QMessageBox.critical(self, "Installation Failed", f"Could not complete installation:\n{target}")
            self.btn_install.setEnabled(True)
            self.btn_install.setText("⚡ Install to PC")


def check_first_run_install(config: ConfigManager, parent=None) -> None:
    """Check if the user is running from an uninstalled location and prompt if appropriate."""
    if is_running_installed():
        return

    # Check if user previously dismissed
    if config.settings.get("install_prompt_dismissed", False):
        return

    # If running from outside install directory, show prompt
    dialog = InstallPromptDialog(config, parent)
    dialog.exec()

