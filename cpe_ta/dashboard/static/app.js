/* CPE Dashboard v2 — vanilla JS, no CDN, hash-routing */
'use strict';

const main = () => document.getElementById('main');

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const routes = {
  '/':        viewOverview,
  '/domains': viewDomains,
  '/runs':    viewRuns,
  '/testbed': viewTestbed,
  '/start':   viewStart,
  '/help':    viewHelp,
};

function route() {
  const hash = location.hash.replace(/^#/, '') || '/';
  if (hash.startsWith('/runs/')) {
    const runId = hash.slice(6);
    viewRunDetail(runId);
    return;
  }
  const fn = routes[hash];
  if (fn) fn();
  else viewOverview();
  setActiveNav(hash);
}

function setActiveNav(hash) {
  document.querySelectorAll('nav a').forEach(a => {
    const href = a.getAttribute('href');
    a.classList.toggle('active',
      href === '#' + hash || (hash === '/' && href === '#/'));
  });
}

window.addEventListener('hashchange', route);
window.addEventListener('load', route);

// ---------------------------------------------------------------------------
// Central API fetch wrapper (AC-42) — structured error messages, no raw tracebacks
// ---------------------------------------------------------------------------
async function apiFetch(path, opts) {
  let r;
  try {
    r = await fetch('/api' + path, opts);
  } catch (e) {
    throw new Error('Network error: ' + e.message);
  }
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const body = await r.json();
      if (body && body.detail) msg = String(body.detail);
    } catch (_) { /* use status text */ }
    throw new Error(msg);
  }
  return r.json();
}

function apiPost(path, body) {
  return apiFetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
}

function ts(t) { return new Date(t * 1000).toLocaleString(); }

function dur(s) {
  if (s < 60) return s.toFixed(1) + 's';
  return Math.floor(s / 60) + 'm ' + (s % 60 | 0) + 's';
}

function badge(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function errHtml(msg) {
  return `<p class="err">Error: ${esc(msg)}</p>`;
}

// Empty-state helper (AC-40) — handlungsleitend
function emptyState(message, action) {
  return `<div class="empty-state">
    <p class="empty-msg">${esc(message)}</p>
    ${action ? `<p class="empty-action">${action}</p>` : ''}
  </div>`;
}

// ---------------------------------------------------------------------------
// Filter bar builder (AC-34)
// ---------------------------------------------------------------------------
function filterBar(id, opts) {
  const statuses = ['', 'passed', 'failed', 'skipped', 'error'];
  const statusOpts = statuses.map(s =>
    `<option value="${s}"${opts.status === s ? ' selected' : ''}>${s || 'All statuses'}</option>`
  ).join('');
  const sorts = [
    {v:'', l:'Default order'}, {v:'time', l:'Time ↑'}, {v:'-time', l:'Time ↓'},
    {v:'duration', l:'Duration ↑'}, {v:'-duration', l:'Duration ↓'},
    {v:'status', l:'Status (fail first)'}, {v:'-status', l:'Status (pass first)'},
  ];
  const sortOpts = sorts.map(s =>
    `<option value="${s.v}"${opts.sort === s.v ? ' selected' : ''}>${s.l}</option>`
  ).join('');
  return `<div class="filter-bar" id="${id}">
    <input type="text" class="filter-q" placeholder="Search…" value="${esc(opts.q||'')}"
      title="Free-text search across run ID, test name, domain and git SHA">
    <select class="filter-status" title="Filter by test/run status">${statusOpts}</select>
    <select class="filter-sort" title="Sort results">${sortOpts}</select>
    <button class="btn-sm" onclick="applyFilter('${id}')">Apply</button>
  </div>`;
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------
async function viewOverview() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await apiFetch('/overview');
    const last = d.last_run
      ? `<div class="card"><h2>Last Run</h2>
           <table>
             <tr><th>Run ID</th><td><a class="link" href="#/runs/${d.last_run.run_id}">${d.last_run.run_id}</a></td></tr>
             <tr><th>Time</th><td>${ts(d.last_run.timestamp)}</td></tr>
             <tr><th>Duration</th><td>${dur(d.last_run.duration_s)}</td></tr>
             <tr><th>Git SHA</th><td>${d.last_run.git_sha || '—'}</td></tr>
           </table></div>`
      : emptyState('No runs yet.', '<a class="link" href="#/start">→ Start a test run</a> or <a class="link" href="#/help">view the Setup guide</a>.');
    const domains = d.domains.slice(0, 6).map(dom =>
      `<div class="bar-row">
        <span class="bar-label"><a class="link" href="#/domains">${esc(dom.name)}</a></span>
        <div class="bar-bg"><div class="bar-fill" style="width:${(dom.pass_rate*100).toFixed(0)}%"></div></div>
        <span class="bar-pct">${(dom.pass_rate*100).toFixed(0)}%</span>
       </div>`
    ).join('');
    main().innerHTML = `
      <h1>Overview</h1>
      <div class="stat-row">
        <div class="stat passed" title="Tests that passed in the last run"><div class="value">${d.passed}</div><div class="label">Passed</div></div>
        <div class="stat failed" title="Tests that failed — click Runs for details"><div class="value">${d.failed}</div><div class="label">Failed</div></div>
        <div class="stat skipped" title="Tests skipped (capability mismatch or marker exclusion)"><div class="value">${d.skipped}</div><div class="label">Skipped</div></div>
        <div class="stat error"  title="Tests that errored (setup/teardown failures)"><div class="value">${d.error}</div><div class="label">Error</div></div>
      </div>
      ${last}
      ${d.domains.length ? `<div class="card"><h2>Domains</h2>${domains}</div>` : ''}
    `;
  } catch (e) {
    main().innerHTML = errHtml(e.message);
  }
}

