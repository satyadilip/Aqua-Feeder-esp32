/**
 * aquaCON Cloud™ — Customer Application Engine
 * Developed for Commercial Aquaculture Farmers & Supervisors
 * Direct Hardware Integration with AWS DynamoDB & IoT Core
 */

const API_BASE_URL = 'https://s1ilr3py74.execute-api.us-east-1.amazonaws.com/prod';

// Default Ponds Registry
const defaultPonds = [
  { id: 'P-01', name: 'Pond P-01', acres: 1.8, stock: 'Vannamei Shrimp', lat: 16.5062, lng: 81.6708 },
  { id: 'P-02', name: 'Pond P-02', acres: 2.2, stock: 'Black Tiger Shrimp', lat: 16.5045, lng: 81.6710 },
  { id: 'P-03', name: 'Pond P-03', acres: 1.5, stock: 'Vannamei Shrimp', lat: 16.5030, lng: 81.6695 }
];

// Default Feeders Registry
const defaultDevices = [
  {
    id: 'e072a1fffef6249c',
    name: 'aquaCON Feeder 01 (Live AF_9C2472E0)',
    pondId: 'P-01',
    status: 'FEEDING',
    feedAvailable: true,
    dispensedKg: 14.70,
    targetKg: 25.0,
    currentEvent: 147,
    totalEvents: 250,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 2.9,
    motorTimeSec: 1.0,
    scheduleValid: true
  },
  {
    id: 'aquaCON-Feeder-02',
    name: 'aquaCON Feeder 02 (North)',
    pondId: 'P-01',
    status: 'IDLE',
    feedAvailable: true,
    dispensedKg: 0.0,
    targetKg: 18.0,
    currentEvent: 0,
    totalEvents: 180,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 3.9,
    motorTimeSec: 1.0,
    scheduleValid: true
  },
  {
    id: 'aquaCON-Feeder-03',
    name: 'aquaCON Feeder 03',
    pondId: 'P-02',
    status: 'IDLE',
    feedAvailable: true,
    dispensedKg: 1.20,
    targetKg: 20.0,
    currentEvent: 12,
    totalEvents: 200,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 3.5,
    motorTimeSec: 1.0,
    scheduleValid: true
  }
];

// Default Alert Contacts (Charan 9154696777 as Primary Alert Lead)
const defaultContacts = [
  {
    name: 'Charan',
    phone: '+91 91546 96777',
    rawPhone: '9154696777',
    role: 'Farm Alert Lead (Primary)',
    isDefault: true
  }
];

// Central Customer Application State
const appState = {
  isAuthenticated: false,
  currentUser: null,
  activeTab: 'tab-status',
  
  // Data Store
  ponds: [],
  devices: [],
  
  // Selected Context
  selectedPondId: 'P-01',
  selectedDeviceId: 'e072a1fffef6249c',
  
  // Historical Metrics Cache
  deviceMetrics: {},
  
  // Alert Contacts
  contacts: [...defaultContacts]
};

// Global reference for diagnostics & testing
window.appState = appState;

let leafletMap = null;
let pondPolygons = [];
let feederMapMarkers = [];

// DOM Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  loadDataFromStorage();
  initAuthSession();
  initAuthUI();
  initFarmClock();
  initScheduleEngine();
  startTelemetryLoop();
});

/* ==========================================================================
   1. DATA REPOSITORY & LOCAL STORAGE SYNC
   ========================================================================== */
function loadDataFromStorage() {
  const savedPonds = localStorage.getItem('aquacon_ponds');
  appState.ponds = savedPonds ? JSON.parse(savedPonds) : [...defaultPonds];

  const savedDevices = localStorage.getItem('aquacon_devices');
  appState.devices = savedDevices ? JSON.parse(savedDevices) : [...defaultDevices];

  const savedContacts = localStorage.getItem('aquacon_contacts');
  appState.contacts = savedContacts ? JSON.parse(savedContacts) : [...defaultContacts];
  if (!appState.contacts || appState.contacts.length === 0) {
    appState.contacts = [...defaultContacts];
  }
}

function saveDataToStorage() {
  localStorage.setItem('aquacon_ponds', JSON.stringify(appState.ponds));
  localStorage.setItem('aquacon_devices', JSON.stringify(appState.devices));
  localStorage.setItem('aquacon_contacts', JSON.stringify(appState.contacts));
}

/* ==========================================================================
   2. AUTHENTICATION CONTROLLER
   ========================================================================== */
function initAuthSession() {
  const storedUser = localStorage.getItem('aquacon_session_user');
  if (storedUser) {
    try {
      appState.currentUser = JSON.parse(storedUser);
      appState.isAuthenticated = true;
      revealMainApp();
      return;
    } catch (e) {
      localStorage.removeItem('aquacon_session_user');
    }
  }
  revealAuthGate();
}

function revealAuthGate() {
  appState.isAuthenticated = false;
  appState.currentUser = null;
  const authScreen = document.getElementById('screen-auth');
  const mainShell = document.getElementById('main-app-shell');
  if (authScreen) authScreen.style.display = 'flex';
  if (mainShell) mainShell.style.display = 'none';
}

function revealMainApp() {
  const authScreen = document.getElementById('screen-auth');
  const mainShell = document.getElementById('main-app-shell');
  if (authScreen) authScreen.style.display = 'none';
  if (mainShell) mainShell.style.display = 'flex';

  if (appState.currentUser) {
    const profName = document.getElementById('sys-operator-name');
    const profPhone = document.getElementById('sys-operator-phone');
    const profFarm = document.getElementById('sys-farm-name');
    if (profName) profName.textContent = appState.currentUser.name || 'aquaCON Supervisor';
    if (profPhone) profPhone.textContent = `+91 ${appState.currentUser.phone || '90004 20999'}`;
    if (profFarm) profFarm.textContent = appState.currentUser.farmName || 'Pioneer Aqua Farm';
  }

  // Populate Ponds & Devices UI
  refreshPondsDropdown();
  updatePondContextBar();
  renderPondsDirectory();
  renderAlertContacts();
  renderHistoryView();

  // Initialize Map
  setTimeout(() => {
    initSatelliteMap();
  }, 250);
}

