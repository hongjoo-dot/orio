/**
 * 예상 판매량 통합 조회 JavaScript
 * - 탭: 통합 조회 / BOM 분해
 * - 피벗 테이블: 행(브랜드/채널/상품) × 열(연월별)
 */

const API_BASE = '/api/expected-sales-integration';
let currentYearMonths = [];
let currentData = [];
let currentTab = 'integration';

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        setDefaultRange();
        await onRangeChange();
    } catch (e) {
        console.error('초기화 실패:', e);
        const tbody = document.querySelector('#pivotTable tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:var(--danger);">
            초기화 실패: ${e.message}</td></tr>`;
    }
});

// ==================== 탭 전환 ====================
function switchTab(tab) {
    currentTab = tab;
    document.getElementById('tabIntegration').className =
        tab === 'integration' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabBom').className =
        tab === 'bom' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tableTitle').textContent =
        tab === 'bom' ? 'BOM 분해 결과' : '통합 조회 결과';
    loadData();
}

// ==================== 기본 연월 범위 설정 ====================
function setDefaultRange() {
    const now = new Date();
    const from = new Date(now.getFullYear(), now.getMonth(), 1);
    const to = new Date(now.getFullYear(), now.getMonth() + 2, 1);

    document.getElementById('filterYearMonthFrom').value = formatMonth(from);
    document.getElementById('filterYearMonthTo').value = formatMonth(to);
}

function formatMonth(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// ==================== 연월 범위 변경 시 ====================
async function onRangeChange() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) return;

    await Promise.all([loadInputMonths(), loadBrands(), loadChannels()]);
    await loadData();
}

function getRangeParams() {
    return {
        year_month_from: document.getElementById('filterYearMonthFrom').value,
        year_month_to: document.getElementById('filterYearMonthTo').value
    };
}

// ==================== 입력월 목록 로드 ====================
async function loadInputMonths() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const months = await api.get(`${API_BASE}/input-months${qs}`);
        const sel = document.getElementById('filterInputMonth');
        const cur = sel.value;
        sel.innerHTML = '<option value="">전체</option>';
        months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m; opt.textContent = m;
            sel.appendChild(opt);
        });
        sel.value = cur || '';
    } catch (e) {
        console.error('입력월 로드 실패:', e);
    }
}

// ==================== 브랜드 목록 로드 ====================
async function loadBrands() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const brands = await api.get(`${API_BASE}/brands${qs}`);
        const sel = document.getElementById('filterBrand');
        const cur = sel.value;
        sel.innerHTML = '<option value="">전체</option>';
        brands.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b; opt.textContent = b;
            sel.appendChild(opt);
        });
        sel.value = cur || '';
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

// ==================== 채널 목록 로드 ====================
async function loadChannels() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const channels = await api.get(`${API_BASE}/channels${qs}`);
        const sel = document.getElementById('filterChannel');
        const cur = sel.value;
        sel.innerHTML = '<option value="">전체</option>';
        channels.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c; opt.textContent = c;
            sel.appendChild(opt);
        });
        sel.value = cur || '';
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

// ==================== 데이터 로드 ====================
async function loadData() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) {
        showAlert('연월 범위를 설정해주세요.', 'warning');
        return;
    }

    const tbody = document.querySelector('#pivotTable tbody');
    tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    try {
        const qs = api.buildQueryString({
            year_month_from: from,
            year_month_to: to,
            input_month: document.getElementById('filterInputMonth').value,
            brand: document.getElementById('filterBrand').value,
            channel: document.getElementById('filterChannel').value
        });

        const endpoint = currentTab === 'bom' ? '/bom-data' : '/data';
        const result = await api.get(`${API_BASE}${endpoint}${qs}`);

        currentYearMonths = result.year_months || [];
        currentData = result.data || [];

        if (currentTab === 'bom') {
            renderBomTable(currentYearMonths, currentData);
        } else {
            renderPivotTable(currentYearMonths, currentData);
        }
        document.getElementById('dataCount').textContent = `(${currentData.length}개 상품)`;
    } catch (e) {
        console.error('데이터 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:var(--danger);">
            데이터 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

// ==================== 통합 조회 피벗 테이블 렌더링 ====================
function renderPivotTable(yearMonths, data) {
    const thead = document.querySelector('#pivotTable thead tr');
    const tbody = document.querySelector('#pivotTable tbody');

    thead.innerHTML = '';
    ['브랜드', '채널', '상품명'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const thAmt = document.createElement('th');
        thAmt.textContent = `${ym}(매출)`;
        thAmt.style.textAlign = 'right';
        thead.appendChild(thAmt);

        const thQty = document.createElement('th');
        thQty.textContent = `${ym}(수량)`;
        thQty.style.textAlign = 'right';
        thead.appendChild(thQty);
    });

    ['합계(매출)', '합계(수량)'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        th.style.textAlign = 'right';
        th.style.background = 'rgba(34,197,94,0.1)';
        thead.appendChild(th);
    });

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length * 2 + 2;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${escapeHtml(item.brand)}</td>
            <td>${escapeHtml(item.channel)}</td>
            <td>${escapeHtml(item.name)}</td>
        `;

        yearMonths.forEach(ym => {
            const ymData = item.months[ym] || { amount: 0, quantity: 0 };

            const tdAmt = document.createElement('td');
            tdAmt.className = 'col-amount';
            tdAmt.textContent = ymData.amount ? ymData.amount.toLocaleString() : '-';
            tr.appendChild(tdAmt);

            const tdQty = document.createElement('td');
            tdQty.className = 'col-qty';
            tdQty.textContent = ymData.quantity ? ymData.quantity.toLocaleString() : '-';
            tr.appendChild(tdQty);
        });

        const tdTotalAmt = document.createElement('td');
        tdTotalAmt.className = 'col-total';
        tdTotalAmt.textContent = item.totalAmount ? item.totalAmount.toLocaleString() : '-';
        tr.appendChild(tdTotalAmt);

        const tdTotalQty = document.createElement('td');
        tdTotalQty.className = 'col-total';
        tdTotalQty.textContent = item.totalQuantity ? item.totalQuantity.toLocaleString() : '-';
        tr.appendChild(tdTotalQty);

        tbody.appendChild(tr);
    });
}

