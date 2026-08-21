const API_BASE = '/api';
const tokenKey = 'ledgerly_access_token';

function token() { return localStorage.getItem(tokenKey); }
function decodeToken(value) {
    try { return JSON.parse(atob(value.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))); }
    catch (error) { return {}; }
}
function currentIdentity() { return token() ? decodeToken(token()) : {}; }
function initials(identity) { return (identity.name || identity.email || 'User').split(/[ @._-]/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'U'; }
function money(value) { return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0)); }
function date(value) { return value ? new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—'; }
function status(value) { const clean = String(value || 'UNKNOWN').toLowerCase(); return `<span class="status status-${clean}">${clean.replace('_', ' ')}</span>`; }
function toast(message, error = false) { const region = document.querySelector('#toast-region'); if (!region) return; const item = document.createElement('div'); item.className = `toast${error ? ' error' : ''}`; item.textContent = message; region.appendChild(item); setTimeout(() => item.remove(), 3500); }

async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) { localStorage.removeItem(tokenKey); if (!location.pathname.endsWith('/login')) location.href = '/login'; throw new Error(body.error || 'Authentication required'); }
    if (!response.ok) throw new Error(body.error || 'The request could not be completed.');
    return body;
}
async function upload(path, form) {
    const headers = {}; if (token()) headers.Authorization = `Bearer ${token()}`;
    const response = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: new FormData(form) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || 'Upload failed.');
    return body;
}
function formData(form) { return Object.fromEntries(new FormData(form).entries()); }
function showModal(id, open) { const modal = document.getElementById(id); if (modal) modal.hidden = !open; }
function setIdentity() {
    const identity = currentIdentity(); const label = identity.role ? identity.role.replace('_', ' ') : 'Authenticated';
    document.querySelectorAll('[data-user-initials]').forEach(item => item.textContent = initials(identity));
    document.querySelectorAll('[data-user-name]').forEach(item => item.textContent = identity.email || 'Signed in user');
    document.querySelectorAll('[data-user-role]').forEach(item => item.textContent = label);
    document.querySelectorAll('[data-user-first-name]').forEach(item => item.textContent = (identity.email || 'there').split('@')[0]);
}
function setupShell() {
    setIdentity();
    document.querySelector('#menu-toggle')?.addEventListener('click', () => document.querySelector('#sidebar')?.classList.toggle('open'));
    document.querySelector('#logout-button')?.addEventListener('click', async () => { try { await api('/users/logout', { method: 'POST' }); } catch (error) {} localStorage.removeItem(tokenKey); location.href = '/login'; });
    document.querySelector('#refresh-button')?.addEventListener('click', () => location.reload());
    document.querySelectorAll('[data-open-modal]').forEach(button => button.addEventListener('click', () => showModal(button.dataset.openModal, true)));
    document.querySelectorAll('[data-close-modal]').forEach(button => button.addEventListener('click', () => showModal(button.closest('.modal-backdrop').id, false)));
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => backdrop.addEventListener('click', event => { if (event.target === backdrop) showModal(backdrop.id, false); }));
}

async function initLogin() {
    if (token()) { location.href = '/'; return; }
    document.querySelector('#login-form')?.addEventListener('submit', async event => {
        event.preventDefault(); const message = document.querySelector('#login-message'); const button = event.target.querySelector('button'); button.disabled = true; message.textContent = '';
        try { const result = await fetch(`${API_BASE}/users/sigin`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData(event.target)) }); const body = await result.json(); if (!result.ok) throw new Error(body.error || 'Unable to sign in'); localStorage.setItem(tokenKey, body.access_token); location.href = String(decodeToken(body.access_token).role || '').toUpperCase() === 'MANAGER' ? '/manager' : '/'; }
        catch (error) { message.textContent = error.message; button.disabled = false; }
    });
}

