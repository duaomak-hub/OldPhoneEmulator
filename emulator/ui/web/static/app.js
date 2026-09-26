/**
 * OldPhoneEmulator - Frontend JS
 * Handles iconic keypad, ROM import, app launcher, device switching
 */

let state = {
    device: null,
    roms: [],
    apps: [],
    drives: {},
    cpu: {},
    running: false
};

// DOM refs
const appGrid = document.getElementById('app-grid');
const romsList = document.getElementById('roms-list');
const disksList = document.getElementById('disks-list');
const appsList = document.getElementById('apps-list');
const drivesList = document.getElementById('drives-list');
const logsEl = document.getElementById('logs');
const screenCanvas = document.getElementById('phone-screen');
const ctx = screenCanvas.getContext('2d');

// Init
document.addEventListener('DOMContentLoaded', () => {
    initKeypad();
    initUpload();
    initDropZone();
    initScreen();
    startPolling();
    updateTime();
    setInterval(updateTime, 1000);
});

function updateTime() {
    const now = new Date();
    const el = document.getElementById('screen-time');
    if (el) el.textContent = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Keypad handling
function initKeypad() {
    document.querySelectorAll('.key').forEach(btn => {
        const key = btn.dataset.key;

        btn.addEventListener('mousedown', (e) => {
            e.preventDefault();
            handleKeyPress(key, 'press');
            btn.classList.add('active');
        });

        btn.addEventListener('mouseup', () => {
            handleKeyPress(key, 'release');
            btn.classList.remove('active');
        });

        btn.addEventListener('mouseleave', () => {
            btn.classList.remove('active');
        });

        // Touch
        btn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            handleKeyPress(key, 'press');
            btn.classList.add('active');
        }, {passive: false});

        btn.addEventListener('touchend', (e) => {
            e.preventDefault();
            handleKeyPress(key, 'release');
            btn.classList.remove('active');
        });
    });

    // Keyboard mapping
    document.addEventListener('keydown', (e) => {
        const map = {
            'ArrowUp': 'dpad_up',
            'ArrowDown': 'dpad_down',
            'ArrowLeft': 'dpad_left',
            'ArrowRight': 'dpad_right',
            'Enter': 'dpad_center',
            'SoftLeft': 'soft_left',
            'SoftRight': 'soft_right',
            'Escape': 'end',
            'Backspace': 'end'
        };
        let k = map[e.key] || e.key.toLowerCase();
        if (/^[0-9*#]$/.test(e.key)) k = e.key;
        if (k) handleKeyPress(k, 'press');
    });
}

function handleKeyPress(key, action) {
    // Visual feedback
    const screenMenu = document.getElementById('screen-menu');
    if (screenMenu && action === 'press') {
        const items = screenMenu.querySelectorAll('.menu-item');
        let activeIdx = Array.from(items).findIndex(i => i.classList.contains('active'));

        if (key === 'dpad_down') {
            if (activeIdx >=0) items[activeIdx].classList.remove('active');
            activeIdx = (activeIdx + 1) % items.length;
            items[activeIdx].classList.add('active');
        } else if (key === 'dpad_up') {
            if (activeIdx >=0) items[activeIdx].classList.remove('active');
            activeIdx = (activeIdx - 1 + items.length) % items.length;
            items[activeIdx].classList.add('active');
        } else if (key === 'dpad_center' || key === '5') {
            const active = screenMenu.querySelector('.menu-item.active');
            if (active) {
                // Simulate launch
                active.style.background = '#00d4ff';
                setTimeout(() => active.style.background = '', 200);
            }
        }

        // Number keys show on screen
        if (/^[0-9*#]$/.test(key)) {
            const overlay = document.getElementById('screen-content');
            if (overlay) {
                // Flash key
                const flash = document.createElement('div');
                flash.textContent = key;
                flash.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:48px;font-weight:800;color:#000;opacity:0.8;';
                overlay.appendChild(flash);
                setTimeout(() => flash.remove(), 300);
            }
        }
    }

    // Send to backend
    fetch('/api/keypress', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key, action})
    }).then(r => r.json()).then(data => {
        if (data.key === 'power') {
            state.running = !state.running;
            updatePowerStatus();
        }
    });

    // Haptic if available
    if (navigator.vibrate && action === 'press') navigator.vibrate(20);
}

function updatePowerStatus() {
    const el = document.getElementById('header-status');
    if (el) {
        el.textContent = state.running ? 'ON' : 'OFF';
        el.className = state.running ? 'status-on' : 'status-off';
    }
    const canvas = document.getElementById('phone-screen');
    if (canvas) {
        canvas.style.filter = state.running ? 'none' : 'brightness(0.5)';
    }
}