function initAuthUI() {
  const tabLoginBtn = document.getElementById('tab-login-btn');
  const tabRegBtn = document.getElementById('tab-register-btn');
  const panelSignin = document.getElementById('panel-signin');
  const panelRegister = document.getElementById('panel-register');
  const alertBox = document.getElementById('auth-alert-box');

  if (tabLoginBtn && tabRegBtn) {
    tabLoginBtn.addEventListener('click', () => {
      tabLoginBtn.classList.add('active');
      tabRegBtn.classList.remove('active');
      panelSignin.classList.add('active');
      panelRegister.classList.remove('active');
      if (alertBox) alertBox.style.display = 'none';
    });

    tabRegBtn.addEventListener('click', () => {
      tabRegBtn.classList.add('active');
      tabLoginBtn.classList.remove('active');
      panelRegister.classList.add('active');
      panelSignin.classList.remove('active');
      if (alertBox) alertBox.style.display = 'none';
    });
  }

  // Password Visibility Toggle
  const pwToggleBtn = document.getElementById('pw-toggle-btn');
  const pwInput = document.getElementById('auth-pw-input');
  if (pwToggleBtn && pwInput) {
    pwToggleBtn.addEventListener('click', () => {
      const isPw = pwInput.type === 'password';
      pwInput.type = isPw ? 'text' : 'password';
      pwToggleBtn.textContent = isPw ? '🔒' : '👁️';
    });
  }

  // Sign In Action
  const btnLogin = document.getElementById('btn-login-submit');
  if (btnLogin) {
    btnLogin.addEventListener('click', async () => {
      const phoneInput = document.getElementById('auth-phone-input');
      const pwInput = document.getElementById('auth-pw-input');
      const btnText = document.getElementById('login-btn-text');

      const phone = phoneInput ? phoneInput.value.trim() : '9000420999';
      const password = pwInput ? pwInput.value.trim() : 'admin';

      if (!phone || !password) {
        showAuthAlert('Please enter mobile number and password', 'error');
        return;
      }

      if (btnText) btnText.textContent = 'Connecting...';

      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, password })
        });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
          appState.currentUser = data.user;
          appState.isAuthenticated = true;
          localStorage.setItem('aquacon_session_user', JSON.stringify(data.user));
          showAuthAlert('✅ Welcome back! Loading your ponds...', 'success');
          setTimeout(() => revealMainApp(), 400);
        } else {
          showAuthAlert(data.error || 'Invalid phone or password. Default: 9000420999 / admin', 'error');
        }
      } catch (err) {
        if (phone === '9000420999' && password === 'admin') {
          const user = { phone, name: 'aquaCON Supervisor', farmName: 'Pioneer Aqua Farm', role: 'Admin' };
          appState.currentUser = user;
          appState.isAuthenticated = true;
          localStorage.setItem('aquacon_session_user', JSON.stringify(user));
          showAuthAlert('✅ Welcome back! Loading your ponds...', 'success');
          setTimeout(() => revealMainApp(), 400);
        } else {
          showAuthAlert('Network error. Check credentials or use Default: 9000420999 / admin', 'error');
        }
      } finally {
        if (btnText) btnText.textContent = 'Sign In to Farm →';
      }
    });
  }

  // Instant Demo Bypass Button
  const btnDemo = document.getElementById('btn-demo-bypass');
  if (btnDemo) {
    btnDemo.addEventListener('click', () => {
      const demoUser = { phone: '9000420999', name: 'Pioneer Supervisor', farmName: 'Pioneer Aqua Farm', role: 'Supervisor' };
      appState.currentUser = demoUser;
      appState.isAuthenticated = true;
      localStorage.setItem('aquacon_session_user', JSON.stringify(demoUser));
      showToast('🧪 Entering aquaCON Farm Dashboard');
      revealMainApp();
    });
  }

  // Register Farm Action
  const btnRegister = document.getElementById('btn-register-submit');
  if (btnRegister) {
    btnRegister.addEventListener('click', async () => {
      const name = document.getElementById('reg-name-input')?.value.trim();
      const phone = document.getElementById('reg-phone-input')?.value.trim();
      const farmName = document.getElementById('reg-farm-input')?.value.trim();
      const password = document.getElementById('reg-pw-input')?.value.trim();
      const btnText = document.getElementById('reg-btn-text');

      if (!name || !phone || !password) {
        showAuthAlert('Please fill in Farmer Name, Mobile Number, and Password', 'error');
        return;
      }

      if (btnText) btnText.textContent = 'Creating Farm Account...';

      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, phone, farmName, password })
        });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
          showAuthAlert('✅ Farm registered! Please sign in with your phone.', 'success');
          tabLoginBtn?.click();
          const phoneInput = document.getElementById('auth-phone-input');
          if (phoneInput) phoneInput.value = phone;
        } else {
          showAuthAlert(data.error || 'Registration failed', 'error');
        }
      } catch (e) {
        showAuthAlert('Registration connection error', 'error');
      } finally {
        if (btnText) btnText.textContent = 'Register Farm 📋';
      }
    });
  }
}

function showAuthAlert(msg, type) {
  const box = document.getElementById('auth-alert-box');
  if (!box) return;
  box.textContent = msg;
  box.className = `auth-alert ${type}`;
  box.style.display = 'block';
}

function handleLogout() {
  if (confirm('Sign out from aquaCON?')) {
    localStorage.removeItem('aquacon_session_user');
    showToast('Signed out');
    revealAuthGate();
  }
}

/* ==========================================================================
   3. POND & DEVICE MANAGEMENT
   ========================================================================== */
function refreshPondsDropdown() {
  const select = document.getElementById('header-pond-select');
  if (!select) return;

  select.innerHTML = appState.ponds.map(p => `
    <option value="${p.id}" ${p.id === appState.selectedPondId ? 'selected' : ''}>
      ${p.name} (${p.acres} Acres)
    </option>
  `).join('');
}

function switchActivePond(pondId) {
  appState.selectedPondId = pondId;
  const pond = appState.ponds.find(p => p.id === pondId);
  if (!pond) return;

  // Find devices belonging to this pond
  const pondDevices = appState.devices.filter(d => d.pondId === pondId);
  if (pondDevices.length > 0) {
    appState.selectedDeviceId = pondDevices[0].id;
  }

  updatePondContextBar();
  loadSelectedDeviceToUI();
  renderHistoryView();
  showToast(`Switched to ${pond.name}`);

  // Center Map if on Map Tab
  if (leafletMap && pond.lat && pond.lng) {
    leafletMap.setView([pond.lat, pond.lng], 16);
  }
}

