/**
 * 예상 판매량 통합 조회 JavaScript
 * - 탭: 예상 매출 관리 / BOM 분해
 * - 예상 매출 관리: 상품 합산 + 디테일 패널
 * - BOM 분해: SKU 중심 발주 수량 + 분해 상세
 */

const API_BASE = '/api/expected-sales-integration';
let currentTab = 'sku';
let selectedSkuCode = null;
let selectedBomCode = null;

// Sort state
let skuSortKey = null, skuSortDir = null;
let bomSortKey = null, bomSortDir = null;

// Multi-select instances
let msBrand, msChannel, msOwner;

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Multi-select 초기화
        msBrand = new MultiSelect('filterBrand', { placeholder: '전체' });
        msChannel = new MultiSelect('filterChannel', { placeholder: '전체' });
        msOwner = new MultiSelect('filterOwner', { placeholder: '전체', onChange: () => onRangeChange() });

        await loadOwners();
        await Promise.all([loadYearMonths(), loadInputMonths()]);
        document.getElementById('filterInputMonth').addEventListener('change', onInputMonthChange);
    } catch (e) {
        console.error('초기화 실패:', e);
        console.error('초기화 상세:', e.message);
    }

    // 인라인 편집 이탈 방지
    window.addEventListener('beforeunload', (e) => {
        if (window._skuDirtySet && window._skuDirtySet.size > 0) {
            e.preventDefault();
        }
    });
});

// ==================== 탭 전환 ====================
function switchTab(tab) {
    currentTab = tab;
    skuSortKey = null; skuSortDir = null;
    bomSortKey = null; bomSortDir = null;
    document.getElementById('tabSku').className =
        tab === 'sku' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabBom').className =
        tab === 'bom' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';

    // 섹션 표시/숨김
    document.getElementById('bomSection').style.display = (tab === 'bom') ? '' : 'none';
    document.getElementById('skuSection').style.display = (tab === 'sku') ? '' : 'none';

    loadData();
}

// ==================== 연월 목록 로드 ====================
async function loadYearMonths() {
    try {
        const p = {};
        const im = document.getElementById('filterInputMonth').value;
        if (im) p.input_month = im;
        if (msOwner) {
            const ow = msOwner.getSelectedString();
            if (ow) p.owner = ow;
        }
        const qs = api.buildQueryString(p);
        const months = await api.get(`${API_BASE}/year-months${qs}`);
        const sel = document.getElementById('filterYearMonth');
        const cur = sel.value;
        sel.innerHTML = '<option value="">선택</option>';
        months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m; opt.textContent = m;
            sel.appendChild(opt);
        });
        // 기존 선택값 유지
        if (cur && months.includes(cur)) {
            sel.value = cur;
        }
    } catch (e) {
        console.error('연월 로드 실패:', e);
    }
}

// ==================== 입력월 변경 시 ====================
async function onInputMonthChange() {
    await loadYearMonths();
    const ym = document.getElementById('filterYearMonth').value;
    if (!ym) return;
    await Promise.all([loadBrands(), loadChannels()]);
    await loadData();
}

// ==================== 연월 변경 시 ====================
async function onYearMonthChange() {
    const ym = document.getElementById('filterYearMonth').value;
    if (!ym) return;
    await Promise.all([loadInputMonths(), loadBrands(), loadChannels()]);
    await loadData();
}

