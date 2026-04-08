/**
 * WMS 재고 조회 페이지
 * - Master-Detail 레이아웃 (7:3)
 * - 재고 0인 상품 자동 필터링
 * - 상품 클릭 → 우측 패널에 요약 + 로케이션 상세
 */

let currentData = null;

// ==========================================
// 초기화
// ==========================================
document.addEventListener('DOMContentLoaded', async function() {
    await loadMetadata();

    document.getElementById('filterSearch')?.addEventListener('keypress', e => {
        if (e.key === 'Enter') applyFilters();
    });
});

// ==========================================
// 메타데이터 로드
// ==========================================
async function loadMetadata() {
    try {
        const res = await api.get('/api/sabangnet/inventory/metadata');

        const dateSelect = document.getElementById('filterDate');
        (res.dates || []).forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            dateSelect.appendChild(opt);
        });

        if (res.dates && res.dates.length > 0) {
            dateSelect.value = res.dates[0];
        }

        const brandSelect = document.getElementById('filterBrand');
        (res.brands || []).forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.BrandID;
            opt.textContent = b.Name;
            brandSelect.appendChild(opt);
        });
    } catch (e) {
        showAlert('메타데이터 로드 실패: ' + e.message, 'error');
    }
}

// ==========================================
// 데이터 로드
// ==========================================
async function loadData() {
    const date = document.getElementById('filterDate').value;
    if (!date) {
        showAlert('날짜를 선택하세요.', 'warning');
        return;
    }

    try {
        const tbody = document.getElementById('inventory-tbody');
        tbody.innerHTML = '<tr><td colspan="11" class="inv-empty-msg">로딩 중...</td></tr>';

        const params = { snapshot_date: date };
        const time = document.getElementById('filterTime').value;
        const brandId = document.getElementById('filterBrand').value;
        const search = document.getElementById('filterSearch').value.trim();

        if (time) params.snapshot_time = time;
        if (brandId) params.brand_id = brandId;
        if (search) params.search = search;

        const query = api.buildQueryString(params);
        const res = await api.get(`/api/sabangnet/inventory${query}`);

        // 재고가 없는 상품 필터링 (TotalStock == 0)
        const filtered = (res.data || []).filter(item => Number(item.TotalStock) !== 0);

        currentData = filtered;
        renderTable(filtered);

        // 우측 패널 초기화
        hideDetailPanel();
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

// ==========================================
// 테이블 렌더링
// ==========================================
function renderTable(data) {
    const tbody = document.getElementById('inventory-tbody');
    tbody.innerHTML = '';

    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="inv-empty-msg">데이터가 없습니다.</td></tr>';
        document.getElementById('totalCount').textContent = '';
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.dataset.shippingProductId = item.ShippingProductID;
        tr.dataset.snapshotDate = item.SnapshotDate;
        tr.dataset.snapshotTime = item.SnapshotTime;
        tr.dataset.idx = data.indexOf(item);

        tr.addEventListener('click', () => onRowClick(tr));

        tr.innerHTML = `
            <td class="inv-td-fixed" style="left:0;">${escapeHtml(item.BrandName)}</td>
            <td class="inv-td-fixed" style="left:100px;">${escapeHtml(item.ProductCode || item.ERPUniqueCode)}</td>
            <td class="inv-td-fixed inv-td-fixed-last" style="left:200px;">${escapeHtml(item.ERPProductName || item.ProductName)}</td>
            <td class="inv-td-total">${formatStock(item.TotalStock)}</td>
            <td class="inv-td-stock">${formatStock(item.NormalStock)}</td>
            <td class="inv-td-stock">${formatStock(item.ReceivingStock)}</td>
            <td class="inv-td-stock">${formatStock(item.OrderStock)}</td>
            <td class="inv-td-stock">${formatStock(item.ShippingStock)}</td>
            <td class="inv-td-stock">${formatStock(item.DamagedStock)}</td>
            <td class="inv-td-stock">${formatStock(item.ReturnStock)}</td>
            <td class="inv-td-stock">${formatStock(item.KeepingStock)}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('totalCount').textContent = `(${data.length}개 상품)`;
}

// ==========================================
// 재고 수량 포맷
// ==========================================
function formatStock(val) {
    const n = Number(val) || 0;
    if (n === 0) return '<span class="stock-zero">-</span>';
    if (n < 0) return `<span class="stock-negative">${n.toLocaleString()}</span>`;
    return n.toLocaleString();
}

// ==========================================
// 행 클릭 → 우측 패널에 요약 + 로케이션
// ==========================================
async function onRowClick(tr) {
    document.querySelectorAll('#inventory-tbody tr').forEach(r => r.classList.remove('selected-row'));
    tr.classList.add('selected-row');

    const idx = Number(tr.dataset.idx);
    const item = currentData[idx];
    const spid = tr.dataset.shippingProductId;
    const date = tr.dataset.snapshotDate;
    const time = tr.dataset.snapshotTime;

    // 우측 패널 표시
    showDetailPanel(item);

    // 로케이션 로드
    await loadLocations(spid, date, time);
}

// ==========================================
// 우측 패널: 요약 표시
// ==========================================
function showDetailPanel(item) {
    document.getElementById('emptyDetailCard').style.display = 'none';
    document.getElementById('summaryCard').style.display = 'block';
    document.getElementById('locationCard').style.display = 'block';

    // 상품 정보
    document.getElementById('detailProductName').textContent = item.ERPProductName || item.ProductName;
    document.getElementById('detailProductCode').textContent = item.ProductCode || item.ERPUniqueCode || '';

    // 재고 요약
    document.getElementById('detailTotalStock').textContent = formatStockValue(item.TotalStock);
    document.getElementById('detailNormalStock').textContent = formatStockValue(item.NormalStock);
    document.getElementById('detailReceivingStock').textContent = formatStockValue(item.ReceivingStock);
    document.getElementById('detailOrderStock').textContent = formatStockValue(item.OrderStock);
    document.getElementById('detailShippingStock').textContent = formatStockValue(item.ShippingStock);
    document.getElementById('detailDamagedStock').textContent = formatStockValue(item.DamagedStock);
    document.getElementById('detailReturnStock').textContent = formatStockValue(item.ReturnStock);
    document.getElementById('detailKeepingStock').textContent = formatStockValue(item.KeepingStock);
}

function hideDetailPanel() {
    document.getElementById('emptyDetailCard').style.display = 'block';
    document.getElementById('summaryCard').style.display = 'none';
    document.getElementById('locationCard').style.display = 'none';
}

function formatStockValue(val) {
    const n = Number(val) || 0;
    if (n === 0) return '-';
    return n.toLocaleString();
}

// ==========================================
// 로케이션 로드
// ==========================================
async function loadLocations(spid, date, time) {
    const content = document.getElementById('locationContent');
    content.innerHTML = '<div class="inv-detail-empty" style="padding:20px;"><div>로딩 중...</div></div>';

    try {
        const query = api.buildQueryString({
            snapshot_date: date,
            snapshot_time: time,
            shipping_product_id: spid
        });
        const res = await api.get(`/api/sabangnet/inventory/locations${query}`);

        content.innerHTML = '';

        if (!res.data || res.data.length === 0) {
            content.innerHTML = '<div class="inv-detail-empty" style="padding:20px;"><div>로케이션 데이터 없음</div></div>';
            return;
        }

        res.data.forEach(loc => {
            const row = document.createElement('div');
            row.className = 'inv-location-row';
            row.innerHTML = `
                <div>
                    <span class="inv-location-name">${escapeHtml(loc.LocationName)}</span>
                    <span class="inv-location-type">${escapeHtml(loc.LocTypeName)}</span>
                    ${loc.ExpireDate ? `<div class="inv-location-expire">유통기한: ${formatExpireDate(loc.ExpireDate)}</div>` : ''}
                </div>
                <span class="inv-location-qty">${Number(loc.Quantity).toLocaleString()}</span>
            `;
            content.appendChild(row);
        });
    } catch (e) {
        content.innerHTML = `<div class="inv-detail-empty" style="padding:20px;color:var(--danger);"><div>로드 실패: ${e.message}</div></div>`;
    }
}

// ==========================================
// 유통기한 포맷 (YYYYMMDD → YYYY-MM-DD)
// ==========================================
function formatExpireDate(dateStr) {
    if (!dateStr || dateStr.length !== 8) return dateStr || '-';
    return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
}

// ==========================================
// 필터
// ==========================================
function applyFilters() {
    loadData();
}

function resetFilters() {
    document.getElementById('filterTime').value = 'PM';
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterSearch').value = '';
    currentData = null;
    document.getElementById('totalCount').textContent = '';
    document.getElementById('inventory-tbody').innerHTML =
        '<tr><td colspan="11" class="inv-empty-msg">날짜를 선택하고 검색 버튼을 클릭하세요.</td></tr>';
    hideDetailPanel();
}