// ---------------------------------------------------------------------------
// Domains
// ---------------------------------------------------------------------------
async function viewDomains() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const domains = await apiFetch('/domains');
    if (!domains.length) {
      main().innerHTML = '<h1>Test Domains</h1>' +
        emptyState('No domain data yet.', '<a class="link" href="#/start">→ Start a test run</a> to populate domain statistics.');
      return;
    }
    const rows = domains.map(d => {
      const pct = (d.pass_rate * 100).toFixed(1);
      return `<tr>
        <td>${esc(d.name)}</td>
        <td>${d.total}</td>
        <td><span style="color:#4ade80">${d.passed}</span></td>
        <td><span style="color:#f87171">${d.failed}</span></td>
        <td><span style="color:#fbbf24">${d.skipped}</span></td>
        <td><div class="bar-bg" style="width:120px"><div class="bar-fill" style="width:${pct}%"></div></div></td>
        <td>${pct}%</td>
      </tr>`;
    }).join('');
    main().innerHTML = `
      <h1>Test Domains</h1>
      <div class="card">
        <table>
          <thead><tr><th>Domain</th><th>Total</th><th>Pass</th><th>Fail</th><th>Skip</th><th>Bar</th><th>Rate</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  } catch (e) {
    main().innerHTML = errHtml(e.message);
  }
}

// ---------------------------------------------------------------------------
// Run History (AC-34 filter/sort, AC-35 export links)
// ---------------------------------------------------------------------------
let _runsFilterState = {q:'', status:'', sort:''};

async function viewRuns(filterState) {
  const fs = filterState || _runsFilterState;
  _runsFilterState = fs;
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    let url = '/runs';
    const params = [];
    if (fs.q) params.push('q=' + encodeURIComponent(fs.q));
    if (fs.sort) params.push('sort=' + encodeURIComponent(fs.sort));
    if (params.length) url += '?' + params.join('&');
    const runs = await apiFetch(url);

    const fb = filterBar('runs-filter', fs);
    if (!runs.length) {
      main().innerHTML = '<h1>Run History</h1>' + fb +
        emptyState('No runs found.', '<a class="link" href="#/start">→ Start a test run</a> to see history here.');
      return;
    }
    const rows = runs.slice().reverse().map(r =>
      `<tr>
        <td><a class="link" href="#/runs/${r.run_id}">${r.run_id}</a></td>
        <td>${ts(r.timestamp)}</td>
        <td>${dur(r.duration_s)}</td>
        <td><span style="color:#4ade80">${r.passed}</span></td>
        <td><span style="color:#f87171">${r.failed}</span></td>
        <td><span style="color:#fbbf24">${r.skipped}</span></td>
        <td>${r.git_sha || '—'}</td>
        <td>
          <a class="link" href="/api/runs/${r.run_id}/export?format=junit"
             title="Download JUnit XML report for this run" download>XML</a>
          &nbsp;
          <a class="link" href="/api/runs/${r.run_id}/export?format=html"
             title="Download HTML report for this run" download>HTML</a>
        </td>
       </tr>`
    ).join('');
    main().innerHTML = `
      <h1>Run History</h1>
      ${fb}
      <div class="card">
        <table>
          <thead><tr><th>Run ID</th><th>Time</th><th>Duration</th><th>Pass</th><th>Fail</th><th>Skip</th><th>Git SHA</th><th>Export</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  } catch (e) {
    main().innerHTML = errHtml(e.message);
  }
}

