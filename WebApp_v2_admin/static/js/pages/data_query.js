/**
 * 데이터 조회 페이지
 * - 일별 채널별 제품별 매출 조회 (채널별 그룹 + 일자 피벗)
 * - 엑셀 다운로드
 */

// ==========================================
// 1. 상태 변수 선언
// ==========================================
let currentFilters = {};
let currentData = null;

// ==========================================
// 2. 초기화 (DOMContentLoaded)
// ==========================================
document.addEventListener('DOMContentLoaded', async function() {
    await loadMetadata();

    // 필터 Enter 키 지원
    ['filterDateFrom', 'filterDateTo'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('keypress', e => {
            if (e.key === 'Enter') applyFilters();
        });
    });
});

// ==========================================
// 3. 메타데이터 로드
// ==========================================
async function loadMetadata() {
    try {
        const res = await api.get('/api/data-query/metadata');

        const brandSelect = document.getElementById('filterBrand');
        res.brands.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.BrandID;
            opt.textContent = b.Name;
            brandSelect.appendChild(opt);
        });

        const channelSelect = document.getElementById('filterChannel');
        res.channels.forEach(ch => {
            const opt = document.createElement('option');
            opt.value = ch;
            opt.textContent = ch;
            channelSelect.appendChild(opt);
        });
    } catch (e) {
        showAlert('메타데이터 로드 실패: ' + e.message, 'error');
    }
}