function updatePondContextBar() {
  const pond = appState.ponds.find(p => p.id === appState.selectedPondId);
  if (!pond) return;

  const titleEl = document.getElementById('context-pond-name');
  const subEl = document.getElementById('context-pond-stock');
  const pillsContainer = document.getElementById('pond-devices-pills');

  const pondDevices = appState.devices.filter(d => d.pondId === pond.id);

  if (titleEl) titleEl.textContent = `${pond.name} (${pond.acres} Acres)`;
  if (subEl) subEl.textContent = `${pond.stock || 'Vannamei Shrimp'} • ${pondDevices.length} Feeder${pondDevices.length === 1 ? '' : 's'}`;

  if (pillsContainer) {
    let html = '';
    pondDevices.forEach(d => {
      const isActive = d.id === appState.selectedDeviceId;
      html += `
        <button type="button" class="device-pill ${isActive ? 'active' : ''}" onclick="switchActiveDevice('${d.id}')">
          <span>🐟</span>
          <span>${d.name}</span>
        </button>
      `;
    });

    html += `
      <button type="button" class="device-pill-add" onclick="openAddDeviceModal()">
        + Add Feeder
      </button>
    `;

    pillsContainer.innerHTML = html;
  }
}

function switchActiveDevice(deviceId) {
  appState.selectedDeviceId = deviceId;
  updatePondContextBar();
  loadSelectedDeviceToUI();
  renderHistoryView();
  const dev = appState.devices.find(d => d.id === deviceId);
  if (dev) showToast(`Selected: ${dev.name}`);
}

function calculateNextFeedTimestamp(dev) {
  if (!dev) return { timeStr: '--:-- --', subStr: 'No Device' };

  const startH = dev.startHour !== undefined ? dev.startHour : 6;
  const startM = dev.startMin !== undefined ? dev.startMin : 0;
  const endH = dev.endHour !== undefined ? dev.endHour : 18;
  const endM = dev.endMin !== undefined ? dev.endMin : 0;
  const curEv = dev.currentEvent || 0;
  const totEv = dev.totalEvents || 250;
  const interval = dev.intervalMin || 2.9;

  function formatClock(hours, mins, ampm) {
    const dh = hours % 12 === 0 ? 12 : hours % 12;
    const dm = mins < 10 ? '0' + mins : mins;
    return `${dh < 10 ? '0' + dh : dh}:${dm} ${ampm}`;
  }

  // 1. If completed today's target events
  if (totEv > 0 && curEv >= totEv) {
    const nextStartStr = formatClock(startH, startM, startH >= 12 ? 'PM' : 'AM');
    return {
      timeStr: nextStartStr,
      subStr: `Tomorrow (Cycle Complete • ${curEv}/${totEv} Done)`
    };
  }

  // 2. If device is manually paused or stopped
  if (dev.status === 'STOPPED') {
    return {
      timeStr: 'PAUSED',
      subStr: `Cycle Paused at Event ${curEv}/${totEv}`
    };
  }

  const now = new Date();
  const nowMinsTotal = now.getHours() * 60 + now.getMinutes() + (now.getSeconds() / 60.0);
  const startMinsTotal = startH * 60 + startM;
  const endMinsTotal = endH * 60 + endM;

  // 3. If currently before the daily start window
  if (nowMinsTotal < startMinsTotal) {
    const startStr = formatClock(startH, startM, startH >= 12 ? 'PM' : 'AM');
    return {
      timeStr: startStr,
      subStr: `Today at ${startStr} (Interval: ${interval.toFixed(1)} mins)`
    };
  }

  // 4. If currently after the daily end window
  if (nowMinsTotal >= endMinsTotal) {
    const nextStartStr = formatClock(startH, startM, startH >= 12 ? 'PM' : 'AM');
    return {
      timeStr: nextStartStr,
      subStr: `Tomorrow at ${nextStartStr} (Cycle Complete)`
    };
  }

  // 5. Active Feeding Window: Determine next upcoming deterministic clock timestamp
  const stepsSoFar = Math.floor((nowMinsTotal - startMinsTotal) / interval);
  let nextMinsTotal = startMinsTotal + ((stepsSoFar + 1) * interval);

  if (nextMinsTotal >= endMinsTotal) {
    const nextStartStr = formatClock(startH, startM, startH >= 12 ? 'PM' : 'AM');
    return {
      timeStr: nextStartStr,
      subStr: `Tomorrow at ${nextStartStr} (Window Finished)`
    };
  }

  const nextH = Math.floor(nextMinsTotal / 60) % 24;
  const nextMin = Math.floor(nextMinsTotal % 60);
  const ampm = nextH >= 12 ? 'PM' : 'AM';
  const timeStr = formatClock(nextH, nextMin, ampm);
  const nextEvNum = Math.min(totEv, curEv + 1);

  return {
    timeStr: timeStr,
    subStr: `Interval: ${interval.toFixed(1)} mins (Event #${nextEvNum} of ${totEv})`,
    nextMinsTotal: nextMinsTotal
  };
}

