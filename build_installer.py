"""
Volume Booster Pro - Complete Installer & Release Builder
1. Builds standalone executable using PyInstaller.
2. Generates Inno Setup Windows installer (VolumeBoosterPro-Setup.exe) if Inno Setup is available.
3. Generates portable release ZIP (VolumeBoosterPro-Windows-Portable.zip).
"""

import os
import sys
import shutil
import zipfile
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def find_inno_setup_compiler():
    """Look for ISCC.exe in standard Windows locations or PATH."""
    cmd = shutil.which("iscc")
    if cmd:
        return cmd

    standard_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe")
    ]
    for p in standard_paths:
        if os.path.exists(p):
            return p
    return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=========================================================")
    print("      VOLUME BOOSTER PRO - FULL RELEASE BUILDER          ")
    print("=========================================================\n")

    # Step 1: Run PyInstaller build
    print("[1/3] Compiling standalone executable with PyInstaller...")
    ret = subprocess.call([sys.executable, "build_exe.py"])
    if ret != 0:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(1)

    dist_dir = os.path.join(base_dir, "dist", "VolumeBoosterPro")
    if not os.path.exists(dist_dir):
        print(f"\n[ERROR] Build directory not found: {dist_dir}")
        sys.exit(1)

    # Step 2: Inno Setup Installer
    print("\n[2/3] Checking for Inno Setup Compiler...")
    iscc = find_inno_setup_compiler()
    if iscc:
        print(f"  [+] Found Inno Setup: {iscc}")
        print("  Generating dist\\VolumeBoosterPro-Setup.exe...")
        ret_iscc = subprocess.call([iscc, "installer.iss"])
        if ret_iscc == 0:
            setup_exe = os.path.join(base_dir, "dist", "VolumeBoosterPro-Setup.exe")
            print(f"  [+] Setup Installer created: {setup_exe}")
        else:
            print("  [!] Inno Setup compilation returned non-zero code.")
    else:
        print("  [INFO] Inno Setup (ISCC.exe) not found on local machine.")
        print("         To compile VolumeBoosterPro-Setup.exe locally, install Inno Setup 6:")
        print("         https://jrsoftware.org/isdl.php")
        print("         (Note: GitHub Actions will build it automatically upon push!)")

    # Step 3: Create Portable ZIP
    print("\n[3/3] Creating portable ZIP archive...")
    zip_path = os.path.join(base_dir, "VolumeBoosterPro-Windows-Portable.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, os.path.join(base_dir, "dist"))
                zipf.write(abs_file, rel_file)

    print(f"  [+] Portable ZIP created: {zip_path}")

    print("\n=========================================================")
    print("BUILD COMPLETE! Artifacts ready in dist/ and project root.")
    print("=========================================================")

if __name__ == "__main__":
    main()

