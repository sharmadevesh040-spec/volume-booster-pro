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

    def is_speaker_configured(self) -> bool:
        """Check if Realtek / Laptop Speakers are registered in Equalizer APO registry."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO\Child APOs") as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)
                for i in range(num_subkeys):
                    sub = winreg.EnumKey(key, i)
                    try:
                        dev_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\\" + sub + r"\Properties"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, dev_key_path) as dkey:
                            val, _ = winreg.QueryValueEx(dkey, "{a45c254e-df1c-4efd-8020-67d146a850e0},2")
                            if val and "speaker" in str(val).lower() and "bth" not in str(val).lower():
                                return True
                    except Exception:
                        pass
        except Exception:
            pass
        return False

    def launch_configurator(self) -> bool:
        """Launch Equalizer APO Configurator (DeviceSelector.exe) as Administrator."""
        import ctypes
        if not self.install_dir:
            return False
        for name in ["DeviceSelector.exe", "Configurator.exe", "DeviceSelector", "Configurator"]:
            exe = os.path.join(self.install_dir, name)
            if os.path.exists(exe):
                try:
                    res = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, None, None, 1)
                    return res > 32
                except Exception:
                    return False
        return False

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
        Disables sample 'Preamp: -6 dB' so it does not cancel out the volume boost.
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

        # Read existing config.txt
        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return False, f"Failed to read config.txt: {e}"

        modified = False
        # If it has the default sample "Preamp: -6 dB", comment it out so it doesn't reduce volume
        if "Preamp: -6 dB" in content and "# Preamp: -6 dB" not in content:
            content = content.replace("Preamp: -6 dB", "# Preamp: -6 dB  # Disabled by Volume Booster Pro")
            modified = True

        if INCLUDE_DIRECTIVE not in content:
            content += f"\n\n# Added by Volume Booster Pro\n{INCLUDE_DIRECTIVE}\n"
            modified = True

        if modified:
            # Backup existing config.txt
            backup_path = self.main_config_path + ".bak"
            if not os.path.exists(backup_path):
                try:
                    shutil.copy2(self.main_config_path, backup_path)
                except Exception:
                    pass

            try:
                with open(self.main_config_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True, "Successfully linked Volume Booster Pro into Equalizer APO."
            except Exception as e:
                return False, f"Error updating config.txt: {e}"

        return True, "Already integrated."

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
            "",
            "# Apply boost and DSP to all active audio endpoints",
            "Device: all",
            "",
            f"Preamp: {preamp_db:+.2f} dB",
            "",
            f"Filter 1: {filter_state} LSC Fc 150.0 Hz Gain {bass_db:+.2f} dB",
            f"Filter 2: {filter_state} PK Fc 2200.0 Hz Gain {voice_db:+.2f} dB Q 1.00",
            f"Filter 3: {filter_state} HSC Fc 7000.0 Hz Gain {treble_db:+.2f} dB",
            ""
        ]

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