function applyFilter(filterId) {
  const bar = document.getElementById(filterId);
  if (!bar) return;
  const q = bar.querySelector('.filter-q')?.value || '';
  const status = bar.querySelector('.filter-status')?.value || '';
  const sort = bar.querySelector('.filter-sort')?.value || '';
  if (filterId === 'runs-filter') viewRuns({q, status, sort});
  if (filterId.startsWith('detail-filter-')) {
    const runId = filterId.slice('detail-filter-'.length);
    viewRunDetail(runId, {q, status, sort});
  }
}

// ---------------------------------------------------------------------------
// Run Detail (AC-34 filter, AC-35 export)
// ---------------------------------------------------------------------------
async function viewRunDetail(runId, filterState) {
  const fs = filterState || {q:'', status:'', sort:''};
  setActiveNav('/runs');
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    let url = '/runs/' + runId;
    const params = [];
    if (fs.status) params.push('status=' + encodeURIComponent(fs.status));
    if (fs.q) params.push('q=' + encodeURIComponent(fs.q));
    if (params.length) url += '?' + params.join('&');
    const d = await apiFetch(url);

    const fb = filterBar('detail-filter-' + runId, fs);
    const rows = d.tests.map(t => {
      const detail = (t.status === 'failed' || t.status === 'error') && t.message
        ? `<details><summary style="cursor:pointer;color:#94a3b8">Details</summary><pre>${esc(t.message)}\n${esc(t.stacktrace||'')}</pre></details>`
        : '';
      return `<tr>
        <td>${badge(t.status)}</td>
        <td>${esc(t.name)}</td>
        <td>${esc(t.domain)}</td>
        <td>${t.duration_s.toFixed(3)}s</td>
        <td>${detail}</td>
       </tr>`;
    }).join('');
    const emptyRow = rows ? '' : '<tr><td colspan="5">' +
      emptyState('No tests match the current filter.', '<a class="link" href="#/runs/' + runId + '">Clear filter</a>') +
      '</td></tr>';
    main().innerHTML = `
      <h1>Run <code>${esc(runId)}</code></h1>
      <p style="color:#64748b">${ts(d.timestamp)} · ${dur(d.duration_s)} · SHA: ${d.git_sha||'—'}
        &nbsp;|&nbsp;
        <a class="link" href="/api/runs/${esc(runId)}/export?format=junit"
           title="Download JUnit XML for this run" download>↓ XML</a>
        &nbsp;
        <a class="link" href="/api/runs/${esc(runId)}/export?format=html"
           title="Download HTML report for this run" download>↓ HTML</a>
      </p>
      ${fb}
      <div class="card">
        <table>
          <thead><tr><th>Status</th><th>Test</th><th>Domain</th><th>Duration</th><th></th></tr></thead>
          <tbody>${rows || emptyRow}</tbody>
        </table>
      </div>
      <p><a class="link" href="#/runs">← Back to History</a></p>`;
  } catch (e) {
    main().innerHTML = errHtml(e.message) + '<p><a class="link" href="#/runs">← Back</a></p>';
  }
}

