async function systemAdminApp() {
    const root = $('#system-admin-app');
    root.innerHTML = `<div class="page-heading"><div><p class="eyebrow">SYSTEM ADMINISTRATION</p><h1>System Admin Console</h1><p class="muted">Manage users, expense categories, and company policies.</p></div><button class="button primary" id="refresh-system-admin" type="button">Refresh</button></div><div class="grid"><section class="panel"><div class="panel-head"><h2>User accounts</h2></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody id="system-users"></tbody></table></div></section><section class="panel"><div class="panel-head"><h2>Create category</h2></div><form id="category-form" class="form-grid"><label>Name<input name="name" required></label><label class="full">Description<textarea name="description"></textarea></label><button class="button primary full" type="submit">Create category</button></form></section></div><div class="grid"><section class="panel"><div class="panel-head"><h2>Expense categories</h2></div><div id="system-categories" class="list"></div></section><section class="panel"><div class="panel-head"><h2>Create policy</h2></div><form id="policy-form" class="form-grid"><label>Category<select name="category_id" id="policy-category" required></select></label><label>Maximum per item<input name="max_amount" type="number" min="0" step="0.01"></label><label>Daily limit<input name="daily_limit" type="number" min="0" step="0.01"></label><label>Requires receipt<select name="requires_receipt"><option value="true">Yes</option><option value="false">No</option></select></label><button class="button primary full" type="submit">Create policy</button></form><div id="system-policies" class="list"></div></section></div>`;
    
    const load = async () => {
        try {
            const [users, categories, policies] = await Promise.all([apiFetch('/users'), apiFetch('/categories'), apiFetch('/policies')]);
            $('#system-users').innerHTML = users.map(user => `<tr><td>${user.id}</td><td>${esc(user.username)}</td><td>${esc(user.email)}</td><td><select class="user-role" data-id="${user.id}"><option ${user.role === 'EMPLOYEE' ? 'selected' : ''}>EMPLOYEE</option><option ${user.role === 'MANAGER' ? 'selected' : ''}>MANAGER</option><option ${user.role === 'FINANCE_ADMIN' ? 'selected' : ''}>FINANCE_ADMIN</option><option ${user.role === 'ADMIN' ? 'selected' : ''}>ADMIN</option><option ${user.role === 'SYSTEM_ADMIN' ? 'selected' : ''}>SYSTEM_ADMIN</option></select></td><td>${user.is_active ? 'Active' : 'Inactive'}</td><td><button class="link toggle-user" data-id="${user.id}" data-active="${user.is_active}" type="button">${user.is_active ? 'Deactivate' : 'Activate'}</button></td></tr>`).join('') || '<tr><td colspan="6" class="empty">No users found.</td></tr>';
            $('#system-categories').innerHTML = categories.map(category => `<div class="row"><div class="row-content"><strong>${esc(category.name)}</strong><small>${esc(category.description || '-')}</small></div><button class="link toggle-category" data-id="${category.id}" data-active="${category.is_active}" type="button">${category.is_active ? 'Deactivate' : 'Activate'}</button></div>`).join('') || '<p class="empty">No categories found.</p>';
            $('#policy-category').innerHTML = categories.filter(category => category.is_active).map(category => `<option value="${category.id}">${esc(category.name)}</option>`).join('');
            $('#system-policies').innerHTML = policies.map(policy => `<div class="row"><div class="row-content"><strong>Category ${policy.category_id}</strong><small>Max ${money(policy.max_amount)} | Daily ${money(policy.daily_limit)} | Receipt ${policy.requires_receipt ? 'required' : 'optional'}</small></div><button class="link toggle-policy" data-id="${policy.id}" data-active="${policy.is_active}" type="button">${policy.is_active ? 'Deactivate' : 'Activate'}</button></div>`).join('') || '<p class="empty">No policies found.</p>';
        } catch (error) { toast(error.message); }
    };

    root.addEventListener('click', async event => {
        const userToggle = event.target.closest('.toggle-user');
        const categoryToggle = event.target.closest('.toggle-category');
        const policyToggle = event.target.closest('.toggle-policy');
        try {
            if (userToggle) await apiFetch(`/users/${userToggle.dataset.id}`, { method: 'PUT', body: JSON.stringify({ is_active: userToggle.dataset.active !== 'true' }) });
            if (categoryToggle) await apiFetch(`/categories/${categoryToggle.dataset.id}`, { method: 'PUT', body: JSON.stringify({ is_active: categoryToggle.dataset.active !== 'true' }) });
            if (policyToggle) await apiFetch(`/policies/${policyToggle.dataset.id}`, { method: 'PUT', body: JSON.stringify({ is_active: policyToggle.dataset.active !== 'true' }) });
            if (userToggle || categoryToggle || policyToggle) { toast('System setting updated'); await load(); }
        } catch (error) { toast(error.message); }
    });
    root.addEventListener('change', async event => {
        const role = event.target.closest('.user-role');
        if (!role) return;
        try { await apiFetch(`/users/${role.dataset.id}`, { method: 'PUT', body: JSON.stringify({ role: role.value }) }); toast('User role updated'); } catch (error) { toast(error.message); await load(); }
    });
    $('#category-form').onsubmit = async event => {
        event.preventDefault();
        try { await apiFetch('/categories', { method: 'POST', body: JSON.stringify(jsonBody(event.target)) }); toast('Category created'); event.target.reset(); await load(); } catch (error) { toast(error.message); }
    };
    $('#policy-form').onsubmit = async event => {
        event.preventDefault();
        const data = jsonBody(event.target);
        try { await apiFetch('/policies', { method: 'POST', body: JSON.stringify({ category_id: Number(data.category_id), max_amount: data.max_amount ? Number(data.max_amount) : null, daily_limit: data.daily_limit ? Number(data.daily_limit) : null, requires_receipt: data.requires_receipt === 'true' }) }); toast('Policy created'); event.target.reset(); await load(); } catch (error) { toast(error.message); }
    };
    $('#refresh-system-admin').onclick = load;
    await load();
}

if (document.body.dataset.role === 'SYSTEM_ADMIN') systemAdminApp();