// ==================== BOM 분해 테이블 렌더링 ====================
function renderBomTable(yearMonths, data) {
    const thead = document.querySelector('#pivotTable thead tr');
    const tbody = document.querySelector('#pivotTable tbody');

    thead.innerHTML = '';
    ['브랜드', '채널', '상품명'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const th = document.createElement('th');
        th.textContent = `${ym}(수량)`;
        th.style.textAlign = 'right';
        thead.appendChild(th);
    });

    const thTotal = document.createElement('th');
    thTotal.textContent = '합계(수량)';
    thTotal.style.textAlign = 'right';
    thTotal.style.background = 'rgba(34,197,94,0.1)';
    thead.appendChild(thTotal);

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length + 1;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${escapeHtml(item.brand)}</td>
            <td>${escapeHtml(item.channel)}</td>
            <td>${escapeHtml(item.name)}</td>
        `;

        yearMonths.forEach(ym => {
            const qty = item.months[ym] || 0;
            const td = document.createElement('td');
            td.className = 'col-qty';
            td.textContent = qty ? qty.toLocaleString() : '-';
            tr.appendChild(td);
        });

        const tdTotal = document.createElement('td');
        tdTotal.className = 'col-total';
        tdTotal.textContent = item.totalQuantity ? item.totalQuantity.toLocaleString() : '-';
        tr.appendChild(tdTotal);

        tbody.appendChild(tr);
    });
}

// ==================== 필터 초기화 ====================
function resetFilters() {
    document.getElementById('filterInputMonth').value = '';
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterChannel').value = '';
    setDefaultRange();
    onRangeChange();
}

// ==================== 엑셀 다운로드 ====================
function downloadExcel() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) {
        showAlert('연월 범위를 설정해주세요.', 'warning');
        return;
    }

    const token = localStorage.getItem('access_token');
    const qs = api.buildQueryString({
        year_month_from: from,
        year_month_to: to,
        input_month: document.getElementById('filterInputMonth').value,
        brand: document.getElementById('filterBrand').value,
        channel: document.getElementById('filterChannel').value
    });

    const endpoint = currentTab === 'bom' ? '/bom-download' : '/download';
    const filePrefix = currentTab === 'bom' ? 'BOM분해' : '예상판매량_통합';

    fetch(`${API_BASE}${endpoint}${qs}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(resp => {
        if (!resp.ok) throw new Error('다운로드 실패');
        return resp.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filePrefix}_${from}~${to}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(e => {
        console.error('엑셀 다운로드 실패:', e);
        showAlert('엑셀 다운로드에 실패했습니다.', 'error');
    });
}
