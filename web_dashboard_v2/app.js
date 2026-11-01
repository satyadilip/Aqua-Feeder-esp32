/**
 * AquaFeeder Pro — Precision Aquaculture Telemetry Controller
 * Matches commercial automated feed dispenser intentions & hardware telemetry
 */

const API_BASE_URL = 'https://s1ilr3py74.execute-api.us-east-1.amazonaws.com/prod';

// Default Ponds
const defaultPonds = [
  { id: 'P-02', name: 'Pond P-02 (South)', acres: 2.2, stock: 'Vannamei Shrimp', location: 'South Jetty' },
  { id: 'P-01', name: 'Pond P-01 (North)', acres: 1.8, stock: 'Vannamei Shrimp', location: 'North Jetty' }
];

// Default Feeders
const defaultDevices = [
  {
    id: 'e072a1fffef64134',
    name: 'Feeder 03',
    pondId: 'P-02',
    status: 'ACTIVE',
    connected: true,
    dispensedKg: 0.00,
    targetKg: 15.0,
    currentEvent: 0,
    totalEvents: 150,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 4.8,
    batteryV: 12.8,
    solarV: 18.2,
    solarMa: 340,
    hopperPercent: 85,
    hopperKg: 42.5,
    motorAmps: 0.88,
    rssi: -84,
    snr: 9.2,
    isPaused: false
  },
  {
    id: 'e072a1fffef6249c',
    name: 'Feeder 01',
    pondId: 'P-01',
    status: 'STANDBY',
    connected: false,
    dispensedKg: 0.00,
    targetKg: 15.0,
    currentEvent: 0,
    totalEvents: 150,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 4.8,
    batteryV: 12.6,
    solarV: 0.0,
    solarMa: 0,
    hopperPercent: 90,
    hopperKg: 45.0,
    motorAmps: 0.0,
    rssi: -94,
    snr: 4.1,
    isPaused: false
  },
  {
    id: 'e072a1fffef5ba08',
    name: 'Feeder 02',
    pondId: 'P-01',
    status: 'STANDBY',
    connected: false,
    dispensedKg: 0.00,
    targetKg: 15.0,
    currentEvent: 0,
    totalEvents: 150,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 4.8,
    batteryV: 12.5,
    solarV: 0.0,
    solarMa: 0,
    hopperPercent: 80,
    hopperKg: 40.0,
    motorAmps: 0.0,
    rssi: -96,
    snr: 3.8,
    isPaused: false
  }
];

// App State
let appState = {
  selectedPondId: localStorage.getItem('aquacon_selected_pond') || 'P-02',
  selectedDeviceId: localStorage.getItem('aquacon_selected_device') || 'e072a1fffef64134',
  currentTheme: localStorage.getItem('aquacon_theme') || 'theme-light',
  devices: defaultDevices,
  currentTab: 'tab-telemetry',
  telemetryLogs: []
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  document.body.className = appState.currentTheme;

  const pondSelect = document.getElementById('pond-select');
  if (pondSelect) pondSelect.value = appState.selectedPondId;

  renderFeederPills();
  renderActiveFeeder();
  renderAnalyticsLogs();
  initDockPill();
  fetchLiveTelemetry();

  // Polling every 15s
  setInterval(fetchLiveTelemetry, 15000);
});

// ============================================================================
// Theme Switcher
// ============================================================================
function toggleTheme() {
  const isDark = document.body.classList.contains('theme-dark');
  const newTheme = isDark ? 'theme-light' : 'theme-dark';
  document.body.className = newTheme;
  appState.currentTheme = newTheme;
  localStorage.setItem('aquacon_theme', newTheme);
  showToast(isDark ? '☀️ Sunlight Contrast Mode' : '🌙 Dark Marina Mode');
}

// ============================================================================
// Dock Navigation
// ============================================================================
function initDockPill() {
  const activeBtn = document.querySelector('.dock-tab-btn.active, .dock-item-btn.active');
  if (activeBtn) updateDockPill(activeBtn);
}

function updateDockPill(targetBtn) {
  const pill = document.getElementById('dock-pill');
  if (!pill || !targetBtn) return;
  pill.style.left = `${targetBtn.offsetLeft}px`;
  pill.style.width = `${targetBtn.offsetWidth}px`;
}