function loadSelectedDeviceToUI() {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (!dev) return;

  // Tab 1 Hero Card
  const devTag = document.getElementById('current-device-tag');
  const devName = document.getElementById('current-device-name');
  const stateBadge = document.getElementById('feeder-state-badge');
  const dispensedText = document.getElementById('dispensed-val-text');
  const targetText = document.getElementById('target-val-text');
  const burstCountText = document.getElementById('burst-count-text');
  const nextIntervalText = document.getElementById('next-feed-interval');
  const nextFeedTimeText = document.getElementById('next-feed-time');
  const feedDot = document.getElementById('feed-status-dot');
  const feedStatusText = document.getElementById('feed-status-text');
  const fillBar = document.getElementById('feed-progress-fill');

  if (devTag) devTag.textContent = dev.id;
  if (devName) devName.textContent = dev.name;

  if (stateBadge) {
    stateBadge.textContent = dev.status || 'IDLE';
    stateBadge.className = `badge-state ${dev.status === 'RUNNING' || dev.status === 'FEEDING' ? 'b-run' : 'b-idle'}`;
  }

  // Live computed dispensed amount from event count
  const curEv = dev.currentEvent || 0;
  const totEv = dev.totalEvents || 250;
  const fpe = dev.fpeGrams || 100;
  const liveDispensed = dev.dispensedKg !== undefined 
    ? parseFloat(dev.dispensedKg) 
    : parseFloat(((curEv * fpe) / 1000.0).toFixed(2));
  dev.dispensedKg = liveDispensed;

  const targetKg = dev.targetKg || 25.0;

  if (dispensedText) dispensedText.textContent = liveDispensed.toFixed(2);
  if (targetText) targetText.textContent = targetKg.toFixed(1);
  if (burstCountText) burstCountText.textContent = `${curEv} / ${totEv}`;

  // Deterministic Next Feed Event Timestamp (Clock format hh:mm A)
  const nextInfo = calculateNextFeedTimestamp(dev);
  if (nextIntervalText) nextIntervalText.textContent = nextInfo.timeStr;
  if (nextFeedTimeText) nextFeedTimeText.textContent = nextInfo.subStr;

  // Feed Available / Empty Status
  if (feedDot && feedStatusText) {
    if (dev.feedAvailable !== false) {
      feedDot.className = 'feed-dot dot-available';
      feedStatusText.textContent = 'Available';
      feedStatusText.className = 'cell-value text-emerald';
    } else {
      feedDot.className = 'feed-dot dot-empty';
      feedStatusText.textContent = 'Empty / Refill';
      feedStatusText.className = 'cell-value text-coral';
    }
  }

  // Also sync Operational Status Summary Pill
  const pillFeedDot = document.getElementById('pill-feed-dot');
  const pillFeedStatus = document.getElementById('pill-feed-status');
  if (pillFeedDot && pillFeedStatus) {
    if (dev.feedAvailable !== false) {
      pillFeedDot.className = 'pill-dot dot-available';
      pillFeedStatus.textContent = 'Feed Available';
    } else {
      pillFeedDot.className = 'pill-dot dot-empty';
      pillFeedStatus.textContent = 'Refill Needed';
    }
  }

  // Progress Bar
  const pct = Math.min(100, Math.max(0, ((liveDispensed || 0) / (targetKg || 25.0)) * 100));
  if (fillBar) fillBar.style.width = `${pct.toFixed(1)}%`;

  // Tab 3 Param Editor Inputs
  const paramDevName = document.getElementById('param-device-name');
  if (paramDevName) paramDevName.textContent = dev.name;

  const inputQty = document.getElementById('input-qty');
  const sliderQty = document.getElementById('slider-qty');
  const inputFpe = document.getElementById('input-fpe');
  const sliderFpe = document.getElementById('slider-fpe');
  const inputStartHour = document.getElementById('input-start-hour');
  const inputStartMin = document.getElementById('input-start-min');
  const inputEndHour = document.getElementById('input-end-hour');
  const inputEndMin = document.getElementById('input-end-min');

  // CRITICAL: Only populate inputs if user is NOT actively typing or focused on them!
  const activeId = document.activeElement ? document.activeElement.id : '';
  const isEditingSettings = ['input-qty', 'slider-qty', 'input-fpe', 'slider-fpe', 
    'input-start-hour', 'input-start-min', 'input-end-hour', 'input-end-min'].includes(activeId);

  if (!isEditingSettings) {
    if (inputQty && sliderQty) {
      inputQty.value = dev.targetKg !== undefined ? dev.targetKg : 25.0;
      sliderQty.value = dev.targetKg !== undefined ? dev.targetKg : 25.0;
    }

    if (inputFpe && sliderFpe) {
      inputFpe.value = dev.fpeGrams !== undefined ? dev.fpeGrams : 100;
      sliderFpe.value = dev.fpeGrams !== undefined ? dev.fpeGrams : 100;
    }

    if (inputStartHour) inputStartHour.value = dev.startHour !== undefined ? dev.startHour : 6;
    if (inputStartMin) inputStartMin.value = dev.startMin !== undefined ? dev.startMin : 0;
    if (inputEndHour) inputEndHour.value = dev.endHour !== undefined ? dev.endHour : 18;
    if (inputEndMin) inputEndMin.value = dev.endMin !== undefined ? dev.endMin : 0;
  }

  recalculateSchedule();
}

/* ==========================================================================
   4. ADD NEW POND & ADD NEW DEVICE MODALS
   ========================================================================== */
function openAddPondModal() {
  const modal = document.getElementById('modal-add-pond');
  if (modal) modal.style.display = 'flex';
}

function closeAddPondModal() {
  const modal = document.getElementById('modal-add-pond');
  if (modal) modal.style.display = 'none';
}

function submitAddNewPond() {
  const idInput = document.getElementById('new-pond-id');
  const acresInput = document.getElementById('new-pond-acres');
  const stockInput = document.getElementById('new-pond-stock');
  const latInput = document.getElementById('new-pond-lat');
  const lngInput = document.getElementById('new-pond-lng');

  const name = idInput?.value.trim() || `Pond P-0${appState.ponds.length + 1}`;
  const acres = parseFloat(acresInput?.value || '2.0');
  const stock = stockInput?.value.trim() || 'Vannamei Shrimp';
  const lat = parseFloat(latInput?.value || '16.5040');
  const lng = parseFloat(lngInput?.value || '81.6710');

  const newPond = {
    id: `P-0${appState.ponds.length + 1}`,
    name,
    acres,
    stock,
    lat,
    lng
  };

  appState.ponds.push(newPond);
  saveDataToStorage();

  refreshPondsDropdown();
  renderPondsDirectory();
  switchActivePond(newPond.id);
  closeAddPondModal();

  showToast(`✅ ${name} added successfully!`);
}

function openAddDeviceModal() {
  const modal = document.getElementById('modal-add-device');
  const pondSelect = document.getElementById('new-device-pond-select');
  const devIdInput = document.getElementById('new-device-id');

  if (pondSelect) {
    pondSelect.innerHTML = appState.ponds.map(p => `
      <option value="${p.id}" ${p.id === appState.selectedPondId ? 'selected' : ''}>${p.name}</option>
    `).join('');
  }

  if (devIdInput) {
    devIdInput.value = `aquaCON-0${appState.devices.length + 1}`;
  }

  if (modal) modal.style.display = 'flex';
}

function closeAddDeviceModal() {
  const modal = document.getElementById('modal-add-device');
  if (modal) modal.style.display = 'none';
}

