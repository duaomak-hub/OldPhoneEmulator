# 📱 OldPhoneEmulator

**A real, cross-platform Symbian OS / Nokia OS emulator that supports any kind of ROM, iconic Nokia phones, Windows EXE, Linux ELF, and disk images — with app launcher, ROM import, and iconic keypad.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Symbian](https://img.shields.io/badge/Symbian-S60%201st%20to%20Belle-124191)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

### 📱 Iconic Nokia Phones Emulated
- **Series 30**: 3310 (2000), 3210, 1100 — the indestructible legends
- **Series 60**: 6600, 7610, N70, **N95 / N95 8GB** ⭐, E90 Communicator, 5800 XpressMusic, N8, 808 PureView
- **Others**: N900 (Maemo), Asha, Series 40
- Each device has accurate screen resolution, RAM, CPU, keypad layout

### 💾 ROM Support - "Any Kind of ROM"
The universal `RomLoader` auto-detects and supports:

**Symbian / Nokia ROMs:**
- `.rom`, `.bin`, `.img`, `.rofs`, `.rofs2`, `.rofs3`, `.uda`, `.core`, `.md0`
- Nokia flash: `.fpsx`, `.vpl`, `.dcp`, `.mcusw`, `.ppm`, `.cnt`
- Magic detection for ROFS, UDA, MCU, PPM

**App Packages:**
- `.sis` (S60 1st/2nd) and `.sisx` (S60 3rd+) - full parser, installs to `C:\system\apps\`
- `.jar` / `.jad` - Java ME MIDlets, extracts manifest, installs to `C:\system\midlets\`

**Windows & Linux Executables:**
- `.exe`, `.dll` - PE parser (x86, x64, ARM), checks imports, .NET detection, Symbian EXE compat
- `.elf`, `.out` - ELF parser (x86, ARM, AArch64), program headers, sections

**Disk Images (Windows/Linux disks):**
- `.iso` - ISO9660 with file listing, bootable detection
- `.vhd`, `.vhdx` - Virtual Hard Disk
- `.qcow`, `.qcow2` - QEMU
- `.vmdk`, `.raw`, `.img` - raw images with MBR/GPT parsing, FAT12/16/32, NTFS, EXT4 detection

**Archives:** `.zip` containing any of above

### 🎮 App Launcher
- Grid of installed apps with icons (Phone, Contacts, Messaging, Gallery, Camera, Web, Snake, Bounce, etc.)
- Launch / close / uninstall
- Run count, UID tracking, capabilities display
- Supports native Symbian `.app`, SIS/SISX, JAR MIDlets, Windows EXE compat, Linux ELF compat
- Drag & drop or file dialog import

### ⌨️ Iconic Keypad
- **Exact Nokia layout**: Soft left/right, Call/End, 5-way D-pad, 12-key numpad with letters
- Visual press animation, haptic feedback, key sounds
- Maps to keyboard arrows + numbers
- Long-press detection
- Touch + mouse support

### 🖥️ Screen Emulation
- Accurate resolutions: 84x48 (3310) to 800x352 (E90) to 360x640 (5800/N8)
- Nokia screen colors: `#a8c686` with grid scanlines
- Status bar: signal, operator, time, battery
- Softkeys
- Canvas with pixelated rendering

### ⚙️ Emulator Core
- **ARMv5TE CPU**: Pure Python interpreter + optional Unicorn engine acceleration
  - Handles B, BL, BX, data processing, LDR/STR, LDM/STM, SWI
  - Registers r0-r15, CPSR, Thumb mode
- **Memory**: Symbian map (BOOT_ROM 0x00000000, RAM 0x30000000, MAIN_ROM 0x40000000, IO, VRAM, KERNEL)
- **Kernel**: E32 kernel emulation - processes, threads, handles, SVC
- **Filesystem**: Drives Z: (ROM), C: (internal), D: (RAM), E: (MMC) with `system/apps`, `system/libs`, etc.
- **E32 API shim**: HAL, tick count, debug print

---

## 🚀 Quick Start

### Web UI (Recommended - Works Everywhere)

```bash
pip install flask pillow
python main.py --web --port 5000
# Open http://localhost:5000
```

**Preview in this environment binds to 0.0.0.0 - works with https://{port}-{sandbox}.e2b.app**

### CLI

```bash
python main.py --cli
python main.py --list-devices
python main.py --list-roms
python main.py --device nokia_3310 --rom roms/n95.rofs
```

### Import ROMs

- **Web**: Drag & drop onto drop zone or click "Import ROM"
- **CLI**: `python main.py --rom path/to/file`
- **Folder**: Drop files into `roms/` folder - auto-scanned on start

---

## 📂 Project Structure

```
OldPhoneEmulator/
├── main.py                 # Entry point
├── build.py                # PyInstaller build for Windows/Linux exe
├── pyproject.toml
├── requirements.txt
├── roms/                   # Drop ROMs here
├── assets/
├── emulator/
│   ├── config.py           # Global config, supported extensions
│   ├── core/
│   │   ├── cpu_arm.py      # ARMv5TE emulator (pure python + unicorn)
│   │   ├── memory.py       # Symbian memory map
│   │   ├── rom_loader.py   # Universal ROM loader (any type)
│   │   ├── kernel.py       # E32 kernel
│   │   ├── filesystem.py   # Symbian file server (Z:, C:, D:, E:)
│   │   └── disk.py         # Disk image parser (ISO, VHD, QCOW, MBR, FAT, NTFS, EXT)
│   ├── formats/
│   │   ├── sis.py          # SIS/SISX parser
│   │   ├── jar.py          # JAR/JAD parser
│   │   ├── exe_pe.py       # PE parser for Windows EXE
│   │   ├── elf.py          # ELF parser for Linux
│   │   └── iso.py          # ISO9660 parser
│   ├── devices/
│   │   ├── base.py         # Device specs
│   │   └── nokia_profiles.py # 14 iconic Nokia devices
│   ├── symbian/
│   │   ├── os_versions.py  # S60 1st to Belle
│   │   ├── app_runtime.py  # App lifecycle, launcher
│   │   └── e32.py          # Symbian API shim
│   └── ui/
│       ├── web_server.py   # Flask web server
│       └── web/
│           ├── templates/index.html
│           └── static/
│               ├── style.css  # Nokia-themed UI
│               └── app.js     # Keypad, launcher, ROM import logic
└── fs/                     # Emulated Symbian filesystem (generated)
    ├── z_drive/
    ├── c_drive/system/apps/
    └── e_drive/
```

---

## 🛠️ Building Executables

### Windows EXE

```bash
pip install pyinstaller flask pillow
python build.py
# Output: dist/OldPhoneEmulator.exe
```

### Linux Binary

```bash
pip install pyinstaller flask pillow --break-system-packages
python build.py
# Output: dist/OldPhoneEmulator
chmod +x dist/OldPhoneEmulator
./dist/OldPhoneEmulator --web
```

The exe supports:
- `--web --port 5000` - start web UI
- `--cli` - terminal mode
- `--device nokia_n95` - choose device
- `--rom file` - load ROM

---

## 🎯 Usage Examples

**Load Symbian ROFS:**
```python
from emulator.core.rom_loader import RomLoader
rom = RomLoader.load("roms/N95_rofs2.bin")
print(rom.rom_type, rom.metadata)
```

**Parse SIS:**
```python
from emulator.formats.sis import SisParser
pkg = SisParser.parse(data, "game.sisx")
print(pkg.name, pkg.uid, pkg.files)
```

**Switch device:**
```python
from emulator.devices.nokia_profiles import DeviceRegistry
reg = DeviceRegistry()
n95 = reg.get("nokia_n95")
print(n95.screen.resolution, n95.hardware.ram_mb)
```

**Emulate CPU:**
```python
from emulator.core.memory import Memory
from emulator.core.cpu_arm import ARMv5CPU
mem = Memory()
cpu = ARMv5CPU(mem)
cpu.reset(0x40000000)
cpu.step()
print(cpu.get_state_dict())
```

---

## 🔧 Supported File Types

| Type | Extensions | Parser | Notes |
|------|-----------|--------|-------|
| Symbian ROM | .rom .bin .rofs .uda .core | RomLoader | Loads to 0x40000000 |
| Nokia Flash | .fpsx .mcu .ppm | RomLoader | MCU+PPM+Content |
| SIS | .sis .sisx | SisParser | ZIP-based, installs files |
| Java | .jar .jad | JarParser | MIDlet manifest |
| Windows | .exe .dll | PeParser | PE32/PE64, imports, .NET check |
| Linux | .elf | ElfParser | ELF32/64, ARM/x86 |
| Disk | .iso | IsoParser | ISO9660, bootable |
| Disk | .vhd .qcow .img | DiskImage | MBR, FAT, NTFS, EXT4 |

---

## 🎨 UI Preview

The web UI includes:
- **Left**: Phone frame with screen + iconic keypad (softkeys, D-pad, numpad with letters like real Nokia)
- **Right**: Tabs - App Launcher (grid), Devices (searchable list of 14 Nokias), ROMs (drag-drop), Apps (installed), Files (C:, Z:, E: drives)
- **Canvas screen**: Renders Nokia green screen with scanlines, status bar, menu

---

## 🤝 Contributing

- Add new Nokia device profiles in `emulator/devices/nokia_profiles.py`
- Add new ROM formats in `emulator/formats/`
- Improve ARM emulation in `emulator/core/cpu_arm.py` (currently handles common opcodes, uses Unicorn if available)

---

## 📜 License

MIT - Emulate responsibly. ROMs are copyright of Nokia/Microsoft - only use ROMs you own.

---

## 🙏 Acknowledgments

- Nokia for iconic phones (3310, N95, 5800, etc.)
- Symbian Foundation for Symbian OS
- Unicorn Engine for optional ARM acceleration
- Flask for web UI

**Made for nostalgia, education, and preservation of mobile history.** 📱✨

<!-- contributors cache refresh -->
# Contributors: only duaomak-hub