function getRangeParams() {
    const ym = document.getElementById('filterYearMonth').value;
    const p = {};
    if (ym) {
        p.year_month_from = ym;
        p.year_month_to = ym;
    }
    if (msOwner) {
        const ow = msOwner.getSelectedString();
        if (ow) p.owner = ow;
    }
    return p;
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
        msBrand.setOptions(brands);
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

// ==================== 채널 목록 로드 ====================
async function loadChannels() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const channels = await api.get(`${API_BASE}/channels${qs}`);
        msChannel.setOptions(channels);
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

// ==================== 담당자(Owner) 목록 로드 ====================
async function loadOwners() {
    try {
        const owners = await api.get(`${API_BASE}/owners`);
        msOwner.setOptions(owners);
    } catch (e) {
        console.error('담당자 목록 로드 실패:', e);
    }
}

// ==================== 데이터 로드 ====================
async function loadData() {
    const ym = document.getElementById('filterYearMonth').value;
    if (!ym) {
        showAlert('연월을 설정해주세요.', 'warning');
        return;
    }

    if (currentTab === 'sku') {
        await loadSkuData();
        return;
    }

    if (currentTab === 'bom') {
        await loadBomSummary();
        return;
    }
}

// ==================== BOM 분해 v2 ====================

async function loadBomSummary() {
    const tbody = document.querySelector('#bomSkuTable tbody');
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;
    _resetBomDetailPanel();

    try {
        const ym = document.getElementById('filterYearMonth').value;
        const params = {
            year_month_from: ym,
            year_month_to: ym,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) params.owner = ow; }
        const qs = api.buildQueryString(params);

        const result = await api.get(`${API_BASE}/bom-summary${qs}`);
        renderBomSummaryTable(result.data, result.summary);
    } catch (e) {
        console.error('BOM 데이터 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--danger);">
            데이터 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

function renderBomSummaryTable(data, summary) {
    // 요약 카드
    document.getElementById('bomSkuCount').textContent = summary.skuCount ? summary.skuCount.toLocaleString() : '-';
    document.getElementById('bomTotalQty').textContent = summary.totalQty ? summary.totalQty.toLocaleString() : '-';
    document.getElementById('bomFromSetQty').textContent = summary.fromSetQty ? summary.fromSetQty.toLocaleString() : '-';
    document.getElementById('bomFromSingleQty').textContent = summary.fromSingleQty ? summary.fromSingleQty.toLocaleString() : '-';
    document.getElementById('bomDataCount').textContent = `(${data.length}개 SKU)`;

    window._bomItems = data;
    _renderBomSkuHeader();

    const tbody = document.querySelector('#bomSkuTable tbody');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    const sorted = _sortData(data, bomSortKey, bomSortDir);
    _renderBomSkuRows(sorted, tbody);
}

function _renderBomSkuHeader() {
    const table = document.getElementById('bomSkuTable');
    const thead = table.querySelector('thead tr');
    thead.innerHTML = '';
    table._layoutFixed = false;
    table.style.tableLayout = '';

    const cols = [
        { header: 'SKU코드', sortKey: 'code' },
        { header: '상품명', sortKey: 'name' },
        { header: '총 발주수량', sortKey: 'totalQty', align: 'right' },
        { header: '세트유래', sortKey: 'fromSet', align: 'right' },
        { header: '단품', sortKey: 'fromSingle', align: 'right' },
        { header: '상세', sortKey: null }
    ];

    cols.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        if (col.align) th.style.textAlign = col.align;
        if (col.sortKey) {
            _makeSortable(th, col.sortKey, bomSortKey, bomSortDir, _handleBomSort);
        }
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });
}

function _renderBomSkuRows(data, tbody) {
    tbody.innerHTML = data.map(item => {
        const origIdx = window._bomItems.indexOf(item);
        return `
        <tr style="cursor:pointer" onclick="onBomRowClick(${origIdx}, this)">
            <td>${escapeHtml(item.code)}</td>
            <td>${escapeHtml(item.name)}</td>
            <td class="col-qty" style="font-weight:600;color:var(--accent);">${item.totalQty ? item.totalQty.toLocaleString() : '-'}</td>
            <td class="col-qty" style="color:var(--warning);">${item.fromSet ? item.fromSet.toLocaleString() : '-'}</td>
            <td style="text-align:right;color:var(--success);">${item.fromSingle ? item.fromSingle.toLocaleString() : '-'}</td>
            <td style="text-align:center;"><button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); onBomRowClick(${origIdx}, this.closest('tr'));" style="padding:2px 10px;font-size:11px;">상세</button></td>
        </tr>`;
    }).join('');
}

function onBomRowClick(idx, trEl) {
    const item = window._bomItems[idx];
    if (!item) return;
    selectBomSku(item.code, item.name, trEl);
}

async function selectBomSku(code, name, rowEl) {
    selectedBomCode = code;

    // 활성 행 표시
    document.querySelectorAll('#bomSkuTable tbody tr').forEach(tr => tr.classList.remove('active'));
    if (rowEl) rowEl.classList.add('active');

    document.getElementById('bomDetailTitle').textContent = `${code} - ${name}`;
    const contentEl = document.getElementById('bomDetailContent');
    contentEl.innerHTML = `<div style="text-align:center;padding:30px;">
        <div class="spinner"></div>
        <div style="margin-top:8px;color:var(--text-muted);font-size:11px;">불러오는 중...</div>
    </div>`;

    try {
        const ym = document.getElementById('filterYearMonth').value;
        const detailParams = {
            unique_code: code,
            year_month_from: ym,
            year_month_to: ym,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) detailParams.owner = ow; }
        const qs = api.buildQueryString(detailParams);

        const detailData = await api.get(`${API_BASE}/bom-detail${qs}`);
        renderBomDetail(detailData);
    } catch (e) {
        console.error('BOM 디테일 로드 실패:', e);
        contentEl.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);">
            디테일 로드 실패: ${escapeHtml(e.message)}</div>`;
    }
}

function renderBomDetail(detailData) {
    const container = document.getElementById('bomDetailContent');
    container.innerHTML = '';

    const { fromSet, fromSingle } = detailData;

    // 모든 항목을 하나로 합침
    const allItems = [];
    fromSet.forEach(setGroup => {
        setGroup.details.forEach(d => allItems.push(d));
    });
    fromSingle.forEach(d => allItems.push(d));

    if (allItems.length === 0) {
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">
            상세 데이터가 없습니다</div>`;
        return;
    }

    // 채널별 → 소스타입별 집계
    const channelMap = new Map();
    allItems.forEach(d => {
        const ch = d.channel || '(채널없음)';
        if (!channelMap.has(ch)) channelMap.set(ch, { channel: ch, sources: new Map(), total: 0 });
        const chGroup = channelMap.get(ch);

        // 소스타입 정규화: 정기/비정기/불출
        let sourceLabel;
        if (d.sourceType.includes('비정기')) sourceLabel = '비정기';
        else if (d.sourceType === '불출') sourceLabel = '불출';
        else sourceLabel = '정기';

        if (!chGroup.sources.has(sourceLabel)) chGroup.sources.set(sourceLabel, 0);
        chGroup.sources.set(sourceLabel, chGroup.sources.get(sourceLabel) + (d.qty || 0));
        chGroup.total += (d.qty || 0);
    });

    // 총합계
    const grandTotal = Array.from(channelMap.values()).reduce((s, v) => s + v.total, 0);

    // 수량 내림차순 정렬
    const sorted = Array.from(channelMap.values()).sort((a, b) => b.total - a.total);

    // 합계 헤더
    const totalDiv = document.createElement('div');
    totalDiv.className = 'sku-channel-header';
    totalDiv.style.cssText = 'border-bottom:2px solid var(--border);margin-bottom:4px;';
    totalDiv.innerHTML = `
        <span><i class="fa-solid fa-calculator" style="margin-right:6px;opacity:0.5;"></i>합계</span>
        <span class="sku-channel-subtotal">수량 <b>${grandTotal.toLocaleString()}</b></span>
    `;
    container.appendChild(totalDiv);

    sorted.forEach(chGroup => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'sku-channel-group';

        // 채널 헤더
        const chHeader = document.createElement('div');
        chHeader.className = 'sku-channel-header';
        const ratio = grandTotal > 0 ? (chGroup.total / grandTotal * 100).toFixed(1) : 0;
        chHeader.innerHTML = `
            <span><i class="fa-solid fa-store" style="margin-right:6px;opacity:0.5;"></i>${escapeHtml(chGroup.channel)}</span>
            <span class="sku-channel-subtotal">수량 <b>${chGroup.total.toLocaleString()}</b> (${ratio}%)</span>
        `;
        groupDiv.appendChild(chHeader);

        // 소스타입 인라인 표시
        const parts = [];
        ['정기', '비정기'].forEach(src => {
            if (!chGroup.sources.has(src)) return;
            const qty = chGroup.sources.get(src);
            const badgeClass = src === '비정기' ? 'irregular' : 'regular';
            parts.push(`<span class="sku-source-badge ${badgeClass}">${src}</span> <span style="font-weight:500;">${qty.toLocaleString()}</span>`);
        });
        if (parts.length > 0) {
            const row = document.createElement('div');
            row.className = 'detail-inline-row';
            row.innerHTML = parts.join('<span class="detail-inline-sep">·</span>');
            groupDiv.appendChild(row);
        }

        container.appendChild(groupDiv);
    });

}

