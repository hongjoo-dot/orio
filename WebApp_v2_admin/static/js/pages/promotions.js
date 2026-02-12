/**
 * 비정기 관리 페이지 JavaScript
 * - 마스터: 비정기 목록 (Promotion) — 컴팩트 그룹 뷰
 * - 디테일: 비정기 상품 (PromotionProduct) — 인라인 편집
 */

// ==================== 상태 변수 ====================
let masterTableManager, detailTableManager;
let uploadModal, uploadResultModal;

// 마스터 데이터
let currentMasterData = [];          // 정렬용
let masterDataMap = {};              // {PromotionID: row}
let currentPromotionId = null;
let currentPromotionData = null;

// 디테일 데이터
let currentDetailItems = [];         // 정렬용
let originalData = {};               // {PromotionProductID: {PromotionPrice, ExpectedSalesAmount, ExpectedQuantity, Notes}}
let dirtyRows = new Map();           // Map<PromotionProductID, {PromotionPrice, ExpectedSalesAmount, ExpectedQuantity, Notes}>

// 필터
let currentFilters = {};

// ==================== 마스터 컬럼 정의 ====================
const masterColumns = [
    {
        key: 'PromotionName',
        header: '비정기',
        sortKey: 'PromotionName',
        render: (row) => {
            const statusLabels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
            const statusLabel = statusLabels[row.Status] || row.Status;
            const dateRange = (row.StartDate && row.EndDate) ? `${row.StartDate} ~ ${row.EndDate}` : '';
            return `<div class="group-info">
                <span class="group-title">${escapeHtml(row.PromotionName)}</span>
                <span class="group-meta">
                    ${escapeHtml(row.ChannelName)} · ${escapeHtml(row.PromotionType)}
                    <span class="status-badge status-${row.Status}" style="margin-left:4px;">${statusLabel}</span>
                </span>
                ${dateRange ? `<span class="group-meta">${dateRange}</span>` : ''}
            </div>`;
        }
    },
    {
        key: 'TotalSalesAmount',
        header: '예상매출',
        sortKey: 'TotalSalesAmount',
        render: (row) => `<div style="text-align:right;font-size:13px;">${row.TotalSalesAmount.toLocaleString()}</div>`
    },
    {
        key: 'ProductCount',
        header: '상품수',
        sortKey: 'ProductCount',
        render: (row) => `<div style="text-align:right;font-size:13px;">${row.ProductCount}</div>`
    }
];

