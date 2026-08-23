async function financeApp() {
    const root = $('#finance-app');
    root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">FINANCE ADMIN</p><h1>Financial verification</h1><p class="muted">Verify manager-approved claims and process reimbursements.</p></div></div><div class="metrics" id="finance-metrics"></div><section class="panel"><div class="panel-head"><h2>Claim verification queue</h2><div><input id="finance-search" placeholder="Employee or claim ID"><select id="finance-filter"><option value="APPROVED">Awaiting verification</option><option value="VERIFIED">Verified</option><option value="REJECTED">Rejected</option><option value="">All statuses</option></select><input id="finance-date" type="date" aria-label="Submitted after"></div></div><div class="table-wrap"><table><thead><tr><th>Claim</th><th>Employee</th><th>Travel request</th><th>Total</th><th>Submitted</th><th>Status</th><th>Action</th></tr></thead><tbody id="finance-claims"></tbody></table></div></section><section class="panel" id="finance-detail" hidden></section><section class="panel"><div class="panel-head"><h2>Reimbursements</h2><button class="button secondary" id="refresh-finance" type="button">Refresh</button></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Claim</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead><tbody id="reimbursements"></tbody></table></div></section>`;
    let claims = [];
    let employees = [];
    let travel = [];
    let reimbursements = [];
    const detail = $('#finance-detail');
    const employeeName = id => { const person = employees.find(item => item.id === id); return person ? `${person.first_name} ${person.last_name}` : `Employee ${id}`; };

    const load = async () => {
        try {
            [claims, employees, travel] = await Promise.all([apiFetch('/claims'), apiFetch('/employees'), apiFetch('/travel-requests')]);
            const reimbursementLists = await Promise.all(['PENDING', 'PROCESSING', 'PAID', 'REJECTED'].map(statusValue => apiFetch(`/reimbursements?status=${statusValue}`).catch(() => [])));
            reimbursements = reimbursementLists.flat();
            render();
            renderReimbursements();
        } catch (error) { toast(error.message); }
    };

    const render = () => {
        const search = $('#finance-search').value.trim().toLowerCase();
        const selectedStatus = $('#finance-filter').value;
        const after = $('#finance-date').value;
        const filtered = claims.filter(claim => (!selectedStatus || claim.status === selectedStatus) && (!search || `${employeeName(claim.employee_id)} ${claim.claim_number} ${claim.id}`.toLowerCase().includes(search)) && (!after || (claim.submitted_at || claim.created_at).slice(0, 10) >= after));
        const pending = claims.filter(claim => claim.status === 'APPROVED');
        $('#finance-metrics').innerHTML = card('Awaiting verification', pending.length, 'Manager-approved claims') + card('Pending value', money(pending.reduce((sum, claim) => sum + Number(claim.total_amount || 0), 0)), 'Submitted claim totals') + card('Reimbursements', reimbursements.length, 'Pending finance actions');
        $('#finance-claims').innerHTML = filtered.map(claim => `<tr><td>${esc(claim.claim_number)}</td><td>${esc(employeeName(claim.employee_id))}</td><td>${claim.travel_request_id || '-'}</td><td>${money(claim.total_amount)}</td><td>${date(claim.submitted_at)}</td><td>${status(claim.status)}</td><td><button class="link finance-claim-detail" data-id="${claim.id}" type="button">View details</button>${claim.status === 'APPROVED' ? '<button class="link finance-verify" data-id="' + claim.id + '" type="button">Verify</button><button class="link danger finance-return" data-id="' + claim.id + '" type="button">Return</button>' : '-'}</td></tr>`).join('') || '<tr><td colspan="7" class="empty">No claims found.</td></tr>';
    };

    const renderReimbursements = () => {
        $('#reimbursements').innerHTML = reimbursements.map(item => `<tr><td>${item.id}</td><td>${item.claim_id}</td><td>${money(item.amount)}</td><td>${status(item.status)}</td><td>${item.status === 'PENDING' ? `<button class="link reimbursement-process" data-id="${item.id}" data-status="PROCESSING" type="button">Start processing</button>` : item.status === 'PROCESSING' ? `<button class="link reimbursement-process" data-id="${item.id}" data-status="PAID" type="button">Mark paid</button>` : '-'}</td></tr>`).join('') || '<tr><td colspan="5" class="empty">No pending reimbursements.</td></tr>';
    };

    const showClaim = async claimId => {
        try {
            const claim = await apiFetch(`/claims/${claimId}`);
            const request = claim.travel_request_id ? await apiFetch(`/travel-requests/${claim.travel_request_id}`) : null;
            const items = await apiFetch(`/expense-items?claim_id=${claim.id}`);
            const policies = await apiFetch('/policies');
            const details = await Promise.all(items.map(async item => ({ item, receipts: await apiFetch(`/receipts?expense_item_id=${item.id}`) })));
            const approvals = await apiFetch(`/approvals?claim_id=${claim.id}`);
            const invalid = details.filter(({ item, receipts }) => { const policy = policies.find(value => value.category_id === item.category_id && value.is_active); return policy && ((policy.max_amount != null && Number(item.amount) > Number(policy.max_amount)) || (policy.requires_receipt && !receipts.length)); });
            const validAmount = details.filter(({ item }) => !invalid.some(entry => entry.item.id === item.id)).reduce((sum, entry) => sum + Number(entry.item.amount), 0);
            detail.hidden = false;
            detail.innerHTML = `<div class="panel-head"><div><h2>Claim ${esc(claim.claim_number)}</h2><p class="muted">Financial verification details</p></div><button class="button secondary close-finance-detail" type="button">Close</button></div><div class="profile-grid"><div><span class="muted">Employee</span><strong>${esc(employeeName(claim.employee_id))}</strong></div><div><span class="muted">Claim ID</span><strong>${claim.id}</strong></div><div><span class="muted">Travel request</span><strong>${request ? `${esc(request.destination)} (${date(request.start_date)} - ${date(request.end_date)})` : '-'}</strong></div><div><span class="muted">Claimed amount</span><strong>${money(claim.total_amount)}</strong></div><div><span class="muted">Valid reimbursable amount</span><strong>${money(validAmount)}</strong></div><div><span class="muted">Status</span><strong>${status(claim.status)}</strong></div></div>${request ? `<hr><h3>Approved travel request</h3><p>${esc(request.destination)} - ${esc(request.purpose)}</p><p class="muted">Estimated cost ${money(request.estimated_cost)} | ${status(request.status)} | Comment: ${esc(request.manager_comment || '-')}</p>` : ''}<hr><h3>Expense items and policy checks</h3><div class="list">${details.map(({ item, receipts }) => { const policy = policies.find(value => value.category_id === item.category_id && value.is_active); const itemInvalid = invalid.some(entry => entry.item.id === item.id); return `<div class="row"><div class="row-content"><strong>${esc(item.description)} - ${money(item.amount)}</strong><small>Category ${item.category_id} | ${date(item.expense_date)} | Limit ${policy?.max_amount == null ? 'none' : money(policy.max_amount)} | ${receipts.length} receipt(s)</small>${itemInvalid ? '<small class="error">Invalid expense or required receipt missing</small>' : '<small>Policy check passed</small>'}<small>${receipts.map(receipt => `${esc(receipt.file_name)} (${esc(receipt.file_type)}) <button class="link receipt-download" data-id="${receipt.id}" type="button">View/download</button>`).join('<br>') || 'No receipt uploaded'}</small></div></div>`; }).join('') || '<p class="empty">No expense items.</p>'}</div><hr><h3>Manager approval history</h3><div class="list">${approvals.map(approval => `<div class="row"><div class="row-content"><strong>${esc(approval.action)}</strong><small>User ${approval.approver_id} | ${date(approval.created_at)}</small></div><span>${esc(approval.comment || '')}</span></div>`).join('') || '<p class="empty">No approval history.</p>'}</div><div class="form-grid"><button class="button primary finance-verify" data-id="${claim.id}" type="button" ${claim.status !== 'APPROVED' || invalid.length ? 'disabled' : ''}>Verify claim</button><button class="button secondary finance-return" data-id="${claim.id}" type="button" ${claim.status !== 'APPROVED' ? 'disabled' : ''}>Return claim</button>${claim.status === 'VERIFIED' ? `<button class="button primary create-reimbursement" data-id="${claim.id}" data-amount="${validAmount}" type="button">Create reimbursement (${money(validAmount)})</button>` : ''}</div>`;
            detail.querySelector('.close-finance-detail').onclick = () => { detail.hidden = true; };
            detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) { toast(error.message); }
    };

    root.addEventListener('click', async event => {
        const claimButton = event.target.closest('.finance-claim-detail');
        if (claimButton) return showClaim(Number(claimButton.dataset.id));
        const receipt = event.target.closest('.receipt-download');
        if (receipt) { try { const response = await fetch(`${API_BASE}/receipts/${receipt.dataset.id}/download`, { headers: { Authorization: `Bearer ${getToken()}` } }); if (!response.ok) throw new Error('Receipt download failed.'); const link = document.createElement('a'); link.href = URL.createObjectURL(await response.blob()); link.download = ''; link.click(); URL.revokeObjectURL(link.href); } catch (error) { toast(error.message); } return; }
        const verify = event.target.closest('.finance-verify');
        if (verify) { verify.disabled = true; try { await apiFetch('/approvals', { method: 'POST', body: JSON.stringify({ claim_id: Number(verify.dataset.id), action: 'VERIFY' }) }); toast('Claim verified'); await load(); } catch (error) { verify.disabled = false; toast(`Verify failed: ${error.message}`); } return; }
        const reject = event.target.closest('.finance-return');
        if (reject) { const comment = prompt('Reason for returning this claim:'); if (!comment?.trim()) return; try { await apiFetch('/approvals', { method: 'POST', body: JSON.stringify({ claim_id: Number(reject.dataset.id), action: 'REJECT', comment: comment.trim() }) }); toast('Claim returned'); await load(); } catch (error) { toast(error.message); } return; }
        const create = event.target.closest('.create-reimbursement');
        if (create) { try { await apiFetch('/reimbursements', { method: 'POST', body: JSON.stringify({ claim_id: Number(create.dataset.id), amount: Number(create.dataset.amount) }) }); toast('Reimbursement created'); await load(); } catch (error) { toast(error.message); } return; }
        const process = event.target.closest('.reimbursement-process');
        if (process) { const payload = { status: process.dataset.status }; if (process.dataset.status === 'PAID') { payload.payment_method = prompt('Payment method:'); payload.transaction_reference = prompt('Transaction reference:'); if (!payload.payment_method || !payload.transaction_reference) return; } process.disabled = true; try { await apiFetch(`/reimbursements/${process.dataset.id}/process`, { method: 'PATCH', body: JSON.stringify(payload) }); toast(process.dataset.status === 'PAID' ? 'Reimbursement marked paid' : 'Reimbursement processing started'); await load(); } catch (error) { process.disabled = false; toast(`Reimbursement update failed: ${error.message}`); } }
    });
    $('#finance-search').oninput = render;
    $('#finance-filter').onchange = render;
    $('#finance-date').onchange = render;
    $('#refresh-finance').onclick = load;
    await load();
}

if (['FINANCE_ADMIN'].includes(document.body.dataset.role)) financeApp();