function _resetBomDetailPanel() {
    selectedBomCode = null;
    document.querySelectorAll('#bomSkuTable tbody tr').forEach(tr => tr.classList.remove('active'));
    document.getElementById('bomDetailTitle').textContent = '분해 상세';
    document.getElementById('bomDetailContent').innerHTML = `
        <div class="sku-detail-empty">
            <i class="fa-solid fa-arrow-left" style="font-size:20px;margin-bottom:8px;opacity:0.3;"></i>
            <div>좌측 목록에서 SKU를 선택해주세요</div>
        </div>`;
}

function _handleBomSort(sortKey) {
    if (bomSortKey === sortKey) {
        bomSortDir = bomSortDir === 'DESC' ? 'ASC' : 'DESC';
    } else {
        bomSortKey = sortKey;
        bomSortDir = 'DESC';
    }
    const tbody = document.querySelector('#bomSkuTable tbody');
    if (!window._bomItems || window._bomItems.length === 0) return;
    _renderBomSkuRows(_sortData(window._bomItems, bomSortKey, bomSortDir), tbody);
    document.querySelectorAll('#bomSkuTable thead th[data-sortable]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.getAttribute('data-sortable') === bomSortKey) {
            th.classList.add(bomSortDir === 'ASC' ? 'sort-asc' : 'sort-desc');
        }
    });
}

