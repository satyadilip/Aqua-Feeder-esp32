// ============================================================================
// AQUA FEEDER AG_V1 — Web Dashboard (PROGMEM HTML/CSS/JS)
// ============================================================================
// Responsive single-page configuration dashboard
// Served from ESP32-S3 SoftAP at http://192.168.4.1
// ============================================================================
#pragma once

const char WEB_DASHBOARD_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aqua Feeder Config</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a1628;--card:#111d32;--border:#1e3a5f;--accent:#00b4d8;--accent2:#0077b6;
--green:#00875a;--red:#e74c3c;--orange:#e67e22;--text:#e0e8f0;--muted:#7a8fa6;--input-bg:#0a1628}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);
min-height:100vh;padding-bottom:20px}
.hdr{background:linear-gradient(135deg,#0d2137,#1a3a5c);padding:18px 20px;text-align:center;
border-bottom:2px solid var(--accent);position:sticky;top:0;z-index:100}
.hdr h1{font-size:20px;color:var(--accent);letter-spacing:1.5px;font-weight:700}
.hdr .sub{color:var(--muted);font-size:11px;margin-top:3px}
.tabs{display:flex;gap:2px;padding:8px 12px;background:#0d1a2e;overflow-x:auto;position:sticky;top:62px;z-index:99}
.tab{flex:1;min-width:80px;padding:10px 8px;text-align:center;font-size:12px;font-weight:600;
color:var(--muted);background:var(--card);border:1px solid var(--border);border-radius:8px;
cursor:pointer;transition:all .2s;white-space:nowrap}
.tab.active{color:var(--accent);border-color:var(--accent);background:#0d2137;
box-shadow:0 0 12px rgba(0,180,216,.15)}
.tab:hover{color:var(--text)}
.panel{display:none;padding:12px}
.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;padding:16px;
transition:border-color .3s}
.card:hover{border-color:#2a5080}
.card h2{color:var(--accent);font-size:14px;margin-bottom:12px;padding-bottom:8px;
border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.card h2 .ico{font-size:16px}
.st-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.st-item{background:#0d1a2e;border-radius:8px;padding:10px 12px}
.st-item .lbl{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
.st-item .val{font-size:18px;font-weight:700;margin-top:2px}
.st-item.full{grid-column:1/-1}
.badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:11px;font-weight:700;letter-spacing:.5px}
.b-idle{background:#2d3e50;color:#8899aa}
.b-run{background:var(--green);color:#fff;animation:pulse 2s infinite}
.b-pause{background:var(--orange);color:#fff}
.b-done{background:#3498db;color:#fff}
.b-err{background:var(--red);color:#fff}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.7}}
.prog{background:#1e3a5f;border-radius:8px;height:16px;margin:8px 0;overflow:hidden;position:relative}
.prog-bar{background:linear-gradient(90deg,var(--accent),var(--accent2));height:100%;border-radius:8px;
transition:width .8s ease;position:relative}
.prog-bar::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;
background:linear-gradient(90deg,transparent,rgba(255,255,255,.1),transparent);animation:shimmer 2s infinite}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.conn-bar{display:flex;gap:8px;flex-wrap:wrap}
.conn-chip{display:flex;align-items:center;gap:4px;padding:5px 10px;border-radius:6px;
font-size:11px;font-weight:600;background:#0d1a2e;border:1px solid var(--border)}
.conn-dot{width:8px;height:8px;border-radius:50%}
.dot-ok{background:#2ecc71;box-shadow:0 0 6px #2ecc71}
.dot-err{background:var(--red)}
.dot-off{background:#555}
.dot-try{background:var(--orange);animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.frm{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.frm.single{grid-template-columns:1fr}
.fg{display:flex;flex-direction:column}
.fg label{color:var(--muted);font-size:11px;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
.fg input,.fg select{background:var(--input-bg);border:1px solid var(--border);color:var(--text);
padding:10px 12px;border-radius:8px;font-size:14px;transition:border-color .2s}
.fg input:focus,.fg select:focus{border-color:var(--accent);outline:none;box-shadow:0 0 8px rgba(0,180,216,.2)}
.fg .hint{font-size:10px;color:var(--muted);margin-top:2px}
.btn-row{display:flex;gap:10px;margin-top:14px}
.btn{flex:1;padding:12px;border:none;border-radius:10px;font-size:13px;font-weight:700;
cursor:pointer;transition:all .15s;text-transform:uppercase;letter-spacing:.5px}
.btn:active{transform:scale(.97)}
.btn-save{background:var(--accent);color:#0a1628}
.btn-start{background:var(--green);color:#fff}
.btn-stop{background:var(--red);color:#fff}
.btn-sec{background:transparent;border:1px solid var(--border);color:var(--muted)}
.btn-sec:hover{border-color:var(--accent);color:var(--text)}
.btn[disabled]{opacity:.35;cursor:not-allowed;transform:none!important}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#1a3a5c;
color:var(--text);padding:12px 24px;border-radius:10px;border:1px solid var(--accent);
font-size:13px;z-index:200;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}
.apn-row{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.apn-chip{padding:6px 12px;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;
background:#0d1a2e;border:1px solid var(--border);color:var(--muted);transition:all .2s}
.apn-chip:hover,.apn-chip.active{border-color:var(--accent);color:var(--accent)}
.time-big{font-size:32px;font-weight:700;color:var(--accent);text-align:center;
font-variant-numeric:tabular-nums;letter-spacing:2px}
@media(max-width:480px){.frm{grid-template-columns:1fr}.st-grid{grid-template-columns:1fr}
.tabs{gap:4px;padding:6px 8px}.tab{padding:8px 6px;font-size:11px}}
</style></head><body>
<div class="hdr">
  <h1>🐟 AQUA FEEDER</h1>
  <div class="sub">AG_V1 • v4.0.0 • http://aquafeeder.local</div>
</div>

<div class="tabs" id="tabs">
  <div class="tab active" data-tab="status">📊 Status</div>
  <div class="tab" data-tab="feed">⚙️ Feed</div>
  <div class="tab" data-tab="network">📡 Network</div>
  <div class="tab" data-tab="system">🔧 System</div>
</div>

<!-- ═══ STATUS TAB ═══ -->
<div class="panel active" id="p-status">
  <div class="card">
    <h2><span class="ico">⏰</span> Live Status</h2>
    <div class="time-big" id="clock">--:--:--</div>
    <div style="text-align:center;margin:6px 0">
      <span class="badge b-idle" id="state-badge">IDLE</span>
    </div>
    <div class="st-grid">
      <div class="st-item"><div class="lbl">Event</div><div class="val" id="s-event">0 / 0</div></div>
      <div class="st-item"><div class="lbl">Next Feed</div><div class="val" id="s-next">--:--</div></div>
      <div class="st-item"><div class="lbl">Voltage</div><div class="val" id="s-volt">-- V</div></div>
      <div class="st-item"><div class="lbl">Current</div><div class="val" id="s-curr">-- mA</div></div>
      <div class="st-item full">
        <div class="lbl">Feed Progress</div>
        <div class="prog"><div class="prog-bar" id="s-prog" style="width:0%"></div></div>
      </div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">📡</span> Connectivity</h2>
    <div class="conn-bar">
      <div class="conn-chip"><div class="conn-dot dot-off" id="d-lora"></div>LoRa</div>
      <div class="conn-chip"><div class="conn-dot dot-off" id="d-wifi"></div>WiFi</div>
      <div class="conn-chip"><div class="conn-dot dot-off" id="d-gsm"></div>GSM</div>
      <div class="conn-chip"><div class="conn-dot dot-off" id="d-sd"></div>SD</div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">🎮</span> Control</h2>
    <div class="btn-row">
      <button class="btn btn-start" id="btn-start" onclick="doStart()">▶ START</button>
      <button class="btn btn-stop" id="btn-stop" onclick="doStop()">⏹ STOP</button>
    </div>
  </div>
</div>

<!-- ═══ FEED SETTINGS TAB ═══ -->
<div class="panel" id="p-feed">
  <div class="card">
    <h2><span class="ico">🍽️</span> Feed Parameters</h2>
    <div class="frm">
      <div class="fg"><label>Total Quantity (Kg)</label>
        <input type="number" id="f-qty" step="0.5" min="0.5" max="120">
        <div class="hint">0.5 – 120.0 Kg</div></div>
      <div class="fg"><label>Feed Per Event (g)</label>
        <input type="number" id="f-fpe" step="5" min="10" max="500">
        <div class="hint">10 – 500 grams</div></div>
      <div class="fg"><label>Feed Duration (Hours)</label>
        <input type="number" id="f-time" min="1" max="12">
        <div class="hint">1 – 12 hours window</div></div>
      <div class="fg"><label>Discharge Rate (g/s)</label>
        <input type="number" id="f-rate" min="1" max="100">
        <div class="hint">1 – 100 grams/sec</div></div>
      <div class="fg"><label>Start Hour</label>
        <input type="number" id="f-shour" min="0" max="23"></div>
      <div class="fg"><label>Start Minute</label>
        <input type="number" id="f-smin" min="0" max="59"></div>
    </div>
    <div class="btn-row">
      <button class="btn btn-save" onclick="saveFeed()">💾 Save Settings</button>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">📊</span> Schedule Preview</h2>
    <div class="st-grid">
      <div class="st-item"><div class="lbl">Total Events</div><div class="val" id="sp-events">--</div></div>
      <div class="st-item"><div class="lbl">Motor/Event</div><div class="val" id="sp-motor">-- s</div></div>
      <div class="st-item"><div class="lbl">Interval</div><div class="val" id="sp-interval">-- min</div></div>
      <div class="st-item"><div class="lbl">Status</div><div class="val" id="sp-status">--</div></div>
    </div>
  </div>
</div>

<!-- ═══ NETWORK TAB ═══ -->
<div class="panel" id="p-network">
  <div class="card">
    <h2><span class="ico">🌐</span> Uplink Mode</h2>
    <div class="frm single">
      <div class="fg"><label>Cloud Communication</label>
        <select id="n-mode">
          <option value="0">Auto Failover (LoRa → WiFi → GSM)</option>
          <option value="1">LoRaWAN Only</option>
          <option value="2">WiFi Only</option>
          <option value="3">GSM Only</option>
        </select></div>
      <div class="fg"><label>Telemetry Interval</label>
        <select id="n-interval">
          <option value="300">5 Minutes</option>
          <option value="900">15 Minutes</option>
          <option value="1800">30 Minutes</option>
          <option value="3600">1 Hour</option>
          <option value="10800" selected>3 Hours (Default)</option>
          <option value="21600">6 Hours</option>
          <option value="43200">12 Hours</option>
          <option value="86400">24 Hours</option>
        </select></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">📻</span> LoRaWAN (IN865)</h2>
    <div class="frm single">
      <div class="fg"><label>Device EUI</label>
        <input type="text" id="n-deveui" maxlength="23" placeholder="00:00:00:00:00:00:00:00"></div>
      <div class="fg"><label>Application EUI</label>
        <input type="text" id="n-appeui" maxlength="23" placeholder="00:00:00:00:00:00:00:00"></div>
      <div class="fg"><label>Application Key</label>
        <input type="text" id="n-appkey" maxlength="47" placeholder="00:00:00:...:00"></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">📶</span> WiFi Station</h2>
    <div class="frm">
      <div class="fg"><label>WiFi SSID</label><input type="text" id="n-wssid" maxlength="32"></div>
      <div class="fg"><label>WiFi Password</label><input type="password" id="n-wpass" maxlength="64"></div>
      <div class="fg"><label>MQTT Server</label><input type="text" id="n-mqsrv" maxlength="64" placeholder="xxxxx.iot.region.amazonaws.com"></div>
      <div class="fg"><label>MQTT Port</label><input type="number" id="n-mqport" value="8883"></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">📱</span> GSM / SIM800L</h2>
    <div class="fg" style="margin-bottom:8px"><label>Quick APN Select</label></div>
    <div class="apn-row">
      <div class="apn-chip" onclick="setAPN('airtelgprs.com')">Airtel</div>
      <div class="apn-chip" onclick="setAPN('jionet')">Jio</div>
      <div class="apn-chip" onclick="setAPN('www')">Vi</div>
      <div class="apn-chip" onclick="setAPN('bsnlnet')">BSNL</div>
    </div>
    <div class="frm">
      <div class="fg"><label>APN</label><input type="text" id="n-apn" maxlength="32"></div>
      <div class="fg"><label>APN User</label><input type="text" id="n-guser" maxlength="16" placeholder="(optional)"></div>
      <div class="fg"><label>APN Password</label><input type="password" id="n-gpass" maxlength="16" placeholder="(optional)"></div>
      <div class="fg"><label>GSM MQTT Server</label><input type="text" id="n-gmqsrv" maxlength="64"></div>
    </div>
    <div class="btn-row">
      <button class="btn btn-save" onclick="saveNetwork()">💾 Save Network Config</button>
    </div>
  </div>
</div>

<!-- ═══ SYSTEM TAB ═══ -->
<div class="panel" id="p-system">
  <div class="card">
    <h2><span class="ico">🔋</span> Power Monitor</h2>
    <div class="st-grid">
      <div class="st-item"><div class="lbl">Bus Voltage</div><div class="val" id="sys-volt">-- V</div></div>
      <div class="st-item"><div class="lbl">Current</div><div class="val" id="sys-curr">-- mA</div></div>
      <div class="st-item"><div class="lbl">Power</div><div class="val" id="sys-pwr">-- mW</div></div>
      <div class="st-item"><div class="lbl">Uptime</div><div class="val" id="sys-up">--</div></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">🩺</span> Hardware Diagnostics (Boot Check)</h2>
    <div class="st-grid">
      <div class="st-item"><div class="lbl">DS3231 RTC</div><div class="val" id="diag-rtc">--</div></div>
      <div class="st-item"><div class="lbl">INA219 Power</div><div class="val" id="diag-pwr">--</div></div>
      <div class="st-item"><div class="lbl">20x4 LCD</div><div class="val" id="diag-lcd">--</div></div>
      <div class="st-item"><div class="lbl">SX1262 LoRa</div><div class="val" id="diag-lora">--</div></div>
      <div class="st-item"><div class="lbl">SIM800L GSM</div><div class="val" id="diag-gsm">--</div></div>
      <div class="st-item"><div class="lbl">MicroSD Card</div><div class="val" id="diag-sd">--</div></div>
      <div class="st-item"><div class="lbl">Push Buttons</div><div class="val" id="diag-btns">--</div></div>
      <div class="st-item"><div class="lbl">Proximity</div><div class="val" id="diag-prox">--</div></div>
      <div class="st-item full"><div class="lbl">I2C Bus Scan</div><div class="val" id="diag-i2c" style="font-size:12px;word-break:break-all">--</div></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">🛠️</span> Device Info</h2>
    <div class="st-grid">
      <div class="st-item"><div class="lbl">Device ID</div><div class="val" id="sys-devid" style="font-size:12px">--</div></div>
      <div class="st-item"><div class="lbl">Firmware</div><div class="val" style="font-size:12px">v4.0.0</div></div>
      <div class="st-item"><div class="lbl">Free Heap</div><div class="val" id="sys-heap">--</div></div>
      <div class="st-item"><div class="lbl">SD Card</div><div class="val" id="sys-sd">--</div></div>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">🧪</span> Hardware Test</h2>
    <div class="btn-row">
      <button class="btn btn-sec" onclick="testRelay(1)">Test Loader</button>
      <button class="btn btn-sec" onclick="testRelay(2)">Test Dispenser</button>
      <button class="btn btn-sec" onclick="testHooter()">Test Hooter</button>
    </div>
  </div>
  <div class="card">
    <h2><span class="ico">⚠️</span> Maintenance</h2>
    <div class="btn-row">
      <button class="btn btn-sec" onclick="if(confirm('Reset all settings?'))resetDevice()">Factory Reset</button>
      <button class="btn btn-stop" onclick="if(confirm('Reboot device?'))rebootDevice()" style="flex:.5">Reboot</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// Tab navigation
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById('p-'+t.dataset.tab).classList.add('active');
  });
});

// Toast
function toast(msg,dur){
  const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),dur||2500);
}

// APN quick select
function setAPN(apn){
  document.getElementById('n-apn').value=apn;
  document.querySelectorAll('.apn-chip').forEach(c=>{
    c.classList.toggle('active',c.textContent.toLowerCase().includes(apn.split('.')[0])||
      (apn==='www'&&c.textContent==='Vi')||(apn==='jionet'&&c.textContent==='Jio'));
  });
}

// Status polling
let pollTimer=null;
function pollStatus(){
  fetch('/api/status').then(r=>r.json()).then(d=>{
    // Clock
    document.getElementById('clock').textContent=d.time||'--:--:--';
    // State badge
    const sb=document.getElementById('state-badge');
    const stMap={0:'INIT',1:'IDLE',2:'AP CONFIG',3:'PRE-WARMUP',4:'DISPENSING',
      5:'POST-CLEAR',6:'WAITING',7:'PAUSED',8:'FINISHED',9:'ERROR'};
    const clMap={0:'b-idle',1:'b-idle',2:'b-idle',3:'b-run',4:'b-run',
      5:'b-run',6:'b-run',7:'b-pause',8:'b-done',9:'b-err'};
    sb.textContent=stMap[d.state]||'UNKNOWN';
    sb.className='badge '+(clMap[d.state]||'b-idle');
    // Events
    document.getElementById('s-event').textContent=(d.currentEvent||0)+' / '+(d.totalEvents||0);
    // Next feed
    document.getElementById('s-next').textContent=d.nextFeed||'--:--';
    // Power
    document.getElementById('s-volt').textContent=(d.voltage!==undefined?d.voltage.toFixed(2)+' V':'-- V');
    document.getElementById('s-curr').textContent=(d.current!==undefined?d.current.toFixed(0)+' mA':'-- mA');
    document.getElementById('sys-volt').textContent=document.getElementById('s-volt').textContent;
    document.getElementById('sys-curr').textContent=document.getElementById('s-curr').textContent;
    document.getElementById('sys-pwr').textContent=(d.power!==undefined?d.power.toFixed(0)+' mW':'-- mW');
    // Progress
    const prog=(d.totalEvents>0)?((d.currentEvent/d.totalEvents)*100):0;
    document.getElementById('s-prog').style.width=prog+'%';
    // Connectivity dots
    function setDot(id,st){
      const dotMap={0:'dot-off',1:'dot-try',2:'dot-ok',3:'dot-err',4:'dot-off'};
      document.getElementById(id).className='conn-dot '+(dotMap[st]||'dot-off');
    }
    setDot('d-lora',d.loraStatus||0);
    setDot('d-wifi',d.wifiStatus||0);
    setDot('d-gsm',d.gsmStatus||0);
    document.getElementById('d-sd').className='conn-dot '+(d.sdOK?'dot-ok':'dot-off');
    // Schedule preview
    document.getElementById('sp-events').textContent=d.totalEvents||'--';
    document.getElementById('sp-motor').textContent=d.motorTimeMs?(d.motorTimeMs/1000).toFixed(1)+' s':'--';
    document.getElementById('sp-interval').textContent=d.intervalMs?(d.intervalMs/60000).toFixed(1)+' min':'--';
    document.getElementById('sp-status').textContent=d.schedValid?'✅ Valid':'❌ '+d.schedError;
    // Feed form (only set once)
    if(!window._feedLoaded&&d.cfg){
      window._feedLoaded=true;
      document.getElementById('f-qty').value=d.cfg.qty;
      document.getElementById('f-fpe').value=d.cfg.fpe;
      document.getElementById('f-time').value=d.cfg.ftime;
      document.getElementById('f-rate').value=d.cfg.rate;
      document.getElementById('f-shour').value=d.cfg.shour;
      document.getElementById('f-smin').value=d.cfg.smin;
      document.getElementById('n-mode').value=d.cfg.uplinkMode||0;
      document.getElementById('n-interval').value=d.cfg.txInterval||10800;
      if(d.cfg.wssid)document.getElementById('n-wssid').value=d.cfg.wssid;
      if(d.cfg.mqsrv)document.getElementById('n-mqsrv').value=d.cfg.mqsrv;
      if(d.cfg.mqport)document.getElementById('n-mqport').value=d.cfg.mqport;
      if(d.cfg.apn)document.getElementById('n-apn').value=d.cfg.apn;
      if(d.cfg.devid)document.getElementById('sys-devid').textContent=d.cfg.devid;
    }
    // System & Diagnostics
    if(d.heap)document.getElementById('sys-heap').textContent=(d.heap/1024).toFixed(0)+' KB';
    document.getElementById('sys-sd').textContent=d.sdOK?'OK':'Not Found';
    if(d.uptime)document.getElementById('sys-up').textContent=fmtUptime(d.uptime);
    if(d.diag){
      document.getElementById('diag-rtc').textContent=d.diag.rtc?'PASS ✅':'FAIL ❌';
      document.getElementById('diag-pwr').textContent=d.diag.power?'PASS ✅':'FAIL ❌';
      document.getElementById('diag-lcd').textContent=d.diag.lcd?'PASS ✅':'Not Found';
      document.getElementById('diag-lora').textContent=d.diag.lora?'PASS ✅':'Not Found';
      document.getElementById('diag-gsm').textContent=d.diag.gsm?('PASS ✅ (CSQ:'+d.diag.csq+')'):'Not Found';
      document.getElementById('diag-sd').textContent=d.diag.sd?'PASS ✅':'Not Found';
      document.getElementById('diag-btns').textContent=(d.diag.sw1&&d.diag.sw2&&d.diag.sw3&&d.diag.sw4)?'PASS ✅':'WARN ⚠️';
      document.getElementById('diag-prox').textContent=d.diag.proxClear?'Clear ✅':'Blocked ⚠️';
      document.getElementById('diag-i2c').textContent=d.diag.i2cCount>0?(d.diag.i2cCount+' active: '+d.diag.i2cAddrs.map(a=>'0x'+a.toString(16).toUpperCase()).join(', ')):'None';
    }
  }).catch(()=>{});
}
function fmtUptime(ms){
  let s=Math.floor(ms/1000),m=Math.floor(s/60),h=Math.floor(m/60),d=Math.floor(h/24);
  if(d>0)return d+'d '+h%24+'h';if(h>0)return h+'h '+m%60+'m';return m+'m '+s%60+'s';
}

// API calls
function saveFeed(){
  const fd=new URLSearchParams();
  fd.append('qty',document.getElementById('f-qty').value);
  fd.append('fpe',document.getElementById('f-fpe').value);
  fd.append('ftime',document.getElementById('f-time').value);
  fd.append('rate',document.getElementById('f-rate').value);
  fd.append('shour',document.getElementById('f-shour').value);
  fd.append('smin',document.getElementById('f-smin').value);
  fetch('/api/settings',{method:'POST',body:fd}).then(r=>r.json())
    .then(d=>{toast(d.ok?'✅ Settings saved!':'❌ '+d.error)}).catch(()=>toast('❌ Connection error'));
}
function saveNetwork(){
  const fd=new URLSearchParams();
  fd.append('mode',document.getElementById('n-mode').value);
  fd.append('interval',document.getElementById('n-interval').value);
  fd.append('deveui',document.getElementById('n-deveui').value);
  fd.append('appeui',document.getElementById('n-appeui').value);
  fd.append('appkey',document.getElementById('n-appkey').value);
  fd.append('wssid',document.getElementById('n-wssid').value);
  fd.append('wpass',document.getElementById('n-wpass').value);
  fd.append('mqsrv',document.getElementById('n-mqsrv').value);
  fd.append('mqport',document.getElementById('n-mqport').value);
  fd.append('apn',document.getElementById('n-apn').value);
  fd.append('guser',document.getElementById('n-guser').value);
  fd.append('gpass',document.getElementById('n-gpass').value);
  fd.append('gmqsrv',document.getElementById('n-gmqsrv').value);
  fetch('/api/network',{method:'POST',body:fd}).then(r=>r.json())
    .then(d=>{toast(d.ok?'✅ Network config saved!':'❌ '+d.error)}).catch(()=>toast('❌ Connection error'));
}
function doStart(){fetch('/api/start',{method:'POST'}).then(r=>r.json())
  .then(d=>{toast(d.ok?'✅ Feed started!':'❌ '+d.error)}).catch(()=>toast('❌ Error'));}
function doStop(){fetch('/api/stop',{method:'POST'}).then(r=>r.json())
  .then(d=>{toast(d.ok?'⏹ Stopped!':'❌ '+d.error)}).catch(()=>toast('❌ Error'));}
function testRelay(r){fetch('/api/test?relay='+r,{method:'POST'}).then(()=>toast('🔧 Testing relay '+r+'...')).catch(()=>toast('❌ Error'));}
function testHooter(){fetch('/api/test?hooter=1',{method:'POST'}).then(()=>toast('🔊 Hooter test...')).catch(()=>toast('❌ Error'));}
function rebootDevice(){fetch('/api/reboot',{method:'POST'}).then(()=>toast('🔄 Rebooting...')).catch(()=>{});}
function resetDevice(){fetch('/api/reset',{method:'POST'}).then(()=>toast('⚠️ Factory reset... Rebooting.')).catch(()=>{});}

// Start polling
pollStatus();
pollTimer=setInterval(pollStatus,2000);
</script>
</body></html>
)rawliteral";