// Screen rendering - Nokia style
function initScreen() {
    if (!ctx) return;
    renderScreen();
}

function renderScreen() {
    if (!ctx) return;
    const w = screenCanvas.width;
    const h = screenCanvas.height;

    // Nokia screen background
    ctx.fillStyle = '#a8c686';
    ctx.fillRect(0, 0, w, h);

    // Grid effect
    ctx.fillStyle = 'rgba(0,0,0,0.03)';
    for (let y = 0; y < h; y += 4) {
        ctx.fillRect(0, y, w, 1);
    }

    // Running apps indicator
    if (state.running && state.apps) {
        const running = state.apps.filter(a => a.state === 'running');
        if (running.length > 0) {
            ctx.fillStyle = '#000';
            ctx.font = 'bold 12px "JetBrains Mono"';
            ctx.fillText(`Running: ${running[0].name}`, 8, 24);
            ctx.font = '10px "JetBrains Mono"';
            ctx.fillText(`UID: ${running[0].uid}`, 8, 36);
        }
    }

    // Signal bars
    ctx.fillStyle = '#000';
    for (let i = 0; i < 4; i++) {
        const x = w - 40 + i*8;
        const height = 4 + i*3;
        ctx.fillRect(x, 12 - height, 6, height);
    }

    requestAnimationFrame(renderScreen);
}

// Upload
function initUpload() {
    const input = document.getElementById('rom-upload');
    if (!input) return;
    input.addEventListener('change', async (e) => {
        const files = e.target.files;
        for (let file of files) {
            await uploadFile(file);
        }
        input.value = '';
    });
}

function initDropZone() {
    const zone = document.getElementById('drop-zone');
    if (!zone) return;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });
    zone.addEventListener('drop', async (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        for (let file of files) {
            await uploadFile(file);
        }
    });
}

async function uploadFile(file) {
    const form = new FormData();
    form.append('file', file);

    // Show uploading
    addLog(`Uploading ${file.name} (${(file.size/1024/1024).toFixed(2)} MB)...`);

    try {
        const res = await fetch('/api/roms/upload', { method: 'POST', body: form });
        const data = await res.json();
        if (data.success) {
            addLog(`✅ Imported ${file.name} as ${data.rom.type}`);
            await refreshState();
        } else {
            addLog(`❌ Failed ${file.name}: ${data.error}`);
        }
    } catch (e) {
        addLog(`❌ Error uploading ${file.name}: ${e}`);
    }
}

// Polling state
function startPolling() {
    refreshState();
    setInterval(refreshState, 2000);
}

async function refreshState() {
    try {
        const res = await fetch('/api/state');
        const data = await res.json();
        state = data;
        renderAll();
    } catch (e) {
        console.error(e);
    }
}

function renderAll() {
    renderApps();
    renderRoms();
    renderDrives();
    renderCPU();
    renderLogs();
    renderDevicesSelect();

    document.getElementById('header-roms').textContent = `${state.roms.length} ROMs`;
    document.getElementById('header-device').textContent = state.device ? state.device.name : 'No Device';
    updatePowerStatus();
}

function renderApps() {
    if (!appGrid) return;
    appGrid.innerHTML = '';

    const apps = state.apps || [];
    document.getElementById('apps-count').textContent = `${apps.length} apps`;

    const iconMap = {
        'Phone': '📞',
        'Contacts': '👥',
        'Messages': '💬',
        'Gallery': '🖼️',
        'Camera': '📸',
        'Web': '🌐',
        'Calendar': '📅',
        'Clock': '⏰',
        'File Manager': '📁',
        'Log': '📋',
        'Snake': '🐍',
        'Bounce': '🔴',
        'Music Player': '🎵',
        'App Manager': '📦',
        'Maps': '🗺️'
    };

    apps.forEach(app => {
        const div = document.createElement('div');
        div.className = `app-icon ${app.state === 'running' ? 'running' : ''}`;
        const icon = iconMap[app.name] || (app.type === 'java_midlet' ? '☕' : app.type === 'pe_exe' ? '🪟' : app.type === 'elf' ? '🐧' : '📱');
        div.innerHTML = `
            <div class="app-icon-emoji">${icon}</div>
            <div class="app-icon-name">${app.name}</div>
            <div class="app-icon-uid">${app.uid}</div>
        `;
        div.onclick = () => launchApp(app.uid);
        div.oncontextmenu = (e) => {
            e.preventDefault();
            if (confirm(`Uninstall ${app.name}?`)) uninstallApp(app.uid);
        };
        appGrid.appendChild(div);
    });

    // Also render in apps list
    if (appsList) {
        appsList.innerHTML = '';
        apps.forEach(app => {
            const card = document.createElement('div');
            card.className = 'rom-card';
            card.innerHTML = `
                <div class="rom-icon">${iconMap[app.name] || '📱'}</div>
                <div class="rom-info">
                    <div class="rom-name">${app.name} <span style="opacity:0.5">${app.version}</span></div>
                    <div class="rom-meta">${app.uid} • ${app.type} • ${app.caps.join(', ') || 'no caps'} • runs: ${app.runs}</div>
                </div>
                <div style="display:flex;gap:4px">
                    <button class="btn btn-xs" onclick="launchApp('${app.uid.replace('0x','')}')">${app.state === 'running' ? 'Running' : 'Launch'}</button>
                    <button class="btn btn-xs" onclick="uninstallApp('${app.uid.replace('0x','')}')">🗑️</button>
                </div>
            `;
            appsList.appendChild(card);
        });
    }
}