// ==========================================
// 4. 데이터 로드
// ==========================================
async function loadData() {
    try {
        const tableBody = document.querySelector('#data-table tbody');
        const tableHead = document.querySelector('#data-table thead tr');
        tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;padding:40px;color:var(--text-muted);">로딩 중...</td></tr>';

        const params = { ...currentFilters };
        const query = api.buildQueryString(params);
        const res = await api.get(`/api/data-query/daily-sales${query}`);

        currentData = res;
        renderPivotTable(res);
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

// ==========================================
// 5. 피벗 테이블 렌더링
// ==========================================
function renderPivotTable(data) {
    const table = document.getElementById('data-table');
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    const dates = data.dates || [];
    const channels = data.channels || [];

    // 헤더: ERPCode | 상품명 | 일자1 | 일자2 | ...
    thead.innerHTML = '';
    ['ERPCode', '상품명'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        th.style.position = 'sticky';
        th.style.left = h === 'ERPCode' ? '0' : '100px';
        th.style.zIndex = '2';
        thead.appendChild(th);
    });
    dates.forEach(d => {
        const th = document.createElement('th');
        th.textContent = d.substring(5); // MM-DD
        th.title = d;
        th.style.minWidth = '80px';
        th.style.textAlign = 'right';
        thead.appendChild(th);
    });

    // 바디
    tbody.innerHTML = '';

    if (channels.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 2 + dates.length;
        td.textContent = '검색 조건을 설정하고 검색 버튼을 클릭하세요.';
        td.style.textAlign = 'center';
        td.style.padding = '40px';
        td.style.color = 'var(--text-muted)';
        tr.appendChild(td);
        tbody.appendChild(tr);
        document.getElementById('totalCount').textContent = '';
        return;
    }

    let totalProducts = 0;

    channels.forEach(ch => {
        // 채널 그룹 헤더 행
        const groupTr = document.createElement('tr');
        groupTr.className = 'channel-group-row';
        const groupTd = document.createElement('td');
        groupTd.colSpan = 2 + dates.length;
        groupTd.innerHTML = `<strong><i class="fa-solid fa-store" style="margin-right:6px;"></i>${escapeHtml(ch.ChannelName)}</strong> <span class="text-muted" style="font-size:12px;">(${ch.products.length}개 상품)</span>`;
        groupTd.style.background = 'rgba(99, 102, 241, 0.1)';
        groupTd.style.padding = '10px 12px';
        groupTr.appendChild(groupTd);
        tbody.appendChild(groupTr);

        // 제품별 수량/매출 행
        ch.products.forEach(product => {
            totalProducts++;

            // 수량 행
            const qtyTr = document.createElement('tr');
            const qtyCodeTd = document.createElement('td');
            qtyCodeTd.textContent = product.ERPCode;
            qtyCodeTd.style.position = 'sticky';
            qtyCodeTd.style.left = '0';
            qtyCodeTd.style.fontSize = '12px';
            qtyTr.appendChild(qtyCodeTd);

            const qtyNameTd = document.createElement('td');
            qtyNameTd.innerHTML = `${escapeHtml(product.PRODUCT_NAME)} <span class="badge badge-info" style="font-size:10px;">수량</span>`;
            qtyNameTd.style.position = 'sticky';
            qtyNameTd.style.left = '100px';
            qtyTr.appendChild(qtyNameTd);

            dates.forEach(d => {
                const td = document.createElement('td');
                const val = product.daily[d]?.Quantity || 0;
                td.textContent = val ? Number(val).toLocaleString() : '';
                td.style.textAlign = 'right';
                td.style.fontSize = '13px';
                qtyTr.appendChild(td);
            });
            tbody.appendChild(qtyTr);

            // 매출 행
            const amtTr = document.createElement('tr');
            const amtCodeTd = document.createElement('td');
            amtCodeTd.style.position = 'sticky';
            amtCodeTd.style.left = '0';
            amtTr.appendChild(amtCodeTd);

            const amtNameTd = document.createElement('td');
            amtNameTd.innerHTML = `<span class="text-muted">${escapeHtml(product.PRODUCT_NAME)}</span> <span class="badge badge-success" style="font-size:10px;">매출</span>`;
            amtNameTd.style.position = 'sticky';
            amtNameTd.style.left = '100px';
            amtTr.appendChild(amtNameTd);

            dates.forEach(d => {
                const td = document.createElement('td');
                const val = product.daily[d]?.TaxableAmount || 0;
                td.textContent = val ? Number(val).toLocaleString() : '';
                td.style.textAlign = 'right';
                td.style.fontSize = '13px';
                td.style.color = 'var(--text-muted)';
                amtTr.appendChild(td);
            });
            tbody.appendChild(amtTr);
        });
    });

    document.getElementById('totalCount').textContent =
        `${channels.length}개 채널, ${totalProducts}개 상품, ${dates.length}일`;
}

// ==========================================
// 6. 필터
// ==========================================
function applyFilters() {
    currentFilters = {};
    const brandId = document.getElementById('filterBrand')?.value;
    const channelName = document.getElementById('filterChannel')?.value;
    const dateFrom = document.getElementById('filterDateFrom')?.value;
    const dateTo = document.getElementById('filterDateTo')?.value;

    if (brandId) currentFilters.brand_id = brandId;
    if (channelName) currentFilters.channel_name = channelName;
    if (dateFrom) currentFilters.date_from = dateFrom;
    if (dateTo) currentFilters.date_to = dateTo;

    loadData();
}

function resetFilters() {
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterChannel').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    currentFilters = {};
    currentData = null;
    document.getElementById('totalCount').textContent = '';

    const tbody = document.querySelector('#data-table tbody');
    const thead = document.querySelector('#data-table thead tr');
    thead.innerHTML = '<th>ERPCode</th><th>상품명</th>';
    tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;padding:40px;color:var(--text-muted);">검색 조건을 설정하고 검색 버튼을 클릭하세요.</td></tr>';
}

// ==========================================
// 7. 엑셀 다운로드
// ==========================================
async function downloadExcel() {
    if (!currentData || !currentData.channels || currentData.channels.length === 0) {
        showAlert('먼저 데이터를 검색하세요.', 'warning');
        return;
    }

    try {
        const params = { ...currentFilters };
        const query = api.buildQueryString(params);
        const token = localStorage.getItem('access_token');

        const res = await fetch(`/api/data-query/daily-sales/download/excel${query}`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '다운로드 실패');
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const disposition = res.headers.get('Content-Disposition');
        let filename = '일별매출_조회결과.xlsx';
        if (disposition) {
            const match = disposition.match(/filename\*=UTF-8''(.+)/);
            if (match) filename = decodeURIComponent(match[1]);
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showAlert('다운로드 완료', 'success');
    } catch (e) {
        showAlert('다운로드 실패: ' + e.message, 'error');
    }
}