async function loadClaims() {
    const table = document.querySelector('#claims-table'); if (!table) return;
    const statusFilter = document.querySelector('#claim-tabs .tab.active')?.dataset.status || ''; const search = document.querySelector('#claim-search')?.value.trim();
    try {
        const params = new URLSearchParams(); if (statusFilter) params.set('status', statusFilter); if (search) params.set('search', search);
        const claims = await api(`/claims${params.toString() ? `?${params}` : ''}`); document.querySelector('#claim-count').textContent = claims.length;
        const role = String(currentIdentity().role || '').toUpperCase();
        table.innerHTML = claims.length ? claims.map(claim => `<tr><td><strong>${claim.claim_number || 'Claim'}</strong><small>${claim.id ? `ID ${claim.id}` : ''}</small></td><td>${date(claim.submitted_at || claim.created_at)}</td><td>${claim.description || 'No description'}</td><td><strong>${money(claim.total_amount)}</strong></td><td>${status(claim.status)}</td><td>${claim.status === 'DRAFT' ? `<button class="text-link submit-claim" data-id="${claim.id}">Submit</button>` : role === 'MANAGER' && ['SUBMITTED','PENDING'].includes(claim.status) ? `<button class="text-link review-claim" data-id="${claim.id}" data-action="APPROVE">Approve</button>` : role === 'FINANCE' && claim.status === 'APPROVED' ? `<button class="text-link review-claim" data-id="${claim.id}" data-action="VERIFY">Verify</button>` : '—'}</td></tr>`).join('') : '<tr><td colspan="6" class="table-state">No claims match this view.</td></tr>';
        document.querySelectorAll('.submit-claim').forEach(button => button.addEventListener('click', () => submitClaim(button.dataset.id)));
        document.querySelectorAll('.review-claim').forEach(button => button.addEventListener('click', () => reviewClaim(button.dataset.id, button.dataset.action)));
    } catch (error) { table.innerHTML = `<tr><td colspan="6" class="table-state">${error.message}</td></tr>`; }
}
async function initClaims() {
    if (!document.querySelector('#claims-table')) return;
    try { const categories = await api('/categories?active=true'); document.querySelector('#claim-category').innerHTML = categories.map(category => `<option value="${category.id}">${category.name}</option>`).join(''); } catch (error) { toast(error.message, true); }
    await loadClaims();
    document.querySelectorAll('#claim-tabs .tab').forEach(tab => tab.addEventListener('click', () => { document.querySelectorAll('#claim-tabs .tab').forEach(item => item.classList.remove('active')); tab.classList.add('active'); loadClaims(); }));
    let timer; document.querySelector('#claim-search')?.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(loadClaims, 300); });
    document.querySelector('#claim-form')?.addEventListener('submit', async event => { event.preventDefault(); try { const values = formData(event.target); const claim = await api('/claims', { method: 'POST', body: JSON.stringify({ claim_number: values.claim_number, description: values.description }) }); const item = await api('/expense-items', { method: 'POST', body: JSON.stringify({ claim_id: claim.claim.id, category_id: Number(values.category_id), description: values.description, amount: Number(values.total_amount), expense_date: values.expense_date }) }); const receipt = event.target.querySelector('[name="receipt"]'); if (receipt.files[0]) { const receiptForm = new FormData(); receiptForm.append('expense_item_id', item.expense_item.id); receiptForm.append('file', receipt.files[0]); await upload('/receipts/upload', receiptForm); } showModal('claim-modal', false); event.target.reset(); toast('Claim created with line item.'); await loadClaims(); } catch (error) { toast(error.message, true); } });
}
async function submitClaim(id) { try { await api(`/claims/${id}/submit`, { method: 'POST' }); toast('Claim submitted for review.'); loadClaims(); } catch (error) { toast(error.message, true); } }
async function reviewClaim(id, action) { try { await api('/approvals', { method: 'POST', body: JSON.stringify({ claim_id: Number(id), action }) }); toast(`Claim ${action.toLowerCase()}d.`); loadClaims(); } catch (error) { toast(error.message, true); } }