async function submitAddNewDevice() {
  const id = document.getElementById('new-device-id')?.value.trim();
  const name = document.getElementById('new-device-name')?.value.trim() || `aquaCON Feeder 0${appState.devices.length + 1}`;
  const pondId = document.getElementById('new-device-pond-select')?.value;
  const targetKg = parseFloat(document.getElementById('new-device-target')?.value || '15.0');

  if (!id) {
    showToast('Please enter Feeder Serial ID');
    return;
  }

  const newDev = {
    id,
    name,
    pondId,
    status: 'IDLE',
    feedAvailable: true,
    dispensedKg: 0.0,
    targetKg,
    currentEvent: 0,
    totalEvents: Math.floor((targetKg * 1000) / 100),
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 4.7,
    motorTimeSec: 1.0,
    scheduleValid: true
  };

  appState.devices.push(newDev);
  saveDataToStorage();

  // Send to AWS DynamoDB
  try {
    fetch(`${API_BASE_URL}/api/devices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        deviceId: id,
        deviceName: name,
        pondId,
        feedQuantity_kg: targetKg
      })
    });
  } catch (e) {
    console.log('Saved to local storage');
  }

  updatePondContextBar();
  renderPondsDirectory();
  switchActiveDevice(id);
  closeAddDeviceModal();

  showToast(`✅ ${name} registered to ${pondId}!`);
}

/* ==========================================================================
   5. HISTORIC DATA & TRENDS (NEW!)
   ========================================================================== */
async function renderHistoryView() {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (!dev) return;

  const pond = appState.ponds.find(p => p.id === dev.pondId);

  // Update Header labels
  const titleEl = document.getElementById('history-feeder-title');
  const pondEl = document.getElementById('history-feeder-pond');
  const targetLbl = document.getElementById('chart-target-lbl');

  if (titleEl) titleEl.textContent = `${dev.name} Trends`;
  if (pondEl) pondEl.textContent = pond ? pond.name : dev.pondId;
  if (targetLbl) targetLbl.textContent = `${(dev.targetKg || 15.0).toFixed(1)} Kg`;

  // Fetch or generate 7-day metric data
  let metrics = appState.deviceMetrics[dev.id];
  if (!metrics) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/metrics/${dev.id}`);
      const data = await res.json();
      if (data && data.metrics && data.metrics.length > 0) {
        metrics = data.metrics;
        appState.deviceMetrics[dev.id] = metrics;
      }
    } catch (e) {}
  }

  // Fallback 7-day records if offline or pending
  if (!metrics || metrics.length === 0) {
    const today = new Date();
    metrics = [];
    const base = dev.targetKg || 15.0;
    const offsets = [0.2, -0.4, 0.5, -0.1, 0.3, -0.2, 0.0];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' });
      const disp = i === 0 ? (dev.dispensedKg || 0.40) : Math.max(0.5, parseFloat((base + offsets[6 - i]).toFixed(1)));
      metrics.push({
        dateLabel: dStr,
        feedKg: disp,
        targetKg: base,
        isToday: i === 0
      });
    }
    appState.deviceMetrics[dev.id] = metrics;
  }

  // Ensure today's live dispensedKg is synchronized with today's bar
  if (metrics && metrics.length > 0) {
    const todayStr = new Date().toISOString().slice(0, 10);
    metrics.forEach((m, idx) => {
      if (m.feedKg === undefined && m.FeedDispensed_kg !== undefined) {
        m.feedKg = parseFloat(m.FeedDispensed_kg);
      }
      if (m.Date === todayStr || m.isToday || idx === metrics.length - 1) {
        if (dev.dispensedKg !== undefined && dev.dispensedKg > 0) {
          m.feedKg = dev.dispensedKg;
          m.FeedDispensed_kg = dev.dispensedKg;
        }
        m.isToday = true;
      }
    });
  }

  // Compute Stats Overview
  const totalWeek = metrics.reduce((acc, m) => acc + (m.feedKg || m.FeedDispensed_kg || 0), 0);
  const avgDaily = (totalWeek / metrics.length).toFixed(1);
  const avgAdherence = (metrics.reduce((acc, m) => acc + (m.AdherencePct || Math.min(100, (m.feedKg / (dev.targetKg || 15.0)) * 100)), 0) / metrics.length).toFixed(1);

  const statWeek = document.getElementById('stat-week-total');
  const statAvg = document.getElementById('stat-daily-avg');
  const statAdherence = document.getElementById('stat-adherence');

  if (statWeek) statWeek.textContent = `${totalWeek.toFixed(1)} Kg`;
  if (statAvg) statAvg.textContent = `${avgDaily} Kg`;
  if (statAdherence) statAdherence.textContent = `${Math.min(100, Math.max(0, avgAdherence))}%`;

  // Render Bar Chart
  renderBarChart(metrics, dev.targetKg || 15.0);

  // Render Feed Events Log
  renderEventsLog(dev);
}