// ---------------------------------------------------------------------------
// Testbed Status (AC-43 sim/real display + validate button)
// ---------------------------------------------------------------------------
async function viewTestbed() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await apiFetch('/testbed');
    const devRows = d.hal_devices.map(dev => {
      const simReal = dev.detail ? esc(dev.detail) : (d.source === 'real' ? 'real' : 'sim');
      return `<tr>
        <td>${esc(dev.name)}</td>
        <td>${esc(dev.type)}</td>
        <td>${dev.connected ? '<span style="color:#4ade80" title="Device reachable">● connected</span>' : '<span style="color:#f87171" title="Device not reachable">● disconnected</span>'}</td>
        <td><span class="badge badge-mode" title="Simulator or real hardware">${simReal}</span></td>
       </tr>`;
    }).join('') || '<tr><td colspan="4">' + emptyState('No HAL devices configured.', 'Edit testbed.yaml and add switches, PDUs etc. See <a class="link" href="#/help">Help & Setup</a>.') + '</td></tr>';
    const svcs = d.services.length
      ? d.services.map(s => `<li title="Service running in ${d.source} mode">${esc(s)}</li>`).join('')
      : '<li>' + emptyState('No services configured.', 'Add services to testbed.yaml. See <a class="link" href="#/help">Help & Setup</a>.') + '</li>';
    const sourceColor = d.source === 'missing' ? '#f87171' : d.source === 'sim' ? '#fbbf24' : '#4ade80';
    main().innerHTML = `
      <h1>Testbed Status</h1>
      <div class="card">
        <table>
          <tr><th>DUT</th><td>${esc(d.dut)}</td></tr>
          <tr><th title="sim = simulators active, real = physical hardware connected">Mode</th>
              <td><span style="color:${sourceColor};font-weight:600">${d.source}</span>
              <span style="color:#64748b;font-size:.85rem;margin-left:.5rem">
                ${d.source === 'sim' ? '(Simulator mode — no physical hardware needed)' : d.source === 'real' ? '(Real hardware mode)' : '(No testbed.yaml found)'}
              </span></td></tr>
        </table>
      </div>
      <div class="card"><h2>HAL Devices</h2>
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Mode</th></tr></thead>
          <tbody>${devRows}</tbody>
        </table>
      </div>
      <div class="card"><h2>Infrastructure Services</h2><ul>${svcs}</ul></div>
      <div class="card">
        <h2>Inventory Validation</h2>
        <p style="color:#94a3b8;font-size:.9rem">Runs the same checks as <code>cpe-ta inventory-validate</code>.</p>
        <button class="run-btn" onclick="runInventoryValidate()" title="Validate the testbed.yaml inventory file — checks structure and wiring consistency">Validate Inventory</button>
        <div id="inv-result"></div>
      </div>`;
  } catch (e) {
    main().innerHTML = errHtml(e.message);
  }
}

async function runInventoryValidate() {
  const el = document.getElementById('inv-result');
  if (el) el.innerHTML = '<p class="loading">Validating…</p>';
  try {
    const r = await apiPost('/inventory/validate', {});
    if (!el) return;
    if (r.ok) {
      el.innerHTML = '<p style="color:#4ade80">✓ Inventory is valid.</p>';
    } else {
      const errs = (r.errors || []).map(e => `<li>${esc(e)}</li>`).join('');
      el.innerHTML = `<p style="color:#f87171">✗ Inventory has errors:</p><ul>${errs}</ul>`;
    }
  } catch (e) {
    if (el) el.innerHTML = errHtml(e.message);
  }
}

// ---------------------------------------------------------------------------
// Run Starter (AC-32 presets, AC-33 cancel button)
// ---------------------------------------------------------------------------
let _pollTimer = null;

const MARKER_PRESETS = [
  {id:'smoke',      label:'smoke',      title:'Quick sanity check — ~30 tests, fast'},
  {id:'full',       label:'full',       title:'Full test suite including all headless tests'},
  {id:'regression', label:'regression', title:'Regression suite — run before releases'},
  {id:'headless',   label:'headless',   title:'All tests that run without physical hardware'},
  {id:'tech_dsl',   label:'tech:DSL',   title:'DSL access technology tests'},
  {id:'tech_docsis',label:'tech:DOCSIS',title:'DOCSIS/cable access technology tests'},
  {id:'tech_pon',   label:'tech:PON',   title:'PON/fiber access technology tests'},
  {id:'tech_fwa',   label:'tech:FWA',   title:'Fixed Wireless Access technology tests'},
];