function switchNavTab(tabId, btnElement) {
  appState.currentTab = tabId;

  document.querySelectorAll('.feeder-screen, .view-screen').forEach(s => s.classList.remove('active-screen'));
  const targetScreen = document.getElementById(tabId);
  if (targetScreen) targetScreen.classList.add('active-screen');

  document.querySelectorAll('.dock-tab-btn, .dock-item-btn').forEach(b => b.classList.remove('active'));
  if (btnElement) {
    btnElement.classList.add('active');
    updateDockPill(btnElement);
  }
}

// ============================================================================
// Pond & Feeder Switching
// ============================================================================
function handlePondChange(pondId) {
  appState.selectedPondId = pondId;
  localStorage.setItem('aquacon_selected_pond', pondId);

  const pondDevs = appState.devices.filter(d => d.pondId === pondId);
  if (pondDevs.length > 0) {
    selectFeeder(pondDevs[0].id);
  } else {
    renderFeederPills();
    renderActiveFeeder();
  }
}

function selectFeeder(deviceId) {
  appState.selectedDeviceId = deviceId;
  localStorage.setItem('aquacon_selected_device', deviceId);
  renderFeederPills();
  renderActiveFeeder();
}

function renderFeederPills() {
  const container = document.getElementById('feeder-pills-container');
  if (!container) return;

  const pondDevs = appState.devices.filter(d => d.pondId === appState.selectedPondId);

  container.innerHTML = pondDevs.map(dev => {
    const isActive = dev.id === appState.selectedDeviceId;
    return `
      <div class="feeder-unit-pill ${isActive ? 'active' : ''}" onclick="selectFeeder('${dev.id}')">
        <span class="unit-pip"></span>
        <span>${dev.name}</span>
      </div>
    `;
  }).join('');
}

// ============================================================================
// Render Feeder Telemetry & Broadcast Engine
// ============================================================================
function getActiveDevice() {
  return appState.devices.find(d => d.id === appState.selectedDeviceId) || appState.devices[0];
}

function renderActiveFeeder() {
  const dev = getActiveDevice();
  if (!dev) return;

  const currentPond = defaultPonds.find(p => p.id === dev.pondId) || defaultPonds[0];

  // Names & Locations
  const heroNameEl = document.getElementById('hero-feeder-name');
  if (heroNameEl) heroNameEl.textContent = dev.name;

  const pondNameEl = document.getElementById('hero-pond-name');
  if (pondNameEl) pondNameEl.textContent = `${currentPond.name} • ${currentPond.location}`;

  const protoNameEl = document.getElementById('proto-feeder-name');
  if (protoNameEl) protoNameEl.textContent = dev.name;

  // Status Badge
  const statusPill = document.getElementById('hero-status-pill');
  const statusText = document.getElementById('hero-status-text');
  if (statusPill && statusText) {
    if (dev.isPaused) {
      statusPill.className = 'status-chip-live status-paused';
      statusPill.style.background = 'rgba(2, 132, 199, 0.12)';
      statusPill.style.borderColor = 'rgba(2, 132, 199, 0.35)';
      statusPill.style.color = '#0284C7';
      statusText.textContent = 'CYCLE PAUSED';
    } else if (dev.status === 'ACTIVE' || dev.connected) {
      statusPill.className = 'status-chip-live online';
      statusPill.style.background = 'rgba(16, 185, 129, 0.12)';
      statusPill.style.borderColor = 'rgba(16, 185, 129, 0.35)';
      statusPill.style.color = '#10B981';
      statusText.textContent = 'SCHEDULE ACTIVE';
    } else {
      statusPill.className = 'status-chip-live standby';
      statusPill.style.background = 'rgba(100, 116, 139, 0.12)';
      statusPill.style.borderColor = 'rgba(100, 116, 139, 0.3)';
      statusPill.style.color = '#64748B';
      statusText.textContent = 'STANDBY';
    }
  }

  // Dispense Metrics
  const dispensedEl = document.getElementById('hero-dispensed-kg');
  if (dispensedEl) dispensedEl.textContent = Number(dev.dispensedKg || 0).toFixed(2);

  const targetEl = document.getElementById('hero-target-kg');
  if (targetEl) targetEl.textContent = Number(dev.targetKg || 15).toFixed(1);

  // Feed Progress Bar
  const percent = Math.min(100, Math.max(0, (dev.dispensedKg / dev.targetKg) * 100));
  const progressBar = document.getElementById('feed-progress-bar');
  if (progressBar) progressBar.style.width = `${percent}%`;

  const percentLabel = document.getElementById('hero-progress-percent');
  if (percentLabel) percentLabel.textContent = `${percent.toFixed(0)}% Completed`;

  const remKg = Math.max(0, dev.targetKg - dev.dispensedKg);
  const remainingLabel = document.getElementById('hero-remaining-kg');
  if (remainingLabel) remainingLabel.textContent = `${remKg.toFixed(2)} kg Remaining`;

  // Schedule Strip
  const fpeEl = document.getElementById('hero-fpe');
  if (fpeEl) fpeEl.textContent = `${dev.fpeGrams || 100} g`;

  const eventsEl = document.getElementById('hero-events-progress');
  if (eventsEl) eventsEl.textContent = `${dev.currentEvent || 0} / ${dev.totalEvents || 150}`;

  // Pause Button
  const pauseLabel = document.getElementById('btn-pause-label');
  if (pauseLabel) {
    pauseLabel.textContent = dev.isPaused ? 'Resume' : 'Pause';
  }

  // Bento Modules
  renderBentoModules(dev);
  syncProtocolForm(dev);
}

