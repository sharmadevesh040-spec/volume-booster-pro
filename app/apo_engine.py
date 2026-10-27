"""
Volume Booster Pro - Equalizer APO System Engine Integration
Safely inspects, configures, and dynamically controls Equalizer APO on Windows 10 & 11.
"""

import os
import shutil
import winreg
from typing import Optional, Dict, Any, Tuple

DEFAULT_APO_PATHS = [
    r"C:\Program Files\EqualizerAPO",
    r"C:\Program Files (x86)\EqualizerAPO"
]

INCLUDE_DIRECTIVE = "Include: VolumeBoosterPro.txt"
CONFIG_FILE_NAME = "config.txt"
PROFILE_FILE_NAME = "VolumeBoosterPro.txt"


class EqualizerApoEngine:
    """Manages system-level audio processing via Equalizer APO."""

    def __init__(self):
        self.install_dir = self.detect_install_dir()
        self.config_dir = os.path.join(self.install_dir, "config") if self.install_dir else None
        self.main_config_path = os.path.join(self.config_dir, CONFIG_FILE_NAME) if self.config_dir else None
        self.profile_path = os.path.join(self.config_dir, PROFILE_FILE_NAME) if self.config_dir else None

    def detect_install_dir(self) -> Optional[str]:
        """Detect Equalizer APO directory via Registry or standard file paths."""
        # 1. Check Registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO", 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "InstallPath")
                if val and os.path.isdir(val):
                    return val
        except Exception:
            pass

        # 2. Check Standard Folders
        for path in DEFAULT_APO_PATHS:
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "EqualizerAPO.dll")):
                return path

        return None

    def is_installed(self) -> bool:
        """Check if Equalizer APO is properly installed on the system."""
        if not self.install_dir or not os.path.isdir(self.install_dir):
            return False
        dll_path = os.path.join(self.install_dir, "EqualizerAPO.dll")
        return os.path.exists(dll_path)

    def is_integrated(self) -> bool:
        """Check if VolumeBoosterPro.txt is included in main config.txt."""
        if not self.main_config_path or not os.path.exists(self.main_config_path):
            return False
        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                content = f.read()
                return INCLUDE_DIRECTIVE in content
        except Exception:
            return False

    def ensure_integration(self) -> Tuple[bool, str]:
        """
        Safely insert 'Include: VolumeBoosterPro.txt' into config.txt.
        Creates an automatic backup 'config.txt.bak' first.
        """
        if not self.is_installed():
            return False, "Equalizer APO is not installed."

        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create config directory: {e}"

        # If config.txt does not exist, create it
        if not os.path.exists(self.main_config_path):
            try:
                with open(self.main_config_path, "w", encoding="utf-8") as f:
                    f.write(f"# Equalizer APO Configuration\n{INCLUDE_DIRECTIVE}\n")
                return True, "Created config.txt and enabled Volume Booster Pro."
            except Exception as e:
                return False, f"Failed to create config.txt: {e}"

        # If already included, nothing to do
        if self.is_integrated():
            return True, "Already integrated."

        # Backup existing config.txt
        backup_path = self.main_config_path + ".bak"
        if not os.path.exists(backup_path):
            try:
                shutil.copy2(self.main_config_path, backup_path)
            except Exception as e:
                print(f"[APO] Warning: Could not create config.txt backup: {e}")

        # Append Include directive without overwriting user's other configurations
        try:
            with open(self.main_config_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n# Added by Volume Booster Pro\n{INCLUDE_DIRECTIVE}\n")
            return True, "Successfully linked Volume Booster Pro into Equalizer APO."
        except Exception as e:
            return False, f"Error updating config.txt: {e}"

    def update_profile(self, volume_percent: float, bass_db: float, voice_db: float,
                       treble_db: float, bypassed: bool = False, device_name: str = "") -> Tuple[bool, str]:
        """
        Atomically write VolumeBoosterPro.txt for real-time audiodg.exe DSP processing.
        """
        if not self.is_installed():
            return False, "Equalizer APO is not installed."

        self.ensure_integration()

        # Calculate decibel preamp from percentage
        import math
        gain = max(1.0, volume_percent / 100.0)
        preamp_db = 0.0 if bypassed else (20.0 * math.log10(gain))
        filter_state = "OFF" if bypassed else "ON"

        lines = [
            "# ==============================================================",
            "# Volume Booster Pro - Windows System-Wide Audio DSP Profile",
            "# Automatically updated by Volume Booster Pro desktop app.",
            "# ==============================================================",
            ""
        ]

        if device_name and device_name.strip():
            # Target specific device
            lines.append(f'Device: "{device_name.strip()}"')
            lines.append("")

        # Master amplification preamp
        lines.append(f"Preamp: {preamp_db:+.2f} dB")
        lines.append("")

        # 3-Band Equalizer filters
        # 1. Bass (Low Shelf at 150 Hz)
        lines.append(f"Filter 1: {filter_state} LSC Fc 150.0 Hz Gain {bass_db:+.2f} dB")
        # 2. Voice Clarity (Peaking filter at 2200 Hz with Q=1.0)
        lines.append(f"Filter 2: {filter_state} PK Fc 2200.0 Hz Gain {voice_db:+.2f} dB Q 1.00")
        # 3. Treble (High Shelf at 7000 Hz)
        lines.append(f"Filter 3: {filter_state} HSC Fc 7000.0 Hz Gain {treble_db:+.2f} dB")
        lines.append("")

        content = "\n".join(lines)

        # Write atomically via temp file to avoid partial reads
        temp_path = self.profile_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            # Atomic replace
            os.replace(temp_path, self.profile_path)
            return True, "Profile updated successfully."
        except Exception as e:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass
            return False, f"Failed to write APO profile: {e}"

    def remove_integration(self) -> Tuple[bool, str]:
        """Remove VolumeBoosterPro directive and restore original config.txt."""
        if not self.main_config_path or not os.path.exists(self.main_config_path):
            return True, "No config to clean up."

        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = [l for l in lines if INCLUDE_DIRECTIVE not in l and "Volume Booster Pro" not in l]

            with open(self.main_config_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            if self.profile_path and os.path.exists(self.profile_path):
                os.remove(self.profile_path)

            return True, "Volume Booster Pro integration cleanly removed."
        except Exception as e:
            return False, f"Error removing integration: {e}"
