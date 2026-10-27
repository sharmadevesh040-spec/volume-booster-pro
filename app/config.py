"""
Volume Booster Pro - Configuration and Settings Manager
Handles persistent settings, Windows startup registry, presets, and path management.
"""

import os
import json
import winreg
from typing import Dict, Any, Optional

APP_NAME = "VolumeBoosterPro"
APP_DISPLAY_NAME = "Volume Booster Pro"
APP_VERSION = "2.0.0"

# Application storage directory in %LOCALAPPDATA%
LOCAL_APP_DATA = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
APP_DATA_DIR = os.path.join(LOCAL_APP_DATA, APP_NAME)
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
CUSTOM_PRESETS_FILE = os.path.join(APP_DATA_DIR, "custom_presets.json")

# Standard Tuned DSP Presets
DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "name": "Normal",
        "volume": 100,
        "bass": 0.0,
        "voice": 0.0,
        "treble": 0.0,
        "description": "Flat, unaltered response with zero coloration."
    },
    "balanced": {
        "name": "Balanced",
        "volume": 125,
        "bass": 1.5,
        "voice": 2.0,
        "treble": 1.0,
        "description": "Sweet spot for laptop speakers: warm bass, clear vocals."
    },
    "bass_boost": {
        "name": "Bass Boost",
        "volume": 140,
        "bass": 4.5,
        "voice": 1.0,
        "treble": 1.5,
        "description": "Rich low-end rumble for EDM, hip-hop, and movies."
    },
    "movie": {
        "name": "Movie",
        "volume": 150,
        "bass": 2.0,
        "voice": 3.5,
        "treble": 1.5,
        "description": "Dialogue forward with controlled cinematic dynamics."
    },
    "voice": {
        "name": "Voice",
        "volume": 160,
        "bass": -2.0,
        "voice": 5.0,
        "treble": 2.0,
        "description": "Maximum vocal clarity; cuts low boominess for podcasts."
    }
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "volume": 125,
    "preset": "balanced",
    "bass": 1.5,
    "voice": 2.0,
    "treble": 1.0,
    "bypassed": False,
    "device_name": "",
    "start_with_windows": False,
    "minimize_to_tray": False,
    "close_to_tray": False,
    "dark_mode": True
}


def ensure_app_data_dir() -> str:
    """Ensure that the local application directory exists."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    return APP_DATA_DIR


class ConfigManager:
    """Manages application state and settings persistence."""

    def __init__(self):
        ensure_app_data_dir()
        self.settings = self.load_settings()
        self.custom_presets = self.load_custom_presets()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON, merging with defaults."""
        settings = dict(DEFAULT_SETTINGS)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        settings.update(data)
            except Exception as e:
                print(f"[Config] Error reading settings: {e}")
        return settings

    def save_settings(self) -> bool:
        """Persist current settings to JSON."""
        ensure_app_data_dir()
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"[Config] Error writing settings: {e}")
            return False

    def load_custom_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load user-defined presets from JSON."""
        if os.path.exists(CUSTOM_PRESETS_FILE):
            try:
                with open(CUSTOM_PRESETS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                print(f"[Config] Error reading custom presets: {e}")
        return {}

    def save_custom_preset(self, name: str, volume: float, bass: float, voice: float, treble: float) -> bool:
        """Save a new user-defined preset."""
        key = name.strip().lower().replace(" ", "_")
        self.custom_presets[key] = {
            "name": name.strip(),
            "volume": volume,
            "bass": bass,
            "voice": voice,
            "treble": treble,
            "description": "User custom preset"
        }
        ensure_app_data_dir()
        try:
            with open(CUSTOM_PRESETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.custom_presets, f, indent=2)
            return True
        except Exception as e:
            print(f"[Config] Error saving custom preset: {e}")
            return False

    def get_preset(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a preset by key from defaults or custom."""
        if key in DEFAULT_PRESETS:
            return DEFAULT_PRESETS[key]
        if key in self.custom_presets:
            return self.custom_presets[key]
        return None

    def set_start_with_windows(self, enable: bool, exe_path: Optional[str] = None) -> bool:
        """Configure Windows Startup via HKCU Run registry key."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    if not exe_path:
                        import sys
                        exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath("main.py")
                    val = f'"{exe_path}" --minimized'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, val)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            self.settings["start_with_windows"] = enable
            self.save_settings()
            return True
        except Exception as e:
            print(f"[Config] Error modifying Windows Run registry key: {e}")
            return False

    def is_start_with_windows_enabled(self) -> bool:
        """Check if Windows Startup entry exists in registry."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