// ==================== 디테일 컬럼 정의 ====================
const detailColumns = [
    {
        key: 'ERPCode',
        header: '품목코드',
        sortKey: 'ERPCode',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.ERPCode) || '-'}</span>`
    },
    {
        key: 'ProductName',
        header: '상품명',
        sortKey: 'ProductName',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.ProductName) || '-'}</span>`
    },
    {
        key: 'SellingPrice',
        header: '판매가',
        sortKey: 'SellingPrice',
        render: (row) => `<div style="text-align:right;font-size:13px;">${(row.SellingPrice || 0).toLocaleString()}</div>`
    },
    {
        key: 'PromotionPrice',
        header: '비정기가',
        sortKey: 'PromotionPrice',
        render: (row) => {
            const dirty = dirtyRows.get(row.PromotionProductID);
            const val = dirty && dirty.PromotionPrice !== undefined ? dirty.PromotionPrice : (row.PromotionPrice || 0);
            const orig = originalData[row.PromotionProductID];
            const isDirty = orig && val !== orig.PromotionPrice;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.PromotionProductID}" data-field="PromotionPrice"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onAmountBlur(this)">`;
        }
    },
    {
        key: 'ExpectedSalesAmount',
        header: '예상매출',
        sortKey: 'ExpectedSalesAmount',
        render: (row) => {
            const dirty = dirtyRows.get(row.PromotionProductID);
            const val = dirty && dirty.ExpectedSalesAmount !== undefined ? dirty.ExpectedSalesAmount : (row.ExpectedSalesAmount || 0);
            const orig = originalData[row.PromotionProductID];
            const isDirty = orig && val !== orig.ExpectedSalesAmount;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.PromotionProductID}" data-field="ExpectedSalesAmount"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onAmountBlur(this)">`;
        }
    },
    {
        key: 'ExpectedQuantity',
        header: '예상수량',
        sortKey: 'ExpectedQuantity',
        render: (row) => {
            const dirty = dirtyRows.get(row.PromotionProductID);
            const val = dirty && dirty.ExpectedQuantity !== undefined ? dirty.ExpectedQuantity : (row.ExpectedQuantity || 0);
            const orig = originalData[row.PromotionProductID];
            const isDirty = orig && val !== orig.ExpectedQuantity;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.PromotionProductID}" data-field="ExpectedQuantity"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onQuantityBlur(this)">`;
        }
    },
    {
        key: 'Notes',
        header: '비고',
        render: (row) => {
            const dirty = dirtyRows.get(row.PromotionProductID);
            const val = dirty && dirty.Notes !== undefined ? dirty.Notes : (row.Notes || '');
            const orig = originalData[row.PromotionProductID];
            const isDirty = orig && val !== (orig.Notes || '');
            return `<input type="text" class="inline-input${isDirty ? ' dirty' : ''}"
                data-id="${row.PromotionProductID}" data-field="Notes"
                value="${escapeHtml(val)}"
                oninput="onNotesInput(this)">`;
        }
    }
];

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async function () {
    // 미저장 변경사항 이탈 방지
    window.addEventListener('beforeunload', (e) => {
        if (dirtyRows.size > 0) {
            e.preventDefault();
        }
    });

    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 마스터 테이블 매니저
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'PromotionID',
        onRowClick: (row, tr) => {
            selectPromotion(row.PromotionID, tr);
        },
        onSelectionChange: (selectedIds) => {
            updateMasterActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            sortAndRenderMaster(sortKey, sortDir);
        },
        emptyMessage: '비정기 데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    // 디테일 테이블 매니저
    detailTableManager = new TableManager('detail-table', {
        selectable: true,
        idKey: 'PromotionProductID',
        onSelectionChange: (selectedIds) => {
            updateDetailActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            if (dirtyRows.size > 0) {
                showConfirm('저장하지 않은 변경사항이 있습니다. 정렬하시겠습니까?', () => {
                    dirtyRows.clear();
                    updateSaveBar();
                    sortAndRenderDetail(sortKey, sortDir);
                });
                return;
            }
            sortAndRenderDetail(sortKey, sortDir);
        },
        emptyMessage: '비정기 상품이 없습니다.'
    });
    detailTableManager.renderHeader(detailColumns);

    // 패널 리사이즈 초기화
    initPanelResize('promoMasterDetail', 'panelResizeHandle');

    // 공통 데이터 로드
    loadBrands();
    loadChannels();
    loadPromotionTypes();
    loadStatuses();
    await loadYearMonths();

    // 마스터 로드
    loadMasterData();
});

// ==================== 패널 리사이즈 ====================
function initPanelResize(containerId, handleId) {
    const container = document.getElementById(containerId);
    const handle = document.getElementById(handleId);
    if (!container || !handle) return;

    let isResizing = false;
    let startX, startMasterWidth;

    handle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isResizing = true;
        startX = e.clientX;
        startMasterWidth = container.querySelector('.master-panel').offsetWidth;
        handle.classList.add('active');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const containerWidth = container.offsetWidth;
        const delta = e.clientX - startX;
        const newMasterWidth = Math.max(200, Math.min(containerWidth - 350, startMasterWidth + delta));
        container.style.gridTemplateColumns = `${newMasterWidth}px 0px 1fr`;
    });

    document.addEventListener('mouseup', () => {
        if (!isResizing) return;
        isResizing = false;
        handle.classList.remove('active');
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
    });
}

// ==================== 마스터 패널 ====================
async function loadMasterData() {
    try {
        masterTableManager.showLoading(masterColumns.length);

        const params = { ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/promotions/master-summary${queryString}`);
        const data = result.data || [];

        currentMasterData = data;
        masterDataMap = {};
        data.forEach(row => masterDataMap[row.PromotionID] = row);

        document.getElementById('masterCount').textContent = `(${data.length}개)`;

        masterTableManager.render(data, masterColumns);
        applyMasterSelection();

        if (currentPromotionId && !masterDataMap[currentPromotionId]) {
            resetDetail();
        }

    } catch (e) {
        console.error('비정기 목록 로드 실패:', e);
        showAlert('비정기 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderMaster(sortKey, sortDir) {
    sortArray(currentMasterData, sortKey, sortDir);
    masterTableManager.render(currentMasterData, masterColumns);
    applyMasterSelection();
}

function applyMasterSelection() {
    if (!currentPromotionId) return;
    document.querySelectorAll('#master-table tbody tr').forEach(tr => {
        if (tr.dataset.id === currentPromotionId) {
            tr.classList.add('selected');
        }
    });
}

// ==================== 비정기 선택 (마스터 행 클릭) ====================
function selectPromotion(promotionId, tr) {
    if (dirtyRows.size > 0 && promotionId !== currentPromotionId) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 비정기를 전환하시겠습니까?', () => {
            dirtyRows.clear();
            updateSaveBar();
            doSelectPromotion(promotionId, tr);
        });
        return;
    }
    doSelectPromotion(promotionId, tr);
}