function renderBarChart(metrics, targetKg) {
  const container = document.getElementById('history-chart-container');
  if (!container) return;

  const maxVal = Math.max(targetKg * 1.3, ...metrics.map(m => m.feedKg || m.FeedDispensed_kg || 0));

  let html = '';
  metrics.forEach(m => {
    const val = m.feedKg !== undefined ? m.feedKg : m.FeedDispensed_kg;
    const heightPct = Math.min(100, Math.max(5, (val / maxVal) * 100));
    const dayLabel = m.dateLabel || (m.Date ? m.Date.slice(5) : 'Day');
    const isToday = m.isToday || (m.Date && m.Date === new Date().toISOString().slice(0, 10));

    html += `
      <div class="bar-column">
        <span class="bar-val-lbl">${val.toFixed(1)}</span>
        <div class="bar-pillar ${isToday ? 'today' : ''}" style="height: ${heightPct}%;"></div>
        <span class="bar-day-lbl">${dayLabel}</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderEventsLog(dev) {
  const container = document.getElementById('events-log-container');
  if (!container) return;

  const eventsCount = dev.currentEvent || 0;
  const fpe = dev.fpeGrams || 100;
  const interval = dev.intervalMin || 2.9;
  const startH = dev.startHour !== undefined ? dev.startHour : 6;
  const startM = dev.startMin !== undefined ? dev.startMin : 0;

  if (eventsCount === 0) {
    const sHStr = startH < 10 ? '0' + startH : startH;
    const sMStr = startM < 10 ? '0' + startM : startM;
    container.innerHTML = `
      <div class="event-log-item" style="justify-content:center;color:var(--text-dim);padding:24px;">
        No feed events executed yet today. Scheduled to begin at ${sHStr}:${sMStr} AM.
      </div>
    `;
    return;
  }

  // Anchor the latest completed event to the actual live cycle time
  const nextInfo = calculateNextFeedTimestamp(dev);
  let lastEventMins;

  if (nextInfo && nextInfo.nextMinsTotal) {
    // During active feeding: the last completed event occurred 1 interval before the upcoming event
    lastEventMins = nextInfo.nextMinsTotal - interval;
  } else {
    // If completed or outside feeding window, anchor to wall-clock time
    const now = new Date();
    lastEventMins = now.getHours() * 60 + now.getMinutes();
  }

  function formatClockFromMins(totalMins) {
    let mTotal = Math.round(totalMins);
    while (mTotal < 0) mTotal += 1440;
    mTotal = mTotal % 1440;
    const h = Math.floor(mTotal / 60);
    const m = Math.floor(mTotal % 60);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const dh = h % 12 === 0 ? 12 : h % 12;
    const dm = m < 10 ? '0' + m : m;
    return `${dh < 10 ? '0' + dh : dh}:${dm} ${ampm}`;
  }

  // Show the latest 20 events in reverse order (most recent first)
  const maxToShow = Math.min(eventsCount, 20);
  let html = '';
  for (let i = eventsCount; i > eventsCount - maxToShow; i--) {
    const eventMins = lastEventMins - ((eventsCount - i) * interval);
    const t = formatClockFromMins(eventMins);
    html += `
      <div class="event-log-item">
        <div>
          <span class="event-log-time">${t}</span>
          <div class="event-log-desc">Feed Event #${i} • ${fpe}g dispensed</div>
        </div>
        <span class="event-log-tag tag-completed">Completed 🟢</span>
      </div>
    `;
  }

  if (eventsCount > maxToShow) {
    html += `
      <div style="text-align:center;padding:10px;font-size:12px;color:var(--text-dim);">
        + ${eventsCount - maxToShow} earlier events completed today
      </div>
    `;
  }

  container.innerHTML = html;
}

function refreshHistoryData() {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (dev) {
    delete appState.deviceMetrics[dev.id];
    renderHistoryView();
    showToast('Refreshed historic trends');
  }
}

/* ==========================================================================
   6. REALTIME GOOGLE MAPS LINK & LEAFLET MAP
   ========================================================================== */
function openCurrentPondInGoogleMaps() {
  const pond = appState.ponds.find(p => p.id === appState.selectedPondId);
  if (!pond) return;

  const url = `https://www.google.com/maps/search/?api=1&query=${pond.lat},${pond.lng}`;
  window.open(url, '_blank');
}

function openPondInGoogleMaps(pondId) {
  const pond = appState.ponds.find(p => p.id === pondId);
  if (!pond) return;

  const url = `https://www.google.com/maps/search/?api=1&query=${pond.lat},${pond.lng}`;
  window.open(url, '_blank');
}

function renderPondsDirectory() {
  const container = document.getElementById('ponds-list-container');
  if (!container) return;

  container.innerHTML = appState.ponds.map(pond => {
    const pondDevices = appState.devices.filter(d => d.pondId === pond.id);
    return `
      <div class="pond-item-card">
        <div class="pond-item-header">
          <span class="pond-item-name">${pond.name}</span>
          <span class="pond-item-acres">${pond.acres} Acres</span>
        </div>
        <div class="pond-devices-summary">
          ${pondDevices.map(d => `<span class="device-chip-badge">🐟 ${d.name} (${d.status})</span>`).join('')}
          ${pondDevices.length === 0 ? '<span class="device-chip-badge">No Feeders Assigned</span>' : ''}
        </div>
        <div class="pond-item-actions">
          <button type="button" class="btn-view-pond" onclick="switchActivePond('${pond.id}'); navigateToTab('tab-status');">View Feeder Console →</button>
          <button type="button" class="btn-gmaps" onclick="openPondInGoogleMaps('${pond.id}')">🗺️ Open in Google Maps</button>
        </div>
      </div>
    `;
  }).join('');
}

function initSatelliteMap() {
  const mapContainer = document.getElementById('satellite-map');
  if (!mapContainer || leafletMap) return;

  const centerPond = appState.ponds[0] || { lat: 16.5062, lng: 81.6708 };

  leafletMap = L.map('satellite-map', {
    zoomControl: false,
    attributionControl: false
  }).setView([centerPond.lat, centerPond.lng], 16);

  // Esri Realtime Satellite Imagery Tiles
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19
  }).addTo(leafletMap);

  renderMapPondsAndFeeders();
}

