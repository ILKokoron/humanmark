// Humanmark frontend. Reads are plain JSON-RPC via the FastNEAR mirror.
// Writes go through the visitor's own NEAR wallet (Wallet Selector, see
// wallet.js): this page never holds a key.
const CONTRACT = 'humanmark.bindingvow1106.testnet';
const RPC = 'https://rpc.testnet.fastnear.com';
const EXPLORER_TX = 'https://explorer.testnet.near.org/transactions/';

document.getElementById('contractId').textContent = CONTRACT;

// ---------- navigation ----------
function showScreen(name) {
  document.querySelectorAll('nav button').forEach((x) => x.classList.toggle('active', x.dataset.screen === name));
  document.querySelectorAll('.screen').forEach((x) => x.classList.remove('active'));
  const el = document.getElementById('screen-' + name);
  if (el) el.classList.add('active');
}
document.querySelectorAll('nav button').forEach((b) => {
  b.addEventListener('click', () => showScreen(b.dataset.screen));
});

// ---------- chain reads ----------
async function rpcView(method, args) {
  const res = await fetch(RPC, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0', id: 'hm', method: 'query',
      params: {
        request_type: 'call_function', account_id: CONTRACT, method_name: method,
        args_base64: btoa(unescape(encodeURIComponent(JSON.stringify(args)))), finality: 'final',
      },
    }),
  });
  const j = await res.json();
  if (j.error) throw new Error(JSON.stringify(j.error));
  if (!j.result || !j.result.result || j.result.result.length === 0) return null;
  return JSON.parse(new TextDecoder().decode(new Uint8Array(j.result.result)));
}

function fmtNear(yocto) {
  try {
    const y = BigInt(yocto);
    const whole = y / 10n ** 24n;
    const frac = (y % 10n ** 24n).toString().padStart(24, '0').replace(/0+$/, '');
    return frac ? `${whole}.${frac}` : `${whole}`;
  } catch (e) { return String(yocto); }
}
function fmtTime(ns) {
  if (ns == null) return '';
  try { return new Date(Number(BigInt(ns) / 1000000n)).toLocaleString(); }
  catch (e) { return String(ns); }
}
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
function trunc(s, head, tail) {
  const t = String(s == null ? '' : s);
  const h = head || 16; const tl = tail || 8;
  return t.length > h + tl + 3 ? t.slice(0, h) + '...' + t.slice(-tl) : t;
}
function shortenAccount(a) {
  const t = String(a || '');
  return t.length > 26 ? t.slice(0, 12) + '...' + t.slice(-10) : t;
}
function copySpan(full) {
  return `<code class="copyable" data-copy="${esc(full)}" title="Click to copy">${esc(trunc(full))}</code>`;
}
document.addEventListener('click', (ev) => {
  const el = ev.target.closest ? ev.target.closest('[data-copy]') : null;
  if (!el) return;
  const v = el.getAttribute('data-copy');
  if (v && navigator.clipboard) navigator.clipboard.writeText(v).catch(() => {});
});

// ---------- evidence menu (fixed points) ----------
const EVIDENCE = [
  { key: 'passkey_attestation', label: 'Passkey attestation', axis: 'human', points: 5 },
  { key: 'aged_social_account', label: 'Aged social account', axis: 'human', points: 2 },
  { key: 'live_challenge', label: 'Live challenge', axis: 'human', points: 3 },
  { key: 'continuous_timelapse', label: 'Continuous timelapse', axis: 'process', points: 4 },
  { key: 'layered_source_file', label: 'Layered source file', axis: 'process', points: 2 },
  { key: 'live_redraw', label: 'Live redraw', axis: 'process', points: 3 },
  { key: 'progress_sketches', label: 'Progress sketches', axis: 'process', points: 1 },
];
const EVIDENCE_BY_KEY = {};
EVIDENCE.forEach((e) => { EVIDENCE_BY_KEY[e.key] = e; });
function itemLabel(key) {
  const e = EVIDENCE_BY_KEY[key];
  return e ? `${e.label} (${e.points} pts, ${e.axis})` : String(key);
}
function levelFor(total) {
  return Math.max(1, Math.min(10, Math.round((10 * total) / 20)));
}