function employeeName(employee) { return employee ? `${employee.first_name} ${employee.last_name}` : 'Unknown employee'; }
async function loadManagerTeam() {
    const list = document.querySelector('#manager-team-list'); if (!list) return;
    try {
        const search = document.querySelector('#manager-team-search')?.value.trim();
        const team = await api(`/employees${search ? `?search=${encodeURIComponent(search)}` : ''}`);
        document.querySelector('#manager-team-count').textContent = team.length;
        list.innerHTML = team.length ? team.map(employee => `<div class="data-row"><span class="quick-symbol">${initials({ name: employee.first_name })}</span><div><strong>${employeeName(employee)}</strong><small>${employee.designation || employee.department || 'Team member'}</small></div><span class="muted">${employee.employee_code || ''}</span></div>`).join('') : '<p class="muted">No direct reports found.</p>';
    } catch (error) { list.innerHTML = `<p class="muted">${error.message}</p>`; }
}
async function loadManagerClaims() {
    const table = document.querySelector('#manager-claims-table'); if (!table) return;
    try {
        const statusFilter = document.querySelector('#manager-claim-tabs .tab.active')?.dataset.status || '';
        const search = document.querySelector('#manager-claim-search')?.value.trim();
        const params = new URLSearchParams(); if (statusFilter) params.set('status', statusFilter); if (search) params.set('search', search);
        const [claims, team] = await Promise.all([api(`/claims${params.toString() ? `?${params}` : ''}`), api('/employees')]);
        const employees = Object.fromEntries(team.map(employee => [employee.id, employee]));
        const queue = claims.filter(claim => ['SUBMITTED', 'PENDING', 'IN_REVIEW'].includes(String(claim.status).toUpperCase()));
        document.querySelector('#manager-claim-count').textContent = queue.length;
        document.querySelector('#manager-review-value').textContent = money(queue.reduce((sum, claim) => sum + Number(claim.total_amount || 0), 0));
        table.innerHTML = queue.length ? queue.map(claim => `<tr><td><strong>${claim.claim_number || `Claim #${claim.id}`}</strong><small>${claim.description || 'No description'}</small></td><td>${employeeName(employees[claim.employee_id])}</td><td>${date(claim.submitted_at || claim.created_at)}</td><td><strong>${money(claim.total_amount)}</strong></td><td>${status(claim.status)}</td><td><button class="text-link manager-claim-action" data-id="${claim.id}" data-action="APPROVE">Approve</button><button class="text-link danger-link manager-claim-action" data-id="${claim.id}" data-action="REJECT">Reject</button></td></tr>`).join('') : '<tr><td colspan="6" class="table-state">No claims need your review.</td></tr>';
        document.querySelectorAll('.manager-claim-action').forEach(button => button.addEventListener('click', () => managerClaimDecision(button.dataset.id, button.dataset.action)));
    } catch (error) { table.innerHTML = `<tr><td colspan="6" class="table-state">${error.message}</td></tr>`; }
}
async function managerClaimDecision(id, action) { try { await api('/approvals', { method: 'POST', body: JSON.stringify({ claim_id: Number(id), action }) }); toast(`Claim ${action.toLowerCase()}d.`); loadManagerClaims(); } catch (error) { toast(error.message, true); } }
async function loadManagerTravel() {
    const table = document.querySelector('#manager-travel-table'); if (!table) return;
    try {
        const filter = document.querySelector('#manager-travel-filter')?.value || '';
        const [requests, team] = await Promise.all([api(`/travel-requests${filter ? `?status=${filter}` : ''}`), api('/employees')]);
        const employees = Object.fromEntries(team.map(employee => [employee.id, employee]));
        document.querySelector('#manager-travel-count').textContent = requests.filter(item => item.status === 'PENDING').length;
        table.innerHTML = requests.length ? requests.map(item => `<tr><td><strong>${item.destination}</strong><small>${item.purpose || 'Travel request'}</small></td><td>${employeeName(employees[item.employee_id])}</td><td>${date(item.start_date)} – ${date(item.end_date)}</td><td>${money(item.estimated_cost)}</td><td>${status(item.status)}</td><td>${item.status === 'PENDING' ? `<button class="text-link manager-travel-action" data-id="${item.id}" data-action="APPROVED">Approve</button><button class="text-link danger-link manager-travel-action" data-id="${item.id}" data-action="REJECTED">Reject</button>` : '—'}</td></tr>`).join('') : '<tr><td colspan="6" class="table-state">No travel requests found.</td></tr>';
        document.querySelectorAll('.manager-travel-action').forEach(button => button.addEventListener('click', () => managerTravelDecision(button.dataset.id, button.dataset.action)));
    } catch (error) { table.innerHTML = `<tr><td colspan="6" class="table-state">${error.message}</td></tr>`; }
}
async function managerTravelDecision(id, nextStatus) {
    if (nextStatus === 'REJECTED') { const form = document.querySelector('#manager-reject-form'); form.request_id.value = id; showModal('manager-reject-modal', true); return; }
    try { await api('/travel-requests', { method: 'PATCH', body: JSON.stringify({ request_id: Number(id), status: nextStatus }) }); toast('Travel request approved.'); loadManagerTravel(); } catch (error) { toast(error.message, true); }
}
async function initManagerDashboard() {
    if (!document.querySelector('#manager-team-list')) return;
    await Promise.all([loadManagerTeam(), loadManagerClaims(), loadManagerTravel()]);
    document.querySelector('#manager-refresh')?.addEventListener('click', () => Promise.all([loadManagerTeam(), loadManagerClaims(), loadManagerTravel()]));
    document.querySelectorAll('#manager-claim-tabs .tab').forEach(tab => tab.addEventListener('click', () => { document.querySelectorAll('#manager-claim-tabs .tab').forEach(item => item.classList.remove('active')); tab.classList.add('active'); loadManagerClaims(); }));
    let teamTimer; document.querySelector('#manager-team-search')?.addEventListener('input', () => { clearTimeout(teamTimer); teamTimer = setTimeout(loadManagerTeam, 250); });
    let claimTimer; document.querySelector('#manager-claim-search')?.addEventListener('input', () => { clearTimeout(claimTimer); claimTimer = setTimeout(loadManagerClaims, 250); });
    document.querySelector('#manager-travel-filter')?.addEventListener('change', loadManagerTravel);
    document.querySelector('#manager-reject-form')?.addEventListener('submit', async event => { event.preventDefault(); try { const values = formData(event.target); await api('/travel-requests', { method: 'PATCH', body: JSON.stringify({ request_id: Number(values.request_id), status: 'REJECTED', manager_comment: values.manager_comment }) }); showModal('manager-reject-modal', false); event.target.reset(); toast('Travel request rejected.'); loadManagerTravel(); } catch (error) { toast(error.message, true); } });
}

async function loadTravel() {
    const table = document.querySelector('#travel-table'); if (!table) return; const filter = document.querySelector('#travel-filter')?.value || '';
    try { const requests = await api(`/travel-requests${filter ? `?status=${encodeURIComponent(filter)}` : ''}`); table.innerHTML = requests.length ? requests.map(item => `<tr><td><strong>${item.destination}</strong><small>Request #${item.id}</small></td><td>${item.purpose}</td><td>${date(item.start_date)} – ${date(item.end_date)}</td><td>${money(item.estimated_cost)}</td><td>${status(item.status)}</td><td>${currentIdentity().role && ['MANAGER','ADMIN','SYSTEM_ADMIN'].includes(currentIdentity().role.toUpperCase()) && item.status === 'PENDING' ? `<button class="text-link approve-travel" data-id="${item.id}">Approve</button>` : '—'}</td></tr>`).join('') : '<tr><td colspan="6" class="table-state">No travel requests yet.</td></tr>'; document.querySelectorAll('.approve-travel').forEach(button => button.addEventListener('click', () => updateTravel(button.dataset.id, 'APPROVED'))); }
    catch (error) { table.innerHTML = `<tr><td colspan="6" class="table-state">${error.message}</td></tr>`; }
}
async function updateTravel(id, nextStatus) { try { await api(`/travel-requests/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status: nextStatus }) }); toast('Travel request updated.'); loadTravel(); } catch (error) { toast(error.message, true); } }
async function initTravel() { if (!document.querySelector('#travel-table')) return; await loadTravel(); document.querySelector('#travel-filter')?.addEventListener('change', loadTravel); document.querySelector('#travel-form')?.addEventListener('submit', async event => { event.preventDefault(); try { await api('/travel-requests', { method: 'POST', body: JSON.stringify(formData(event.target)) }); showModal('travel-modal', false); event.target.reset(); toast('Travel request submitted.'); await loadTravel(); } catch (error) { toast(error.message, true); } }); }

async function loadDashboard() { if (!document.querySelector('#metric-claims')) return; try { const [claims, travel] = await Promise.all([api('/claims'), api('/travel-requests')]); const approved = claims.filter(item => String(item.status).toUpperCase() === 'APPROVED'); const pending = claims.filter(item => ['PENDING','SUBMITTED','IN_REVIEW'].includes(String(item.status).toUpperCase())); document.querySelector('#metric-claims').textContent = claims.length; document.querySelector('#metric-review').textContent = pending.length; document.querySelector('#metric-approved').textContent = money(approved.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)); document.querySelector('#metric-travel').textContent = travel.length; const recent = document.querySelector('#recent-claims'); recent.innerHTML = claims.slice(-4).reverse().map(item => `<div class="data-row"><span class="quick-symbol">$</span><div><strong>${item.claim_number || 'Expense claim'}</strong><small>${item.description || 'No description'}</small></div>${status(item.status)}</div>`).join('') || '<p class="muted">No claims to show yet.</p>'; } catch (error) { toast(error.message, true); } }
async function initReports() { if (!document.querySelector('#status-report')) return; try { const claims = await api('/claims'); const groups = ['APPROVED','PENDING','DRAFT','REJECTED'].map(value => ({ value, count: claims.filter(item => String(item.status).toUpperCase() === value).length })); const total = claims.reduce((sum, item) => sum + Number(item.total_amount || 0), 0); document.querySelector('#report-total').textContent = money(total); document.querySelector('#report-approved').textContent = money(claims.filter(item => String(item.status).toUpperCase() === 'APPROVED').reduce((sum, item) => sum + Number(item.total_amount || 0), 0)); document.querySelector('#report-pending').textContent = groups[1].count; document.querySelector('#report-draft').textContent = groups[2].count; document.querySelector('#status-report').innerHTML = groups.map(group => `<div class="bar-item"><span>${group.value.toLowerCase()}</span><div class="bar-track"><div class="bar-fill" style="width:${claims.length ? Math.max(5, group.count / claims.length * 100) : 5}%"></div></div><strong>${group.count}</strong></div>`).join(''); document.querySelector('#export-report')?.addEventListener('click', () => { const csv = ['claim_number,status,total_amount', ...claims.map(item => `${item.claim_number || ''},${item.status || ''},${item.total_amount || 0}`)].join('\n'); const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); link.download = 'ledgerly-claims.csv'; link.click(); }); } catch (error) { toast(error.message, true); } }

if (document.body.classList.contains('login-page')) initLogin(); else { setupShell(); initManagerDashboard(); loadDashboard(); initClaims(); initTravel(); initReports(); }