function renderBentoModules(dev) {
  // 1. Hopper Silo
  const hopPercent = document.getElementById('tile-hopper-percent');
  if (hopPercent) hopPercent.textContent = `${dev.hopperPercent || 85}%`;

  const hopKg = document.getElementById('tile-hopper-kg');
  if (hopKg) hopKg.textContent = `~${dev.hopperKg || 42.5} kg dry feed remaining`;

  const hopBar = document.getElementById('hopper-fill-bar');
  if (hopBar) hopBar.style.width = `${dev.hopperPercent || 85}%`;

  // 2. Battery & Solar
  const battVolt = document.getElementById('tile-battery-volt');
  if (battVolt) battVolt.textContent = Number(dev.batteryV || 12.8).toFixed(1);

  const solarSub = document.getElementById('tile-solar-sub');
  if (solarSub) solarSub.textContent = `PV Array: ${dev.solarV || 18.2}V • Floating`;

  // 3. Auger Motor
  const motorAmp = document.getElementById('tile-motor-amp');
  if (motorAmp) motorAmp.textContent = Number(dev.motorAmps || 0.88).toFixed(2);

  // 4. LoRaWAN
  const rssiEl = document.getElementById('tile-rssi');
  if (rssiEl) rssiEl.textContent = dev.rssi || -84;

  const snrEl = document.getElementById('tile-snr-sub');
  if (snrEl) snrEl.textContent = `SNR: +${dev.snr || 9.2} dB • 0 Drops`;
}

// ============================================================================
// Feeder Dispense Micro-Interaction (Feeder Machine Auger, Spreader & Spray)
// ============================================================================
function triggerBroadcastThrow() {
  // 1. Activate Authentic Feeder Machine Dispensing Animation
  const feederSvg = document.getElementById('feeder-machine-svg');
  const stage = document.getElementById('feeder-stage');
  if (feederSvg) {
    feederSvg.classList.add('dispensing-active');
    if (stage) stage.classList.add('dispensing-active');
    setTimeout(() => {
      feederSvg.classList.remove('dispensing-active');
      if (stage) stage.classList.remove('dispensing-active');
    }, 1800);
  }

  // 2. Legacy fallback for impeller/fan elements if present
  const impeller = document.getElementById('impeller-dish');
  if (impeller) {
    impeller.classList.add('impeller-spinning');
    setTimeout(() => impeller.classList.remove('impeller-spinning'), 1800);
  }
  const fan = document.getElementById('broadcast-fan');
  if (fan) {
    fan.classList.add('active-throw');
    setTimeout(() => fan.classList.remove('active-throw'), 1800);
  }

  // 3. Auger Motor Badge in Bento Card
  const augerBadge = document.getElementById('auger-status-badge');
  if (augerBadge) {
    augerBadge.textContent = 'DISPENSING';
    augerBadge.className = 'state-chip chip-emerald';
    setTimeout(() => {
      augerBadge.textContent = 'Normal';
      augerBadge.className = 'state-chip chip-blue';
    }, 1800);
  }
}