function buildChecklist() {
  const mk = (axis, mountId) => {
    const mount = document.getElementById(mountId);
    EVIDENCE.filter((e) => e.axis === axis).forEach((e) => {
      const row = document.createElement('label');
      row.className = 'checkrow';
      row.innerHTML = `<input type="checkbox" class="evidence-check" value="${esc(e.key)}"> <span>${esc(e.label)} <b>${e.points} pts</b></span>`;
      mount.appendChild(row);
    });
  };
  mk('human', 'humanItems');
  mk('process', 'processItems');
  document.querySelectorAll('.evidence-check').forEach((c) => c.addEventListener('change', updatePreview));
}
function selectedItems() {
  return [...document.querySelectorAll('.evidence-check:checked')].map((c) => c.value);
}
function axisTotals(items) {
  let human = 0; let process = 0;
  (items || []).forEach((k) => {
    const e = EVIDENCE_BY_KEY[k];
    if (!e) return;
    if (e.axis === 'human') human += e.points; else process += e.points;
  });
  return { human, process, total: human + process };
}
function updatePreview() {
  const t = axisTotals(selectedItems());
  document.getElementById('humanSubtotal').textContent = t.human;
  document.getElementById('processSubtotal').textContent = t.process;
  const el = document.getElementById('passPreviewText');
  const base = `at 3 of 5 examiner votes this selection reaches Human ${t.human} / Process ${t.process}.`;
  if (t.human >= 5 && t.process >= 5) {
    el.innerHTML = `${esc(base)} <span class="ok">That clears both axes (5 needed on each). Preview level if every claimed item is verified: ${levelFor(t.total)}, as in "certified at level ${levelFor(t.total)} based on this evidence".</span>`;
  } else {
    const miss = [];
    if (t.human < 5) miss.push(`Human needs ${5 - t.human} more`);
    if (t.process < 5) miss.push(`Process needs ${5 - t.process} more`);
    el.innerHTML = `${esc(base)} <span class="warn">Not a pass yet: ${esc(miss.join('; '))}.</span>`;
  }
}
buildChecklist();
updatePreview();

// ---------- image hash ----------
let imageHash = null;
document.getElementById('imageFile').addEventListener('change', async (ev) => {
  const f = ev.target.files[0];
  const out = document.getElementById('imageHashOut');
  if (!f) { imageHash = null; out.textContent = 'pick a file'; return; }
  const buf = await f.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buf);
  imageHash = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
  out.textContent = imageHash;
});

// ---------- min fee ----------
let minFeeYocto = null;
async function loadMinFee() {
  const note = document.getElementById('minFeeNote');
  try {
    const v = await rpcView('min_fee', {});
    if (v == null) { note.textContent = 'Minimum fee: could not be read from chain yet. Default is 0.05 NEAR.'; return; }
    minFeeYocto = String(v);
    const near = fmtNear(minFeeYocto);
    document.getElementById('feeInput').value = near;
    document.getElementById('feeInput').min = near;
    note.textContent = `Minimum fee: ${near} NEAR (read from chain). You may raise it, you may not lower it.`;
  } catch (e) {
    note.textContent = 'Minimum fee: read failed (' + e.message + '). Default is 0.05 NEAR.';
  }
}
loadMinFee();

// ---------- wallet (multi-wallet, see wallet.js) ----------
document.getElementById('btnWallet').addEventListener('click', async () => {
  if (!window.hmWallet) {
    document.getElementById('walletState').textContent = 'Wallet module still loading, try again in a second.';
    return;
  }
  try { await window.hmWallet.open(); }
  catch (e) { document.getElementById('walletState').textContent = e.message; }
});
async function callContract(method, args, depositYocto) {
  if (!window.hmWallet) throw new Error('Wallet module still loading.');
  return window.hmWallet.call(method, args, depositYocto);
}

