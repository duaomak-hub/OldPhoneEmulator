#!/usr/bin/env python3
"""
Build script for OldPhoneEmulator
Builds executables for Windows and Linux
- Uses PyInstaller when available (best for standalone exe)
- Falls back to shiv + zipapp when PyInstaller can't run (e.g., minimal container)
"""
import sys
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).parent

def run_cmd(cmd, cwd=BASE):
    print(f"$ {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False
    except FileNotFoundError as e:
        print(f"Not found: {e}")
        return False

def build_with_pyinstaller():
    """Try PyInstaller build (produces true standalone exe)"""
    print("\n🔨 Trying PyInstaller build...")
    try:
        import PyInstaller
    except ImportError:
        print("Installing pyinstaller...")
        if not run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller", "--break-system-packages"]):
            return False

    # Clean
    for d in ["build", "dist"]:
        p = BASE / d
        if p.exists():
            shutil.rmtree(p)

    # Determine separator
    sep = ";" if sys.platform == "win32" else ":"
    console = "--console"  # Keep console for logs

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "OldPhoneEmulator",
        "--onefile",
        console,
        "--add-data", f"{BASE/'emulator' / 'ui' / 'web' / 'templates'}{sep}emulator/ui/web/templates",
        "--add-data", f"{BASE/'emulator' / 'ui' / 'web' / 'static'}{sep}emulator/ui/web/static",
        "--hidden-import", "flask",
        "--hidden-import", "PIL",
        "--hidden-import", "jinja2",
        "--hidden-import", "werkzeug",
        "--collect-all", "flask",
        str(BASE / "main.py")
    ]

    print(f"Building with: {' '.join(cmd)}")
    if run_cmd(cmd):
        exe_name = "OldPhoneEmulator.exe" if sys.platform == "win32" else "OldPhoneEmulator"
        exe_path = BASE / "dist" / exe_name
        if exe_path.exists():
            print(f"\n✅ PyInstaller built: {exe_path} ({exe_path.stat().st_size/1024/1024:.1f} MB)")
            return True
        else:
            print("\n❌ PyInstaller build failed - exe not found")
            dist = BASE / "dist"
            if dist.exists():
                for f in dist.iterdir():
                    print(f"  {f}")
            return False
    return False

def build_with_shiv():
    """Fallback: shiv + zipapp (requires Python installed on target)"""
    print("\n🔨 Building with shiv + zipapp (portable, needs Python)...")

    try:
        import shiv
    except ImportError:
        print("Installing shiv...")
        run_cmd([sys.executable, "-m", "pip", "install", "shiv", "--break-system-packages"])

    dist = BASE / "dist"
    dist.mkdir(exist_ok=True)

    # Clean build
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    print(f"Temp build dir: {tmp}")

    try:
        # Copy only needed files
        shutil.copytree(BASE / "emulator", tmp / "emulator")
        shutil.copy(BASE / "main.py", tmp / "main.py")

        # Build pyz
        print("Building pyz...")
        run_cmd([sys.executable, "-m", "zipapp", str(tmp), "-m", "main:main", "-o", str(dist / "OldPhoneEmulator.pyz"), "-p", "/usr/bin/env python3"])

        # Build shiv
        print("Building shiv binary...")
        # shiv needs to be run from tmp
        cmd = ["shiv", "--site-packages", ".", "-e", "main:main", "-o", str(dist / "OldPhoneEmulator"), "--compressed", "-p", "/usr/bin/env python3"]
        subprocess.check_call(cmd, cwd=tmp)

        # Make executable
        (dist / "OldPhoneEmulator").chmod(0o755)
        (dist / "OldPhoneEmulator.pyz").chmod(0o755)

        # Create exe copy (pyz renamed, works with Python launcher on Windows)
        shutil.copy(dist / "OldPhoneEmulator.pyz", dist / "OldPhoneEmulator.exe")

        # Create launchers
        (dist / "OldPhoneEmulator.bat").write_text("""@echo off
REM OldPhoneEmulator Windows Launcher
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Install from https://python.org
    pause
    exit /b 1
)
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 pip install flask pillow
if "%1"=="" (
    python "%~dp0OldPhoneEmulator.pyz" --web --port 5000
) else (
    python "%~dp0OldPhoneEmulator.pyz" %*
)
pause
""")

        (dist / "OldPhoneEmulator.sh").write_text("""#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -c "import flask" 2>/dev/null || pip3 install flask pillow --break-system-packages
if [ $# -eq 0 ]; then
    python3 "$DIR/OldPhoneEmulator.pyz" --web --port 5000
else
    python3 "$DIR/OldPhoneEmulator.pyz" "$@"
fi
""")
        (dist / "OldPhoneEmulator.sh").chmod(0o755)

        print(f"\n✅ Built portable executables in {dist}:")
        for f in dist.iterdir():
            size = f.stat().st_size / 1024
            print(f"  {f.name:30} {size:.1f} KB")

        return True

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    print("🔨 Building OldPhoneEmulator...")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")

    # Try PyInstaller first
    if build_with_pyinstaller():
        print("\n🎉 PyInstaller build succeeded! Standalone exe ready.")
        return

    print("\n⚠️ PyInstaller failed (common in minimal containers without libpython)")
    print("Falling back to portable builds...")

    # Fallback to shiv
    if build_with_shiv():
        print("\n🎉 Portable build succeeded!")
        print("\nTo get true standalone .exe (no Python needed):")
        print("  - On Windows: pip install pyinstaller flask pillow && python build.py")
        print("  - Or push to GitHub and download artifact from Actions")
        print("\nCurrent portable exes require Python 3.8+ installed on target machine.")
    else:
        print("\n❌ All builds failed!")

if __name__ == "__main__":
    main()