// ==================== SKU 데이터 로드 ====================
async function loadSkuData(keepDetail = false) {
    const tbody = document.querySelector('#skuTable tbody');
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    // 디테일 패널 초기화 (keepDetail이면 유지)
    if (!keepDetail) {
        _resetDetailPanel();
    }

    try {
        const params = {
            year_month_from: document.getElementById('filterYearMonth').value,
            year_month_to: document.getElementById('filterYearMonth').value,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) params.owner = ow; }
        const qs = api.buildQueryString(params);

        const result = await api.get(`${API_BASE}/sku-data${qs}`);
        renderSkuTable(result.data, result.summary);
    } catch (e) {
        console.error('SKU 데이터 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--danger);">
            데이터 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

// ==================== SKU 테이블 렌더링 ====================
function renderSkuTable(data, summary) {
    // 요약 카드 업데이트
    document.getElementById('skuTotalAmount').textContent =
        summary.totalAmount ? Math.round(summary.totalAmount).toLocaleString() : '-';
    document.getElementById('skuTotalQty').textContent =
        summary.totalQuantity ? summary.totalQuantity.toLocaleString() : '-';
    document.getElementById('skuProductCount').textContent =
        summary.productCount ? summary.productCount.toLocaleString() : '-';

    document.getElementById('skuDataCount').textContent = `(${data.length}개 SKU)`;

    // SKU 데이터를 전역 배열에 저장
    window._skuItems = data;

    // 헤더에 정렬/리사이즈 적용 (최초 1회)
    _renderSkuHeader();

    const tbody = document.querySelector('#skuTable tbody');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    const sorted = _sortData(data, skuSortKey, skuSortDir);
    _renderSkuRows(sorted, tbody);
}

function _renderSkuHeader() {
    const table = document.getElementById('skuTable');
    const thead = table.querySelector('thead tr');
    thead.innerHTML = '';
    table._layoutFixed = false;
    table.style.tableLayout = '';

    const cols = [
        { header: '코드', sortKey: 'code' },
        { header: '상품명', sortKey: 'name' },
        { header: '매출합계(VAT포함)', sortKey: 'totalAmount', align: 'right' },
        { header: '수량합계', sortKey: 'totalQuantity', align: 'right' },
        { header: '상세', sortKey: null }
    ];

    cols.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        if (col.align) th.style.textAlign = col.align;
        if (col.sortKey) {
            _makeSortable(th, col.sortKey, skuSortKey, skuSortDir, _handleSkuSort);
        }
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });
}

