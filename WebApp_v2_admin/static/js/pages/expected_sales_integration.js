/**
 * 예상 판매량 통합 조회 JavaScript
 * - 탭: 통합 조회 / BOM 분해 / SKU 관리
 * - 피벗 테이블: 행(브랜드/채널/상품) × 열(연월별)
 * - SKU 관리: SKU 합산 + 디테일 패널
 */

const API_BASE = '/api/expected-sales-integration';
let currentYearMonths = [];
let currentData = [];
let currentTab = 'integration';
let selectedSkuCode = null;

// Sort state
let pivotSortKey = null, pivotSortDir = null;
let skuSortKey = null, skuSortDir = null;

// Multi-select instances
let msBrand, msChannel, msOwner;

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Multi-select 초기화
        msBrand = new MultiSelect('filterBrand', { placeholder: '전체' });
        msChannel = new MultiSelect('filterChannel', { placeholder: '전체' });
        msOwner = new MultiSelect('filterOwner', { placeholder: '전체', onChange: () => onRangeChange() });

        setDefaultRange();
        await loadOwners();
        await onRangeChange();
    } catch (e) {
        console.error('초기화 실패:', e);
        const tbody = document.querySelector('#pivotTable tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:var(--danger);">
            초기화 실패: ${e.message}</td></tr>`;
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
    pivotSortKey = null; pivotSortDir = null;
    skuSortKey = null; skuSortDir = null;
    document.getElementById('tabIntegration').className =
        tab === 'integration' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabBom').className =
        tab === 'bom' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabSku').className =
        tab === 'sku' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';

    // 섹션 표시/숨김
    document.getElementById('pivotSection').style.display = (tab === 'sku') ? 'none' : '';
    document.getElementById('skuSection').style.display = (tab === 'sku') ? '' : 'none';

    if (tab !== 'sku') {
        document.getElementById('tableTitle').textContent =
            tab === 'bom' ? 'BOM 분해 결과' : '통합 조회 결과';
    }

    loadData();
}

// ==================== 기본 연월 설정 ====================
function setDefaultRange() {
    const now = new Date();
    const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    document.getElementById('filterYearMonth').value = ym;
}

// ==================== 연월 변경 시 ====================
async function onRangeChange() {
    const ym = document.getElementById('filterYearMonth').value;
    if (!ym) return;

    await Promise.all([loadInputMonths(), loadBrands(), loadChannels()]);
    await loadData();
}

function getRangeParams() {
    const ym = document.getElementById('filterYearMonth').value;
    const p = {
        year_month_from: ym,
        year_month_to: ym
    };
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

    const tbody = document.querySelector('#pivotTable tbody');
    tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    try {
        const params = {
            year_month_from: ym,
            year_month_to: ym,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) params.owner = ow; }
        const qs = api.buildQueryString(params);

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
    const table = document.getElementById('pivotTable');
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    thead.innerHTML = '';
    table._layoutFixed = false;
    table.style.tableLayout = '';

    const staticCols = [
        { header: '브랜드', sortKey: 'brand' },
        { header: '채널', sortKey: 'channel' },
        { header: '상품명', sortKey: 'name' }
    ];

    staticCols.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        _makeSortable(th, col.sortKey, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const thAmt = document.createElement('th');
        thAmt.textContent = `${ym}(매출)`;
        thAmt.style.textAlign = 'right';
        _makeSortable(thAmt, `amt_${ym}`, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(thAmt, table);
        thead.appendChild(thAmt);

        const thQty = document.createElement('th');
        thQty.textContent = `${ym}(수량)`;
        thQty.style.textAlign = 'right';
        _makeSortable(thQty, `qty_${ym}`, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(thQty, table);
        thead.appendChild(thQty);
    });

    [{ header: '합계(매출)', key: 'totalAmount' }, { header: '합계(수량)', key: 'totalQuantity' }].forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        th.style.textAlign = 'right';
        th.style.background = 'rgba(34,197,94,0.1)';
        _makeSortable(th, col.key, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length * 2 + 2;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    const sorted = _sortData(data, pivotSortKey, pivotSortDir);
    sorted.forEach(item => {
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
    const table = document.getElementById('pivotTable');
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    thead.innerHTML = '';
    table._layoutFixed = false;
    table.style.tableLayout = '';

    const staticCols = [
        { header: '브랜드', sortKey: 'brand' },
        { header: '채널', sortKey: 'channel' },
        { header: '상품명', sortKey: 'name' }
    ];

    staticCols.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        _makeSortable(th, col.sortKey, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const th = document.createElement('th');
        th.textContent = `${ym}(수량)`;
        th.style.textAlign = 'right';
        _makeSortable(th, `qty_${ym}`, pivotSortKey, pivotSortDir, _handlePivotSort);
        _addResizeHandle(th, table);
        thead.appendChild(th);
    });

    const thTotal = document.createElement('th');
    thTotal.textContent = '합계(수량)';
    thTotal.style.textAlign = 'right';
    thTotal.style.background = 'rgba(34,197,94,0.1)';
    _makeSortable(thTotal, 'totalQuantity', pivotSortKey, pivotSortDir, _handlePivotSort);
    _addResizeHandle(thTotal, table);
    thead.appendChild(thTotal);

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length + 1;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    const sorted = _sortData(data, pivotSortKey, pivotSortDir);
    sorted.forEach(item => {
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

// ==================== SKU 데이터 로드 ====================
async function loadSkuData(keepDetail = false) {
    const tbody = document.querySelector('#skuTable tbody');
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    // 디테일 모달 숨김 (keepDetail이면 유지)
    if (!keepDetail) {
        closeSkuDetail();
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
        summary.totalAmount ? Math.round(summary.totalAmount / 1.1).toLocaleString() : '-';
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
        { header: '매출합계', sortKey: 'totalAmount', align: 'right' },
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
            <td class="col-amount">${item.totalAmount ? item.totalAmount.toLocaleString() : '-'}</td>
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

// ==================== SKU 디테일 모달 ====================
let skuDetailModal = null;

function getSkuDetailModal() {
    if (!skuDetailModal) {
        skuDetailModal = new ModalManager('skuDetailModal');
        // hide() 오버라이드: 미저장 변경사항 확인
        const originalHide = skuDetailModal.hide.bind(skuDetailModal);
        skuDetailModal.hide = function() {
            if (window._skuDirtySet && window._skuDirtySet.size > 0) {
                showConfirm('저장하지 않은 변경사항이 있습니다. 닫으시겠습니까?', () => {
                    window._skuDirtySet = new Set();
                    originalHide();
                    selectedSkuCode = null;
                    document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
                });
                return;
            }
            originalHide();
            selectedSkuCode = null;
            document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
        };
    }
    return skuDetailModal;
}

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

    // 모달 표시
    document.getElementById('skuDetailTitle').textContent = `${code} - ${name}`;
    const contentEl = document.getElementById('skuDetailContent');
    contentEl.innerHTML = `<div style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </div>`;
    getSkuDetailModal().show();

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

        // 구분별 섹션
        chGroup.sources.forEach(srcGroup => {
            const section = document.createElement('div');
            section.className = 'sku-source-section';

            // 구분 헤더
            const srcHeader = document.createElement('div');
            srcHeader.className = 'sku-source-header';
            const badgeClass = srcGroup.sourceType.includes('비정기') ? 'irregular'
                : srcGroup.sourceType === '불출' ? 'withdrawal' : 'regular';
            let headerHtml = `<span class="sku-source-badge ${badgeClass}">${escapeHtml(srcGroup.sourceType)}</span>`;
            if (srcGroup.irregularName) {
                headerHtml += `<span class="sku-irregular-label">${escapeHtml(srcGroup.irregularName)}</span>`;
            }
            srcHeader.innerHTML = headerHtml;
            section.appendChild(srcHeader);

            // 데이터 테이블
            const table = document.createElement('table');
            table.className = 'sku-detail-table';

            const thead = document.createElement('thead');
            thead.innerHTML = `<tr><th style="width:100px;">연월</th><th>매출</th><th>수량</th></tr>`;
            table.appendChild(thead);

            const tbody = document.createElement('tbody');
            const isWithdrawal = srcGroup.sourceType === '불출';

            srcGroup.indices.forEach(idx => {
                const item = detailData[idx];
                const tr = document.createElement('tr');
                tr.id = `skuDetail-${idx}`;
                const fmtAmt = (item.amount || 0).toLocaleString();
                const fmtQty = (item.quantity || 0).toLocaleString();
                tr.innerHTML = `
                    <td>${escapeHtml(item.yearMonth)}</td>
                    <td style="text-align:right;">
                        <input type="text" value="${fmtAmt}" data-idx="${idx}" data-field="amount"
                               onfocus="_skuInputFocus(this)" onblur="_skuInputBlur(this, ${idx})"
                               ${isWithdrawal ? 'disabled' : ''}>
                    </td>
                    <td style="text-align:right;">
                        <input type="text" value="${fmtQty}" data-idx="${idx}" data-field="quantity"
                               onfocus="_skuInputFocus(this)" onblur="_skuInputBlur(this, ${idx})">
                    </td>
                `;
                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            section.appendChild(table);
            groupDiv.appendChild(section);
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
            amount: _parseNum(inputs[0].value),
            quantity: _parseNum(inputs[1].value)
        });
    });

    try {
        const result = await api.put(`${API_BASE}/sku-inline-update`, { items });
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
    if (skuDetailModal) skuDetailModal.hide();
}

// ==================== 필터 초기화 ====================
function resetFilters() {
    document.getElementById('filterInputMonth').value = '';
    msBrand.reset();
    msChannel.reset();
    msOwner.reset();
    setDefaultRange();
    onRangeChange();
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

function _handlePivotSort(sortKey) {
    if (pivotSortKey === sortKey) {
        pivotSortDir = pivotSortDir === 'DESC' ? 'ASC' : 'DESC';
    } else {
        pivotSortKey = sortKey;
        pivotSortDir = 'DESC';
    }
    if (currentTab === 'bom') {
        renderBomTable(currentYearMonths, currentData);
    } else {
        renderPivotTable(currentYearMonths, currentData);
    }
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
        if (key === 'totalAmount' || key === 'totalQuantity') {
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