function renderRoms() {
    if (!romsList) return;
    romsList.innerHTML = '';

    (state.roms || []).forEach(rom => {
        const div = document.createElement('div');
        div.className = 'rom-card';
        const typeClass = rom.type.includes('symbian') || rom.type.includes('rofs') || rom.type.includes('rom') ? 'symbian' : rom.type.includes('sis') ? 'sis' : rom.type.includes('exe') ? 'exe' : rom.type.includes('elf') ? 'elf' : '';
        const icon = rom.type === 'pe_exe' ? '🪟' : rom.type === 'elf' ? '🐧' : rom.type === 'iso' ? '💿' : rom.type.includes('sis') ? '📦' : rom.type === 'jar' ? '☕' : '💾';

        div.innerHTML = `
            <div class="rom-icon">${icon}</div>
            <div class="rom-info">
                <div class="rom-name">${rom.path.split('/').pop()} <span class="rom-type ${typeClass}">${rom.type}</span></div>
                <div class="rom-meta">${(rom.size/1024).toFixed(1)} KB • MD5: ${rom.md5.slice(0,8)} • Entry: ${rom.entry_point}</div>
            </div>
            <button class="btn btn-xs" onclick="loadRom('${rom.path}')">Load</button>
        `;
        romsList.appendChild(div);
    });

    // Disks
    if (disksList) {
        disksList.innerHTML = '';
        (state.disks || []).forEach(disk => {
            const div = document.createElement('div');
            div.className = 'rom-card';
            div.innerHTML = `
                <div class="rom-icon">💿</div>
                <div class="rom-info">
                    <div class="rom-name">${disk.label} <span class="rom-type">${disk.type}</span></div>
                    <div class="rom-meta">${disk.fs} • ${(disk.size/1024/1024).toFixed(1)} MB • Bootable: ${disk.bootable ? 'Yes' : 'No'} • ${disk.partitions} partitions</div>
                </div>
            `;
            disksList.appendChild(div);
        });
    }
}

function renderDrives() {
    if (!drivesList) return;
    drivesList.innerHTML = '';

    const drives = state.drives || {};
    Object.entries(drives).forEach(([letter, info]) => {
        if (info.error) return;
        const usedPct = info.total ? (info.used / info.total * 100) : 0;
        const div = document.createElement('div');
        div.className = 'drive-card';
        div.innerHTML = `
            <div class="drive-letter">${letter}: <span class="drive-type">${info.type}</span></div>
            <div class="drive-bar"><div class="drive-fill" style="width:${usedPct}%"></div></div>
            <div class="drive-stats">${(info.used/1024/1024).toFixed(1)} / ${(info.total/1024/1024).toFixed(1)} MB • Free ${(info.free/1024/1024).toFixed(1)} MB</div>
        `;
        div.onclick = () => {
            showPanel('files');
            loadPath(`${letter}:\\`);
        };
        drivesList.appendChild(div);
    });
}

function renderCPU() {
    const cpu = state.cpu || {};
    const kernel = state.kernel || {};

    if (document.getElementById('cpu-pc')) document.getElementById('cpu-pc').textContent = cpu.pc || '0x40000000';
    if (document.getElementById('cpu-cycles')) document.getElementById('cpu-cycles').textContent = `${cpu.cycles || 0} cycles`;
    if (document.getElementById('ram-usage')) document.getElementById('ram-usage').textContent = state.device ? `${state.device.hardware.ram} MB` : '64 MB';
    if (document.getElementById('proc-count')) document.getElementById('proc-count').textContent = kernel.processes || 1;
    if (document.getElementById('thread-count')) document.getElementById('thread-count').textContent = `${kernel.threads || 1} threads`;
    if (document.getElementById('uptime')) {
        const sec = Math.floor(kernel.uptime || 0);
        const m = Math.floor(sec/60).toString().padStart(2,'0');
        const s = (sec%60).toString().padStart(2,'0');
        document.getElementById('uptime').textContent = `${m}:${s}`;
    }
    if (document.getElementById('unicorn-status')) {
        document.getElementById('unicorn-status').textContent = cpu.unicorn ? 'yes' : 'no (pure python)';
    }
}