function _renderSkuRows(data, tbody) {
    // Re-index based on original _skuItems for onclick reference
    tbody.innerHTML = data.map(item => {
        const origIdx = window._skuItems.indexOf(item);
        return `
        <tr style="cursor:pointer" onclick="onSkuRowClick(${origIdx}, this)">
            <td>${escapeHtml(item.code)}</td>
            <td>${escapeHtml(item.name)}</td>
            <td class="col-amount">${item.totalAmount ? Math.round(item.totalAmount).toLocaleString() : '-'}</td>
            <td class="col-qty">${item.totalQuantity ? item.totalQuantity.toLocaleString() : '-'}</td>
            <td style="text-align:center;"><button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); onSkuRowClick(${origIdx}, this.closest('tr'));" style="padding:2px 10px;font-size:11px;">상세</button></td>
        </tr>`;
    }).join('');
}

// ==================== SKU 행 클릭 핸들러 ====================
function onSkuRowClick(idx, trEl) {
    const item = window._skuItems[idx];
    if (!item) return;
    selectSku(item.code, item.name, trEl);
}

// ==================== SKU 디테일 패널 ====================

// ==================== SKU 선택 (디테일 로드) ====================
async function selectSku(code, name, rowEl) {
    // 수정사항 있을 때 다른 SKU 선택 시 확인
    if (window._skuDirtySet && window._skuDirtySet.size > 0 && selectedSkuCode && selectedSkuCode !== code) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 다른 SKU를 선택하시겠습니까?', () => {
            window._skuDirtySet = new Set();
            _doSelectSku(code, name, rowEl);
        });
        return;
    }
    await _doSelectSku(code, name, rowEl);
}

async function _doSelectSku(code, name, rowEl) {
    selectedSkuCode = code;

    // 활성 행 표시
    document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
    if (rowEl) rowEl.classList.add('active');

    // 패널 표시
    document.getElementById('skuDetailTitle').textContent = `${code} - ${name}`;
    const contentEl = document.getElementById('skuDetailContent');
    contentEl.innerHTML = `<div style="text-align:center;padding:30px;">
        <div class="spinner"></div>
        <div style="margin-top:8px;color:var(--text-muted);font-size:11px;">불러오는 중...</div>
    </div>`;

    try {
        const detailParams = {
            unique_code: code,
            year_month_from: document.getElementById('filterYearMonth').value,
            year_month_to: document.getElementById('filterYearMonth').value,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) detailParams.owner = ow; }
        const qs = api.buildQueryString(detailParams);

        const detailData = await api.get(`${API_BASE}/sku-detail${qs}`);
        renderSkuDetail(detailData);
    } catch (e) {
        console.error('SKU 디테일 로드 실패:', e);
        contentEl.innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);">
            디테일 로드 실패: ${escapeHtml(e.message)}</div>`;
    }
}

// ==================== SKU 디테일 렌더링 (계층 UI) ====================
function renderSkuDetail(detailData) {
    const container = document.getElementById('skuDetailContent');
    const footer = document.getElementById('skuDetailFooter');
    container.innerHTML = '';

    // dirty 상태 초기화
    window._skuDetailItems = detailData;
    window._skuDirtySet = new Set();
    if (footer) footer.style.display = 'none';

    if (detailData.length === 0) {
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">
            상세 데이터가 없습니다</div>`;
        return;
    }

    // 데이터를 채널 > 구분(+행사명) 계층으로 그룹화
    const channelGroups = _groupSkuDetail(detailData);

    channelGroups.forEach(chGroup => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'sku-channel-group';

        // 채널 헤더 + 소계
        const chHeader = document.createElement('div');
        chHeader.className = 'sku-channel-header';
        const chAmtTotal = chGroup.items.reduce((s, i) => s + (i.amount || 0), 0);
        const chQtyTotal = chGroup.items.reduce((s, i) => s + (i.quantity || 0), 0);
        chHeader.innerHTML = `
            <span><i class="fa-solid fa-store" style="margin-right:6px;opacity:0.5;"></i>${escapeHtml(chGroup.channel)}</span>
            <span class="sku-channel-subtotal">
                매출 <b>${chAmtTotal ? chAmtTotal.toLocaleString() : '-'}</b>
                &nbsp;|&nbsp; 수량 <b>${chQtyTotal ? chQtyTotal.toLocaleString() : '-'}</b>
            </span>
        `;
        groupDiv.appendChild(chHeader);

        // 구분별 인라인 표시
        chGroup.sources.forEach(srcGroup => {
            const badgeClass = srcGroup.sourceType.includes('비정기') ? 'irregular'
                : srcGroup.sourceType === '불출' ? 'withdrawal' : 'regular';

            const srcAmt = srcGroup.indices.reduce((s, idx) => s + (detailData[idx].amount || 0), 0);
            const srcQty = srcGroup.indices.reduce((s, idx) => s + (detailData[idx].quantity || 0), 0);

            let labelHtml = `<span class="sku-source-badge ${badgeClass}">${escapeHtml(srcGroup.sourceType)}</span>`;
            if (srcGroup.irregularName) {
                labelHtml += `<span class="sku-irregular-label">${escapeHtml(srcGroup.irregularName)}</span>`;
            }

            const row = document.createElement('div');
            row.className = 'detail-inline-row';

            // 숨겨진 input들 (dirty 추적용)
            let hiddenInputs = '';
            srcGroup.indices.forEach(idx => {
                const item = detailData[idx];
                hiddenInputs += `
                    <input type="hidden" id="skuDetail-amt-${idx}" value="${item.amount || 0}" data-idx="${idx}" data-field="amount">
                    <input type="hidden" id="skuDetail-qty-${idx}" value="${item.quantity || 0}" data-idx="${idx}" data-field="quantity">
                `;
            });

            row.innerHTML = `
                ${labelHtml}
                <span class="detail-inline-values">
                    매출 <b>${srcAmt ? srcAmt.toLocaleString() : '-'}</b>
                    <span class="detail-inline-sep">·</span>
                    수량 <b>${srcQty ? srcQty.toLocaleString() : '-'}</b>
                </span>
                ${hiddenInputs}
            `;
            groupDiv.appendChild(row);
        });

        container.appendChild(groupDiv);
    });
}