// ---------- submit case ----------
document.getElementById('btnSubmitCase').addEventListener('click', async () => {
  const msg = document.getElementById('submitMsg');
  try {
    const bundleHash = document.getElementById('bundleHashInput').value.trim().toLowerCase();
    const claimed = selectedItems();
    if (!imageHash) throw new Error('Pick an image file first, so its SHA-256 is computed.');
    if (!/^[0-9a-f]{64}$/.test(bundleHash)) throw new Error('Bundle hash must be a 64 character hex SHA-256.');
    if (!claimed.length) throw new Error('Claim at least one evidence item.');
    const feeNear = document.getElementById('feeInput').value;
    const fee = nearApi.utils.format.parseNearAmount(feeNear);
    if (!fee) throw new Error('Fee is required.');
    if (minFeeYocto && BigInt(fee) < BigInt(minFeeYocto)) {
      throw new Error(`Fee is below the minimum of ${fmtNear(minFeeYocto)} NEAR.`);
    }
    const result = await callContract('submit_case', {
      image_hash: imageHash,
      bundle_hash: bundleHash,
      claimed_items: claimed,
      judging_window_secs: Number(document.getElementById('judgeWinSelect').value),
    }, fee);
    const hash = result && result.transaction ? result.transaction.hash : '';
    msg.innerHTML = hash
      ? `Submitted. Transaction: <a href="${EXPLORER_TX}${hash}" target="_blank">${esc(hash)}</a>. Examiners can now commit and reveal. Load the Cases screen to find the new case.`
      : 'Submitted. Load the Cases screen to find the new case.';
  } catch (e) { msg.textContent = 'Submit failed: ' + e.message; }
});