// Counter Interpolation
function animateCounter(el, start, end, duration) {
  if (!el) return;
  const startTime = performance.now();
  function tick(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const current = start + (end - start) * progress;
    el.textContent = current.toFixed(2);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ============================================================================
// Direct Hardware Action Handlers
// ============================================================================
function handleQuickFeed() {
  const dev = getActiveDevice();
  if (!dev) return;

  // Dispatched via AWS IoT Core API
  sendDownlinkCommand(dev.id, 'FEED_PULSE', { grams: 100 });

  // Feeder Visuals
  triggerBroadcastThrow();

  const prev = dev.dispensedKg;
  dev.dispensedKg += (dev.fpeGrams / 1000);
  dev.currentEvent += 1;

  const el = document.getElementById('hero-dispensed-kg');
  animateCounter(el, prev, dev.dispensedKg, 600);

  renderActiveFeeder();
  showToast(`⚡ 100g feed discharged via auger into ${dev.name}`);
}

function handleTogglePause() {
  const dev = getActiveDevice();
  if (!dev) return;

  dev.isPaused = !dev.isPaused;
  const cmd = dev.isPaused ? 'PAUSE' : 'RESUME';
  sendDownlinkCommand(dev.id, cmd);

  renderActiveFeeder();
  showToast(dev.isPaused ? `⏸ ${dev.name} cycle paused` : `▶ ${dev.name} cycle resumed`);
}

// ============================================================================
// Protocol Form Controls
// ============================================================================
function syncProtocolForm(dev) {
  const targetVal = document.getElementById('proto-target-val');
  if (targetVal) targetVal.textContent = Number(dev.targetKg).toFixed(1);

  const fpeVal = document.getElementById('proto-fpe-val');
  if (fpeVal) fpeVal.textContent = dev.fpeGrams;

  const startTime = document.getElementById('proto-start-time');
  if (startTime) {
    startTime.value = `${String(dev.startHour).padStart(2, '0')}:${String(dev.startMin).padStart(2, '0')}`;
  }

  const endTime = document.getElementById('proto-end-time');
  if (endTime) {
    endTime.value = `${String(dev.endHour).padStart(2, '0')}:${String(dev.endMin).padStart(2, '0')}`;
  }

  recalculateSchedule();
}

function adjustTarget(delta) {
  const dev = getActiveDevice();
  if (!dev) return;

  dev.targetKg = Math.max(1.0, Math.min(50.0, dev.targetKg + delta));
  const el = document.getElementById('proto-target-val');
  if (el) el.textContent = dev.targetKg.toFixed(1);

  recalculateSchedule();
}

function adjustFpe(delta) {
  const dev = getActiveDevice();
  if (!dev) return;

  dev.fpeGrams = Math.max(25, Math.min(500, dev.fpeGrams + delta));
  const el = document.getElementById('proto-fpe-val');
  if (el) el.textContent = dev.fpeGrams;

  recalculateSchedule();
}

function recalculateSchedule() {
  const dev = getActiveDevice();
  if (!dev) return;

  const targetGrams = dev.targetKg * 1000;
  const totalEvents = Math.max(1, Math.round(targetGrams / dev.fpeGrams));
  dev.totalEvents = totalEvents;

  const startEl = document.getElementById('proto-start-time');
  const endEl = document.getElementById('proto-end-time');

  let windowMinutes = 720;
  if (startEl && endEl && startEl.value && endEl.value) {
    const [sh, sm] = startEl.value.split(':').map(Number);
    const [eh, em] = endEl.value.split(':').map(Number);
    const startM = sh * 60 + sm;
    const endM = eh * 60 + em;
    if (endM > startM) windowMinutes = endM - startM;
  }

  const intervalMin = (windowMinutes / totalEvents).toFixed(1);
  dev.intervalMin = intervalMin;

  const pulsesEl = document.getElementById('proto-calc-pulses');
  if (pulsesEl) pulsesEl.textContent = `${totalEvents} Pulses`;

  const intervalEl = document.getElementById('proto-calc-interval');
  if (intervalEl) intervalEl.textContent = `Every ${intervalMin} minutes`;
}

function saveProtocolToDevice() {
  const dev = getActiveDevice();
  if (!dev) return;

  sendDownlinkCommand(dev.id, 'SET_CONFIG', {
    targetKg: dev.targetKg,
    fpeGrams: dev.fpeGrams,
    intervalMin: dev.intervalMin
  });

  renderActiveFeeder();
  showToast(`📡 Protocol transmitted to ${dev.name} via LoRaWAN`);
}

// AWS API Gateway Command Dispatch
async function sendDownlinkCommand(deviceId, commandType, payload = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}/commands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        deviceId: deviceId,
        command: commandType,
        params: payload,
        timestamp: new Date().toISOString()
      })
    });
    if (!res.ok) console.warn('Command response status:', res.status);
  } catch (err) {
    console.warn('Command dispatch error:', err);
  }
}