function renderMapPondsAndFeeders() {
  if (!leafletMap) return;

  // Clear existing layers
  pondPolygons.forEach(p => leafletMap.removeLayer(p));
  feederMapMarkers.forEach(m => leafletMap.removeLayer(m));
  pondPolygons = [];
  feederMapMarkers = [];

  appState.ponds.forEach(pond => {
    const delta = 0.0012;
    const coords = [
      [pond.lat + delta, pond.lng - delta],
      [pond.lat + delta, pond.lng + delta],
      [pond.lat - delta, pond.lng + delta],
      [pond.lat - delta, pond.lng - delta]
    ];

    const poly = L.polygon(coords, {
      color: '#00f0ff',
      weight: 2,
      fillColor: '#00f0ff',
      fillOpacity: 0.18
    }).addTo(leafletMap).bindPopup(`
      <strong>${pond.name}</strong><br>
      Area: ${pond.acres} Acres<br>
      <button onclick="openPondInGoogleMaps('${pond.id}')" style="margin-top:6px;padding:4px 8px;font-size:11px;cursor:pointer;">Open in Google Maps 🗺️</button>
    `);

    pondPolygons.push(poly);

    // Place feeder markers
    const devices = appState.devices.filter(d => d.pondId === pond.id);
    devices.forEach((dev, idx) => {
      const pinOffset = idx * 0.0004;
      const marker = L.marker([pond.lat + pinOffset, pond.lng + pinOffset], {
        icon: L.divIcon({
          className: 'custom-map-pin',
          html: `<div style="background:#00e5a3;width:14px;height:14px;border-radius:50%;box-shadow:0 0 10px #00e5a3;border:2px solid #ffffff;"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        })
      }).addTo(leafletMap).bindPopup(`
        <strong>${dev.name}</strong><br>
        Status: ${dev.status}<br>
        Target: ${dev.targetKg} Kg
      `);

      feederMapMarkers.push(marker);
    });
  });
}

function resetMapView() {
  if (!leafletMap) return;
  const currentPond = appState.ponds.find(p => p.id === appState.selectedPondId) || appState.ponds[0];
  if (currentPond) leafletMap.setView([currentPond.lat, currentPond.lng], 16);
}

/* ==========================================================================
   7. NAVIGATION CONTROLLER (5 TABS)
   ========================================================================== */
function navigateToTab(tabId) {
  appState.activeTab = tabId;

  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.toggle('active', btn.id === `tab-btn-${tabId.replace('tab-', '')}`);
  });

  document.querySelectorAll('.tab-screen').forEach(screen => {
    screen.classList.remove('active');
  });

  const screen = document.getElementById(`screen-${tabId.replace('tab-', '')}`);
  if (screen) screen.classList.add('active');

  if (tabId === 'tab-history') {
    renderHistoryView();
  }

  if (tabId === 'tab-map' && leafletMap) {
    setTimeout(() => {
      leafletMap.invalidateSize();
      renderMapPondsAndFeeders();
      resetMapView();
    }, 200);
  }
}

function toggleNotificationDrawer() {
  const drawer = document.getElementById('notification-drawer');
  if (drawer) drawer.classList.toggle('open');
}

function markAllNotificationsRead() {
  const badge = document.getElementById('notif-unread-count');
  if (badge) badge.style.display = 'none';
  showToast('Notifications marked read');
}

/* ==========================================================================
   8. SCHEDULE CALCULATION TWIN & PARAMETER DEPLOYMENT
   ========================================================================== */
function initScheduleEngine() {
  const sliderQty = document.getElementById('slider-qty');
  const inputQty = document.getElementById('input-qty');
  const sliderFpe = document.getElementById('slider-fpe');
  const inputFpe = document.getElementById('input-fpe');

  function sync(slider, input, callback) {
    if (slider && input) {
      slider.addEventListener('input', () => {
        input.value = slider.value;
        callback();
      });
      input.addEventListener('change', () => {
        slider.value = input.value;
        callback();
      });
    }
  }

  sync(sliderQty, inputQty, recalculateSchedule);
  sync(sliderFpe, inputFpe, recalculateSchedule);

  ['input-start-hour', 'input-start-min', 'input-end-hour', 'input-end-min'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', recalculateSchedule);
  });
}

function recalculateSchedule() {
  const qty = parseFloat(document.getElementById('input-qty')?.value || '15.0');
  const fpe = parseInt(document.getElementById('input-fpe')?.value || '100');
  const sHour = parseInt(document.getElementById('input-start-hour')?.value || '6');
  const sMin = parseInt(document.getElementById('input-start-min')?.value || '0');
  const eHour = parseInt(document.getElementById('input-end-hour')?.value || '18');
  const eMin = parseInt(document.getElementById('input-end-min')?.value || '0');

  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (dev) {
    dev.targetKg = qty;
    dev.fpeGrams = fpe;
    dev.startHour = sHour;
    dev.startMin = sMin;
    dev.endHour = eHour;
    dev.endMin = eMin;
  }

  const validBadge = document.getElementById('calc-valid-badge');
  const totalEventsEl = document.getElementById('calc-total-events');
  const intervalEl = document.getElementById('calc-interval');
  const motorTimeEl = document.getElementById('calc-motor-time');

  // Total Events = (Qty * 1000) / FPE
  const totalEvents = Math.floor((qty * 1000) / fpe);
  const motorTimeSec = Math.max(1.0, fpe / 100); // 100 g/s default calibration
  const windowSec = ((eHour * 60 + eMin) - (sHour * 60 + sMin)) * 60;
  const intervalMin = parseFloat(((windowSec - (totalEvents * motorTimeSec)) / (totalEvents * 60)).toFixed(1));

  if (totalEventsEl) totalEventsEl.textContent = `${totalEvents}`;
  if (intervalEl) intervalEl.textContent = `${intervalMin} min`;
  if (motorTimeEl) motorTimeEl.textContent = `${motorTimeSec.toFixed(1)} s`;

  if (validBadge) {
    validBadge.textContent = intervalMin >= 0.16 ? 'SCHEDULE OK' : 'WINDOW TOO TIGHT';
    validBadge.className = intervalMin >= 0.16 ? 'badge-valid' : 'badge-invalid';
  }

  if (dev) {
    dev.totalEvents = totalEvents;
    dev.intervalMin = intervalMin;
    dev.motorTimeSec = motorTimeSec;
  }
}

async function saveSettingsToFeeder() {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (!dev) return;

  const btnText = document.getElementById('save-btn-text');
  if (btnText) btnText.textContent = 'Saving to Feeder...';

  // Read current input values directly from UI
  const qty = parseFloat(document.getElementById('input-qty')?.value || dev.targetKg || 25.0);
  const fpe = parseInt(document.getElementById('input-fpe')?.value || dev.fpeGrams || 100);
  const shour = parseInt(document.getElementById('input-start-hour')?.value || dev.startHour || 6);
  const smin = parseInt(document.getElementById('input-start-min')?.value || dev.startMin || 0);
  const ehour = parseInt(document.getElementById('input-end-hour')?.value || dev.endHour || 18);
  const emin = parseInt(document.getElementById('input-end-min')?.value || dev.endMin || 0);

  dev.targetKg = qty;
  dev.fpeGrams = fpe;
  dev.startHour = shour;
  dev.startMin = smin;
  dev.endHour = ehour;
  dev.endMin = emin;
  dev.totalEvents = Math.floor((qty * 1000) / fpe);
  dev.settingsLastSavedAt = Date.now();

  saveDataToStorage();

  try {
    const res = await fetch(`${API_BASE_URL}/api/settings/${dev.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        feedQuantity_kg: dev.targetKg,
        feedPerEvent_g: dev.fpeGrams,
        dischargeRate_gs: dev.dischargeRateGs || 100,
        startHour: dev.startHour,
        startMinute: dev.startMin,
        endHour: dev.endHour,
        endMinute: dev.endMin
      })
    });
    const result = await res.json();
    if (result && result.downlinkQueued) {
      showToast(`✅ Settings saved & downlink queued to feeder!`);
    } else {
      showToast(`✅ Settings saved for ${dev.name}!`);
    }
  } catch (e) {
    showToast(`Settings saved locally for ${dev.name}`);
  } finally {
    if (btnText) btnText.textContent = '💾 Save Settings to Feeder';
  }

  loadSelectedDeviceToUI();
}

/* ==========================================================================
   9. REMOTE FEEDER CONTROLS
   ========================================================================== */
async function triggerRemoteAction(action) {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (!dev) return;

  if (action === 'START') {
    if (!confirm(`Start feeding cycle for ${dev.name}?`)) return;
    dev.status = 'FEEDING';
    showToast(`▶ Starting feeder: ${dev.name}`);
  } else {
    dev.status = 'IDLE';
    showToast(`⏹ Feeder stopped: ${dev.name}`);
  }

  saveDataToStorage();
  loadSelectedDeviceToUI();

  try {
    await fetch(`${API_BASE_URL}/api/command/${dev.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: action })
    });
  } catch (e) {
    // Handled locally
  }
}

/* ==========================================================================
   10. FARM CLOCK, CONTACTS & TELEMETRY SYNC
   ========================================================================== */
function initFarmClock() {
  const clockEl = document.getElementById('live-farm-time');
  function tick() {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toLocaleTimeString('en-IN', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
  }
  tick();
  setInterval(tick, 1000);
}

function renderAlertContacts() {
  const container = document.getElementById('contacts-list-container');
  if (!container) return;

  if (!appState.contacts || appState.contacts.length === 0) {
    container.innerHTML = '<div style="color:var(--text-dim);font-size:12px;padding:12px;text-align:center;">No alert contacts configured. Click "+ Add Contact" to add.</div>';
    return;
  }

  container.innerHTML = appState.contacts.map((c, idx) => {
    const rawNumber = c.rawPhone || (c.phone ? c.phone.replace(/[^0-9]/g, '') : '9154696777');
    const deleteBtn = c.isDefault 
      ? '' 
      : `<button type="button" class="btn-delete-contact" onclick="deleteContact(${idx})" title="Remove ${c.name}">✕</button>`;

    return `
      <div class="contact-card">
        <div class="contact-info">
          <span class="contact-name">${c.name}</span>
          <a href="tel:${rawNumber}" class="contact-phone-link">📞 ${c.phone}</a>
        </div>
        <div class="contact-meta">
          <span class="contact-role-badge">${c.role || 'Farm Staff'}</span>
          <div class="contact-actions">
            <a href="tel:${rawNumber}" class="btn-call-contact" title="Direct Phone Call">📞 Call</a>
            ${deleteBtn}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function openAddContactModal() {
  const modal = document.getElementById('modal-add-contact');
  const nameInput = document.getElementById('new-contact-name');
  const phoneInput = document.getElementById('new-contact-phone');
  if (nameInput) nameInput.value = '';
  if (phoneInput) phoneInput.value = '';
  if (modal) modal.style.display = 'flex';
}

function closeAddContactModal() {
  const modal = document.getElementById('modal-add-contact');
  if (modal) modal.style.display = 'none';
}

function submitAddNewContact() {
  const name = document.getElementById('new-contact-name')?.value.trim();
  const rawInput = document.getElementById('new-contact-phone')?.value.trim() || '';
  const digits = rawInput.replace(/[^0-9]/g, '');
  const role = document.getElementById('new-contact-role')?.value || 'Farm Manager';

  if (!name) {
    showToast('Please enter contact name');
    return;
  }

  if (digits.length < 10) {
    showToast('Please enter a valid 10-digit mobile number');
    return;
  }

  const phone10 = digits.slice(-10);
  const formattedPhone = `+91 ${phone10.slice(0, 5)} ${phone10.slice(5)}`;

  appState.contacts.push({
    name,
    phone: formattedPhone,
    rawPhone: phone10,
    role,
    isDefault: false
  });

  saveDataToStorage();
  renderAlertContacts();
  closeAddContactModal();
  showToast(`✅ Alert contact added: ${name}`);
}

function deleteContact(idx) {
  const c = appState.contacts[idx];
  if (!c) return;
  if (c.isDefault) {
    showToast('Primary Alert Lead cannot be removed');
    return;
  }
  if (confirm(`Remove ${c.name} (${c.phone}) from alert contacts?`)) {
    const removedName = c.name;
    appState.contacts.splice(idx, 1);
    saveDataToStorage();
    renderAlertContacts();
    showToast(`Removed ${removedName}`);
  }
}

function handleModalBackdropClick(event, modalId) {
  if (event.target && event.target.id === modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
  }
}

function toggleFeedStockState() {
  const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
  if (!dev) return;

  dev.feedAvailable = !(dev.feedAvailable !== false);
  saveDataToStorage();
  loadSelectedDeviceToUI();

  if (dev.feedAvailable) {
    showToast(`🟢 Feed stock marked AVAILABLE for ${dev.name}`);
  } else {
    showToast(`⚠️ Feed stock marked EMPTY / REFILL for ${dev.name}`);
  }
}

function startTelemetryLoop() {
  async function poll() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/devices`);
      const data = await res.json();

      if (data && data.devices) {
        data.devices.forEach(cloudDev => {
          const localDev = appState.devices.find(d => d.id === cloudDev.DeviceId);
          if (localDev) {
            if (cloudDev.CurrentEvent !== undefined) localDev.currentEvent = cloudDev.CurrentEvent;
            if (cloudDev.Status) localDev.status = cloudDev.Status;
            else if (localDev.currentEvent > 0) localDev.status = 'FEEDING';
            if (cloudDev.FeedAvailable !== undefined) localDev.feedAvailable = cloudDev.FeedAvailable;

            // Only overwrite schedule parameters if user hasn't recently saved custom settings locally
            const recentlySaved = localDev.settingsLastSavedAt && (Date.now() - localDev.settingsLastSavedAt < 25000);
            if (!recentlySaved) {
              if (cloudDev.TotalEvents !== undefined) localDev.totalEvents = cloudDev.TotalEvents;
              if (cloudDev.FeedPerEvent_g !== undefined) localDev.fpeGrams = cloudDev.FeedPerEvent_g;
              if (cloudDev.FeedQuantity_kg !== undefined) localDev.targetKg = cloudDev.FeedQuantity_kg;
              if (cloudDev.IntervalMin !== undefined) localDev.intervalMin = cloudDev.IntervalMin;
              if (cloudDev.StartHour !== undefined) localDev.startHour = cloudDev.StartHour;
              if (cloudDev.StartMinute !== undefined) localDev.startMin = cloudDev.StartMinute;
              if (cloudDev.EndHour !== undefined) localDev.endHour = cloudDev.EndHour;
              if (cloudDev.EndMinute !== undefined) localDev.endMin = cloudDev.EndMinute;
            }

            const curEv = localDev.currentEvent || 0;
            const fpe = localDev.fpeGrams || 100;
            const computedDispensed = parseFloat(((curEv * fpe) / 1000.0).toFixed(2));
            localDev.dispensedKg = cloudDev.DispensedFeed_kg !== undefined 
              ? parseFloat(cloudDev.DispensedFeed_kg) 
              : computedDispensed;
          }
        });

        loadSelectedDeviceToUI();

        // Also update 7-day metrics for selected device if cached
        const curDev = appState.devices.find(d => d.id === appState.selectedDeviceId);
        if (curDev && appState.deviceMetrics[curDev.id]) {
          const mList = appState.deviceMetrics[curDev.id];
          if (mList && mList.length > 0) {
            const todayItem = mList[mList.length - 1];
            if (todayItem) {
              todayItem.feedKg = curDev.dispensedKg;
              todayItem.FeedDispensed_kg = curDev.dispensedKg;
            }
          }
          if (appState.activeTab === 'tab-history') {
            renderHistoryView();
          }
        }
      }
    } catch (e) {}
  }

  // Initial poll immediately
  poll();
  // Poll every 5 seconds for fast live updates
  setInterval(poll, 5000);

  // Update clock/next event ticker every 10 seconds so timestamp moves forward smoothly
  setInterval(() => {
    loadSelectedDeviceToUI();
  }, 10000);
}

/* ==========================================================================
   11. GLOBAL TOAST UTILITY
   ========================================================================== */
let toastTimeout = null;
function showToast(message) {
  const toast = document.getElementById('app-toast');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add('show');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 2600);
}