function buildPresetHtml() {
  return MARKER_PRESETS.map(p =>
    `<label class="preset-label" title="${p.title}">
       <input type="checkbox" class="preset-cb" value="${p.id}" id="preset-${p.id}"
         onchange="updateMarkerFromPresets()">
       ${p.label}
     </label>`
  ).join('');
}

function updateMarkerFromPresets() {
  const checked = Array.from(document.querySelectorAll('.preset-cb:checked')).map(cb => cb.value);
  const markerInput = document.getElementById('markers');
  if (markerInput) markerInput.value = checked.join(' or ');
}

async function viewStart() {
  main().innerHTML = `
    <h1>Start Test Run</h1>
    <div class="card">
      <h2>Marker Presets</h2>
      <p style="color:#94a3b8;font-size:.85rem">Select one or more test groups, or enter a custom expression below.</p>
      <div class="preset-grid">${buildPresetHtml()}</div>
      <label style="display:block;margin-top:1rem;color:#94a3b8;font-size:.85rem">
        Custom marker expression (optional)
      </label>
      <input type="text" id="markers" placeholder="e.g. headless and smoke" value="headless"
        title="Pytest marker expression — combined from presets above or entered manually">
      <button class="run-btn" onclick="startRun()" id="run-btn"
        title="Start a pytest run with the selected markers">Run Tests</button>
    </div>
    <div id="progress"></div>`;
  checkProgress();
}

async function startRun() {
  const markers = document.getElementById('markers')?.value.trim();
  if (!markers) return;
  const btn = document.getElementById('run-btn');
  if (btn) btn.disabled = true;
  try {
    const r = await apiPost('/runs', {markers});
    showProgress({status: 'running', run_id: r.run_id, lines_tail: [], counts: {}});
    pollProgress();
  } catch (e) {
    const el = document.getElementById('progress');
    if (el) el.innerHTML = errHtml(e.message);
    if (btn) btn.disabled = false;
  }
}

async function cancelRun() {
  try {
    await apiPost('/runs/active/cancel', {});
    const el = document.getElementById('progress');
    if (el) el.innerHTML = '<div class="card"><p style="color:#fbbf24">Run cancelled.</p></div>';
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
    const btn = document.getElementById('run-btn');
    if (btn) btn.disabled = false;
  } catch (e) {
    const el = document.getElementById('progress');
    if (el) el.innerHTML = errHtml(e.message);
  }
}

async function checkProgress() {
  try {
    const p = await apiFetch('/runs/active/progress');
    if (p.status === 'running') { showProgress(p); pollProgress(); }
    else if (p.status !== 'idle') showProgress(p);
  } catch (_) { /* ignore on initial load */ }
}

function pollProgress() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    try {
      const p = await apiFetch('/runs/active/progress');
      showProgress(p);
      if (p.status !== 'running') {
        clearInterval(_pollTimer);
        _pollTimer = null;
        const btn = document.getElementById('run-btn');
        if (btn) btn.disabled = false;
        if (p.status === 'finished') {
          setTimeout(() => { location.hash = '#/runs'; }, 1500);
        }
      }
    } catch (_) { clearInterval(_pollTimer); _pollTimer = null; }
  }, 1000);
}

function showProgress(p) {
  const el = document.getElementById('progress');
  if (!el) return;
  const color = p.status === 'finished' ? '#4ade80'
    : p.status === 'cancelled' ? '#fbbf24'
    : p.status === 'failed'    ? '#f87171'
    : '#60a5fa';
  const counts = Object.entries(p.counts || {}).map(([k,v]) => `${v} ${k}`).join(' · ');
  const lines = (p.lines_tail || []).join('\n');
  const cancelBtn = p.status === 'running'
    ? `<button class="btn-cancel" onclick="cancelRun()" title="Stop the currently running test suite">Abort Run</button>`
    : '';
  el.innerHTML = `
    <div class="card">
      <p>Status: <strong style="color:${color}">${p.status}</strong>${p.run_id ? ` · Run ID: ${p.run_id}` : ''}</p>
      ${counts ? `<p>${counts}</p>` : ''}
      ${cancelBtn}
      ${lines ? `<pre>${esc(lines)}</pre>` : ''}
    </div>`;
}