function _groupSkuDetail(data) {
    const channelMap = new Map();

    data.forEach((item, idx) => {
        if (!channelMap.has(item.channel)) {
            channelMap.set(item.channel, { channel: item.channel, sources: [], items: [] });
        }
        const chGroup = channelMap.get(item.channel);
        chGroup.items.push(item);

        // 비정기는 행사명까지 포함한 키로 그룹화
        const sourceKey = item.irregularName
            ? `${item.sourceType}::${item.irregularName}`
            : item.sourceType;

        let srcGroup = chGroup.sources.find(s => s.key === sourceKey);
        if (!srcGroup) {
            srcGroup = {
                key: sourceKey,
                sourceType: item.sourceType,
                irregularName: item.irregularName || null,
                indices: []
            };
            chGroup.sources.push(srcGroup);
        }
        srcGroup.indices.push(idx);
    });

    return [...channelMap.values()];
}

// ==================== SKU 디테일 인라인 편집 ====================
function _parseNum(v) { return Number(String(v).replace(/,/g, '')) || 0; }

function _skuInputFocus(el) {
    // 포커스 시 쉼표 제거하여 편집 가능하게
    el.value = String(el.value).replace(/,/g, '');
    el.select();
}

function _skuInputBlur(el, idx) {
    // 블러 시 천단위 쉼표 적용
    const raw = _parseNum(el.value);
    el.value = raw.toLocaleString();

    // 수량 변경 시 매출 자동 계산: 단가(기존매출/기존수량) × 새수량
    if (el.dataset.field === 'quantity') {
        const item = window._skuDetailItems[idx];
        const origAmt = item.amount || 0;
        const origQty = item.quantity || 0;
        if (origQty > 0) {
            const unitPrice = origAmt / origQty;
            const newAmt = Math.round(unitPrice * raw);
            const tr = document.getElementById(`skuDetail-${idx}`);
            const amtInput = tr.querySelector('input[data-field="amount"]');
            if (amtInput) amtInput.value = newAmt.toLocaleString();
        }
    }

    onSkuDetailInput(idx);
}

