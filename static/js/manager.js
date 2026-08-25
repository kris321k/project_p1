async function managerApp() {
	const root = $('#manager-app');
	root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">MANAGER PORTAL</p><h1>Team approvals</h1><p class="muted">Review direct-report claims and travel requests.</p></div><button class="button primary" id="register-user">Register employee</button></div><div class="metrics" id="manager-metrics"></div><div class="grid"><section class="panel"><div class="panel-head"><h2>Claims</h2><div><input id="claim-search" placeholder="Search claims"><select id="claim-status"><option value="">All statuses</option><option value="SUBMITTED">Submitted</option><option value="PENDING">Pending</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option></select></div></div><div class="table-wrap"><table><thead><tr><th>Claim</th><th>Employee</th><th>Total</th><th>Status</th><th>Action</th></tr></thead><tbody id="manager-claims"></tbody></table></div></section><section class="panel"><div class="panel-head"><h2>Team directory</h2></div><div class="list" id="team-list"></div></section></div><section class="panel"><div class="panel-head"><h2>Travel requests</h2><select id="travel-status"><option value="">All</option><option>PENDING</option><option>APPROVED</option><option>REJECTED</option></select></div><div class="table-wrap"><table><thead><tr><th>Destination</th><th>Employee ID</th><th>Dates</th><th>Cost</th><th>Status</th><th>Action</th></tr></thead><tbody id="manager-travel"></tbody></table></div></section><section class="panel" id="manager-detail" hidden></section><section class="panel" id="register-panel" hidden><h2>Register employee</h2><form id="register-form" class="form-grid"><label>First name<input name="first_name" required></label><label>Last name<input name="last_name" required></label><label>Department<input name="department" required></label><label>Phone number<input name="phone" type="tel" required></label><label>Email<input name="email" type="email" required></label><label>Password<input name="password" type="password" minlength="8" required></label><label>Role<select name="role"><option>EMPLOYEE</option></select></label><button class="button primary full">Create employee</button></form></section>`;

	let people = [];
	let claims = [];
	let travelRequests = [];
	const detail = $('#manager-detail');

	const employeeName = employeeId => {
		const employee = people.find(person => person.id === employeeId);
		return employee ? `${employee.first_name} ${employee.last_name}` : `Employee ${employeeId}`;
	};

	const showTravelDetails = async requestId => {
		try {
			const request = await apiFetch(`/travel-requests/${requestId}`);
			const claim = claims.find(item => item.travel_request_id === request.id);
			detail.hidden = false;
			detail.innerHTML = `<div class="panel-head"><div><h2>Travel request #${request.id}</h2><p class="muted">Complete request information</p></div><button class="button secondary close-detail" type="button">Close</button></div><div class="profile-grid"><div><span class="muted">Employee</span><strong>${esc(employeeName(request.employee_id))}</strong></div><div><span class="muted">Employee ID</span><strong>${request.employee_id}</strong></div><div><span class="muted">Destination</span><strong>${esc(request.destination)}</strong></div><div><span class="muted">Purpose</span><strong>${esc(request.purpose)}</strong></div><div><span class="muted">Start date</span><strong>${date(request.start_date)}</strong></div><div><span class="muted">End date</span><strong>${date(request.end_date)}</strong></div><div><span class="muted">Estimated cost</span><strong>${money(request.estimated_cost)}</strong></div><div><span class="muted">Request status</span><strong>${status(request.status)}</strong></div><div><span class="muted">Manager comment</span><strong>${esc(request.manager_comment || '-')}</strong></div><div><span class="muted">Created</span><strong>${date(request.created_at)}</strong></div></div>${claim ? `<hr><p class="muted">Linked claim</p><strong>${esc(claim.claim_number)} - ${status(claim.status)} - ${money(claim.total_amount)}</strong>` : '<p class="empty">No claim linked to this travel request.</p>'}`;
			detail.querySelector('.close-detail').onclick = () => { detail.hidden = true; };
			detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
		} catch (error) {
			toast(error.message);
		}
	};

	const showClaimDetails = async claimId => {
		try {
			const claim = await apiFetch(`/claims/${claimId}`);
			const items = await apiFetch(`/expense-items?claim_id=${claim.id}`);
			const itemDetails = await Promise.all(items.map(async item => ({ item, receipts: await apiFetch(`/receipts?expense_item_id=${item.id}`) })));
			const approvals = await apiFetch(`/approvals?claim_id=${claim.id}`);
			detail.hidden = false;
			detail.innerHTML = `<div class="panel-head"><div><h2>Claim ${esc(claim.claim_number)}</h2><p class="muted">Complete claim information and approval history</p></div><button class="button secondary close-detail" type="button">Close</button></div><div class="profile-grid"><div><span class="muted">Employee</span><strong>${esc(employeeName(claim.employee_id))}</strong></div><div><span class="muted">Employee ID</span><strong>${claim.employee_id}</strong></div><div><span class="muted">Travel request ID</span><strong>${claim.travel_request_id || '-'}</strong></div><div><span class="muted">Claim total</span><strong>${money(claim.total_amount)}</strong></div><div><span class="muted">Status</span><strong>${status(claim.status)}</strong></div><div><span class="muted">Submitted</span><strong>${date(claim.submitted_at)}</strong></div><div><span class="muted">Created</span><strong>${date(claim.created_at)}</strong></div><div><span class="muted">Updated</span><strong>${date(claim.updated_at)}</strong></div></div><hr><h3>Expense items and receipts</h3><div class="list">${itemDetails.map(({ item, receipts }) => `<div class="row"><div class="row-content"><strong>${esc(item.description)}</strong><small>Category ${item.category_id} - ${money(item.amount)} - ${date(item.expense_date)}${item.merchant ? ` - ${esc(item.merchant)}` : ''}</small><small>${receipts.map(receipt => `${esc(receipt.file_name)} (${esc(receipt.file_type)}, ${receipt.file_size} bytes) <button class="link receipt-download" data-id="${receipt.id}" type="button">Download</button>`).join('<br>') || 'No receipt uploaded'}</small></div><span>${receipts.length} receipt(s)</span></div>`).join('') || '<p class="empty">No expense items.</p>'}</div><hr><h3>Approval history</h3><div class="list">${approvals.map(approval => `<div class="row"><div class="row-content"><strong>${esc(approval.action)}</strong><small>Approver ${approval.approver_id} - ${date(approval.created_at)}</small></div><span>${esc(approval.comment || '')}</span></div>`).join('') || '<p class="empty">No approval history.</p>'}</div>`;
			detail.querySelector('.close-detail').onclick = () => { detail.hidden = true; };
			detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
		} catch (error) {
			toast(error.message);
		}
	};

	const load = async () => {
		try {
			const [claimList, team, travel] = await Promise.all([apiFetch('/claims'), apiFetch('/employees'), apiFetch('/travel-requests')]);
			claims = claimList;
			people = team;
			travelRequests = travel;
			const selectedClaimStatus = $('#claim-status').value;
			const claimSearch = $('#claim-search').value.trim().toLowerCase();
			const visibleClaims = claims.filter(claim => (!selectedClaimStatus || claim.status === selectedClaimStatus) && (!claimSearch || `${claim.claim_number} ${employeeName(claim.employee_id)} ${claim.employee_id}`.toLowerCase().includes(claimSearch)));
			const open = claims.filter(claim => ['SUBMITTED', 'PENDING'].includes(claim.status));
			$('#manager-metrics').innerHTML = card('Pending approvals', open.length, 'Claims needing review') + card('Open value', money(open.reduce((sum, claim) => sum + Number(claim.total_amount || 0), 0)), 'Claim total') + card('Direct reports', team.length, 'Assigned employees');
			$('#manager-claims').innerHTML = visibleClaims.map(claim => `<tr><td>${esc(claim.claim_number)}</td><td>${esc(employeeName(claim.employee_id))}</td><td>${money(claim.total_amount)}</td><td>${status(claim.status)}</td><td><button class="link claim-detail" data-id="${claim.id}" type="button">View details</button>${claim.status === 'SUBMITTED' || claim.status === 'PENDING' ? `<button class="link decision" data-id="${claim.id}" data-action="APPROVE">Approve</button><button class="link danger decision" data-id="${claim.id}" data-action="REJECT">Reject</button>` : '-'}</td></tr>`).join('') || '<tr><td colspan="5" class="empty">No claims found.</td></tr>';
			$('#team-list').innerHTML = team.map(employee => `<div class="row"><div class="row-content"><strong>${esc(`${employee.first_name} ${employee.last_name}`)}</strong><small>${esc(employee.department)} / ${esc(employee.designation)}</small></div></div>`).join('') || '<p class="empty">No direct reports.</p>';
			$('#manager-travel').innerHTML = travel.map(request => `<tr><td>${esc(request.destination)}</td><td>${request.employee_id}</td><td>${date(request.start_date)} - ${date(request.end_date)}</td><td>${money(request.estimated_cost)}</td><td>${status(request.status)}</td><td><button class="link travel-detail" data-id="${request.id}" type="button">View details</button>${request.status === 'PENDING' ? `<button class="link travel-decision" data-id="${request.id}" data-action="APPROVED">Approve</button><button class="link danger travel-decision" data-id="${request.id}" data-action="REJECTED">Reject</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="6" class="empty">No travel requests.</td></tr>';
		} catch (error) {
			toast(error.message);
		}
	};

	await load();
	root.addEventListener('click', async event => {
		const claimDetail = event.target.closest('.claim-detail');
		if (claimDetail) return showClaimDetails(Number(claimDetail.dataset.id));
		const travelDetail = event.target.closest('.travel-detail');
		if (travelDetail) return showTravelDetails(Number(travelDetail.dataset.id));
		const receiptDownload = event.target.closest('.receipt-download');
		if (receiptDownload) {
			try {
				const response = await fetch(`${API_BASE}/receipts/${receiptDownload.dataset.id}/download`, { headers: { Authorization: `Bearer ${getToken()}` } });
				if (!response.ok) throw new Error('Receipt download failed.');
				const link = document.createElement('a');
				link.href = URL.createObjectURL(await response.blob());
				link.download = '';
				link.click();
				URL.revokeObjectURL(link.href);
			} catch (error) { toast(error.message); }
			return;
		}
		const decision = event.target.closest('.decision');
		if (decision) {
			try {
				await apiFetch('/approvals', { method: 'POST', body: JSON.stringify({ claim_id: Number(decision.dataset.id), action: decision.dataset.action }) });
				await load();
			} catch (error) { toast(error.message); }
		}
		const travelDecision = event.target.closest('.travel-decision');
		if (travelDecision) {
			const comment = travelDecision.dataset.action === 'REJECTED' ? prompt('Reason for rejection:') : null;
			if (travelDecision.dataset.action === 'REJECTED' && !comment) return;
			try {
				await apiFetch('/travel-requests', { method: 'PATCH', body: JSON.stringify({ request_id: Number(travelDecision.dataset.id), status: travelDecision.dataset.action, manager_comment: comment }) });
				await load();
			} catch (error) { toast(error.message); }
		}
	});

	
	$('#register-user').onclick = () => { $('#register-panel').hidden = !$('#register-panel').hidden; };
	$('#register-form').onsubmit = async event => {
		event.preventDefault();
		const form = event.target;
		const submit = form.querySelector('button[type="submit"], button:not([type])');
		const data = jsonBody(form);
		submit.disabled = true;
		try {
			await apiFetch('/users/register', { method: 'POST', body: JSON.stringify({ first_name: data.first_name.trim(), last_name: data.last_name.trim(), department: data.department.trim(), phone: data.phone.trim(), email: data.email.trim(), password: data.password, role: data.role.toUpperCase() }) });
			toast('User registered');
			form.reset();
			$('#register-panel').hidden = true;
			await load();
		} catch (error) {
			toast(error.message);
		} finally {
			submit.disabled = false;
		}
	};
	$('#claim-search').oninput = load;
	$('#claim-status').onchange = load;
	$('#travel-status').onchange = async event => {
		try { const list = await apiFetch(`/travel-requests${event.target.value ? `?status=${event.target.value}` : ''}`); toast(`${list.length} requests found`); await load(); } catch (error) { toast(error.message); }
	};
}

if (document.body.dataset.role === 'MANAGER') managerApp();