// ============================================================================
// Telemetry Uplink Polling
// ============================================================================
async function fetchLiveTelemetry() {
  try {
    const res = await fetch(`${API_BASE_URL}/telemetry?limit=10`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        processLatestUplinks(data);
      }
    }
  } catch (err) {
    console.log('Background polling fallback');
  }
}

function processLatestUplinks(items) {
  items.forEach(item => {
    const devId = (item.deviceId || item.device_id || '').toLowerCase();
    const match = appState.devices.find(d => d.id.toLowerCase() === devId);
    if (match) {
      if (item.dispensedKg !== undefined) match.dispensedKg = Number(item.dispensedKg);
      if (item.batteryV !== undefined) match.batteryV = Number(item.batteryV);
      if (item.solarMa !== undefined) match.solarMa = Number(item.solarMa);
      if (item.rssi !== undefined) match.rssi = Number(item.rssi);
      if (item.currentEvent !== undefined) match.currentEvent = Number(item.currentEvent);
    }
  });

  appState.telemetryLogs = items;
  renderActiveFeeder();
  renderAnalyticsLogs();
}

function renderAnalyticsLogs() {
  const logContainer = document.getElementById('telemetry-log-list');
  if (!logContainer) return;

  const logs = appState.telemetryLogs.length > 0 ? appState.telemetryLogs.slice(0, 5) : [
    { time: '14:22:04 IST', event: 'Uplink #142', batt: '12.8V', fpe: '100g', rssi: '-84 dBm' },
    { time: '14:17:15 IST', event: 'Uplink #141', batt: '12.8V', fpe: '100g', rssi: '-85 dBm' },
    { time: '14:12:30 IST', event: 'Uplink #140', batt: '12.8V', fpe: '100g', rssi: '-84 dBm' },
    { time: '14:07:45 IST', event: 'Uplink #139', batt: '12.8V', fpe: '100g', rssi: '-83 dBm' }
  ];

  logContainer.innerHTML = logs.map(l => `
    <div class="uplink-item-row">
      <div>
        <strong style="color: var(--text-primary); font-family: var(--font-mono);">${l.time || '14:00 IST'}</strong>
        <span style="color: var(--text-muted); margin-left: 6px;">${l.event || 'Telemetry Packet'}</span>
      </div>
      <div style="font-family: var(--font-mono); color: var(--pond-teal); font-weight: 700;">
        ${l.batt || '12.8V'} &bull; ${l.rssi || '-84 dBm'}
      </div>
    </div>
  `).join('');
}

// ============================================================================
// Haptic Notifications
// ============================================================================
function showToast(msg) {
  const toast = document.getElementById('toast-container');
  const toastMsg = document.getElementById('toast-message');
  if (!toast || !toastMsg) return;

  toastMsg.textContent = msg;
  toast.classList.remove('hidden');

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 2600);
}
