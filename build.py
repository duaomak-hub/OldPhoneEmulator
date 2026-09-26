#!/usr/bin/env python3
"""
Build script for OldPhoneEmulator
Builds executables for Windows and Linux using PyInstaller
"""
import sys
import shutil
from pathlib import Path
import subprocess

BASE = Path(__file__).parent

def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--break-system-packages"])
        return True

def build_exe():
    check_pyinstaller()

    # Clean previous builds
    for d in ["build", "dist"]:
        p = BASE / d
        if p.exists():
            shutil.rmtree(p)

    # PyInstaller args
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "OldPhoneEmulator",
        "--onefile",
        "--windowed",  # No console on Windows, but we want console for CLI? Use --console for now
        "--add-data", f"{BASE/'emulator' / 'ui' / 'web' / 'templates'}:emulator/ui/web/templates",
        "--add-data", f"{BASE/'emulator' / 'ui' / 'web' / 'static'}:emulator/ui/web/static",
        "--hidden-import", "flask",
        "--hidden-import", "PIL",
        "--collect-all", "flask",
        "--icon", "NONE",
        str(BASE / "main.py")
    ]

    # Adjust for platform
    if sys.platform == "win32":
        cmd[5] = "--add-data"
        cmd[6] = f"{BASE/'emulator' / 'ui' / 'web' / 'templates'};emulator/ui/web/templates"
        cmd[7] = "--add-data"
        cmd[8] = f"{BASE/'emulator' / 'ui' / 'web' / 'static'};emulator/ui/web/static"
        # Use console for Windows too for logs, but can be changed to windowed
        cmd[4] = "--console"

    print(f"Building with: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=BASE)

    exe_name = "OldPhoneEmulator.exe" if sys.platform == "win32" else "OldPhoneEmulator"
    exe_path = BASE / "dist" / exe_name
    if exe_path.exists():
        print(f"\n✅ Built executable: {exe_path} ({exe_path.stat().st_size/1024/1024:.1f} MB)")
        print(f"   Run: {exe_path} --web --port 5000")
    else:
        print("\n❌ Build failed - exe not found")
        # List dist
        dist = BASE / "dist"
        if dist.exists():
            print(f"Contents of {dist}:")
            for f in dist.iterdir():
                print(f"  {f}")

def build_linux_appimage():
    # Placeholder for AppImage build
    print("AppImage build not yet implemented - use PyInstaller binary")

if __name__ == "__main__":
    print("🔨 Building OldPhoneEmulator...")
    print(f"Platform: {sys.platform}")
    build_exe()
