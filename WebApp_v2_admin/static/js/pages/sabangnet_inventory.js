/**
 * WMS 재고 조회 페이지
 * - 일별 스냅샷 조회
 * - 상품 클릭 시 로케이션 상세
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

        // 날짜 목록
        const dateSelect = document.getElementById('filterDate');
        (res.dates || []).forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            dateSelect.appendChild(opt);
        });

        // 최신 날짜 자동 선택
        if (res.dates && res.dates.length > 0) {
            dateSelect.value = res.dates[0];
        }

        // 브랜드 목록
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
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;color:var(--text-muted);">로딩 중...</td></tr>';

        const params = { snapshot_date: date };
        const time = document.getElementById('filterTime').value;
        const brandId = document.getElementById('filterBrand').value;
        const search = document.getElementById('filterSearch').value.trim();

        if (time) params.snapshot_time = time;
        if (brandId) params.brand_id = brandId;
        if (search) params.search = search;

        const query = api.buildQueryString(params);
        const res = await api.get(`/api/sabangnet/inventory${query}`);

        currentData = res.data;
        renderTable(res.data);

        // 로케이션 패널 숨기기
        document.getElementById('location-card').style.display = 'none';
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
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;color:var(--text-muted);">데이터가 없습니다.</td></tr>';
        document.getElementById('totalCount').textContent = '';
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.dataset.shippingProductId = item.ShippingProductID;
        tr.dataset.snapshotDate = item.SnapshotDate;
        tr.dataset.snapshotTime = item.SnapshotTime;
        tr.dataset.productName = item.ERPProductName || item.ProductName;

        tr.addEventListener('click', () => onRowClick(tr));

        tr.innerHTML = `
            <td>${escapeHtml(item.BrandName)}</td>
            <td>${escapeHtml(item.ProductCode || item.ERPUniqueCode)}</td>
            <td>${escapeHtml(item.ERPProductName || item.ProductName)}</td>
            <td style="text-align:right;font-weight:600;">${formatStock(item.TotalStock)}</td>
            <td style="text-align:right;">${formatStock(item.NormalStock)}</td>
            <td style="text-align:right;">${formatStock(item.ReceivingStock)}</td>
            <td style="text-align:right;">${formatStock(item.OrderStock)}</td>
            <td style="text-align:right;">${formatStock(item.ShippingStock)}</td>
            <td style="text-align:right;">${formatStock(item.DamagedStock)}</td>
            <td style="text-align:right;">${formatStock(item.ReturnStock)}</td>
            <td style="text-align:right;">${formatStock(item.KeepingStock)}</td>
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
// 행 클릭 → 로케이션 상세
// ==========================================
async function onRowClick(tr) {
    // 선택 표시
    document.querySelectorAll('#inventory-tbody tr').forEach(r => r.classList.remove('selected-row'));
    tr.classList.add('selected-row');

    const spid = tr.dataset.shippingProductId;
    const date = tr.dataset.snapshotDate;
    const time = tr.dataset.snapshotTime;
    const name = tr.dataset.productName;

    document.getElementById('locationProductName').textContent = name;

    const locationCard = document.getElementById('location-card');
    const locationTbody = document.getElementById('location-tbody');

    locationCard.style.display = 'block';
    locationTbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-muted);">로딩 중...</td></tr>';

    try {
        const query = api.buildQueryString({
            snapshot_date: date,
            snapshot_time: time,
            shipping_product_id: spid
        });
        const res = await api.get(`/api/sabangnet/inventory/locations${query}`);

        locationTbody.innerHTML = '';

        if (!res.data || res.data.length === 0) {
            locationTbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-muted);">로케이션 데이터 없음</td></tr>';
            return;
        }

        res.data.forEach(loc => {
            const locTr = document.createElement('tr');
            locTr.innerHTML = `
                <td>${escapeHtml(loc.LocationName)}</td>
                <td>${escapeHtml(loc.LocTypeName)}</td>
                <td>${loc.ExpireDate ? formatExpireDate(loc.ExpireDate) : '-'}</td>
                <td style="text-align:right;font-weight:600;">${Number(loc.Quantity).toLocaleString()}</td>
            `;
            locationTbody.appendChild(locTr);
        });
    } catch (e) {
        locationTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--danger);">로드 실패: ${e.message}</td></tr>`;
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
    document.getElementById('filterTime').value = '';
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterSearch').value = '';
    currentData = null;
    document.getElementById('totalCount').textContent = '';
    document.getElementById('inventory-tbody').innerHTML =
        '<tr><td colspan="11" style="text-align:center;padding:40px;color:var(--text-muted);">날짜를 선택하고 검색 버튼을 클릭하세요.</td></tr>';
    document.getElementById('location-card').style.display = 'none';
}
