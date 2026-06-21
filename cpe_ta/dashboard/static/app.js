/* CPE Dashboard — vanilla JS, no CDN, hash-routing */
'use strict';

const $ = id => document.getElementById(id);
const main = () => document.getElementById('main');

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const routes = {
  '/':           viewOverview,
  '/domains':    viewDomains,
  '/runs':       viewRuns,
  '/testbed':    viewTestbed,
  '/start':      viewStart,
};

function route() {
  const hash = location.hash.replace(/^#/, '') || '/';
  // Handle /runs/{id}
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
    a.classList.toggle('active', a.getAttribute('href') === '#' + hash || (hash === '/' && a.getAttribute('href') === '#/'));
  });
}

window.addEventListener('hashchange', route);
window.addEventListener('load', route);

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(path, opts) {
  const r = await fetch('/api' + path, opts);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

function ts(t) {
  return new Date(t * 1000).toLocaleString();
}

function dur(s) {
  if (s < 60) return s.toFixed(1) + 's';
  return Math.floor(s / 60) + 'm ' + (s % 60 | 0) + 's';
}

function badge(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------
async function viewOverview() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await api('/overview');
    const last = d.last_run
      ? `<div class="card"><h2>Last Run</h2>
           <table><tr><th>Run ID</th><td><a class="link" href="#/runs/${d.last_run.run_id}">${d.last_run.run_id}</a></td></tr>
           <tr><th>Time</th><td>${ts(d.last_run.timestamp)}</td></tr>
           <tr><th>Duration</th><td>${dur(d.last_run.duration_s)}</td></tr>
           <tr><th>Git SHA</th><td>${d.last_run.git_sha || '—'}</td></tr>
           </table></div>`
      : '';
    const domains = d.domains.slice(0, 6).map(dom =>
      `<div class="bar-row">
        <span class="bar-label"><a class="link" href="#/domains">${dom.name}</a></span>
        <div class="bar-bg"><div class="bar-fill" style="width:${(dom.pass_rate*100).toFixed(0)}%"></div></div>
        <span class="bar-pct">${(dom.pass_rate*100).toFixed(0)}%</span>
       </div>`
    ).join('');
    main().innerHTML = `
      <h1>Overview</h1>
      <div class="stat-row">
        <div class="stat passed"><div class="value">${d.passed}</div><div class="label">Passed</div></div>
        <div class="stat failed"><div class="value">${d.failed}</div><div class="label">Failed</div></div>
        <div class="stat skipped"><div class="value">${d.skipped}</div><div class="label">Skipped</div></div>
        <div class="stat error"><div class="value">${d.error}</div><div class="label">Error</div></div>
      </div>
      ${last}
      ${d.domains.length ? `<div class="card"><h2>Domains</h2>${domains}</div>` : ''}
      ${d.total === 0 ? '<p class="empty">No test data available.</p>' : ''}
    `;
  } catch (e) {
    main().innerHTML = `<p class="err">Error loading overview: ${e.message}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Domains
// ---------------------------------------------------------------------------
async function viewDomains() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const domains = await api('/domains');
    if (!domains.length) { main().innerHTML = '<h1>Domains</h1><p class="empty">No data.</p>'; return; }
    const rows = domains.map(d => {
      const pct = (d.pass_rate * 100).toFixed(1);
      const passW = pct + '%';
      const failW = ((d.failed / d.total) * 100).toFixed(1) + '%';
      return `<tr>
        <td>${d.name}</td>
        <td>${d.total}</td>
        <td><span style="color:#4ade80">${d.passed}</span></td>
        <td><span style="color:#f87171">${d.failed}</span></td>
        <td><span style="color:#fbbf24">${d.skipped}</span></td>
        <td>
          <div class="bar-bg" style="width:120px">
            <div class="bar-fill" style="width:${passW}"></div>
          </div>
        </td>
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
    main().innerHTML = `<p class="err">Error: ${e.message}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Run History
// ---------------------------------------------------------------------------
async function viewRuns() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const runs = await api('/runs');
    if (!runs.length) { main().innerHTML = '<h1>Run History</h1><p class="empty">No runs yet.</p>'; return; }
    const rows = runs.slice().reverse().map(r =>
      `<tr>
        <td><a class="link" href="#/runs/${r.run_id}">${r.run_id}</a></td>
        <td>${ts(r.timestamp)}</td>
        <td>${dur(r.duration_s)}</td>
        <td><span style="color:#4ade80">${r.passed}</span></td>
        <td><span style="color:#f87171">${r.failed}</span></td>
        <td><span style="color:#fbbf24">${r.skipped}</span></td>
        <td>${r.git_sha || '—'}</td>
       </tr>`
    ).join('');
    main().innerHTML = `
      <h1>Run History</h1>
      <div class="card">
        <table>
          <thead><tr><th>Run ID</th><th>Time</th><th>Duration</th><th>Pass</th><th>Fail</th><th>Skip</th><th>Git SHA</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  } catch (e) {
    main().innerHTML = `<p class="err">Error: ${e.message}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Run Detail
// ---------------------------------------------------------------------------
async function viewRunDetail(runId) {
  setActiveNav('/runs');
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await api('/runs/' + runId);
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
    main().innerHTML = `
      <h1>Run <code>${runId}</code></h1>
      <p style="color:#64748b">${ts(d.timestamp)} · ${dur(d.duration_s)} · SHA: ${d.git_sha||'—'}</p>
      <div class="card">
        <table>
          <thead><tr><th>Status</th><th>Test</th><th>Domain</th><th>Duration</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="5" class="empty">No tests.</td></tr>'}</tbody>
        </table>
      </div>
      <p><a class="link" href="#/runs">← Back to History</a></p>`;
  } catch (e) {
    main().innerHTML = `<p class="err">Run not found: ${e.message}</p><p><a class="link" href="#/runs">← Back</a></p>`;
  }
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ---------------------------------------------------------------------------
// Testbed Status
// ---------------------------------------------------------------------------
async function viewTestbed() {
  main().innerHTML = '<p class="loading">Loading…</p>';
  try {
    const d = await api('/testbed');
    const devRows = d.hal_devices.map(dev =>
      `<tr><td>${esc(dev.name)}</td><td>${esc(dev.type)}</td>
       <td>${dev.connected ? '<span style="color:#4ade80">●</span>' : '<span style="color:#f87171">●</span>'}</td>
       <td>${esc(dev.detail)}</td></tr>`
    ).join('') || '<tr><td colspan="4" class="empty">No devices configured.</td></tr>';
    const svcs = d.services.length ? d.services.map(s => `<li>${esc(s)}</li>`).join('') : '<li style="color:#475569">None</li>';
    const sourceColor = d.source === 'missing' ? '#f87171' : d.source === 'sim' ? '#fbbf24' : '#4ade80';
    main().innerHTML = `
      <h1>Testbed Status</h1>
      <div class="card">
        <table>
          <tr><th>DUT</th><td>${esc(d.dut)}</td></tr>
          <tr><th>Source</th><td><span style="color:${sourceColor}">${d.source}</span></td></tr>
        </table>
      </div>
      <div class="card"><h2>HAL Devices</h2>
        <table><thead><tr><th>Name</th><th>Type</th><th>Connected</th><th>Detail</th></tr></thead>
        <tbody>${devRows}</tbody></table>
      </div>
      <div class="card"><h2>Services</h2><ul>${svcs}</ul></div>`;
  } catch (e) {
    main().innerHTML = `<p class="err">Error: ${e.message}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Run Starter
// ---------------------------------------------------------------------------
let _pollTimer = null;

async function viewStart() {
  main().innerHTML = `
    <h1>Start Test Run</h1>
    <div class="card">
      <label>Marker expression</label>
      <input type="text" id="markers" placeholder="e.g. headless and smoke" value="headless">
      <button class="run-btn" onclick="startRun()">Run Tests</button>
    </div>
    <div id="progress"></div>`;
  checkProgress();
}

async function startRun() {
  const markers = $('markers').value.trim();
  if (!markers) return;
  try {
    const r = await api('/runs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({markers})
    });
    showProgress({status: 'running', run_id: r.run_id, lines_tail: [], counts: {}});
    pollProgress();
  } catch (e) {
    $('progress').innerHTML = `<p class="err">Error: ${e.message}</p>`;
  }
}

async function checkProgress() {
  try {
    const p = await api('/runs/active/progress');
    if (p.status === 'running') { showProgress(p); pollProgress(); }
    else if (p.status !== 'idle') showProgress(p);
  } catch (_) {}
}

function pollProgress() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    try {
      const p = await api('/runs/active/progress');
      showProgress(p);
      if (p.status !== 'running') {
        clearInterval(_pollTimer);
        if (p.status === 'finished') {
          setTimeout(() => { location.hash = '#/runs'; }, 1500);
        }
      }
    } catch (_) { clearInterval(_pollTimer); }
  }, 1000);
}

function showProgress(p) {
  const el = $('progress');
  if (!el) return;
  const color = p.status === 'finished' ? '#4ade80' : p.status === 'failed' ? '#f87171' : '#fbbf24';
  const counts = Object.entries(p.counts || {}).map(([k,v]) => `${v} ${k}`).join(' · ');
  const lines = (p.lines_tail || []).join('\n');
  el.innerHTML = `
    <div class="card">
      <p>Status: <strong style="color:${color}">${p.status}</strong>${p.run_id ? ` · Run ID: ${p.run_id}` : ''}</p>
      ${counts ? `<p>${counts}</p>` : ''}
      ${lines ? `<pre>${esc(lines)}</pre>` : ''}
    </div>`;
}
