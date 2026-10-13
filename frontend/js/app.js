import {lineChart, trafficChart} from "./chart.js";
const routes = ['overview', 'system', 'network', 'wifi', 'security', 'privacy', 'optimizer', 'alerts', 'learn', 'settings'];
const icons = ['◉', '▥', '⌁', '◔', '⬡', '◇', '◈', '▤', '?', '⚙'];
const $ = id => document.getElementById(id);
const state = {lang: localStorage.getItem('gb-lang') || 'uz', dict: {}, data: null, boot: null, capabilities: null, history: [], historyAt: 0, historyWindow: "1h", posture: null, processes: null, processesAt: 0, processSort: "top_memory", network: null, networkAt: 0, trafficHistory: [], showAllConnections: false, publicIp: null, publicIpError: null, speedResult: null, speedError: null, latencyResult: null, wifi: null, wifiAt: 0, wifiError: null, rooms: null, roomError: null, devices: null, devicesError: null, integrityResult: null, integrityError: null, projectPath: "", secretResult: null, avJob: null, avError: null, firewall: null, privacy: null, alerts: null, alertsAt: 0};
state.helpTopics = [];
state.settings = null;
state.settingsError = null;
state.optimizer = null;
state.hardening = null;
const text = key => state.dict[key] || key;

function el(tag, className = '', content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}
function route() {
  const current = location.hash.replace(/^#\/?/, '');
  return routes.includes(current) ? current : 'overview';
}
function metric(label, value, detail, target) {
  const card = el('a', 'card metric-card');
  card.href = `#/${target}`;
  card.append(el('h2', '', label), el('div', 'metric', value), el('div', 'sub', detail));
  return card;
}
function renderRadar() {
  const hero = el('div', 'hero');
  const radarCard = el('div', 'card radar-card');
  const radar = el('div', 'radar');
  const center = el('div', 'radar-center');
  center.append(el('small', '', text('securityScore')), el('strong', '', text('unknown')), el('small', '', text('checkCategories')));
  radar.append(center);
  radarCard.append(radar);
  const recommendations = el('div', 'card');
  recommendations.append(el('div', 'eyebrow', text('securityPosture')), el('h2', '', text('recommendation')));
  const list = el('div', 'recommendations');
  list.append(el('div', '', text('noEvidence')));
  recommendations.append(list);
  const categories = state.posture?.posture?.categories || {};
  const categoryList = el('div', 'category-list');
  for (const [name, item] of Object.entries(categories)) {
    const link = el('a', 'category-row');
    link.href = name === 'privacy' ? '#/privacy' : '#/security';
    link.append(el('span', '', text(name)), el('span', `status-${item.status}`, item.status === 'partial' ? text('partial') : text('unknownShort')));
    categoryList.append(link);
  }
  if (categoryList.children.length) recommendations.append(categoryList);
  hero.append(radarCard, recommendations);
  return hero;
}
function renderTools() {
  const section = el('section', 'card tools-section');
  section.append(el('h2', '', text('toolInventory')));
  const grid = el('div', 'grid');
  if (state.capabilities) {
    for (const [name, item] of Object.entries(state.capabilities.tools)) {
      const status = item.available ? text('available') : text('unavailable');
      const target = name === 'wifi' ? 'wifi' : ['smart','amd_gpu'].includes(name) ? 'system' : 'security';
      grid.append(metric(name.replaceAll('_', ' ').toUpperCase(), status, text(item.package_state), target));
    }
  } else grid.append(el('p', 'sub', text('loading')));
  section.append(grid);
  return section;
}
function readableBytes(bytes) {
  if (typeof bytes !== 'number') return text('notAvailable');
  return `${(bytes / 1073741824).toFixed(1)} GiB`;
}
function renderSystem() {
  const readings = state.data?.readings || {};
  const grid = el('div', 'grid');
  const fields = [
    [text('cpuTemperature'), 'cpu_temperature', '°C'],
    [text('gpuTemperature'), 'gpu_temperature', '°C'],
    [text('cpuFrequency'), 'cpu_frequency', 'MHz'],
    [text('gpuUsage'), 'gpu', '%'],
    [text('battery'), 'battery', '%'],
    [text('uptime'), 'uptime_seconds', ''],
  ];
  for (const [label, key, suffix] of fields) {
    const reading = readings[key];
    let value = reading?.value;
    if (key === 'gpu') value = value?.usage_percent;
    if (key === 'battery') value = value?.percent;
    if (key === 'uptime_seconds' && typeof value === 'number') value = `${Math.floor(value / 3600)} h`;
    else if (typeof value === 'number') value = `${value.toFixed(1)} ${suffix}`.trim();
    grid.append(metric(label, value ?? text('notAvailable'), reading?.reason || text('liveMeasurement'), 'system'));
  }
  const gpu = readings.gpu?.value;
  const battery = readings.battery?.value;
  const extras = el('div', 'grid');
  extras.append(metric(text('gpuVram'), gpu?.vram_total_bytes != null ? `${readableBytes(gpu.vram_used_bytes)} / ${readableBytes(gpu.vram_total_bytes)}` : text('notAvailable'), gpu?.vendor || '—', 'system'));
  extras.append(metric(text('gpuPower'), gpu?.power_watts != null ? `${gpu.power_watts.toFixed(1)} W` : text('notAvailable'), gpu?.vendor || '—', 'system'));
  extras.append(metric(text('batteryHealth'), battery?.health_percent != null ? `${battery.health_percent.toFixed(1)}%` : text('notAvailable'), text('sensorEstimate'), 'system'));
  const fans = readings.fans?.value;
  extras.append(metric(text('fanSpeed'), fans?.length ? `${fans[0].rpm} RPM` : text('notAvailable'), fans?.[0]?.label || '—', 'system'));
  const diskIo = readings.disk_io?.value;
  extras.append(metric(text('diskRead'), diskIo ? `${(diskIo.read_bytes_per_second / 1048576).toFixed(2)} MiB/s` : text('notAvailable'), text('liveMeasurement'), 'system'));
  extras.append(metric(text('diskWrite'), diskIo ? `${(diskIo.write_bytes_per_second / 1048576).toFixed(2)} MiB/s` : text('notAvailable'), text('liveMeasurement'), 'system'));
  const perCore = readings.per_core?.value;
  const coreSection = el('section', 'card system-section');
  coreSection.append(el('h2', '', text('perCore')));
  if (Array.isArray(perCore)) {
    const heatmap = el('div', 'heatmap');
    const frequencies = readings.per_core_frequency?.value || [];
    perCore.forEach((value, index) => {
      const cell = el('div', 'core-cell');
      cell.style.setProperty('--intensity', Math.max(.08, Math.min(1, value / 100)));
      cell.append(el('small', '', `CPU ${index + 1}`), el('strong', '', `${value.toFixed(0)}%`));
      if (typeof frequencies[index] === 'number') cell.append(el('small', '', `${frequencies[index].toFixed(0)} MHz`));
      heatmap.append(cell);
    });
    coreSection.append(heatmap);
  } else coreSection.append(el('p', 'sub', text('notAvailable')));
  const memory = readings.memory_detail?.value;
  const disk = readings.disk_detail?.value;
  const detail = el('section', 'card system-section');
  detail.append(el('h2', '', text('capacity')));
  detail.append(el('p', 'sub', `${text('memory')}: ${memory ? `${readableBytes(memory.used)} / ${readableBytes(memory.total)}` : text('notAvailable')}`));
  detail.append(el('p', 'sub', `${text('swap')}: ${memory ? `${readableBytes(memory.swap_used)} / ${readableBytes(memory.swap_total)}` : text('notAvailable')}`));
  detail.append(el('p', 'sub', `${text('disk')}: ${disk ? `${readableBytes(disk.used)} / ${readableBytes(disk.total)}` : text('notAvailable')}`));
  const history = el('section', 'card system-section');
  history.append(el('h2', '', text('cpuHistory')));
  const select = el('select');
  select.setAttribute('aria-label', text('historyWindow'));
  for (const window of ['1h', '24h']) {
    const option = el('option', '', window);
    option.value = window;
    option.selected = window === state.historyWindow;
    select.append(option);
  }
  select.addEventListener('change', () => {state.historyWindow = select.value;state.historyAt = 0;loadHistory();});
  history.append(select);
  if (state.history.length) history.append(lineChart(state.history, 'cpu', text('cpuHistory')));
  else history.append(el('p', 'sub', text('noHistory')));
  const processSection = el('section', 'card system-section');
  processSection.append(el('h2', '', text('processes')));
  const controls = el('div', 'process-controls');
  for (const [key, label] of [['top_memory', text('byMemory')], ['top_cpu', text('byCpu')], ['top_disk', text('byDisk')]]) {
    const button = el('button', key === state.processSort ? 'selected' : '', label);
    button.type = 'button';
    button.addEventListener('click', () => {state.processSort = key;render();});
    controls.append(button);
  }
  processSection.append(controls);
  const rows = state.processes?.data?.[state.processSort] || [];
  if (rows.length) {
    const table = el('table', 'process-table');
    const head = el('thead');
    const headerRow = el('tr');
    for (const label of [text('process'), 'PID', text('usage')]) headerRow.append(el('th', '', label));
    head.append(headerRow);
    const body = el('tbody');
    for (const row of rows) {
      const tr = el('tr');
      const raw = state.processSort === 'top_memory' ? row.memory_bytes : state.processSort === 'top_cpu' ? row.cpu_percent : row.disk_bytes_per_second;
      const value = state.processSort === 'top_memory' ? readableBytes(raw) : state.processSort === 'top_cpu' ? `${raw.toFixed(1)}%` : `${(raw / 1048576).toFixed(2)} MiB/s`;
      for (const cell of [row.name, String(row.pid), value]) tr.append(el('td', '', cell));
      body.append(tr);
    }
    table.append(head, body);
    processSection.append(table);
  } else processSection.append(el('p', 'sub', text('ratePending')));
  processSection.append(el('p', 'sub', text('processCaution')));
  return [grid, extras, coreSection, detail, history, processSection];
}
async function loadProcesses() {
  if (state.boot?.demo) return;
  try {
    const response = await fetch('/api/processes', {cache: 'no-store'});
    if (response.ok) {state.processes = await response.json();state.processesAt = Date.now();}
  } catch {state.processes = null;}
  render();
}
async function loadHistory() {
  if (state.boot?.demo) {state.history = [];render();return;}
  try {
    const response = await fetch(`/api/history?window=${state.historyWindow}`, {cache: 'no-store'});
    if (!response.ok) throw new Error('History unavailable');
    const body = await response.json();
    state.history = body.samples;
    state.historyAt = Date.now();
  } catch {state.history = [];}
  render();
}
function rate(value) {
  return typeof value === 'number' ? `${(value / 1048576).toFixed(2)} MiB/s` : text('notAvailable');
}
function renderNetwork() {
  const root = document.createDocumentFragment();
  const info = state.network?.data;
  const interfaces = info?.traffic?.interfaces || [];
  const connected = interfaces.filter(item => item.up && item.name !== 'lo');
  const down = connected.reduce((sum, item) => sum + (item.download_bytes_per_second || 0), 0);
  const up = connected.reduce((sum, item) => sum + (item.upload_bytes_per_second || 0), 0);
  const ratesKnown = connected.some(item => item.download_bytes_per_second !== null);
  const grid = el('div', 'grid');
  grid.append(metric(text('download'), ratesKnown ? rate(down) : text('notAvailable'), text('liveMeasurement'), 'network'));
  grid.append(metric(text('upload'), ratesKnown ? rate(up) : text('notAvailable'), text('liveMeasurement'), 'network'));
  grid.append(metric(text('gateway'), info?.default_gateway || text('notAvailable'), text('localNetwork'), 'network'));
  root.append(grid);
  const totals = el('div', 'grid');
  totals.append(metric(text('totalReceived'), connected.length ? readableBytes(connected.reduce((sum,item)=>sum+item.received_bytes,0)) : text('notAvailable'), text('sinceBoot'), 'network'));
  totals.append(metric(text('totalSent'), connected.length ? readableBytes(connected.reduce((sum,item)=>sum+item.sent_bytes,0)) : text('notAvailable'), text('sinceBoot'), 'network'));
  root.append(totals);
  const chart = el('section', 'card system-section');
  chart.append(el('h2', '', text('trafficHistory')));
  if (state.trafficHistory.length > 1) chart.append(trafficChart(state.trafficHistory, text('trafficHistory')));
  else chart.append(el('p', 'sub', text('ratePending')));
  root.append(chart);
  const networkInfo = el('section', 'card system-section');
  networkInfo.append(el('h2', '', text('interfaces')));
  if (interfaces.length) {
    for (const item of interfaces) {
      const row = el('div', 'interface-row');
      row.append(el('strong', '', item.name), el('span', '', item.up ? text('connected') : text('disconnected')));
      row.append(el('small', '', item.addresses.join(', ') || text('notAvailable')));
      row.append(el('small', '', `${text('download')}: ${rate(item.download_bytes_per_second)} · ${text('upload')}: ${rate(item.upload_bytes_per_second)}`));
      networkInfo.append(row);
    }
  } else networkInfo.append(el('p', 'sub', text('notAvailable')));
  root.append(networkInfo);
  const dns = el('section', 'card system-section');
  dns.append(el('h2', '', text('dnsServers')), el('p', 'sub', info?.dns_servers?.join(', ') || text('notAvailable')));
  root.append(dns);
  const external = el('section', 'card system-section');
  external.append(el('h2', '', text('publicIp')));
  external.append(el('p', 'sub', text('publicIpDisclosure')));
  const check = el('button', '', text('checkNow'));
  check.type = 'button';
  check.addEventListener('click', async () => {
    if (!window.confirm(text('publicIpConfirm'))) return;
    check.disabled = true;
    try {
      const response = await fetch('/api/network/public-ip', {method: 'POST', headers: {'x-csrf-token': state.boot.csrf}});
      if (!response.ok) throw new Error('Request failed');
      const result = await response.json();
      state.publicIp = result.ip;state.publicIpError = null;
    } catch {state.publicIpError = text('externalRequestFailed');}
    render();
  });
  external.append(check);
  if (state.publicIp) external.append(el('p', 'public-ip-value', state.publicIp));
  if (state.publicIpError) external.append(el('p', 'sub', state.publicIpError));
  root.append(external);
  const speed = el('section', 'card system-section');
  speed.append(el('h2', '', text('speedSample')));
  speed.append(el('p', 'sub', text('speedDisclosure')));
  const speedButton = el('button', '', text('runSample'));
  speedButton.type = 'button';
  speedButton.addEventListener('click', async () => {
    if (!window.confirm(text('speedConfirm'))) return;
    speedButton.disabled = true;
    try {
      const response = await fetch('/api/network/download-sample', {method: 'POST', headers: {'x-csrf-token': state.boot.csrf}});
      if (!response.ok) throw new Error('Sample failed');
      state.speedResult = (await response.json()).result;state.speedError = null;
    } catch {state.speedError = text('externalRequestFailed');}
    render();
  });
  speed.append(speedButton);
  if (state.speedResult) speed.append(el('p', 'public-ip-value', `${state.speedResult.download_mbps} Mbps`));
  if (state.speedError) speed.append(el('p', 'sub', state.speedError));
  root.append(speed);
  const latency = el('section', 'card system-section');
  latency.append(el('h2', '', text('latencySample')));
  latency.append(el('p', 'sub', text('latencyDisclosure')));
  const latencyButton = el('button', '', text('runLatency'));latencyButton.type='button';
  latencyButton.addEventListener('click', async () => {
    if (!window.confirm(text('latencyConfirm'))) return;
    latencyButton.disabled = true;
    try {const response=await fetch('/api/network/latency-sample',{method:'POST',headers:{'x-csrf-token':state.boot.csrf}});if(!response.ok)throw new Error('Probe failed');state.latencyResult=(await response.json()).result;state.latencyError=null;}
    catch {state.latencyError=text('externalRequestFailed');}
    render();
  });
  latency.append(latencyButton);
  if(state.latencyResult){const result=state.latencyResult;latency.append(el('p','sub',`${text('meanLatency')}: ${result.mean_ms??text('notAvailable')} ms · ${text('jitter')}: ${result.jitter_ms??text('notAvailable')} ms · ${text('failedProbes')}: ${result.failed_probes}/${result.total_probes}`));}
  if(state.latencyError) latency.append(el('p','sub',state.latencyError));
  root.append(latency);
  for (const [key, title] of [['listening', text('listeningPorts')], ['active', text('activeConnections')]]) {
    const section = el('section', 'card system-section');
    section.append(el('h2', '', title));
    const rows = info?.connections?.[key] || [];
    if (rows.length) {
      const table = el('table', 'process-table');
      const head = el('thead'), header = el('tr');
      for (const label of [text('localAddress'), text('remoteAddress'), 'PID']) header.append(el('th', '', label));
      head.append(header);
      const body = el('tbody');
      for (const item of rows.slice(0, state.showAllConnections ? 50 : 10)) {
        const tr = el('tr');
        for (const value of [item.local || '—', item.remote || '—', item.pid == null ? '—' : String(item.pid)]) tr.append(el('td', '', value));
        body.append(tr);
      }
      table.append(head, body);section.append(table);
      if (rows.length > 10) {const more = el('button', 'show-more', state.showAllConnections ? text('showLess') : text('showMore'));more.type='button';more.addEventListener('click',()=>{state.showAllConnections=!state.showAllConnections;render();});section.append(more);}
    } else section.append(el('p', 'sub', text('noConnections')));
    root.append(section);
  }
  return root;
}
async function loadNetwork() {
  if (state.boot?.demo) {state.network = {data: null};render();return;}
  try {
    const response = await fetch('/api/network', {cache: 'no-store'});
    if (!response.ok) throw new Error('Network unavailable');
    state.network = await response.json();
    state.networkAt = Date.now();
    const interfaces = state.network.data.traffic.interfaces.filter(item => item.up && item.name !== 'lo');
    const known = interfaces.some(item => item.download_bytes_per_second !== null);
    if (known) {
      state.trafficHistory.push({time: Date.now(), down: interfaces.reduce((sum, item) => sum + (item.download_bytes_per_second || 0), 0), up: interfaces.reduce((sum, item) => sum + (item.upload_bytes_per_second || 0), 0)});
      state.trafficHistory = state.trafficHistory.slice(-60);
    }
  } catch {state.network = null;}
  render();
}
function renderWifi() {
  const root = document.createDocumentFragment();
  const info = state.wifi?.data;
  const adapter = info?.adapter;
  const grid = el('div', 'grid');
  grid.append(metric(text('wifiAdapter'), adapter?.name || text('notAvailable'), adapter?.driver || '—', 'wifi'));
  grid.append(metric(text('signalStrength'), adapter?.rssi_dbm != null ? `${adapter.rssi_dbm} dBm` : text('notAvailable'), text('relativeSignal'), 'wifi'));
  grid.append(metric(text('linkSpeed'), adapter?.tx_mbps != null ? `${adapter.tx_mbps} Mbps` : text('notAvailable'), text('liveMeasurement'), 'wifi'));
  root.append(grid);
  const hardware = el('section', 'card system-section');
  hardware.append(el('h2', '', text('adapterCapabilities')));
  hardware.append(el('p','sub',`${text('chipset')}: ${adapter?.chipset || text('notAvailable')}`));
  hardware.append(el('p','sub',`${text('driver')}: ${adapter?.driver || text('notAvailable')} · ${text('regulatoryCountry')}: ${adapter?.regulatory_country || text('notAvailable')}`));
  if (adapter?.standards) {
    const standards = el('div','standard-list');
    for (const [key,label] of [['wifi4','Wi-Fi 4'],['wifi5','Wi-Fi 5'],['wifi6','Wi-Fi 6'],['wifi6e','Wi-Fi 6E'],['wifi7','Wi-Fi 7']]) {
      standards.append(el('span',adapter.standards[key]?'standard-yes':'standard-no',`${label}: ${adapter.standards[key]?text('available'):text('notAvailable')}`));
    }
    hardware.append(standards,el('p','sub',`${text('enabledBands')}: ${adapter.standards.bands.join(', ') || text('notAvailable')}`));
  }
  root.append(hardware);
  const section = el('section', 'card system-section');
  section.append(el('h2', '', text('nearbyNetworks')));
  section.append(el('p', 'sub', text('wifiCaution')));
  const scan = el('button', '', text('scanWifi'));scan.type='button';
  scan.addEventListener('click', async () => {
    scan.disabled = true;state.wifiError=null;
    try {const response=await fetch('/api/wifi/scan',{method:'POST',headers:{'x-csrf-token':state.boot.csrf}});if(!response.ok)throw new Error(String(response.status));state.wifi=await response.json();state.wifiAt=Date.now();}
    catch {state.wifiError=text('wifiScanFailed');}
    render();
  });
  section.append(scan);
  if (state.wifiError) section.append(el('p', 'sub', state.wifiError));
  const networks = [...(info?.networks || [])].sort((a,b)=>b.signal_percent-a.signal_percent);
  if (networks.length) {
    const list = el('div', 'wifi-list');
    for (const network of networks) {
      const row = el('div', 'wifi-row');
      const name = network.ssid || text('hiddenSsid');
      row.append(el('strong', '', name), el('span', '', `${network.signal_percent}%`));
      const detail = el('small', '', `${network.band} · ${text('channel')} ${network.channel} · ${network.security || text('openNetwork')}`);
      row.append(detail);
      const bar = el('div', 'signal-track');const fill=el('div','signal-fill');fill.style.width=`${network.signal_percent}%`;bar.append(fill);row.append(bar);
      if (network.open) row.append(el('small', 'warning-text', text('openWarning')));
      list.append(row);
    }
    section.append(list);
    const counts = new Map();
    for (const network of networks) counts.set(network.channel, (counts.get(network.channel)||0)+1);
    const channels = el('div', 'channel-grid');
    for (const [channel,count] of [...counts].sort((a,b)=>a[0]-b[0])) channels.append(el('div','channel-cell',`${text('channel')} ${channel}: ${count}`));
    section.append(el('h3', '', text('channelUse')), channels);
    if (networks.some(network=>network.band==='2.4 GHz')) {
      const candidate=[1,6,11].map(channel=>({channel,load:networks.filter(network=>network.band==='2.4 GHz'&&Math.abs(network.channel-channel)<3).reduce((sum,network)=>sum+network.signal_percent,0)})).sort((a,b)=>a.load-b.load)[0];
      section.append(el('p','sub',`${text('channelSuggestion')} ${candidate.channel}. ${text('channelCaution')}`));
    }
  } else section.append(el('p', 'sub', text('noWifiResults')));
  root.append(section);
  root.append(el('p','sub wifi-education',text('wifiEducation')));
  const walk = el('section','card system-section');
  walk.append(el('h2','',text('roomWalkTest')));
  walk.append(el('p','sub',text('roomWalkHelp')));
  const form=el('form','room-form');
  const input=el('input');input.name='room';input.maxLength=80;input.required=true;input.placeholder=text('roomName');input.setAttribute('aria-label',text('roomName'));
  const save=el('button','',text('recordSignal'));save.type='submit';
  form.append(input,save);
  form.addEventListener('submit',async event=>{
    event.preventDefault();save.disabled=true;
    try {const response=await fetch('/api/wifi/rooms',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({room:input.value})});if(!response.ok)throw new Error('Save failed');state.rooms=(await response.json()).samples;state.roomError=null;}
    catch {state.roomError=text('roomSaveFailed');}
    render();
  });
  walk.append(form);
  if(state.roomError) walk.append(el('p','sub',state.roomError));
  if(state.rooms?.length){
    const table=el('table','process-table');const head=el('thead'),header=el('tr');
    for(const label of [text('roomName'),text('signalStrength'),text('attenuation'),text('time')]) header.append(el('th','',label));
    head.append(header);const body=el('tbody');
    for(const row of state.rooms){const tr=el('tr');for(const value of [row.room,`${row.rssi_dbm} dBm`,`${row.relative_attenuation_db} dB`,new Date(row.timestamp*1000).toLocaleTimeString()])tr.append(el('td','',value));body.append(tr);}
    table.append(head,body);walk.append(table);
  }else walk.append(el('p','sub',text('noRoomSamples')));
  root.append(walk);
  const inventory=el('section','card system-section');
  inventory.append(el('h2','',text('localDevices')));
  inventory.append(el('p','sub',text('inventoryDisclosure')));
  const ownership=el('label','ownership-label');const checkbox=el('input');checkbox.type='checkbox';
  ownership.append(checkbox,el('span','',text('confirmOwnership')));inventory.append(ownership);
  const inventoryButton=el('button','',text('showDevices'));inventoryButton.type='button';inventoryButton.disabled=true;
  checkbox.addEventListener('change',()=>{inventoryButton.disabled=!checkbox.checked;});
  inventoryButton.addEventListener('click',async()=>{
    inventoryButton.disabled=true;
    try{const response=await fetch('/api/wifi/devices',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({confirmed_ownership:true})});if(!response.ok)throw new Error('Inventory failed');state.devices=(await response.json()).data;state.devicesError=null;}
    catch{state.devicesError=text('inventoryFailed');}
    render();
  });inventory.append(inventoryButton);
  if(state.devicesError)inventory.append(el('p','sub',state.devicesError));
  if(state.devices){
    inventory.append(el('p','sub',`${text('subnet')}: ${state.devices.subnet}`));
    if(!state.devices.devices.length)inventory.append(el('p','sub',text('noDevices')));
    for(const device of state.devices.devices){
      const row=el('div','device-row');
      row.append(el('strong','',device.ip),el('span','',device.newly_observed?text('newlyObserved'):device.trusted?text('trusted'):text('known')));
      row.append(el('small','',device.mac));
      const trust=el('button','',device.trusted?text('removeTrust'):text('markTrusted'));trust.type='button';
      trust.addEventListener('click',async()=>{
        trust.disabled=true;
        try{const response=await fetch('/api/wifi/devices/trust',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({mac:device.mac,trusted:!device.trusted})});if(!response.ok)throw new Error('Trust failed');device.trusted=!device.trusted;device.newly_observed=false;state.devicesError=null;}
        catch{state.devicesError=text('inventoryFailed');}
        render();
      });row.append(trust);inventory.append(row);
    }
  }
  root.append(inventory);
  return root;
}
async function loadRooms(){
  if(state.boot?.demo){state.rooms=[];return;}
  try{const response=await fetch('/api/wifi/rooms');if(response.ok)state.rooms=(await response.json()).samples;}
  catch {state.rooms=null;}
  render();
}
async function loadWifi() {
  if (state.boot?.demo) {state.wifi={data:null};render();return;}
  try {const response=await fetch('/api/wifi',{cache:'no-store'});if(!response.ok)throw new Error('Wi-Fi unavailable');state.wifi=await response.json();state.wifiAt=Date.now();}
  catch {state.wifi=null;}
  render();
}
function renderProjectProtection() {
  const section=el('section','card system-section');
  section.append(el('h2','',text('projectProtection')));
  section.append(el('p','sub',text('projectProtectionInfo')));
  const input=el('input');input.type='text';input.placeholder=text('projectPath');input.setAttribute('aria-label',text('projectPath'));input.className='project-input';input.value=state.projectPath;input.addEventListener('input',()=>{state.projectPath=input.value;});
  section.append(input);
  const controls=el('div','process-controls');
  for(const [action,label] of [['baseline',text('createBaseline')],['check',text('checkIntegrity')],['secrets',text('scanSecrets')]]){
    const button=el('button','',label);button.type='button';
    button.addEventListener('click',async()=>{
      const path=input.value.trim();
      if(!path){state.integrityError=text('projectPathRequired');render();return;}
      if(!window.confirm(`${text('projectConfirm')} ${path}`))return;
      button.disabled=true;
      try{const response=await fetch(`/api/projects/${action}`,{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({path,confirmed:true})});if(!response.ok)throw new Error(String(response.status));const result=await response.json();if(action==='secrets')state.secretResult=result;else state.integrityResult=result;state.integrityError=null;}
      catch{state.integrityError=text('projectScanFailed');}
      render();
    });controls.append(button);
  }
  section.append(controls);
  if(state.integrityError)section.append(el('p','sub',state.integrityError));
  if(state.integrityResult){
    const result=state.integrityResult;
    if(typeof result.files==='number')section.append(el('p','sub',`${text('baselineFiles')}: ${result.files}`));
    if(result.result){for(const key of ['new','modified','deleted']){
      const group=el('div','integrity-group');group.append(el('strong','',`${text(key)} (${result.result[key].length})`));
      for(const name of result.result[key])group.append(el('div','sub',name));
      section.append(group);
    }}
  }
  if(state.secretResult?.result){
    const result=state.secretResult.result;
    section.append(el('p','sub',`${text('checkedFiles')}: ${result.checked_files} · ${text('findings')}: ${result.findings.length}`));
    for(const item of result.findings)section.append(el('div','integrity-group',`${item.path}${item.line ? `:${item.line}` : ''} · ${text(`secret_${item.kind}`)}`));
    if(result.truncated)section.append(el('p','sub',text('findingsTruncated')));
  }
  return section;
}
function renderAntivirus() {
  const section=el('section','card system-section');
  section.append(el('h2','',text('antivirusScan')));
  section.append(el('p','sub',text('antivirusInfo')));
  const controls=el('div','process-controls');
  const start=el('button','',text('startAntivirus'));start.type='button';
  start.disabled=state.boot?.demo || ['queued','running'].includes(state.avJob?.status);
  start.addEventListener('click',async()=>{
    const path=state.projectPath.trim();
    if(!path){state.avError=text('projectPathRequired');render();return;}
    if(!window.confirm(`${text('antivirusConfirm')} ${path}`))return;
    start.disabled=true;
    try{const response=await fetch('/api/av/scans',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({path,confirmed:true})});if(!response.ok)throw new Error(String(response.status));state.avJob=await response.json();state.avError=null;}
    catch{state.avError=text('antivirusFailed');}
    render();
  });controls.append(start);
  if(['queued','running'].includes(state.avJob?.status)){
    const cancel=el('button','',text('cancelScan'));cancel.type='button';
    cancel.addEventListener('click',async()=>{
      cancel.disabled=true;
      try{const response=await fetch(`/api/av/scans/${encodeURIComponent(state.avJob.id)}/cancel`,{method:'POST',headers:{'x-csrf-token':state.boot.csrf}});if(!response.ok)throw new Error(String(response.status));state.avJob=await response.json();state.avError=null;}
      catch{state.avError=text('antivirusFailed');}
      render();
    });controls.append(cancel);
  }
  section.append(controls);
  if(state.avError)section.append(el('p','sub',state.avError));
  if(state.avJob){
    section.append(el('p','sub',`${text('scanStatus')}: ${text(`scan_${state.avJob.status}`)}`));
    if(state.avJob.error)section.append(el('p','sub',state.avJob.error));
    if(state.avJob.status==='completed')section.append(el('p','sub',`${text('findings')}: ${state.avJob.findings.length}`));
    for(const finding of state.avJob.findings)section.append(el('div','integrity-group',finding));
  }
  return section;
}
function renderFirewall(){
  const section=el('section','card system-section');
  section.append(el('h2','',text('firewallStatus')));
  const data=state.firewall?.data;
  if(!data){section.append(el('p','sub',text(state.boot?.demo?'demoUnavailable':'loading')));return section;}
  section.append(el('p','sub',`${text('firewallManager')}: ${data.manager || text('notAvailable')}`));
  section.append(el('p','sub',`${text('firewallState')}: ${text(`firewall_${data.state}`)}`));
  if(data.defaults)section.append(el('p','sub',`${text('firewallDefaults')}: ${data.defaults}`));
  if(data.reason)section.append(el('p','sub',text(data.reason)));
  for(const rule of data.rules)section.append(el('div','integrity-group',rule));
  return section;
}
function renderHardening(){
  const section=el('section','card system-section');section.append(el('h2','',text('hardeningChecks')));
  const data=state.hardening?.data;
  if(!data){section.append(el('p','sub',text(state.boot?.demo?'demoUnavailable':'loading')));return section;}
  for(const [key,item] of Object.entries(data)){
    const row=el('div','integrity-group');
    row.append(el('strong','',`${text(`hardening_${key}`)} · ${text(`hardening_status_${item.status}`)}`));
    row.append(el('div','sub',text(item.evidence)));
    if(key==='ssh' && item.status==='observed')row.append(el('div','sub',`PermitRootLogin: ${item.permit_root_login ?? text('notAvailable')} · PasswordAuthentication: ${item.password_authentication ?? text('notAvailable')}`));
    section.append(row);
  }
  return section;
}
async function loadHardening(){
  try{const response=await fetch('/api/security/hardening',{cache:'no-store'});if(response.ok)state.hardening=await response.json();}
  catch{state.hardening=null;}
  if(route()==='security')render();
}
async function loadFirewall(){
  try{const response=await fetch('/api/security/firewall',{cache:'no-store'});if(response.ok)state.firewall=await response.json();}
  catch{state.firewall=null;}
  if(route()==='security')render();
}
function renderPrivacy(){
  const root=el('div');
  const notice=el('section','card system-section');notice.append(el('h2','',text('privacyNoticeTitle')),el('p','sub',text('privacyNotice')));root.append(notice);
  const data=state.privacy?.data;
  const vpn=el('section','card system-section');vpn.append(el('h2','',text('vpnStatus')));
  vpn.append(el('p','sub',data ? text(`vpn_${data.vpn.state}`) : text(state.boot?.demo?'demoUnavailable':'loading')));
  if(data?.vpn.reason)vpn.append(el('p','sub',text(data.vpn.reason)));
  for(const connection of data?.vpn.connections || [])vpn.append(el('div','integrity-group',`${connection.name} · ${connection.type} · ${connection.device}`));
  root.append(vpn);
  const dns=el('section','card system-section');dns.append(el('h2','',text('dnsServers')),el('p','sub',data?.dns_servers?.join(', ') || text('notAvailable')),el('p','sub',text('dnsLeakNotRun')));root.append(dns);
  const external=el('section','card system-section');external.append(el('h2','',text('publicIp')),el('p','sub',text('privacyPublicIp')));
  const link=el('a','category-row',text('openNetworkChecks'));link.href='#/network';external.append(link);root.append(external);
  return root;
}
async function loadPrivacy(){
  try{const response=await fetch('/api/privacy',{cache:'no-store'});if(response.ok)state.privacy=await response.json();}
  catch{state.privacy=null;}
  if(route()==='privacy')render();
}
function renderAlerts(){
  const section=el('section','card system-section');section.append(el('h2','',text('incidentTimeline')));
  section.append(el('p','sub',text('alertScope')));
  if(!state.alerts){section.append(el('p','sub',text('loading')));return section;}
  if(!state.alerts.events.length){section.append(el('p','sub',text('noAlerts')));return section;}
  for(const event of state.alerts.events){
    const row=el('div','alert-row');
    row.append(el('strong','',text(`alert_${event.kind}`)),el('span',`alert-${event.severity}`,text(event.severity)));
    row.append(el('small','',`${new Date(event.timestamp*1000).toLocaleString()} · ${event.value.toFixed(1)}${event.kind.includes('temperature')?' °C':'%'}`));
    section.append(row);
  }
  return section;
}
function renderLearn(){
  const root=el('div');
  const intro=el('section','card system-section');intro.append(el('h2','',text('learnIntroTitle')),el('p','sub',text('learnIntro')));root.append(intro);
  const checklist=el('section','card system-section');checklist.append(el('h2','',text('protectionChecklist')));
  for(const key of ['checkUpdates','checkMfa','checkBackup','checkEncryption','checkFirewall','checkProjects'])checklist.append(el('div','integrity-group',text(key)));
  root.append(checklist);
  for(const topic of state.helpTopics){
    const card=el('details','card learn-topic');card.append(el('summary','',topic.title));
    for(const [key,label] of [['what','learnWhat'],['protects','learnProtects'],['limits','learnLimits'],['guardboard','learnGuardboard'],['example','learnExample']]){
      const row=el('p','sub');row.append(el('strong','',`${text(label)}: `),document.createTextNode(topic[key]));card.append(row);
    }
    root.append(card);
  }
  return root;
}
function renderSettings(){
  const section=el('section','card system-section');section.append(el('h2','',text('alertThresholds')));
  section.append(el('p','sub',text('settingsScope')));
  const values=state.settings?.alert_thresholds;
  if(!values){section.append(el('p','sub',text('loading')));return section;}
  if(state.settings.error)section.append(el('p','sub',text(state.settings.error)));
  const fields=el('div','settings-grid');
  const inputs={};
  for(const [key,min,max,unit] of [['cpu_temperature',50,120,'°C'],['gpu_temperature',50,120,'°C'],['memory',50,99,'%'],['disk',50,99,'%'],['battery',1,50,'%']]){
    const label=el('label','settings-field');label.append(el('span','',`${text(`alert_${key}`)} (${unit})`));
    const input=el('input');input.type='number';input.min=String(min);input.max=String(max);input.step='0.1';input.value=String(values[key]);input.disabled=state.boot?.demo;
    label.append(input);fields.append(label);inputs[key]=input;
  }
  section.append(fields);
  const save=el('button','',text('saveSettings'));save.type='button';save.disabled=state.boot?.demo;
  save.addEventListener('click',async()=>{
    const thresholds={};for(const [key,input] of Object.entries(inputs)){if(!input.checkValidity()){input.reportValidity();return;}thresholds[key]=Number(input.value);}
    if(!window.confirm(text('settingsConfirm')))return;
    save.disabled=true;
    try{const response=await fetch('/api/settings/alerts',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':state.boot.csrf},body:JSON.stringify({thresholds,confirmed:true})});if(!response.ok)throw new Error(String(response.status));state.settings=await response.json();state.settingsError=null;}
    catch{state.settingsError=text('settingsFailed');}
    render();
  });section.append(save);
  if(state.settingsError)section.append(el('p','sub',state.settingsError));
  return section;
}
function renderOptimizer(){
  const root=el('div');
  const data=state.optimizer?.data;
  const current=el('section','card system-section');current.append(el('h2','',text('optimizerCurrent')));
  current.append(el('p','sub',text('optimizerReadOnly')));
  for(const [label,value] of [['powerProfile',data?.power_profile],['cpuGovernor',data?.cpu_governor],['swappiness',data?.swappiness],['battery',data?.battery_percent == null ? null : `${data.battery_percent}%`]]){
    current.append(el('div','integrity-group',`${text(label)}: ${value ?? text('notAvailable')}`));
  }
  root.append(current);
  const profiles=el('div','grid');
  for(const key of ['balanced','quiet','performance']){
    const card=el('section','card');card.append(el('h2','',text(`profile_${key}`)),el('p','sub',text(`profile_${key}_description`)),el('p','sub',text('profileNotApplied')));profiles.append(card);
  }
  root.append(profiles);
  return root;
}
async function loadOptimizer(){
  try{const response=await fetch('/api/optimizer',{cache:'no-store'});if(response.ok)state.optimizer=await response.json();}
  catch{state.optimizer=null;}
  if(route()==='optimizer')render();
}
async function loadSettings(){
  try{const response=await fetch('/api/settings',{cache:'no-store'});if(response.ok)state.settings=await response.json();}
  catch{state.settings=null;}
  if(route()==='settings')render();
}
async function loadAlerts(){
  try{const response=await fetch('/api/alerts',{cache:'no-store'});if(response.ok)state.alerts=await response.json();}
  catch{state.alerts=null;}
  state.alertsAt=Date.now();
  if(route()==='alerts')render();
}
async function pollAntivirus(){
  if(!['queued','running'].includes(state.avJob?.status))return;
  try{const response=await fetch(`/api/av/scans/${encodeURIComponent(state.avJob.id)}`,{cache:'no-store'});if(response.ok)state.avJob=await response.json();}
  catch{state.avError=text('antivirusFailed');}
  if(route()==='security')render();
}
function render() {
  const current = route();
  const view = $('view');
  view.replaceChildren();
  $('heading').textContent = text(current);
  $('crumb').textContent = `${text('commandCenter')} / ${text(current)}`;
  $('mode').textContent = state.boot?.demo ? text('demoMode') : text('realMode');
  $('back').hidden = current === 'overview';
  for (const link of document.querySelectorAll('#nav a')) {
    const active = link.dataset.route === current;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  if (current === 'overview' || current === 'system') {
    if (current === 'overview') view.append(renderRadar());
    const grid = el('div', 'grid');
    for (const [label, key] of [['CPU', 'cpu'], ['RAM', 'memory'], [text('disk'), 'disk']]) {
      const value = state.data?.[key];
      grid.append(metric(label, typeof value === 'number' ? `${value.toFixed(1)}%` : text('notAvailable'), state.data?.source || '—', 'system'));
    }
    view.append(grid);
    if (current === 'system') view.append(...renderSystem());
  } else if (current === 'network') {
    view.append(renderNetwork());
  } else if (current === 'wifi') {
    view.append(renderWifi());
  } else if (current === 'privacy') {
    view.append(renderPrivacy());
  } else if (current === 'alerts') {
    view.append(renderAlerts());
  } else if (current === 'learn') {
    view.append(renderLearn());
  } else if (current === 'optimizer') {
    view.append(renderOptimizer());
  } else if (current === 'security' || current === 'settings') {
    view.append(renderTools());
    if(current==='security')view.append(renderFirewall(),renderHardening(),renderProjectProtection(),renderAntivirus());
    if(current==='settings')view.append(renderSettings());
  } else {
    const box = el('section', 'empty');
    box.append(el('div', 'eyebrow', text('module')), el('h2', '', text(current)), el('p', '', text('pending')));
    view.append(box);
  }
}
async function refresh() {
  try {
    const response = await fetch('/api/telemetry', {cache: 'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    $('updated').textContent = `${text('lastUpdate')}: ${new Date().toLocaleTimeString()}`;
  } catch {
    state.data = null;
    $('updated').textContent = text('connectionError');
  }
  if(['overview','system'].includes(route()))render();
  if (route() === 'system') {
    if (Date.now() - state.historyAt > 10000) loadHistory();
    if (Date.now() - state.processesAt > 5000) loadProcesses();
  }
  if (route() === 'network' && Date.now() - state.networkAt > 2000) loadNetwork();
  if (route() === 'wifi' && Date.now() - state.wifiAt > 10000) loadWifi();
  if (route() === 'security') pollAntivirus();
  if (route() === 'alerts' && Date.now()-state.alertsAt>10000) loadAlerts();
}
function renderNavigation() {
  const nav = $('nav');
  nav.replaceChildren();
  routes.forEach((name, index) => {
    const link = el('a');
    link.href = `#/${name}`;
    link.dataset.route = name;
    link.title = text(name);
    link.append(el('b', '', icons[index]), el('span', '', text(name)));
    nav.append(link);
  });
}
function renderPalette() {
  const search = $('quick-search').value.trim().toLocaleLowerCase();
  const results = $('palette-results');
  results.replaceChildren();
  for (const name of routes.filter(name => !search || text(name).toLocaleLowerCase().includes(search))) {
    const button = el('button', 'palette-result', text(name));
    button.type = 'button';
    button.addEventListener('click', () => { location.hash = `#/${name}`; $('palette').close(); });
    results.append(button);
  }
  if (!results.children.length) results.append(el('p', 'sub', text('noResults')));
}
function openPalette() {
  const dialog = $('palette');
  if (!dialog.open) dialog.showModal();
  $('quick-search').value = '';
  renderPalette();
  $('quick-search').focus();
}
async function setLanguage(value) {
  if (!['uz', 'en', 'ru'].includes(value)) value = 'uz';
  const [response, helpResponse] = await Promise.all([fetch(`/assets/i18n/${value}.json`),fetch(`/assets/i18n/help-${value}.json`)]);
  if (!response.ok || !helpResponse.ok) throw new Error('Locale unavailable');
  state.dict = await response.json();
  state.helpTopics = await helpResponse.json();
  state.lang = value;
  localStorage.setItem('gb-lang', value);
  document.documentElement.lang = value;
  $('language').value = value;
  $('palette-title').textContent = text('quickSearch');
  $('brand-subtitle').textContent = text('brandSubtitle');
  $('privacy-label').textContent = text('localPrivate');
  $('instance-label').textContent = text('localInstance');
  $('language').setAttribute('aria-label', text('language'));
  $('back').setAttribute('aria-label', text('back'));
  $('close-palette').setAttribute('aria-label', text('close'));
  $('quick-search').placeholder = text('searchPlaceholder');
  $('open-search').title = text('quickSearch');
  $('back').title = text('back');
  $('theme').title = text('theme');
  $('nav').setAttribute('aria-label', text('navigation'));
  renderNavigation();
  render();
}
$('language').addEventListener('change', event => setLanguage(event.target.value));
$('theme').addEventListener('click', () => {
  document.body.classList.toggle('light');
  localStorage.setItem('gb-theme', document.body.classList.contains('light') ? 'light' : 'dark');
});
$('back').addEventListener('click', () => { location.hash = '#/overview'; });
$('open-search').addEventListener('click', openPalette);
$('quick-search').addEventListener('input', renderPalette);
$('close-palette').addEventListener('click', () => $('palette').close());
window.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    openPalette();
  }
  if (event.altKey && event.key === 'ArrowLeft') location.hash = '#/overview';
});
window.addEventListener('hashchange', () => {render();if (route() === 'system') {loadHistory();loadProcesses();}if (route() === 'network') loadNetwork();if (route() === 'wifi') {loadWifi();loadRooms();}if(route()==='security') {loadFirewall();loadHardening();}if(route()==='privacy')loadPrivacy();if(route()==='alerts')loadAlerts();if(route()==='settings')loadSettings();if(route()==='optimizer')loadOptimizer();});
if (localStorage.getItem('gb-theme') === 'light') document.body.classList.add('light');
try {
  const response = await fetch('/api/bootstrap');
  if (!response.ok) throw new Error('Authentication failed');
  state.boot = await response.json();
} catch { state.boot = null; }
await setLanguage(state.lang);
try {
  const response = await fetch('/api/capabilities');
  if (response.ok) state.capabilities = await response.json();
} catch { /* Module reports unavailable data. */ }
try {const response = await fetch('/api/posture');if (response.ok) state.posture = await response.json();} catch { /* Score remains unknown. */ }
await refresh();
setInterval(() => { if (!document.hidden) refresh(); }, 1000);
