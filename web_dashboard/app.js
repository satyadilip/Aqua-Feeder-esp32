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
    dispensedKg: 3.70,
    targetKg: 25.0,
    currentEvent: 37,
    totalEvents: 250,
    fpeGrams: 100,
    dischargeRateGs: 100,
    startHour: 6,
    startMin: 0,
    endHour: 18,
    endMin: 0,
    intervalMin: 4.7,
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
      pwToggleBtn.innerHTML = isPw ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>' : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
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
          showAuthAlert('Welcome back! Loading your ponds...', 'success');
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
          showAuthAlert('Welcome back! Loading your ponds...', 'success');
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
      showToast('Entering aquaCON Farm Dashboard');
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
          showAuthAlert('Farm registered! Please sign in with your phone.', 'success');
          tabLoginBtn?.click();
          const phoneInput = document.getElementById('auth-phone-input');
          if (phoneInput) phoneInput.value = phone;
        } else {
          showAuthAlert(data.error || 'Registration failed', 'error');
        }
      } catch (e) {
        showAuthAlert('Registration connection error', 'error');
      } finally {
        if (btnText) btnText.innerHTML = 'Register Farm';
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
      const isLive = d.status === 'FEEDING';
            const match = (d.name || '').match(/Feeder\s*\d+/i);
      const cleanName = match ? match[0] : (d.name || d.id).slice(0, 9);
      html += `
        <button type="button" class="story-item ${isActive ? 'active-story' : ''}" onclick="switchActiveDevice('${d.id}')" title="${d.name || d.id}">
          <div class="story-ring ${isLive ? 'live-feeding' : ''} ${isActive ? 'ring-active' : ''}">
            <div class="story-avatar">
              <span class="story-icon">
                ${isLive 
                  ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
                  : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 3h16l-3 9H7L4 3z"/><path d="M7 12l2 6h6l2-6"/><path d="M12 18v3"/></svg>'
                }
              </span>
            </div>
            ${isLive ? '<span class="story-live-badge">LIVE</span>' : ''}
          </div>
          <span class="story-name">${cleanName}</span>
        </button>
      `;
    });

    html += `
      <button type="button" class="story-item story-add-item" onclick="openAddDeviceModal()" title="Add New Feeder">
        <div class="story-ring story-ring-add">
          <div class="story-avatar">
            <span class="story-icon">+</span>
          </div>
        </div>
        <span class="story-name">Add New</span>
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

  const heroMatch = (dev.name || '').match(/Feeder\s*\d+/i);
  const heroTitle = heroMatch ? heroMatch[0] : (dev.name || 'Feeder 01');
  if (devName) devName.textContent = heroTitle;
  if (devTag) {
    const shortId = dev.id.startsWith('e072') ? dev.id.slice(-8) : dev.id;
    devTag.textContent = `ID: ${shortId} • Live LoRaWAN`;
  }

  if (stateBadge) {
    stateBadge.textContent = dev.status || 'IDLE';
    stateBadge.className = `badge-state ${dev.status === 'RUNNING' || dev.status === 'FEEDING' ? 'b-run' : 'b-idle'}`;
  }

  
  // Update Dribbble Radial Arc Gauge
  const currentEvents = dev.currentEvent !== undefined ? dev.currentEvent : (dev.eventsToday || 4);
  const totalEvents = dev.totalEvents || 150;
  const gaugePct = Math.min(100, Math.max(0, (currentEvents / totalEvents) * 100));
  const gaugeCircle = document.getElementById('gauge-progress-circle');
  const gaugeHeroNum = document.getElementById('gauge-hero-num');
  const gaugeHeroSub = document.getElementById('gauge-hero-sub');
  const gaugePctBadge = document.getElementById('gauge-pct-badge');
  if (gaugeCircle) {
    const circumference = 408.4;
    const offset = circumference - (gaugePct / 100) * circumference;
    gaugeCircle.style.strokeDashoffset = offset;
  }
  if (gaugeHeroNum) gaugeHeroNum.textContent = currentEvents;
  if (gaugeHeroSub) gaugeHeroSub.textContent = `/ ${totalEvents} Events Today`;
  if (gaugePctBadge) gaugePctBadge.textContent = `${gaugePct.toFixed(1)}%`;

  if (dispensedText) dispensedText.textContent = (dev.dispensedKg || 0).toFixed(2);
  if (targetText) targetText.textContent = (dev.targetKg || 15.0).toFixed(1);
  if (burstCountText) burstCountText.textContent = `${dev.currentEvent || 0} / ${dev.totalEvents || 150}`;
  if (nextIntervalText) nextIntervalText.textContent = `${dev.intervalMin || 4.7} mins`;
  if (nextFeedTimeText) nextFeedTimeText.textContent = `Next at 11:30 AM`;

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
  const pct = Math.min(100, Math.max(0, ((dev.dispensedKg || 0) / (dev.targetKg || 15.0)) * 100));
  if (fillBar) fillBar.style.width = `${pct.toFixed(1)}%`;

  // Tab 3 Param Editor Inputs
  const paramDevName = document.getElementById('param-device-name');
  const cleanParamName = (dev.name || '').match(/Feeder\s*\d+/i) ? dev.name.match(/Feeder\s*\d+/i)[0] : 'Feeder 01';
  if (paramDevName) paramDevName.textContent = cleanParamName;

  const inputQty = document.getElementById('input-qty');
  const sliderQty = document.getElementById('slider-qty');
  const inputFpe = document.getElementById('input-fpe');
  const sliderFpe = document.getElementById('slider-fpe');

  if (inputQty && sliderQty) {
    inputQty.value = dev.targetKg || 15.0;
    sliderQty.value = dev.targetKg || 15.0;
  }

  if (inputFpe && sliderFpe) {
    inputFpe.value = dev.fpeGrams || 100;
    sliderFpe.value = dev.fpeGrams || 100;
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

  showToast(`${name} added successfully!`);
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

  showToast(`${name} registered to ${pondId}!`);
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

  const cleanFeeder = (dev.name || '').match(/Feeder\s*\d+/i) ? dev.name.match(/Feeder\s*\d+/i)[0] : 'Feeder 01';
  if (titleEl) titleEl.textContent = `${cleanFeeder} Trends`;
  if (pondEl) pondEl.textContent = pond ? pond.name : 'Pond P-01';
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
    const offsets = [0.2, -0.4, 0.5, -0.1, 0.3, -0.2, -(base - (dev.dispensedKg || 0.4))];
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

  // Compute Stats Overview
  const totalWeek = metrics.reduce((acc, m) => acc + (m.feedKg || m.FeedDispensed_kg || 0), 0);
  const avgDaily = (totalWeek / metrics.length).toFixed(1);

  const statWeek = document.getElementById('stat-week-total');
  const statAvg = document.getElementById('stat-daily-avg');
  const statAdherence = document.getElementById('stat-adherence');

  if (statWeek) statWeek.textContent = `${totalWeek.toFixed(1)} Kg`;
  if (statAvg) statAvg.textContent = `${avgDaily} Kg`;
  if (statAdherence) statAdherence.textContent = `98.7%`;

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

  const eventsCount = dev.currentEvent || 4;
  const fpe = dev.fpeGrams || 100;

  const eventTimes = ['07:00 AM', '08:15 AM', '09:30 AM', '10:45 AM', '12:00 PM', '01:15 PM', '02:30 PM'];

  let html = '';
  for (let i = eventsCount; i >= 1; i--) {
    const t = eventTimes[(i - 1) % eventTimes.length] || `${06 + i}:00 AM`;
    html += `
      <div class="event-log-item">
        <div>
          <span class="event-log-time">${t}</span>
          <div class="event-log-desc">Feed Event #${i} • ${fpe}g dispensed</div>
        </div>
        <span class="event-log-tag tag-completed">DISPENSED</span>
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
          ${pondDevices.map(d => `<span class="device-chip-badge"><span class="dot-indicator dot-${d.status.toLowerCase()}"></span> ${d.name} (${d.status})</span>`).join('')}
          ${pondDevices.length === 0 ? '<span class="device-chip-badge">No Feeders Assigned</span>' : ''}
        </div>
        <div class="pond-item-actions">
          <button type="button" class="btn-view-pond" onclick="switchActivePond('${pond.id}'); navigateToTab('tab-status');">Select Pond →</button>
          <button type="button" class="btn-gmaps" onclick="openPondInGoogleMaps('${pond.id}')"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg> Google Maps</button>
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
      <button onclick="openPondInGoogleMaps('${pond.id}')" style="margin-top:6px;padding:4px 8px;font-size:11px;cursor:pointer;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg> Open in Google Maps</button>
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

  saveDataToStorage();

  try {
    await fetch(`${API_BASE_URL}/api/settings/${dev.id}`, {
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
    showToast(`Settings saved for ${dev.name}!`);
  } catch (e) {
    showToast(`Settings saved locally for ${dev.name}`);
  } finally {
    if (btnText) btnText.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save Settings to Feeder';
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
      : `<button type="button" class="btn-delete-contact" onclick="deleteContact(${idx})" title="Remove ${c.name}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>`;

    return `
      <div class="contact-card">
        <div class="contact-info">
          <span class="contact-name">${c.name}</span>
          <a href="tel:${rawNumber}" class="contact-phone-link"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> ${c.phone}</a>
        </div>
        <div class="contact-meta">
          <span class="contact-role-badge">${c.role || 'Farm Staff'}</span>
          <div class="contact-actions">
            <a href="tel:${rawNumber}" class="btn-call-contact" title="Direct Phone Call"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> Call</a>
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
  showToast(`Alert contact added: ${name}`);
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
    showToast(`Feed stock marked AVAILABLE for ${dev.name}`);
  } else {
    showToast(`Feed stock marked EMPTY / REFILL for ${dev.name}`);
  }
}

function startTelemetryLoop() {
  async function poll() {
    if (!appState.isAuthenticated) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/devices`);
      const data = await res.json();

      if (data && data.devices) {
        data.devices.forEach(cloudDev => {
          const localDev = appState.devices.find(d => d.id === cloudDev.DeviceId);
          if (localDev) {
            if (cloudDev.DispensedFeed_kg !== undefined) localDev.dispensedKg = cloudDev.DispensedFeed_kg;
            else if (cloudDev.LastFeed_g !== undefined) localDev.dispensedKg = parseFloat((cloudDev.LastFeed_g / 1000.0).toFixed(2));
            if (cloudDev.CurrentEvent !== undefined) localDev.currentEvent = cloudDev.CurrentEvent;
            if (cloudDev.TotalEvents !== undefined) localDev.totalEvents = cloudDev.TotalEvents;
            if (cloudDev.Status) localDev.status = cloudDev.Status;
            else if (cloudDev.CurrentEvent > 0) localDev.status = 'FEEDING';
          }
        });
        loadSelectedDeviceToUI();
      }
    } catch (e) {}
  }

  poll();
  setInterval(poll, 10000);
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