// ---------- passkey (WebAuthn) ----------
function bufferToBase64Url(buf) {
  const bytes = new Uint8Array(buf);
  let s = '';
  bytes.forEach((b) => { s += String.fromCharCode(b); });
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function paintPasskey() {
  const out = document.getElementById('passkeyIdOut');
  const stored = (() => { try { return localStorage.getItem('humanmark_passkey_credential_id'); } catch (e) { return null; } })();
  if (stored) out.textContent = stored;
}
(function initPasskey() {
  const btn = document.getElementById('btnPasskey');
  const area = document.getElementById('passkeyArea');
  paintPasskey();
  const available = !!(window.PublicKeyCredential && navigator.credentials && navigator.credentials.create && window.isSecureContext);
  if (!available) {
    btn.disabled = true;
    const note = document.createElement('p');
    note.className = 'hint';
    note.textContent = 'WebAuthn is not available in this browser or context, so passkey enrolment is disabled here. The rest of this page works without it. Enrol from a browser with a platform authenticator to produce a passkey attestation.';
    area.appendChild(note);
    return;
  }
  btn.addEventListener('click', async () => {
    const out = document.getElementById('passkeyIdOut');
    try {
      const challenge = crypto.getRandomValues(new Uint8Array(32));
      const userId = crypto.getRandomValues(new Uint8Array(16));
      const cred = await navigator.credentials.create({
        publicKey: {
          challenge,
          rp: { name: 'Humanmark' },
          user: { id: userId, name: 'humanmark-artist', displayName: 'Humanmark artist' },
          pubKeyCredParams: [
            { type: 'public-key', alg: -7 },
            { type: 'public-key', alg: -257 },
          ],
          authenticatorSelection: { authenticatorAttachment: 'platform', userVerification: 'preferred', residentKey: 'preferred' },
          timeout: 60000,
          attestation: 'direct',
        },
      });
      if (!cred) throw new Error('No credential was created.');
      const id = bufferToBase64Url(cred.rawId);
      try { localStorage.setItem('humanmark_passkey_credential_id', id); } catch (e) { /* storage may be unavailable */ }
      try { localStorage.setItem('humanmark_passkey_enrolled_at', new Date().toISOString()); } catch (e) { /* ignore */ }
      out.textContent = id;
    } catch (e) {
      out.textContent = 'Enrolment failed or was cancelled: ' + e.message;
    }
  });
})();

// ---------- examiners ----------
const EXAMINER_META = [
  { match: 'exam1', display: 'Scanner A', detail: 'yaya36095/ai-source-detector', suffix: 'scanner_a' },
  { match: 'exam2', display: 'Scanner B', detail: 'hungnh1201/ai-image-detector', suffix: 'scanner_b' },
  { match: 'exam3', display: 'Scanner C', detail: 'king1oo1/deepfake-model', suffix: 'scanner_c' },
  { match: 'exam4', display: 'Provenance', detail: 'metadata and C2PA scan, no ML', suffix: 'provenance' },
  { match: 'exam5', display: 'Process auditor', detail: "devil's advocate", suffix: 'process' },
];
function examinerMeta(accountId, index) {
  const byName = EXAMINER_META.find((m) => String(accountId || '').includes(m.match));
  if (byName) return byName;
  return EXAMINER_META[index] || { display: 'Examiner', detail: '', suffix: '' };
}
let examinersCache = null;
async function loadExaminers() {
  if (examinersCache) return examinersCache;
  try {
    const list = await rpcView('examiners', {});
    examinersCache = Array.isArray(list) ? list : [];
  } catch (e) { examinersCache = []; }
  return examinersCache;
}

// ---------- cases list ----------
function caseCard(c) {
  const el = document.createElement('div');
  el.className = 'case clickable';
  const claimedCount = Array.isArray(c.claimed_items) ? c.claimed_items.length : 0;
  el.innerHTML =
    `<div class="top"><b>${esc(c.case_id)}</b><span class="chip ${esc(c.status)}">${esc(c.status)}</span></div>` +
    `<dl>` +
    `<dt>Artist</dt><dd title="${esc(c.artist)}">${esc(shortenAccount(c.artist))}</dd>` +
    `<dt>Claimed items</dt><dd>${claimedCount}</dd>` +
    `<dt>Fee</dt><dd>${fmtNear(c.fee)} NEAR</dd>` +
    `<dt>Created</dt><dd>${esc(fmtTime(c.created_ns))}</dd>` +
    `</dl><p class="hint">Click to open case detail.</p>`;
  el.addEventListener('click', () => {
    document.getElementById('detailCaseId').value = c.case_id;
    showScreen('detail');
    loadDetail(c.case_id);
  });
  return el;
}
async function loadCases() {
  const list = document.getElementById('caseList');
  list.innerHTML = '<p class="hint">Reading from chain...</p>';
  try {
    const cases = await rpcView('get_cases', { from_index: 0, limit: 100 });
    const arr = Array.isArray(cases) ? cases.slice().reverse() : [];
    list.innerHTML = '';
    if (!arr.length) { list.innerHTML = '<p class="hint">No cases on chain yet.</p>'; return; }
    arr.forEach((c) => list.appendChild(caseCard(c)));
  } catch (e) { list.innerHTML = `<p class="warn">Load failed: ${esc(e.message)}</p>`; }
}
document.getElementById('btnLoadCases').addEventListener('click', loadCases);

// ---------- case detail ----------
function axisBar(label, points) {
  const p = Number(points || 0);
  const pct = Math.max(0, Math.min(100, (p / 5) * 100));
  const met = p >= 5;
  return `<div class="axisbar"><div class="axishead"><span>${esc(label)}</span><span>${p} points, 5 needed ${met ? '<b class="ok">met</b>' : ''}</span></div>` +
    `<div class="bar"><div class="fill ${met ? 'met' : ''}" style="width:${pct}%"></div></div></div>`;
}
async function probeReports(caseId, examiners) {
  examiners.forEach((accountId, i) => {
    const meta = examinerMeta(accountId, i);
    if (!meta.suffix) return;
    const slot = document.getElementById(`report-link-${i}`);
    if (!slot) return;
    const url = `reports/${caseId}-${meta.suffix}.json`;
    fetch(url, { method: 'HEAD' })
      .then((r) => {
        if (r.ok) slot.innerHTML = `<a href="${esc(url)}" target="_blank">Report JSON</a>`;
      })
      .catch(() => { /* hide link on failure, slot stays empty */ });
  });
}
async function loadDetail(id) {
  const out = document.getElementById('detailOut');
  out.innerHTML = '<p class="hint">Reading from chain...</p>';
  try {
    const c = await rpcView('get_case', { case_id: id });
    if (!c) { out.innerHTML = '<p class="warn">No such case.</p>'; return; }
    const examiners = await loadExaminers();
    const reveals = Array.isArray(c.reveals) ? c.reveals : [];
    let html = '';
    if (c.status === 'passed') {
      html += `<div class="banner pass"><b>Passed.</b> Certified at level ${esc(c.level)} based on this evidence.` +
        (c.cert_token_id ? ` Certificate token: ${copySpan(c.cert_token_id)} <button type="button" class="small" data-cert-open="${esc(c.cert_token_id)}">View certificate</button>` : '') + `</div>`;
    } else if (c.status === 'failed') {
      html += `<div class="banner fail"><b>Failed.</b> No certificate is minted. The examination fee was paid to the examiners for examining, as agreed. Passing was never for sale.</div>`;
    } else {
      html += `<div class="banner open"><b>Open.</b> Commits recorded: ${esc(c.commits_count != null ? c.commits_count : 0)} of ${examiners.length || 5}. Reveals so far: ${reveals.length}. Fee settled: ${c.fee_settled ? 'yes' : 'no'}.</div>`;
    }
    html += `<div class="case"><div class="top"><b>${esc(c.case_id)}</b><span class="chip ${esc(c.status)}">${esc(c.status)}</span></div><dl>` +
      `<dt>Artist</dt><dd>${esc(c.artist)}</dd>` +
      `<dt>Image hash</dt><dd>${c.image_hash ? copySpan(c.image_hash) : ''}</dd>` +
      `<dt>Bundle hash</dt><dd>${c.bundle_hash ? copySpan(c.bundle_hash) : ''}</dd>` +
      `<dt>Fee</dt><dd>${fmtNear(c.fee)} NEAR${c.fee_settled ? ' (settled)' : ''}</dd>` +
      `<dt>Created</dt><dd>${esc(fmtTime(c.created_ns))}</dd>` +
      `<dt>Judging window</dt><dd>${esc(c.judging_window_secs)} seconds</dd>` +
      (c.level != null ? `<dt>Level</dt><dd>${esc(c.level)}</dd>` : '') +
      (c.cert_token_id ? `<dt>Certificate</dt><dd>${copySpan(c.cert_token_id)}</dd>` : '') +
      `</dl></div>`;
    html += `<h3>Claimed items</h3>`;
    if (Array.isArray(c.claimed_items) && c.claimed_items.length) {
      html += '<ul class="items">' + c.claimed_items.map((k) => `<li>${esc(itemLabel(k))}</li>`).join('') + '</ul>';
    } else {
      html += '<p class="hint">None claimed.</p>';
    }
    html += `<h3>Axes</h3>${axisBar('Human', c.human_points)}${axisBar('Process', c.process_points)}`;
    html += `<p class="hint">An item counts only at 3 of 5 examiner votes. Points above are the totals from revealed votes recorded on chain.</p>`;
    html += `<h3>Examiners</h3><p class="hint">Commits recorded on chain: ${esc(c.commits_count != null ? c.commits_count : 0)}. The contract records a commit count, not a per examiner commit list, so a single examiner shows as committed once they have revealed (a reveal is only possible after a commit).</p>`;
    html += '<table class="votes"><tr><th>Examiner</th><th>Committed</th><th>Revealed</th><th>Verified items</th><th>Report hash</th><th>Report</th></tr>';
    const rows = (examiners.length ? examiners : EXAMINER_META.map((m, i) => 'exam' + (i + 1)));
    rows.forEach((accountId, i) => {
      const meta = examinerMeta(accountId, i);
      const reveal = reveals.find((r) => r.examiner === accountId) ||
        reveals.find((r) => String(r.examiner || '').includes(meta.match));
      const verified = reveal && Array.isArray(reveal.verified_items)
        ? (reveal.verified_items.length ? reveal.verified_items.map((k) => esc(itemLabel(k))).join('<br>') : 'none')
        : '-';
      html += `<tr><td><b>${esc(meta.display)}</b><br><span class="mut">${esc(accountId)}</span><br><span class="mut">${esc(meta.detail)}</span></td>` +
        `<td>${reveal ? 'yes' : 'not shown'}</td><td>${reveal ? 'yes' : 'no'}</td><td>${verified}</td>` +
        `<td>${reveal && reveal.report_hash ? copySpan(reveal.report_hash) : '-'}</td>` +
        `<td><span id="report-link-${i}"></span></td></tr>`;
    });
    html += '</table>';
    out.innerHTML = html;
    const certBtn = out.querySelector('[data-cert-open]');
    if (certBtn) {
      certBtn.addEventListener('click', () => {
        document.getElementById('certTokenId').value = certBtn.getAttribute('data-cert-open');
        showScreen('cert');
        loadCert(certBtn.getAttribute('data-cert-open'));
      });
    }
    probeReports(c.case_id, rows);
  } catch (e) { out.innerHTML = `<p class="warn">Load failed: ${esc(e.message)}</p>`; }
}
document.getElementById('btnLoadDetail').addEventListener('click', () => {
  const id = document.getElementById('detailCaseId').value.trim();
  if (id) loadDetail(id);
});

// ---------- certificate ----------
function parseExtra(extra) {
  if (!extra) return null;
  if (typeof extra === 'object') return extra;
  try { return JSON.parse(extra); } catch (e) { return null; }
}
async function loadCert(tokenId) {
  const out = document.getElementById('certOut');
  out.innerHTML = '<p class="hint">Reading from chain...</p>';
  try {
    const t = await rpcView('nft_token', { token_id: tokenId });
    if (!t) { out.innerHTML = '<p class="warn">No such certificate token.</p>'; return; }
    const md = t.metadata || {};
    const extra = parseExtra(md.extra);
    let html = `<div class="case"><div class="top"><b>${esc(md.title || t.token_id)}</b><span class="chip passed">certificate</span></div><dl>` +
      `<dt>Token ID</dt><dd>${copySpan(t.token_id)}</dd>` +
      `<dt>Owner</dt><dd>${esc(t.owner_id)}</dd>` +
      (md.description ? `<dt>Description</dt><dd>${esc(md.description)}</dd>` : '') +
      (md.issued_at ? `<dt>Issued at</dt><dd>${esc(md.issued_at)}</dd>` : '') +
      `</dl></div>`;
    if (extra) {
      const reportHashes = Array.isArray(extra.report_hashes) ? extra.report_hashes
        : (extra.report_hashes ? [extra.report_hashes] : []);
      html += `<div class="panel"><h3>Evidence summary</h3><dl class="summary">` +
        (extra.case_id ? `<dt>Case</dt><dd>${esc(extra.case_id)}</dd>` : '') +
        (extra.image_hash ? `<dt>Image hash</dt><dd>${copySpan(extra.image_hash)}</dd>` : '') +
        (extra.bundle_hash ? `<dt>Bundle hash</dt><dd>${copySpan(extra.bundle_hash)}</dd>` : '') +
        (extra.human_points != null ? `<dt>Human points</dt><dd>${esc(extra.human_points)}</dd>` : '') +
        (extra.process_points != null ? `<dt>Process points</dt><dd>${esc(extra.process_points)}</dd>` : '') +
        (extra.level != null ? `<dt>Level</dt><dd>${esc(extra.level)}</dd>` : '') +
        `</dl>` +
        (extra.level != null ? `<p><b>Certified at level ${esc(extra.level)} based on this evidence.</b></p>` : '') +
        (reportHashes.length
          ? `<h3>Examiner report hashes</h3><ul class="items">${reportHashes.map((h) => `<li>${copySpan(h)}</li>`).join('')}</ul>`
          : '') +
        `</div>`;
    } else if (md.extra) {
      html += `<div class="panel"><h3>Evidence summary (raw)</h3><p><code>${esc(md.extra)}</code></p></div>`;
    }
    out.innerHTML = html;
  } catch (e) { out.innerHTML = `<p class="warn">Load failed: ${esc(e.message)}</p>`; }
}
document.getElementById('btnLoadCert').addEventListener('click', () => {
  const id = document.getElementById('certTokenId').value.trim();
  if (id) loadCert(id);
});