// ---------------------------------------------------------------------------
// Help & Setup — 7th view (AC-36..AC-39)
// ---------------------------------------------------------------------------
async function viewHelp() {
  setActiveNav('/help');
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const h = await apiFetch('/help');

    const steps = (h.quickstart || []).map(s =>
      `<div class="qs-step">
        <div class="qs-num" title="Step ${s.order}">${s.order}</div>
        <div class="qs-body">
          <strong>${esc(s.title)}</strong>
          <p>${esc(s.description)}</p>
          ${s.command ? `<code class="qs-cmd">${esc(s.command)}</code>` : ''}
        </div>
       </div>`
    ).join('');

    function realStatusBadge(rs) {
      const cfg = {
        skeleton:    {color:'#fbbf24', label:'real driver: skeleton'},
        partial:     {color:'#fb923c', label:'real driver: partial'},
        implemented: {color:'#4ade80', label:'real driver: implemented'},
      };
      const c = cfg[rs] || cfg.skeleton;
      return `<span style="font-size:.8rem;color:${c.color}" title="Real driver implementation status">${c.label}</span>`;
    }

    const hwRows = (h.hardware || []).map(d =>
      `<tr>
        <td><strong>${esc(d.name)}</strong></td>
        <td>${esc(d.purpose)}</td>
        <td style="font-size:.85rem;color:#94a3b8">${esc(d.connection)}</td>
        <td title="${d.sim_available ? 'Simulator available — no hardware needed for headless tests' : 'No simulator, requires physical hardware'}">
          ${d.sim_available ? '<span style="color:#4ade80">✓ sim available</span>' : '<span style="color:#fbbf24">sim unavailable</span>'}
          <br>${realStatusBadge(d.real_status)}
        </td>
       </tr>`
    ).join('') || '<tr><td colspan="4">No hardware data.</td></tr>';

    const infraItems = (h.infrastructure || []).map(s =>
      `<div class="infra-item">
        <div class="infra-name" title="${esc(s.note)}">${esc(s.name)}</div>
        <div class="infra-purpose">${esc(s.purpose)}</div>
        <div class="infra-note" title="Sim vs real details">${esc(s.note)}</div>
        <div>${realStatusBadge(s.real_status)}</div>
       </div>`
    ).join('') || emptyState('No infrastructure data.', '');

    main().innerHTML = `
      <h1>Help &amp; Setup</h1>

      <div class="card">
        <h2>Quickstart</h2>
        <div class="qs-list">${steps}</div>
      </div>

      <div class="card">
        <h2>Hardware Wiring Guide</h2>
        <p style="color:#94a3b8;font-size:.85rem">
          All hardware listed below has a built-in simulator — no physical devices are needed for
          headless test runs. Add real devices by configuring <code>testbed.yaml</code>.
        </p>
        <table>
          <thead>
            <tr>
              <th title="HAL interface name">Device</th>
              <th>Purpose</th>
              <th>Connection / Driver</th>
              <th title="Headless simulator available?">Simulator</th>
            </tr>
          </thead>
          <tbody>${hwRows}</tbody>
        </table>
      </div>

      <div class="card">
        <h2>Infrastructure Services for Real Tests</h2>
        <p style="color:#94a3b8;font-size:.85rem">
          Tests that use <code>@hardware</code> markers require these services.
          All have simulators for headless use.
        </p>
        <div class="infra-grid">${infraItems}</div>
      </div>

      <div class="card">
        <h2>Switching from Simulator to Real Hardware</h2>
        <ol style="color:#cbd5e1;line-height:1.8">
          <li>Copy <code>testbed.example.yaml</code> to <code>testbed.yaml</code> and fill in real IPs/credentials.</li>
          <li>Set the environment variable <code>USE_SIM=0</code> before running tests.</li>
          <li>Run <code>cpe-ta inventory-validate testbed.yaml</code> to check the configuration.</li>
          <li>Execute: <code>cpe-ta run -m "regression"</code> — tests now target real hardware.</li>
          <li>Hardware-deferred tests (RF, physical fiber, real CMTS) require the matching physical equipment.</li>
        </ol>
        <p><a class="link" href="#/testbed" title="Open testbed status and inventory validator">→ Open Testbed View &amp; Inventory Validator</a></p>
      </div>`;
  } catch (e) {
    main().innerHTML = errHtml(e.message);
  }
}