function renderLogs() {
    if (!logsEl) return;
    logsEl.innerHTML = (state.logs || []).slice(-50).map(l => `<div class="log-entry">${l}</div>`).join('');
    logsEl.scrollTop = logsEl.scrollHeight;
}

function renderDevicesSelect() {
    // Already rendered server side
}

function addLog(msg) {
    if (!state.logs) state.logs = [];
    state.logs.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
    renderLogs();
}

// Actions
async function switchDevice(deviceId) {
    addLog(`Switching to ${deviceId}...`);
    const res = await fetch(`/api/device/${deviceId}`, {method: 'POST'});
    const data = await res.json();
    if (data.success) {
        addLog(`Switched to ${data.device.name}`);
        // Update screen size
        const canvas = document.getElementById('phone-screen');
        if (canvas && data.device.screen) {
            canvas.width = data.device.screen.width;
            canvas.height = data.device.screen.height;
        }
        await refreshState();
    }
}

async function launchApp(uid) {
    // uid may be hex string
    let numericUid = uid;
    if (typeof uid === 'string' && uid.startsWith('0x')) {
        numericUid = parseInt(uid, 16);
    } else if (typeof uid === 'string') {
        // Try parse hex without 0x
        const parsed = parseInt(uid, 16);
        if (!isNaN(parsed) && parsed > 0x10000000) numericUid = parsed;
    }

    addLog(`Launching app ${uid}...`);
    const res = await fetch(`/api/apps/${numericUid}/launch`, {method: 'POST'});
    const data = await res.json();
    if (data.success) addLog(`App launched`);
    await refreshState();
}

async function uninstallApp(uid) {
    let numericUid = uid;
    if (typeof uid === 'string') {
        numericUid = parseInt(uid, 16) || parseInt(uid);
    }
    const res = await fetch(`/api/apps/${numericUid}/uninstall`, {method: 'POST'});
    await refreshState();
}

async function powerToggle() {
    await fetch('/api/keypress', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({key:'power', action:'press'})
    });
    state.running = !state.running;
    updatePowerStatus();
    addLog(state.running ? '📱 Phone ON - Symbian OS booting...' : '📴 Phone OFF');
}

async function resetCPU() {
    await fetch('/api/cpu/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})});
    addLog('🔄 CPU Reset');
    await refreshState();
}

async function stepCPU() {
    await fetch('/api/cpu/step', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({steps:1})});
    await refreshState();
}

function filterDevices(q) {
    const cards = document.querySelectorAll('.device-card');
    cards.forEach(c => {
        const name = c.dataset.name;
        c.style.display = name.includes(q.toLowerCase()) ? 'flex' : 'none';
    });
}

function showPanel(name) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    const el = document.getElementById(`panel-${name}`);
    if (el) el.classList.add('active');
}

function clearLogs() {
    state.logs = [];
    renderLogs();
}

// File manager
let currentPath = 'C:\\';
async function loadPath(path) {
    currentPath = path;
    document.getElementById('current-path').textContent = path;
    const res = await fetch(`/api/fs/list?path=${encodeURIComponent(path)}`);
    const files = await res.json();
    const list = document.getElementById('files-list');
    if (!list) return;
    list.innerHTML = '';
    files.forEach(f => {
        const div = document.createElement('div');
        div.className = 'rom-card';
        div.innerHTML = `
            <div class="rom-icon">${f.is_dir ? '📁' : '📄'}</div>
            <div class="rom-info">
                <div class="rom-name">${f.name}</div>
                <div class="rom-meta">${f.is_dir ? 'Folder' : (f.size/1024).toFixed(1)+' KB'} • ${new Date(f.modified*1000).toLocaleString()}</div>
            </div>
        `;
        if (f.is_dir) div.onclick = () => loadPath(f.path);
        list.appendChild(div);
    });
}

function navigateUp() {
    const parts = currentPath.replace(/\\$/,'').split('\\');
    parts.pop();
    const newPath = parts.join('\\') + '\\';
    if (newPath.length >= 3) loadPath(newPath);
}

function loadRom(path) {
    addLog(`Loading ROM ${path} into memory...`);
    // Already loaded via import, but we can trigger reset
    resetCPU();
}
