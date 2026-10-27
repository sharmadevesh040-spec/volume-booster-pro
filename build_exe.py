"""
Volume Booster Pro - Standalone Windows Executable Builder
Compiles the application into a standalone Windows binary using PyInstaller.
"""

import os
import sys
import shutil
import subprocess

def build():
    print("==================================================")
    print("BUILDING VOLUME BOOSTER PRO STANDALONE EXECUTABLE")
    print("==================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    icon_path = os.path.join(base_dir, "assets", "icon.ico")
    main_py = os.path.join(base_dir, "main.py")

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        f"--name=VolumeBoosterPro",
        f"--icon={icon_path}",
        f"--add-data=assets;assets",
        "--hidden-import=PySide6",
        "--hidden-import=sounddevice",
        "--hidden-import=numpy",
        "--hidden-import=comtypes",
        "--hidden-import=pycaw",
        "--hidden-import=winreg",
        main_py
    ]

    print(f"Running command: {' '.join(cmd)}\n")
    ret = subprocess.call(cmd)
    if ret == 0:
        dist_dir = os.path.join(base_dir, "dist", "VolumeBoosterPro")
        print("\n==================================================")
        print("BUILD SUCCESSFUL!")
        print(f"Executable folder: {dist_dir}")
        print(f"Main binary: {os.path.join(dist_dir, 'VolumeBoosterPro.exe')}")
        print("==================================================")
    else:
        print(f"\nBuild failed with exit code {ret}")

if __name__ == "__main__":
    build()
