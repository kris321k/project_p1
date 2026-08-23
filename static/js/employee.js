async function employeeApp() {
    const root = $('#employee-app');
    root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">EMPLOYEE PORTAL</p><h1 id="employee-welcome">Welcome back</h1><p class="muted">Manage your travel and expenses</p></div><div class="form-actions"><button class="button primary" id="create-travel">Create Travel Request</button><button class="button secondary" id="create-claim">Create Expense Claim</button></div></div><section class="panel" id="travel-form-panel" hidden><div class="panel-head"><h2>Create travel request</h2><button class="button secondary" id="close-travel" type="button">Close</button></div><form id="travel-form" class="form-grid"><label>Destination<input name="destination" required></label><label>Purpose<input name="purpose" required></label><label>Start date<input name="start_date" type="date" required></label><label>End date<input name="end_date" type="date" required></label><label>Estimated cost<input name="estimated_cost" type="number" min="0" step="0.01" required></label><button class="button primary full" type="submit">Submit request</button></form></section><div class="metrics" id="employee-metrics"></div><div class="grid"><section class="panel"><div class="panel-head"><h2>My Recent Travel Requests</h2><a class="link" href="/employee/travel">View all</a></div><div class="table-wrap"><table><thead><tr><th>Destination</th><th>Dates</th><th>Estimated cost</th><th>Status</th><th>Action</th></tr></thead><tbody id="recent-travel"></tbody></table></div></section><section class="panel"><div class="panel-head"><h2>My Recent Claims</h2><a class="link" href="/employee/claims">View all</a></div><div class="table-wrap"><table><thead><tr><th>Claim</th><th>Amount</th><th>Claim status</th><th>Reimbursement status</th><th>Action</th></tr></thead><tbody id="recent-claims"></tbody></table></div></section></div>`;
    const travelPanel = $('#travel-form-panel');
    $('#create-travel').onclick = () => { travelPanel.hidden = false; travelPanel.scrollIntoView({ behavior: 'smooth', block: 'start' }); };
    $('#close-travel').onclick = () => { travelPanel.hidden = true; };
    $('#create-claim').onclick = () => { window.location.href = '/employee/travel'; };
    $('#travel-form').onsubmit = async event => {
        event.preventDefault();
        const button = event.target.querySelector('button[type="submit"]');
        button.disabled = true;
        try {
            await apiFetch('/travel-requests', { method: 'POST', body: JSON.stringify(jsonBody(event.target)) });
            toast('Travel request submitted');
            event.target.reset();
            travelPanel.hidden = true;
            await loadDashboard();
        } catch (error) {
            toast(error.message);
        } finally {
            button.disabled = false;
        }
    };

    async function loadDashboard() {
        try {
            const [profile, travel, claims, reimbursements] = await Promise.all([apiFetch('/employees/me'), apiFetch('/travel-requests'), apiFetch('/claims'), apiFetch('/reimbursements?mine=true')]);
            $('#employee-welcome').textContent = `Welcome back, ${profile.first_name}`;
            const pending = claims.filter(claim => ['SUBMITTED', 'PENDING'].includes(claim.status));
            const reimbursedAmount = reimbursements.filter(item => ['PENDING', 'PROCESSING', 'PAID'].includes(item.status)).reduce((sum, item) => sum + Number(item.amount || 0), 0);
            $('#employee-metrics').innerHTML = card('Travel Requests', travel.length, 'All requests') + card('Claims', claims.length, 'All claims') + card('Pending', pending.length, 'Awaiting review') + card('Reimbursed', money(reimbursedAmount), 'Reimbursement amount');
            $('#recent-travel').innerHTML = travel.slice(0, 5).map(request => `<tr><td>${esc(request.destination)}</td><td>${date(request.start_date)} - ${date(request.end_date)}</td><td>${money(request.estimated_cost)}</td><td>${status(request.status)}</td><td><a class="link" href="/employee/travel">View</a></td></tr>`).join('') || '<tr><td colspan="5" class="empty">No travel requests found.</td></tr>';
            const reimbursementsByClaim = new Map(reimbursements.map(item => [item.claim_id, item]));
            $('#recent-claims').innerHTML = claims.slice(0, 5).map(claim => { const reimbursement = reimbursementsByClaim.get(claim.id); return `<tr><td>${esc(claim.claim_number)}</td><td>${money(claim.total_amount)}</td><td>${status(claim.status)}</td><td>${reimbursement ? status(reimbursement.status) : '<span class="muted">Not created</span>'}</td><td><a class="link" href="/employee/claims">View</a></td></tr>`; }).join('') || '<tr><td colspan="5" class="empty">No claims found.</td></tr>';
        } catch (error) {
            toast(error.message);
        }
    }

    await loadDashboard();
}

if (document.body.dataset.role === 'EMPLOYEE') employeeApp();