function doSelectPromotion(promotionId, tr) {
    document.querySelectorAll('#master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentPromotionId = promotionId;
    currentPromotionData = masterDataMap[promotionId];

    loadDetailData(currentPromotionData);
}

// ==================== 디테일 패널 ====================
async function loadDetailData(promo) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailContainer').style.display = 'flex';

        detailTableManager.showLoading(detailColumns.length);

        const result = await api.get(`/api/promotions/products?promotion_id=${promo.PromotionID}&page=1&limit=10000`);
        const items = result.data || [];

        currentDetailItems = items;
        document.getElementById('detailItemCount').textContent = `(${items.length}개)`;

        renderPromoSummary(promo);

        // 원본 데이터 저장
        originalData = {};
        items.forEach(item => {
            originalData[item.PromotionProductID] = {
                PromotionPrice: item.PromotionPrice || 0,
                ExpectedSalesAmount: item.ExpectedSalesAmount || 0,
                ExpectedQuantity: item.ExpectedQuantity || 0,
                Notes: item.Notes || ''
            };
        });

        dirtyRows.clear();
        updateSaveBar();
        detailTableManager.clearSelection();
        updateDetailActionButtons([]);

        detailTableManager.render(items, detailColumns);

    } catch (e) {
        console.error('비정기 상품 로드 실패:', e);
        showAlert('비정기 상품 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderDetail(sortKey, sortDir) {
    sortArray(currentDetailItems, sortKey, sortDir);
    detailTableManager.clearSelection();
    updateDetailActionButtons([]);
    detailTableManager.render(currentDetailItems, detailColumns);
}

function renderPromoSummary(promo) {
    const statusLabels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
    const statusLabel = statusLabels[promo.Status] || promo.Status;
    const dateRange = (promo.StartDate && promo.EndDate) ? `${promo.StartDate} ~ ${promo.EndDate}` : '-';

    document.getElementById('promoSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            ${escapeHtml(promo.PromotionName)} 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">채널</span>
                <span class="summary-value">${escapeHtml(promo.ChannelName)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">유형</span>
                <span class="summary-value">${escapeHtml(promo.PromotionType)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">상태</span>
                <span class="summary-value"><span class="status-badge status-${promo.Status}">${statusLabel}</span></span>
            </div>
            <div class="summary-item">
                <span class="summary-label">기간</span>
                <span class="summary-value">${dateRange}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">상품수</span>
                <span class="summary-value">${promo.ProductCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상매출 합계</span>
                <span class="summary-value">${promo.TotalSalesAmount.toLocaleString()}원</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상수량 합계</span>
                <span class="summary-value">${promo.TotalQuantity.toLocaleString()}개</span>
            </div>
        </div>
    `;
}

function resetDetail() {
    currentPromotionId = null;
    currentPromotionData = null;
    originalData = {};
    dirtyRows.clear();
    currentDetailItems = [];

    document.getElementById('detailPlaceholder').style.display = 'flex';
    document.getElementById('detailContainer').style.display = 'none';
    document.getElementById('promoSummary').innerHTML = '';
    detailTableManager.clearSelection();
    updateDetailActionButtons([]);
    updateSaveBar();
}

// ==================== 인라인 편집 ====================
function onInlineFocus(input) {
    const raw = input.value.replace(/,/g, '');
    input.value = raw;
    input.select();
}

function onAmountBlur(input) {
    let val = parseFloat(input.value.replace(/,/g, '')) || 0;
    input.value = val.toLocaleString();
    checkDirty(input);
}

function onQuantityBlur(input) {
    let val = parseInt(input.value.replace(/,/g, '')) || 0;
    input.value = val.toLocaleString();
    checkDirty(input);
}

function onNotesInput(input) {
    checkDirty(input);
}

function checkDirty(input) {
    const id = parseInt(input.dataset.id);
    const field = input.dataset.field;

    const orig = originalData[id];
    if (!orig) return;

    let currentVal;
    if (field === 'PromotionPrice' || field === 'ExpectedSalesAmount') {
        currentVal = parseFloat(input.value.replace(/,/g, '')) || 0;
    } else if (field === 'ExpectedQuantity') {
        currentVal = parseInt(input.value.replace(/,/g, '')) || 0;
    } else {
        currentVal = input.value;
    }

    const isDirty = currentVal !== orig[field];
    input.classList.toggle('dirty', isDirty);

    // 행 단위 dirty 추적
    const row = input.closest('tr');
    const rowInputs = row.querySelectorAll('.inline-input');
    let rowHasDirty = false;

    rowInputs.forEach(inp => {
        if (inp.classList.contains('dirty')) rowHasDirty = true;
    });

    if (rowHasDirty) {
        const rowData = {};
        rowInputs.forEach(inp => {
            const f = inp.dataset.field;
            if (f === 'PromotionPrice' || f === 'ExpectedSalesAmount') {
                rowData[f] = parseFloat(inp.value.replace(/,/g, '')) || 0;
            } else if (f === 'ExpectedQuantity') {
                rowData[f] = parseInt(inp.value.replace(/,/g, '')) || 0;
            } else {
                rowData[f] = inp.value;
            }
        });
        dirtyRows.set(id, rowData);
    } else {
        dirtyRows.delete(id);
    }

    updateSaveBar();
}

// ==================== 저장 ====================
async function saveChanges() {
    if (dirtyRows.size === 0) return;

    const items = [];
    dirtyRows.forEach((data, id) => {
        items.push({
            PromotionProductID: id,
            PromotionPrice: data.PromotionPrice,
            ExpectedSalesAmount: data.ExpectedSalesAmount,
            ExpectedQuantity: data.ExpectedQuantity,
            Notes: data.Notes
        });
    });

    try {
        const result = await api.put('/api/promotions/products/bulk-update', { items });
        showAlert(`${result.updated}건이 저장되었습니다.`, 'success');

        // 원본 데이터 업데이트
        items.forEach(item => {
            originalData[item.PromotionProductID] = {
                PromotionPrice: item.PromotionPrice,
                ExpectedSalesAmount: item.ExpectedSalesAmount,
                ExpectedQuantity: item.ExpectedQuantity,
                Notes: item.Notes
            };
            const detailItem = currentDetailItems.find(d => d.PromotionProductID === item.PromotionProductID);
            if (detailItem) {
                detailItem.PromotionPrice = item.PromotionPrice;
                detailItem.ExpectedSalesAmount = item.ExpectedSalesAmount;
                detailItem.ExpectedQuantity = item.ExpectedQuantity;
                detailItem.Notes = item.Notes;
            }
        });

        dirtyRows.clear();
        updateSaveBar();
        document.querySelectorAll('#detail-table .inline-input.dirty').forEach(inp => {
            inp.classList.remove('dirty');
        });

        // 마스터 새로고침 (합계 업데이트)
        loadMasterData();

    } catch (e) {
        console.error('저장 실패:', e);
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function updateSaveBar() {
    const saveBar = document.getElementById('saveBar');
    const countEl = document.getElementById('dirtyCount');
    if (!saveBar) return;

    if (dirtyRows.size > 0) {
        saveBar.style.display = 'flex';
        countEl.textContent = `${dirtyRows.size}건 변경됨`;
    } else {
        saveBar.style.display = 'none';
    }
}

// ==================== 마스터 액션 버튼 ====================
function updateMasterActionButtons(selectedIds) {
    const editDownloadBtn = document.getElementById('editDownloadButton');
    if (!editDownloadBtn) return;

    if (selectedIds.length > 0) {
        editDownloadBtn.classList.remove('btn-disabled');
        editDownloadBtn.disabled = false;
    } else {
        editDownloadBtn.classList.add('btn-disabled');
        editDownloadBtn.disabled = true;
    }
}

// ==================== 디테일 액션 버튼 ====================
function updateDetailActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('detailDeleteButton');
    const editDownloadBtn = document.getElementById('detailEditDownloadButton');

    if (selectedIds.length > 0) {
        deleteBtn.classList.remove('btn-disabled');
        deleteBtn.disabled = false;
        editDownloadBtn.classList.remove('btn-disabled');
        editDownloadBtn.disabled = false;
    } else {
        deleteBtn.classList.add('btn-disabled');
        deleteBtn.disabled = true;
        editDownloadBtn.classList.add('btn-disabled');
        editDownloadBtn.disabled = true;
    }
}

// ==================== 선택 삭제 ====================
async function bulkDeleteDetail() {
    const selectedIds = detailTableManager.getSelectedRows().map(Number);

    if (selectedIds.length === 0) {
        showAlert('삭제할 상품을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 상품을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/promotions/products/bulk-delete', { ids: selectedIds });

            showAlert(`${result.deleted_count}개 상품이 삭제되었습니다.`, 'success');

            dirtyRows.clear();
            updateSaveBar();
            loadMasterData();

            if (currentPromotionData) {
                loadDetailData(currentPromotionData);
            }

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 필터 ====================
function applyFilters() {
    if (dirtyRows.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 필터를 적용하시겠습니까?', () => {
            dirtyRows.clear();
            updateSaveBar();
            doApplyFilters();
        });
        return;
    }
    doApplyFilters();
}

function doApplyFilters() {
    currentFilters = {};

    const yearMonth = document.getElementById('searchYearMonth').value;
    const brandId = document.getElementById('searchBrand').value;
    const channelId = document.getElementById('searchChannel').value;
    const promotionType = document.getElementById('searchPromotionType').value;
    const status = document.getElementById('searchStatus').value;

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (brandId) currentFilters.brand_id = brandId;
    if (channelId) currentFilters.channel_id = channelId;
    if (promotionType) currentFilters.promotion_type = promotionType;
    if (status) currentFilters.status = status;

    resetDetail();
    loadMasterData();
}

function resetFilters() {
    document.getElementById('searchYearMonth').value = '';
    document.getElementById('searchBrand').value = '';
    document.getElementById('searchChannel').value = '';
    document.getElementById('searchPromotionType').value = '';
    document.getElementById('searchStatus').value = '';

    currentFilters = {};
    resetDetail();
    loadMasterData();
}

// ==================== 공통 데이터 로드 ====================
async function loadBrands() {
    try {
        const result = await api.get('/api/brands/all');
        const brands = result.data || [];

        const select = document.getElementById('searchBrand');
        select.innerHTML = '<option value="">전체</option>';

        brands.forEach(brand => {
            const option = document.createElement('option');
            option.value = brand.BrandID;
            option.textContent = brand.Name;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

async function loadChannels() {
    try {
        const channels = await api.get('/api/channels/list');

        const select = document.getElementById('searchChannel');
        select.innerHTML = '<option value="">전체</option>';

        channels.forEach(channel => {
            const option = document.createElement('option');
            option.value = channel.ChannelID;
            option.textContent = channel.Name;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

async function loadYearMonths() {
    try {
        const result = await api.get('/api/promotions/year-months');
        const yearMonths = result.year_months || [];

        if (yearMonths.length > 0) {
            document.getElementById('searchYearMonth').value = yearMonths[0];
            currentFilters.year_month = yearMonths[0];
        }
    } catch (e) {
        console.error('년월 목록 로드 실패:', e);
    }
}

async function loadPromotionTypes() {
    try {
        const result = await api.get('/api/promotions/promotion-types');
        const types = result.promotion_types || [];

        const select = document.getElementById('searchPromotionType');
        select.innerHTML = '<option value="">전체</option>';

        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('비정기유형 로드 실패:', e);
    }
}

async function loadStatuses() {
    try {
        const result = await api.get('/api/promotions/statuses');
        const statuses = result.statuses || [];
        const labels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };

        const select = document.getElementById('searchStatus');
        select.innerHTML = '<option value="">전체</option>';

        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = labels[status] || status;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('상태 로드 실패:', e);
    }
}

// ==================== 엑셀 다운로드 ====================
function downloadTemplate() {
    window.location.href = '/api/promotions/download';
}

function downloadEditForm() {
    const selectedIds = masterTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 비정기를 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/promotions/download${queryString}`;
}

function downloadDetailEditForm() {
    const selectedIds = detailTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 상품을 선택해주세요.', 'warning');
        return;
    }

    // 선택된 상품이 속한 비정기 ID로 다운로드
    const params = { ids: currentPromotionId };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/promotions/download${queryString}`;
}

// ==================== 업로드 ====================
function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('uploadButton').disabled = true;

    uploadModal.show();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileInfo').style.display = 'block';
        document.getElementById('uploadButton').disabled = false;
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        showAlert('파일을 선택해주세요.', 'warning');
        return;
    }

    try {
        document.getElementById('uploadProgress').style.display = 'block';
        document.getElementById('uploadButton').disabled = true;

        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                document.getElementById('progressBar').style.width = progress + '%';
                document.getElementById('progressText').textContent = progress + '%';
            }
        }, 100);

        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/promotions/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        uploadModal.hide();

        if (!response.ok) {
            const error = await response.json();
            document.getElementById('uploadSuccessSection').style.display = 'none';
            document.getElementById('uploadErrorSection').style.display = 'block';
            document.getElementById('uploadResultTitle').textContent = '업로드 실패';
            document.getElementById('uploadErrorMessage').textContent = error.detail || '업로드 중 오류가 발생했습니다.';
            uploadResultModal.show();
            return;
        }

        const result = await response.json();

        document.getElementById('uploadSuccessSection').style.display = 'block';
        document.getElementById('uploadErrorSection').style.display = 'none';
        document.getElementById('uploadResultTitle').textContent = '업로드 결과';
        document.getElementById('uploadTotalRows').textContent = result.total_rows?.toLocaleString() || 0;
        document.getElementById('promoInserted').textContent = result.promotion_inserted?.toLocaleString() || 0;
        document.getElementById('promoUpdated').textContent = result.promotion_updated?.toLocaleString() || 0;
        document.getElementById('prodInserted').textContent = result.product_inserted?.toLocaleString() || 0;
        document.getElementById('prodUpdated').textContent = result.product_updated?.toLocaleString() || 0;

        uploadResultModal.show();

        // 데이터 새로고침
        resetDetail();
        loadMasterData();

    } catch (e) {
        console.error('업로드 실패:', e);

        uploadModal.hide();

        document.getElementById('uploadSuccessSection').style.display = 'none';
        document.getElementById('uploadErrorSection').style.display = 'block';
        document.getElementById('uploadResultTitle').textContent = '업로드 실패';
        document.getElementById('uploadErrorMessage').textContent = e.message || '업로드 중 오류가 발생했습니다.';
        uploadResultModal.show();
    }
}

