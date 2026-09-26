OldPhoneEmulator - Executables
===============================

Files:
- OldPhoneEmulator         Linux binary (shiv, 60KB) - needs Python 3.8+
                           Run: ./OldPhoneEmulator --web --port 5000

- OldPhoneEmulator.pyz     Portable zipapp (368KB) - Windows/Linux/macOS
                           Run: python OldPhoneEmulator.pyz --web

- OldPhoneEmulator.exe     Windows exe (pyz renamed, 368KB) - needs Python
                           Double-click or: OldPhoneEmulator.exe --web
                           For standalone exe (no Python), build on Windows:
                           pip install pyinstaller flask pillow
                           pyinstaller --onefile --add-data "emulator/ui/web/templates;emulator/ui/web/templates" --add-data "emulator/ui/web/static;emulator/ui/web/static" main.py

- OldPhoneEmulator.bat     Windows batch launcher
- OldPhoneEmulator.sh      Linux shell launcher

Usage:
./OldPhoneEmulator --web --port 5000  (web UI at localhost:5000)
./OldPhoneEmulator --list-devices
./OldPhoneEmulator --list-roms
./OldPhoneEmulator --device nokia_3310 --rom roms/demo.bin
./OldPhoneEmulator --cli

Supported: .rom .bin .rofs .sis .sisx .jar .exe .elf .iso .vhd .qcow .img
Import via drag-drop in web UI or --rom flag.

GitHub Actions builds true standalone Windows exe (30-50MB) automatically on push.
