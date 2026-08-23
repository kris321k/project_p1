function repairEmployeeNavigation() {
    if (document.body.dataset.role !== 'EMPLOYEE') return;
    const targets = {
        'My profile': '/employee/profile',
        'Travel requests': '/employee/travel',
        'Expense claims': '/employee/claims'
    };
    document.querySelectorAll('#navigation a').forEach(link => {
        const target = targets[link.textContent.trim()];
        if (target) link.href = target;
    });
}

repairEmployeeNavigation();
