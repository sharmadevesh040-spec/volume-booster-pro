"""
Volume Booster Pro - Complete Installer & Release Builder
1. Generates wizard branding bitmaps and multi-resolution icons.
2. Compiles standalone binary using PyInstaller.
3. Generates Inno Setup Windows installer (VolumeBoosterPro-Setup.exe).
4. Generates portable release ZIP (VolumeBoosterPro-Windows-Portable.zip).
5. Computes SHA256 integrity checksums.
"""

import os
import sys
import shutil
import zipfile
import hashlib
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def find_inno_setup_compiler():
    """Look for ISCC.exe in standard Windows locations, User AppData, or PATH."""
    cmd = shutil.which("iscc")
    if cmd:
        return cmd

    standard_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe"
    ]
    for p in standard_paths:
        if os.path.exists(p):
            return p
    return None

def compute_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().upper()

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=========================================================")
    print("      VOLUME BOOSTER PRO - FULL RELEASE BUILDER          ")
    print("=========================================================\n")

    # Step 1: Generate Branding & Icons
    print("[1/5] Generating professional wizard branding assets...")
    try:
        import generate_installer_assets
        generate_installer_assets.create_multi_res_icon()
        generate_installer_assets.create_wizard_large_bmp()
        generate_installer_assets.create_wizard_small_bmp()
    except Exception as e:
        print(f"  [!] Note: {e}")

    # Step 2: Run PyInstaller build
    print("\n[2/5] Compiling standalone executable with PyInstaller...")
    ret = subprocess.call([sys.executable, "build_exe.py"])
    if ret != 0:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(1)

    dist_dir = os.path.join(base_dir, "dist", "VolumeBoosterPro")
    if not os.path.exists(dist_dir):
        print(f"\n[ERROR] Build directory not found: {dist_dir}")
        sys.exit(1)

    # Ensure assets and legal docs exist in dist
    assets_target = os.path.join(dist_dir, "assets")
    os.makedirs(assets_target, exist_ok=True)
    for asset_file in os.listdir(os.path.join(base_dir, "assets")):
        src = os.path.join(base_dir, "assets", asset_file)
        dst = os.path.join(assets_target, asset_file)
        shutil.copy2(src, dst)
    for doc in ["LICENSE.txt", "README.md"]:
        src = os.path.join(base_dir, doc)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dist_dir, doc))

    # Step 3: Inno Setup Installer
    print("\n[3/5] Checking for Inno Setup Compiler...")
    iscc = find_inno_setup_compiler()
    setup_exe = os.path.join(base_dir, "dist", "VolumeBoosterPro-Setup.exe")
    if iscc:
        print(f"  [+] Found Inno Setup: {iscc}")
        print("  Generating dist\\VolumeBoosterPro-Setup.exe...")
        ret_iscc = subprocess.call([iscc, "installer.iss"])
        if ret_iscc == 0 and os.path.exists(setup_exe):
            print(f"  [+] Setup Installer created: {setup_exe} ({os.path.getsize(setup_exe):,} bytes)")
        else:
            print("  [!] Inno Setup compilation returned non-zero code.")
            sys.exit(1)
    else:
        print("  [ERROR] Inno Setup compiler (ISCC.exe) not found!")
        print("          Install via: winget install JRSoftware.InnoSetup")
        sys.exit(1)

    # Step 4: Create Portable ZIP
    print("\n[4/5] Creating portable ZIP archive...")
    zip_path = os.path.join(base_dir, "dist", "VolumeBoosterPro-Windows-Portable.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, os.path.join(base_dir, "dist"))
                zipf.write(abs_file, rel_file)

    print(f"  [+] Portable ZIP created: {zip_path} ({os.path.getsize(zip_path):,} bytes)")

    # Step 5: Compute SHA-256 Checksums
    print("\n[5/5] Generating SHA256 integrity checksums...")
    setup_hash = compute_sha256(setup_exe)
    zip_hash = compute_sha256(zip_path)
    checksums_file = os.path.join(base_dir, "dist", "SHA256SUMS.txt")
    with open(checksums_file, "w", encoding="ascii") as f:
        f.write(f"{setup_hash}  VolumeBoosterPro-Setup.exe\n")
        f.write(f"{zip_hash}  VolumeBoosterPro-Windows-Portable.zip\n")

    print(f"  [+] Saved checksums to {checksums_file}")
    print(f"      Setup:    {setup_hash}")
    print(f"      Portable: {zip_hash}")

    print("\n=========================================================")
    print("BUILD COMPLETE! Artifacts ready in dist/:")
    print(f"  - {setup_exe}")
    print(f"  - {zip_path}")
    print(f"  - {checksums_file}")
    print("=========================================================")

if __name__ == "__main__":
    main()
