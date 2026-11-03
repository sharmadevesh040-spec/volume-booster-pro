"""
Volume Booster Pro - GitHub Release Packaging & Publishing Automation
Verifies artifacts, generates SHA-256 checksums, compiles RELEASE_NOTES.md,
and offers 1-click publishing via GitHub CLI (gh).
"""

import os
import sys
import shutil
import hashlib
import subprocess

VERSION = "2.0.0"
TAG = f"v{VERSION}"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
SETUP_EXE = os.path.join(DIST_DIR, "VolumeBoosterPro-Setup.exe")
PORTABLE_ZIP = os.path.join(DIST_DIR, "VolumeBoosterPro-Windows-Portable.zip")
CHECKSUMS_FILE = os.path.join(DIST_DIR, "SHA256SUMS.txt")
RELEASE_NOTES = os.path.join(BASE_DIR, "RELEASE_NOTES.md")

def compute_sha256(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().upper()

def main():
    print("======================================================================")
    print("           VOLUME BOOSTER PRO - GITHUB RELEASE PUBLISHER              ")
    print("======================================================================\n")

    # 1. Verify / Build Artifacts
    if not os.path.exists(SETUP_EXE):
        print("[!] dist/VolumeBoosterPro-Setup.exe not found.")
        print("[*] Running full build first...")
        ret = subprocess.call([sys.executable, "build_installer.py"], cwd=BASE_DIR)
        if ret != 0:
            print("[ERROR] Build failed. Aborting publish.")
            sys.exit(1)

    if not os.path.exists(PORTABLE_ZIP):
        print("[*] Generating portable ZIP archive...")
        app_dist = os.path.join(DIST_DIR, "VolumeBoosterPro")
        shutil.make_archive(os.path.splitext(PORTABLE_ZIP)[0], 'zip', app_dist)

    # 2. Compute SHA-256 Checksums
    print("[*] Computing SHA-256 Checksums...")
    setup_hash = compute_sha256(SETUP_EXE)
    zip_hash = compute_sha256(PORTABLE_ZIP)
    sums_content = f"{setup_hash}  VolumeBoosterPro-Setup.exe\n{zip_hash}  VolumeBoosterPro-Windows-Portable.zip\n"
    with open(CHECKSUMS_FILE, "w", encoding="ascii") as f:
        f.write(sums_content)
    print(f"  [+] Setup.exe:    {setup_hash}")
    print(f"  [+] Portable.zip: {zip_hash}")

    # 3. Generate RELEASE_NOTES.md
    print("\n[*] Generating RELEASE_NOTES.md...")
    notes = f"""# Volume Booster Pro {TAG} — Release Notes

## 🚀 Highlights in Version {VERSION}
- **Professional 1-Click Windows Setup:** Added `VolumeBoosterPro-Setup.exe` with Inno Setup modern wizard, desktop/start menu shortcuts, and uninstaller.
- **Automated Audio Diagnostics:** Automatically detects Equalizer APO installation and provides seamless kernel-level volume amplification without manual configuration.
- **Symmetric Tanh Soft-Limiter:** Eliminates digital clipping while maintaining punchy bass and crystal-clear vocals.
- **3-Band Biquad Parametric EQ:** Tuned presets for Laptop Speakers, Bass Boost, Movies, and Vocal Clarity.
- **Non-Destructive Safety:** Full backup of existing audio configuration files (`config.txt.bak`) before any filter modifications.
- **Portable ZIP Edition:** Standalone zero-install archive for USB drives and test environments.

## 📦 Release Artifacts
| File | Size | Type | Description |
| :--- | :--- | :--- | :--- |
| **VolumeBoosterPro-Setup.exe** | {os.path.getsize(SETUP_EXE):,} bytes | Official Installer | Recommended 1-click Windows installer (Program Files) |
| **VolumeBoosterPro-Windows-Portable.zip** | {os.path.getsize(PORTABLE_ZIP):,} bytes | Portable Archive | Standalone folder — run directly without install |
| **SHA256SUMS.txt** | {os.path.getsize(CHECKSUMS_FILE):,} bytes | Integrity Checksums | SHA-256 validation hashes |

## 🛡️ Integrity Checksums (SHA-256)
```text
{sums_content.strip()}
```

## 📥 Installation Instructions
1. Download **`VolumeBoosterPro-Setup.exe`**.
2. Run the installer and follow the setup wizard.
3. Launch **Volume Booster Pro** from your Desktop or Start Menu!
"""
    with open(RELEASE_NOTES, "w", encoding="utf-8") as f:
        f.write(notes.strip() + "\n")
    print(f"  [+] Saved: {RELEASE_NOTES}")

    # 4. Check for GitHub CLI
    gh_cmd = shutil.which("gh")
    if gh_cmd:
        print("\nGitHub CLI (gh) detected.")
        try:
            do_gh = input("Would you like to publish this release to GitHub now? [y/N]: ").strip().lower()
            if do_gh in ("y", "yes"):
                print(f"[*] Uploading release {TAG} to GitHub...")
                ret = subprocess.call([
                    gh_cmd, "release", "create", TAG,
                    SETUP_EXE, PORTABLE_ZIP, CHECKSUMS_FILE,
                    "--title", f"Volume Booster Pro {TAG}",
                    "--notes-file", RELEASE_NOTES
                ], cwd=BASE_DIR)
                if ret == 0:
                    print(f"\n[SUCCESS] Release {TAG} published on GitHub!")
                    return
                else:
                    print("[!] gh release create exited with non-zero status.")
        except EOFError:
            pass

    print("\n" + "=" * 70)
    print("                     RELEASE PACKAGING COMPLETE!")
    print("=" * 70)
    print("To publish this release manually on GitHub:")
    print(f"  1. Push your tag: git tag {TAG} && git push origin {TAG}")
    print("  2. Go to your GitHub repository -> Releases -> 'Draft a new release'")
    print(f"  3. Select tag '{TAG}'")
    print("  4. Paste the content of RELEASE_NOTES.md into the description")
    print("  5. Attach the following 3 files from dist/:")
    print(f"       - {SETUP_EXE}")
    print(f"       - {PORTABLE_ZIP}")
    print(f"       - {CHECKSUMS_FILE}")
    print("  6. Click 'Publish release'.")
    print("=" * 70)

if __name__ == "__main__":
    main()