function onSkuDetailInput(idx) {
    const item = window._skuDetailItems[idx];
    const tr = document.getElementById(`skuDetail-${idx}`);
    const inputs = tr.querySelectorAll('input[type="text"]');

    const newAmount = _parseNum(inputs[0].value);
    const newQty = _parseNum(inputs[1].value);
    const origAmount = item.amount || 0;
    const origQty = item.quantity || 0;

    if (newAmount !== origAmount || newQty !== origQty) {
        window._skuDirtySet.add(idx);
        tr.classList.add('sku-dirty');
    } else {
        window._skuDirtySet.delete(idx);
        tr.classList.remove('sku-dirty');
    }
    updateSkuDetailFooter();
}

function updateSkuDetailFooter() {
    const footer = document.getElementById('skuDetailFooter');
    if (!footer) return;
    const count = window._skuDirtySet ? window._skuDirtySet.size : 0;
    if (count > 0) {
        footer.style.display = '';
        document.getElementById('skuDirtyCount').textContent = `수정된 항목: ${count}건`;
    } else {
        footer.style.display = 'none';
    }
}

async function saveSkuDetail() {
    if (!window._skuDirtySet || window._skuDirtySet.size === 0) return;

    const items = [];
    window._skuDirtySet.forEach(idx => {
        const item = window._skuDetailItems[idx];
        const tr = document.getElementById(`skuDetail-${idx}`);
        const inputs = tr.querySelectorAll('input[type="text"]');

        items.push({
            recordId: item.recordId,
            sourceType: item.sourceCode,
            channel: item.channel,
            yearMonth: item.yearMonth,
            amount: _parseNum(inputs[0].value),
            quantity: _parseNum(inputs[1].value)
        });
    });

    try {
        const result = await api.put(`${API_BASE}/sku-inline-update`, {
            uniqueCode: selectedSkuCode,
            productName: document.getElementById('skuDetailTitle').textContent.split(' - ').slice(1).join(' - '),
            items
        });
        showAlert(result.message, 'success');

        // 로컬 데이터 업데이트 & dirty 초기화
        window._skuDirtySet.forEach(idx => {
            const tr = document.getElementById(`skuDetail-${idx}`);
            const inputs = tr.querySelectorAll('input[type="text"]');
            window._skuDetailItems[idx].amount = _parseNum(inputs[0].value);
            window._skuDetailItems[idx].quantity = _parseNum(inputs[1].value);
            tr.classList.remove('sku-dirty');
        });
        window._skuDirtySet.clear();
        updateSkuDetailFooter();

        // SKU 합산 테이블 새로고침 (모달 유지)
        loadSkuData(true);
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

// ==================== SKU 디테일 닫기 ====================
function closeSkuDetail() {
    if (window._skuDirtySet && window._skuDirtySet.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 닫으시겠습니까?', () => {
            window._skuDirtySet = new Set();
            _resetDetailPanel();
        });
        return;
    }
    _resetDetailPanel();
}

function _resetDetailPanel() {
    selectedSkuCode = null;
    document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
    document.getElementById('skuDetailTitle').textContent = '상품 상세';
    document.getElementById('skuDetailContent').innerHTML = `
        <div class="sku-detail-empty">
            <i class="fa-solid fa-arrow-left" style="font-size:20px;margin-bottom:8px;opacity:0.3;"></i>
            <div>좌측 목록에서 SKU를 선택해주세요</div>
        </div>`;
    document.getElementById('skuDetailFooter').style.display = 'none';
}

// ==================== 필터 초기화 ====================
async function resetFilters() {
    document.getElementById('filterInputMonth').value = '';
    msBrand.reset();
    msChannel.reset();
    msOwner.reset();
    await loadYearMonths();
    await onYearMonthChange();
}

// ==================== 엑셀 다운로드 ====================
// ==================== 테이블 헤더 정렬/리사이즈 유틸 ====================
function _makeSortable(th, sortKey, currentKey, currentDir, onSortClick) {
    th.setAttribute('data-sortable', sortKey);
    th.style.position = 'relative';
    th.style.cursor = 'pointer';
    th.style.userSelect = 'none';
    th.style.paddingRight = '28px';

    if (currentKey === sortKey) {
        th.classList.add(currentDir === 'ASC' ? 'sort-asc' : 'sort-desc');
    }

    th.addEventListener('click', (e) => {
        if (e.target.classList.contains('resize-handle')) return;
        onSortClick(sortKey);
    });
}

