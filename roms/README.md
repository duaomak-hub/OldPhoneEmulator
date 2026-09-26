# ROMs Folder

Drop your ROMs, apps, and disk images here. The emulator auto-scans on start and supports:

### Symbian / Nokia ROMs
- `.rom`, `.bin`, `.img` - Full ROM dumps
- `.rofs`, `.rofs2`, `.rofs3` - Read-only file system
- `.uda` - User data area
- `.core` - Core OS
- `.fpsx`, `.vpl`, `.dcp` - Nokia flash files (use with Phoenix/WinHex)
- `.mcusw`, `.ppm`, `.cnt` - MCU software, language pack, content

**Where to get:** Dump from your own Nokia device using JAF, Phoenix, or DeadUSB flashing tools. Only use ROMs you legally own.

### App Packages
- `.sis`, `.sisx` - Symbian apps (e.g., Opera Mini, Google Maps, games)
- `.jar`, `.jad` - Java ME MIDlets (e.g., Gmail, Snaptu, old games)

**Where to get:** Your own backups, old Nokia Store downloads.

### Windows / Linux Compatibility
- `.exe`, `.dll` - Windows PE executables (emulator provides compat layer, parses imports)
- `.elf` - Linux binaries (ARM, x86)

### Disk Images
- `.iso` - Windows/Linux installer ISOs, will be parsed for files
- `.vhd`, `.vhdx`, `.qcow`, `.qcow2`, `.vmdk`, `.img` - Virtual disk images, MBR/GPT parsed

### How to Import
1. **Web UI**: Drag & drop onto the drop zone or click "Import ROM" button
2. **File system**: Copy files into this folder and restart emulator or click refresh
3. **CLI**: `python main.py --rom path/to/file`

### Example Structure
```
roms/
├── N95_8GB_ROFS2.bin      (Symbian ROFS)
├── N95_UDA.bin
├── OperaMini.sisx         (will auto-install to C:\system\apps\)
├── Bounce.jar             (Java game)
├── windows_app.exe        (PE - compat layer)
├── linux_tool.elf         (ELF - compat layer)
└── ubuntu.iso             (disk image)
```

### Auto-Handling
- Symbian ROMs → loaded to memory at 0x40000000, CPU reset to entry point
- SIS/SISX → installed to emulated C: drive, appears in app launcher
- JAR → installed as MIDlet, appears in launcher
- EXE/ELF → imported as compat app, file saved to C:\system\apps\
- ISO/VHD → mounted info, file list extracted, appears in disks list

**Note:** This folder is gitignored for large files, but you can keep small test ROMs.
