/**
 * WMS 입고 관리 페이지 (조회 전용)
 * - 탭: 입고예정 / 입고작업내역
 */

let currentPlanPage = 1;
let currentWorkPage = 1;

// ==========================================
// 탭 전환
// ==========================================
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');

    document.getElementById('tab-plans').style.display = tab === 'plans' ? 'block' : 'none';
    document.getElementById('tab-works').style.display = tab === 'works' ? 'block' : 'none';
}

// ==========================================
// 입고예정 목록
// ==========================================
async function loadPlans(page) {
    if (page) currentPlanPage = page;

    try {
        const tbody = document.getElementById('plans-tbody');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-muted);">로딩 중...</td></tr>';

        const params = { page: currentPlanPage, limit: 20 };
        const planDate = document.getElementById('planFilterDate').value.trim();
        const planStatus = document.getElementById('planFilterStatus').value;

        if (planDate) params.plan_date = planDate;
        if (planStatus) params.plan_status = planStatus;

        const query = api.buildQueryString(params);
        const res = await api.get(`/api/sabangnet/inbound/plans${query}`);

        renderPlans(res);
    } catch (e) {
        showAlert('입고예정 로드 실패: ' + e.message, 'error');
    }
}

function renderPlans(res) {
    const tbody = document.getElementById('plans-tbody');
    tbody.innerHTML = '';
    const data = res.data || [];

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted);">데이터가 없습니다.</td></tr>';
        document.getElementById('planCount').textContent = '';
        return;
    }

    data.forEach(plan => {
        const tr = document.createElement('tr');
        tr.addEventListener('click', () => loadPlanDetail(plan.ReceivingPlanID));
        tr.innerHTML = `
            <td>${plan.ReceivingPlanID}</td>
            <td>${escapeHtml(plan.ReceivingPlanCode)}</td>
            <td>${formatPlanDate(plan.PlanDate)}</td>
            <td><span class="status-badge status-${plan.PlanStatus}">${escapeHtml(plan.PlanStatusName)}</span></td>
            <td style="text-align:right;">${plan.ProductCount}</td>
            <td>${escapeHtml(plan.CompleteDt)}</td>
            <td>${escapeHtml(plan.Memo)}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('planCount').textContent = `(총 ${res.total}건)`;
    renderPagination('plans-pagination', res.page, res.total_pages, loadPlans);
}

// ==========================================
// 입고예정 상세
// ==========================================
async function loadPlanDetail(planId) {
    try {
        const res = await api.get(`/api/sabangnet/inbound/plans/${planId}`);

        document.getElementById('planDetailTitle').textContent =
            `${res.ReceivingPlanCode || planId} (${res.PlanStatusName})`;

        const tbody = document.getElementById('plan-detail-tbody');
        tbody.innerHTML = '';

        (res.products || []).forEach(p => {
            const tr = document.createElement('tr');
            const recvQty = p.ReceivingQuantity !== null ? p.ReceivingQuantity : '-';
            tr.innerHTML = `
                <td>${escapeHtml(p.BrandName)}</td>
                <td>${escapeHtml(p.UniqueCode)}</td>
                <td>${escapeHtml(p.ProductName)}</td>
                <td style="text-align:right;font-weight:600;">${Number(p.Quantity).toLocaleString()}</td>
                <td style="text-align:right;font-weight:600;">${recvQty === '-' ? '-' : Number(recvQty).toLocaleString()}</td>
                <td>${p.PlanProductStatusName ? `<span class="status-badge status-${p.PlanProductStatus}">${escapeHtml(p.PlanProductStatusName)}</span>` : '-'}</td>
                <td>${formatPlanDate(p.ExpireDate)}</td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('plan-detail-card').style.display = 'block';
    } catch (e) {
        showAlert('상세 로드 실패: ' + e.message, 'error');
    }
}

// ==========================================
// 입고작업내역
// ==========================================
async function loadWorks(page) {
    if (page) currentWorkPage = page;

    try {
        const tbody = document.getElementById('works-tbody');
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:var(--text-muted);">로딩 중...</td></tr>';

        const params = { page: currentWorkPage, limit: 50 };
        const start = document.getElementById('workFilterStart').value;
        const end = document.getElementById('workFilterEnd').value;
        const wt = document.getElementById('workFilterType').value;

        if (start) params.start_date = start;
        if (end) params.end_date = end;
        if (wt) params.work_type = wt;

        const query = api.buildQueryString(params);
        const res = await api.get(`/api/sabangnet/inbound/works${query}`);

        renderWorks(res);
    } catch (e) {
        showAlert('입고작업 로드 실패: ' + e.message, 'error');
    }
}

function renderWorks(res) {
    const tbody = document.getElementById('works-tbody');
    tbody.innerHTML = '';
    const data = res.data || [];

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--text-muted);">데이터가 없습니다.</td></tr>';
        document.getElementById('workCount').textContent = '';
        return;
    }

    data.forEach(w => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="white-space:nowrap;">${escapeHtml(w.WorkDate)}</td>
            <td>${escapeHtml(w.WorkTypeName)}</td>
            <td>${escapeHtml(w.ReceivingTypeName)}</td>
            <td>${escapeHtml(w.BrandName)}</td>
            <td>${escapeHtml(w.ProductName)}</td>
            <td style="text-align:right;font-weight:600;">${Number(w.Quantity).toLocaleString()}</td>
            <td>${formatPlanDate(w.ExpireDate)}</td>
            <td style="text-align:right;">${w.BoxQuantity || '-'}</td>
            <td style="text-align:right;">${w.PalletQuantity || '-'}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('workCount').textContent = `(총 ${res.total}건)`;
    renderPagination('works-pagination', res.page, res.total_pages, loadWorks);
}

// ==========================================
// 페이지네이션
// ==========================================
function renderPagination(containerId, currentPage, totalPages, loadFn) {
    const container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }

    let html = '<div style="display:flex;justify-content:center;gap:4px;">';

    if (currentPage > 1)
        html += `<button class="btn btn-secondary btn-sm" onclick="${loadFn.name}(${currentPage - 1})">이전</button>`;

    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);
    for (let i = start; i <= end; i++) {
        const active = i === currentPage ? 'btn-primary' : 'btn-secondary';
        html += `<button class="btn ${active} btn-sm" onclick="${loadFn.name}(${i})">${i}</button>`;
    }

    if (currentPage < totalPages)
        html += `<button class="btn btn-secondary btn-sm" onclick="${loadFn.name}(${currentPage + 1})">다음</button>`;

    html += '</div>';
    container.innerHTML = html;
}

// ==========================================
// 유틸
// ==========================================
function formatPlanDate(d) {
    if (!d) return '-';
    if (d.length === 8) return `${d.substring(0, 4)}-${d.substring(4, 6)}-${d.substring(6, 8)}`;
    return d;
}

function resetPlanFilters() {
    document.getElementById('planFilterDate').value = '';
    document.getElementById('planFilterStatus').value = '';
    document.getElementById('plan-detail-card').style.display = 'none';
}

function resetWorkFilters() {
    document.getElementById('workFilterStart').value = '';
    document.getElementById('workFilterEnd').value = '';
    document.getElementById('workFilterType').value = '';
}
