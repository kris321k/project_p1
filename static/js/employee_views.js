async function loadEmployeeView() {
    const root = $('#employee-view');
    const view = root.dataset.view;
    try {
        if (view === 'profile') {
            const employee = await apiFetch('/employees/me');
            root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">EMPLOYEE PROFILE</p><h1>My profile</h1><p class="muted">Your employee account details.</p></div></div><section class="panel profile-grid"><div><span class="muted">Employee code</span><strong>${esc(employee.employee_code)}</strong></div><div><span class="muted">Name</span><strong>${esc(`${employee.first_name} ${employee.last_name}`)}</strong></div><div><span class="muted">Department</span><strong>${esc(employee.department)}</strong></div><div><span class="muted">Designation</span><strong>${esc(employee.designation)}</strong></div><div><span class="muted">Phone</span><strong>${esc(employee.phone || '-')}</strong></div><div><span class="muted">Manager ID</span><strong>${esc(employee.manager_id || '-')}</strong></div></section>`;
            return;
        }

        if (view === 'travel') {
            const [requests, claims] = await Promise.all([apiFetch('/travel-requests'), apiFetch('/claims')]);
            const claimsByTravelRequest = new Map(claims.filter(claim => claim.travel_request_id != null).map(claim => [claim.travel_request_id, claim]));
            root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">EMPLOYEE PORTAL</p><h1>Travel requests</h1><p class="muted">View your travel requests and create one claim for each request.</p></div></div><section class="panel"><div class="table-wrap"><table><thead><tr><th>Destination</th><th>Purpose</th><th>Start</th><th>End</th><th>Estimated cost</th><th>Status</th><th>Action</th></tr></thead><tbody>${requests.map(item => { const claim = claimsByTravelRequest.get(item.id); const action = claim ? `<button class="button secondary" type="button" disabled>Create claim</button><div>${status(claim.status)}</div><small class="muted">Claim ${esc(claim.claim_number)}</small>` : `<button class="button secondary create-travel-claim" data-id="${item.id}" type="button">Create claim</button>`; return `<tr><td>${esc(item.destination)}</td><td>${esc(item.purpose)}</td><td>${date(item.start_date)}</td><td>${date(item.end_date)}</td><td>${money(item.estimated_cost)}</td><td>${status(item.status)}</td><td>${action}</td></tr>`; }).join('') || '<tr><td colspan="7" class="empty">No travel requests found.</td></tr>'}</tbody></table></div></section><section class="panel" id="travel-claim-workflow" hidden></section>`;
            const workflow = $('#travel-claim-workflow');
            const categories = await apiFetch('/categories?active=true');

            const renderItems = items => {
                workflow.querySelector('#claim-total').textContent = money(items.reduce((total, item) => total + Number(item.amount || 0), 0));
                workflow.querySelector('#claim-items').innerHTML = items.map(item => `<div class="row"><div class="row-content"><strong>${esc(item.description)}</strong><small>${esc(item.category_name)} - ${money(item.amount)} - ${item.receipt_count} receipt(s)</small></div><span>${item.receipt_count ? status('RECEIPT READY') : status('RECEIPT REQUIRED')}</span></div>`).join('');
            };

            root.addEventListener('click', async event => {
                const button = event.target.closest('.create-travel-claim');
                if (!button) return;
                workflow.hidden = false;
                workflow.innerHTML = `<div class="panel-head"><div><h2>Claim for travel request #${button.dataset.id}</h2><p class="muted">Claim number will be generated automatically. Add every expense, upload a receipt for each item, then submit the claim.</p></div><button class="button secondary" id="close-travel-claim" type="button">Close</button></div><form id="travel-claim-form" class="form-grid"><button class="button primary full">Create claim and add expenses</button></form><div id="travel-item-area" hidden><hr><div class="panel-head"><div><h3>Add expense item</h3><p class="muted">Each item needs a category, amount, description, and receipt.</p></div><strong id="claim-total">${money(0)}</strong></div><form id="travel-item-form" class="form-grid"><label>Category<select name="category_id" required>${categories.map(category => `<option value="${category.id}">${esc(category.name)}</option>`).join('')}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required></label><label class="full">Description<input name="description" required></label><label class="full">Receipt<input name="receipt" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" required></label><button class="button secondary full">Add expense item</button></form><div id="claim-items" class="list"></div><button class="button primary full" id="submit-travel-claim" type="button" disabled>Upload receipts and submit claim</button></div>`;

                let claimId = null;
                const items = [];
                const claimForm = workflow.querySelector('#travel-claim-form');
                const itemArea = workflow.querySelector('#travel-item-area');
                const itemForm = workflow.querySelector('#travel-item-form');
                const submitButton = workflow.querySelector('#submit-travel-claim');
                renderItems(items);

                workflow.querySelector('#close-travel-claim').onclick = () => { workflow.hidden = true; };
                claimForm.onsubmit = async submitEvent => {
                    submitEvent.preventDefault();
                    try {
                        const claim = await apiFetch('/claims', { method: 'POST', body: JSON.stringify({
                            travel_request_id: Number(button.dataset.id),
                        }) });
                        claimId = claim.claim.id;
                        claimForm.hidden = true;
                        itemArea.hidden = false;
                        toast('Claim created. Add expenses and receipts.');
                    } catch (error) {
                        toast(error.message);
                    }
                };

                itemForm.onsubmit = async submitEvent => {
                    submitEvent.preventDefault();
                    if (!claimId) return;
                    const data = jsonBody(itemForm);
                    const file = itemForm.querySelector('[name="receipt"]').files[0];
                    try {
                        const itemResponse = await apiFetch('/expense-items', { method: 'POST', body: JSON.stringify({
                            claim_id: claimId,
                            category_id: Number(data.category_id),
                            description: data.description,
                            amount: Number(data.amount),
                            expense_date: requests.find(request => request.id === Number(button.dataset.id)).start_date,
                        }) });
                        const uploadData = new FormData();
                        uploadData.append('expense_item_id', itemResponse.expense_item.id);
                        uploadData.append('file', file);
                        await apiFetch('/receipts/upload', { method: 'POST', body: uploadData });
                        const category = categories.find(item => item.id === Number(data.category_id));
                        items.push({ description: data.description, amount: Number(data.amount), category_name: category.name, receipt_count: 1 });
                        renderItems(items);
                        itemForm.reset();
                        submitButton.disabled = false;
                        toast('Expense item and receipt added.');
                    } catch (error) {
                        toast(error.message);
                    }
                };

                submitButton.onclick = async () => {
                    if (!items.length) return;
                    submitButton.disabled = true;
                    try {
                        await apiFetch(`/claims/${claimId}/submit`, { method: 'POST' });
                        toast('Claim submitted successfully.');
                        setTimeout(() => loadEmployeeView(), 500);
                    } catch (error) {
                        submitButton.disabled = false;
                        toast(error.message);
                    }
                };
                workflow.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            return;
        }

        const [claims, reimbursements] = await Promise.all([apiFetch('/claims'), apiFetch('/reimbursements?mine=true')]);
        const reimbursementsByClaim = new Map(reimbursements.map(item => [item.claim_id, item]));
        root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">EMPLOYEE PORTAL</p><h1>Expense claims</h1><p class="muted">View all your expense claims and reimbursement progress.</p></div></div><section class="panel"><div class="table-wrap"><table><thead><tr><th>Claim number</th><th>Total</th><th>Claim status</th><th>Reimbursement status</th><th>Submitted</th></tr></thead><tbody>${claims.map(claim => { const reimbursement = reimbursementsByClaim.get(claim.id); return `<tr><td>${esc(claim.claim_number)}</td><td>${money(claim.total_amount)}</td><td>${status(claim.status)}</td><td>${reimbursement ? status(reimbursement.status) : '<span class="muted">Not created</span>'}</td><td>${date(claim.submitted_at || claim.created_at)}</td></tr>`; }).join('') || '<tr><td colspan="5" class="empty">No expense claims found.</td></tr>'}</tbody></table></div></section>`;
    } catch (error) {
        root.innerHTML = `<section class="panel"><p class="empty">${esc(error.message)}</p></section>`;
    }
}

loadEmployeeView();