function _addResizeHandle(th, table) {
    th.style.position = 'relative';
    const handle = document.createElement('div');
    handle.className = 'resize-handle';
    handle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (!table._layoutFixed) {
            table.querySelectorAll('thead th').forEach(t => {
                t.style.width = t.offsetWidth + 'px';
            });
            table.style.tableLayout = 'fixed';
            table._layoutFixed = true;
        }

        const startX = e.pageX;
        const startWidth = th.offsetWidth;
        handle.classList.add('resizing');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';

        const onMove = (ev) => {
            th.style.width = Math.max(40, startWidth + (ev.pageX - startX)) + 'px';
        };
        const onUp = () => {
            handle.classList.remove('resizing');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
    th.appendChild(handle);
}

function _handleSkuSort(sortKey) {
    if (skuSortKey === sortKey) {
        skuSortDir = skuSortDir === 'DESC' ? 'ASC' : 'DESC';
    } else {
        skuSortKey = sortKey;
        skuSortDir = 'DESC';
    }
    // Re-render with current data (summary cards already set)
    const tbody = document.querySelector('#skuTable tbody');
    if (!window._skuItems || window._skuItems.length === 0) return;
    _renderSkuRows(_sortData(window._skuItems, skuSortKey, skuSortDir), tbody);
    // Update sort indicator on headers
    document.querySelectorAll('#skuTable thead th[data-sortable]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.getAttribute('data-sortable') === skuSortKey) {
            th.classList.add(skuSortDir === 'ASC' ? 'sort-asc' : 'sort-desc');
        }
    });
}

function _sortData(data, key, dir) {
    if (!key || !dir) return data;
    const sorted = [...data];
    const mult = dir === 'ASC' ? 1 : -1;

    sorted.sort((a, b) => {
        let va, vb;
        // Pivot/BOM table keys
        if (key === 'brand' || key === 'channel' || key === 'name') {
            va = (a[key] || ''); vb = (b[key] || '');
            return mult * va.localeCompare(vb, 'ko');
        }
        if (key === 'totalAmount' || key === 'totalQuantity' || key === 'totalQty' || key === 'fromSet' || key === 'fromSingle') {
            va = a[key] || 0; vb = b[key] || 0;
            return mult * (va - vb);
        }
        // SKU table keys
        if (key === 'code') {
            va = (a.code || ''); vb = (b.code || '');
            return mult * va.localeCompare(vb, 'ko');
        }
        // Month-specific keys: amt_2025-01, qty_2025-01
        const amtMatch = key.match(/^amt_(.+)$/);
        if (amtMatch) {
            const ym = amtMatch[1];
            va = (a.months && a.months[ym]) ? a.months[ym].amount || 0 : 0;
            vb = (b.months && b.months[ym]) ? b.months[ym].amount || 0 : 0;
            return mult * (va - vb);
        }
        const qtyMatch = key.match(/^qty_(.+)$/);
        if (qtyMatch) {
            const ym = qtyMatch[1];
            if (a.months && typeof a.months[qtyMatch[1]] === 'number') {
                // BOM: months[ym] is a number
                va = a.months[ym] || 0; vb = b.months[ym] || 0;
            } else {
                va = (a.months && a.months[ym]) ? a.months[ym].quantity || 0 : 0;
                vb = (b.months && b.months[ym]) ? b.months[ym].quantity || 0 : 0;
            }
            return mult * (va - vb);
        }
        return 0;
    });
    return sorted;
}

function downloadExcel() {
    const ym = document.getElementById('filterYearMonth').value;
    if (!ym) {
        showAlert('연월을 설정해주세요.', 'warning');
        return;
    }

    const token = localStorage.getItem('access_token');
    const dlParams = {
        year_month_from: ym,
        year_month_to: ym,
        input_month: document.getElementById('filterInputMonth').value,
        brand: msBrand.getSelectedString(),
        channel: msChannel.getSelectedString()
    };
    { const ow = msOwner.getSelectedString(); if (ow) dlParams.owner = ow; }
    const qs = api.buildQueryString(dlParams);

    const endpoint = currentTab === 'bom' ? '/bom-download' : '/download';
    const filePrefix = currentTab === 'bom' ? 'BOM분해' : '예상매출_통합';

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
        a.download = `${filePrefix}_${ym}.xlsx`;
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
