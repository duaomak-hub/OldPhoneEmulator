# Building Windows EXE

The GitHub App token in this sandbox cannot push `.github/workflows/` files due to permission restrictions.
To enable automatic Windows EXE builds, manually add the workflow file:

## Manual Step (one-time):

1. On GitHub, go to your repo: https://github.com/duaomak-hub/OldPhoneEmulator
2. Create file `.github/workflows/build.yml` with content below
3. Or run these commands locally (with your personal PAT that has workflow permission):

```bash
mkdir -p .github/workflows
cat > .github/workflows/build.yml << 'YML'
name: Build Executables

on:
  push:
    branches: [ main, arena/* ]
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          python -m pip install --upgrade pip
          pip install flask pillow pyinstaller
      - run: |
          pyinstaller --name OldPhoneEmulator --onefile --console --add-data "emulator/ui/web/templates;emulator/ui/web/templates" --add-data "emulator/ui/web/static;emulator/ui/web/static" --hidden-import flask --hidden-import PIL --collect-all flask main.py
      - uses: actions/upload-artifact@v4
        with:
          name: OldPhoneEmulator-Windows
          path: dist/OldPhoneEmulator.exe
YML
git add .github/workflows/build.yml
git commit -m "ci: add Windows exe build workflow"
git push origin main
```

## Building EXE locally:

### Windows (standalone exe, no Python needed):
```cmd
pip install flask pillow pyinstaller
pyinstaller --name OldPhoneEmulator --onefile --console --add-data "emulator/ui/web/templates;emulator/ui/web/templates" --add-data "emulator/ui/web/static;emulator/ui/web/static" --hidden-import flask --hidden-import PIL --collect-all flask main.py
dist\OldPhoneEmulator.exe --web --port 5000
```

### Linux (portable, needs Python):
```bash
pip install flask pillow shiv
python build.py
./dist/OldPhoneEmulator --web --port 5000
```

Current portable exes already built in `dist/`:
- OldPhoneEmulator (Linux shiv, 60KB)
- OldPhoneEmulator.pyz (portable, 368KB)
- OldPhoneEmulator.exe (Windows, pyz renamed, 368KB)
- OldPhoneEmulator.bat / .sh launchers

See dist/README.txt for details.
