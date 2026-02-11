/**
 * 목표 관리 페이지 JavaScript
 * - 정기 목표: 마스터-디테일 (채널별 인라인 편집)
 * - 비정기 목표: 플랫 테이블
 */

// ==================== 공통 상태 ====================
let currentTab = 'base';
let uploadModal, uploadResultModal;
let currentFilters = {};

// ==================== 비정기 목표 상태 ====================
let promotionTableManager;
let paginationManager;
let currentPage = 1;
let currentLimit = 20;
let currentSortBy = null;
let currentSortDir = null;

// ==================== 정기 목표 마스터-디테일 상태 ====================
let baseMasterTableManager;          // TableManager for master table
let baseDetailTableManager;          // TableManager for detail table
let channelDataMap = {};             // {ChannelID: channelObj}
let currentChannels = [];            // 마스터 데이터 (정렬용)
let currentChannelId = null;
let currentChannelData = null;
let baseOriginalData = {};           // {TargetBaseID: {TargetAmount, TargetQuantity, Notes}}
let baseDirtyRows = new Map();       // Map<TargetBaseID, {TargetAmount, TargetQuantity, Notes}>
let currentDetailItems = [];         // 디테일 데이터 (정렬용)

// ==================== 정기 목표 마스터 컬럼 정의 ====================
const baseMasterColumns = [
    {
        key: 'ChannelName',
        header: '채널',
        sortKey: 'ChannelName',
        render: (row) => `<div class="group-info"><span class="group-title">${escapeHtml(row.ChannelName)}</span></div>`
    },
    {
        key: 'TotalAmount',
        header: '목표금액(VAT포함)',
        sortKey: 'TotalAmount',
        render: (row) => `<div style="text-align:right;font-size:13px;">${row.TotalAmount.toLocaleString()}</div>`
    },
    {
        key: 'ProductCount',
        header: '품목수',
        sortKey: 'ProductCount',
        render: (row) => `<div style="text-align:right;font-size:13px;">${row.ProductCount}</div>`
    }
];

// ==================== 정기 목표 디테일 컬럼 정의 ====================
const baseDetailColumns = [
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
        key: 'TargetAmount',
        header: '목표금액(VAT포함)',
        sortKey: 'TargetAmount',
        render: (row) => {
            const dirty = baseDirtyRows.get(row.TargetBaseID);
            const val = dirty && dirty.TargetAmount !== undefined ? dirty.TargetAmount : (row.TargetAmount || 0);
            const original = baseOriginalData[row.TargetBaseID];
            const isDirty = original && val !== original.TargetAmount;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetBaseID}" data-field="TargetAmount"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onAmountBlur(this)">`;
        }
    },
    {
        key: 'TargetQuantity',
        header: '목표수량',
        sortKey: 'TargetQuantity',
        render: (row) => {
            const dirty = baseDirtyRows.get(row.TargetBaseID);
            const val = dirty && dirty.TargetQuantity !== undefined ? dirty.TargetQuantity : (row.TargetQuantity || 0);
            const original = baseOriginalData[row.TargetBaseID];
            const isDirty = original && val !== original.TargetQuantity;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetBaseID}" data-field="TargetQuantity"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onQuantityBlur(this)">`;
        }
    },
    {
        key: 'Notes',
        header: '비고',
        render: (row) => {
            const dirty = baseDirtyRows.get(row.TargetBaseID);
            const val = dirty && dirty.Notes !== undefined ? dirty.Notes : (row.Notes || '');
            const original = baseOriginalData[row.TargetBaseID];
            const isDirty = original && val !== (original.Notes || '');
            return `<input type="text" class="inline-input${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetBaseID}" data-field="Notes"
                value="${escapeHtml(val)}"
                oninput="onNotesInput(this)">`;
        }
    }
];

// ==================== 비정기 목표 컬럼 정의 ====================
const promotionColumns = [
    { key: 'PromotionName', header: '행사명', sortKey: 'PromotionName', render: (row) => row.PromotionName || '-' },
    { key: 'PromotionType', header: '행사유형', sortKey: 'PromotionType', render: (row) => row.PromotionType || '-' },
    {
        key: 'StartDate',
        header: '시작일',
        sortKey: 'StartDate',
        render: (row) => {
            const date = row.StartDate || '';
            const time = row.StartTime || '00:00:00';
            return date ? `${date} ${time}` : '-';
        }
    },
    {
        key: 'EndDate',
        header: '종료일',
        sortKey: 'EndDate',
        render: (row) => {
            const date = row.EndDate || '';
            const time = row.EndTime || '23:59:59';
            return date ? `${date} ${time}` : '-';
        }
    },
    { key: 'BrandName', header: '브랜드', sortKey: 'BrandName', render: (row) => row.BrandName || '-' },
    { key: 'ChannelName', header: '채널명', sortKey: 'ChannelName', render: (row) => row.ChannelName || '-' },
    { key: 'ProductName', header: '상품명', sortKey: 'ProductName', render: (row) => row.ProductName || '-' },
    {
        key: 'TargetAmount',
        header: '목표금액',
        sortKey: 'TargetAmount',
        align: 'right',
        render: (row) => `<div style="text-align:right;">${(row.TargetAmount || 0).toLocaleString()}</div>`
    },
    {
        key: 'TargetQuantity',
        header: '목표수량',
        sortKey: 'TargetQuantity',
        align: 'right',
        render: (row) => `<div style="text-align:right;">${(row.TargetQuantity || 0).toLocaleString()}</div>`
    }
];

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async function () {
    // 모달 초기화
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 정기 목표 마스터 테이블 매니저 (리사이즈 + 정렬 + 체크박스)
    baseMasterTableManager = new TableManager('base-master-table', {
        selectable: true,
        idKey: 'ChannelID',
        onRowClick: (row, tr) => {
            selectChannel(row.ChannelID, tr);
        },
        onSelectionChange: (selectedIds) => {
            updateMasterActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            sortAndRenderMaster(sortKey, sortDir);
        },
        emptyMessage: '데이터가 없습니다.'
    });
    baseMasterTableManager.renderHeader(baseMasterColumns);

    // 정기 목표 디테일 테이블 매니저 (리사이즈 + 정렬 + 체크박스)
    baseDetailTableManager = new TableManager('base-detail-table', {
        selectable: true,
        idKey: 'TargetBaseID',
        onSelectionChange: (selectedIds) => {
            updateDetailActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            if (baseDirtyRows.size > 0) {
                showConfirm('저장하지 않은 변경사항이 있습니다. 정렬하시겠습니까?', () => {
                    baseDirtyRows.clear();
                    updateSaveBar();
                    sortAndRenderDetail(sortKey, sortDir);
                });
                return;
            }
            sortAndRenderDetail(sortKey, sortDir);
        },
        emptyMessage: '상품이 없습니다.'
    });
    baseDetailTableManager.renderHeader(baseDetailColumns);

    // 비정기 목표 테이블 매니저
    promotionTableManager = new TableManager('promotion-table', {
        selectable: true,
        idKey: 'TargetPromotionID',
        onSelectionChange: (selectedIds) => {
            updatePromoActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadData(1, currentLimit);
        },
        emptyMessage: '목표 데이터가 없습니다.'
    });
    promotionTableManager.renderHeader(promotionColumns);

    // 페이지네이션 초기화
    paginationManager = new PaginationManager('promoPagination', {
        onPageChange: (page, limit) => loadData(page, limit),
        onLimitChange: (page, limit) => loadData(page, limit)
    });

    // 패널 리사이즈 초기화
    initPanelResize();

    // 공통 데이터 로드
    loadBrands();
    loadChannels();
    await loadYearMonths();

    // 정기 목표 마스터 로드
    loadChannelMaster();
});

// ==================== 패널 리사이즈 ====================
function initPanelResize() {
    const container = document.getElementById('baseMasterDetail');
    const handle = document.getElementById('panelResizeHandle');
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

// ==================== 탭 전환 ====================
function switchTab(tab) {
    if (tab === currentTab) return;

    if (currentTab === 'base' && baseDirtyRows.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 탭을 전환하시겠습니까?', () => {
            baseDirtyRows.clear();
            updateSaveBar();
            doSwitchTab(tab);
        });
        return;
    }
    doSwitchTab(tab);
}

function doSwitchTab(tab) {
    currentTab = tab;

    // 탭 버튼 스타일
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    // 컨테이너 토글
    document.getElementById('baseMasterDetail').style.display = tab === 'base' ? 'grid' : 'none';
    document.getElementById('promotionFlatTable').style.display = tab === 'promotion' ? '' : 'none';

    // 필터 표시/숨김
    document.getElementById('channelFilterWrap').style.display = tab === 'promotion' ? '' : 'none';
    document.getElementById('promotionFilterWrap').style.display = tab === 'promotion' ? '' : 'none';

    // 업로드 모달 제목
    document.getElementById('uploadModalTitle').textContent =
        tab === 'base' ? '정기 목표 데이터 업로드' : '비정기 목표 데이터 업로드';

    if (tab === 'promotion') {
        loadPromotionTypes();
        currentSortBy = null;
        currentSortDir = null;
        promotionTableManager.clearSelection();
        updatePromoActionButtons([]);
        loadData(1, currentLimit);
    }
}

// ==================== 정기 목표: 마스터 패널 ====================
async function loadChannelMaster() {
    const yearMonth = document.getElementById('searchYearMonth').value;
    if (!yearMonth) {
        currentChannels = [];
        baseMasterTableManager.render([], baseMasterColumns);
        document.getElementById('channelCount').textContent = '';
        resetBaseDetail();
        return;
    }

    try {
        const brandId = document.getElementById('searchBrand').value;
        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/base/channels${queryString}`);
        const channels = result.data || [];

        // 데이터 저장
        currentChannels = channels;
        channelDataMap = {};
        channels.forEach(ch => channelDataMap[ch.ChannelID] = ch);

        document.getElementById('channelCount').textContent = `(${channels.length}개)`;

        // TableManager로 렌더링 (리사이즈 + 정렬 자동 포함)
        baseMasterTableManager.render(channels, baseMasterColumns);

        // 선택된 채널 표시 복원
        applyMasterSelection();

        // 이전에 선택된 채널이 목록에 없으면 리셋
        if (currentChannelId && !channelDataMap[currentChannelId]) {
            resetBaseDetail();
        }

    } catch (e) {
        console.error('채널 목록 로드 실패:', e);
        showAlert('채널 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderMaster(sortKey, sortDir) {
    currentChannels.sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];

        if (valA == null) valA = '';
        if (valB == null) valB = '';

        if (typeof valA === 'number' && typeof valB === 'number') {
            return sortDir === 'ASC' ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortDir === 'ASC' ? -1 : 1;
        if (strA > strB) return sortDir === 'ASC' ? 1 : -1;
        return 0;
    });

    baseMasterTableManager.render(currentChannels, baseMasterColumns);
    applyMasterSelection();
}

function applyMasterSelection() {
    if (!currentChannelId) return;
    document.querySelectorAll('#base-master-table tbody tr').forEach(tr => {
        if (tr.dataset.id == currentChannelId) {
            tr.classList.add('selected');
        }
    });
}

// ==================== 정기 목표: 채널 선택 ====================
function selectChannel(channelId, tr) {
    if (baseDirtyRows.size > 0 && channelId !== currentChannelId) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 채널을 전환하시겠습니까?', () => {
            baseDirtyRows.clear();
            updateSaveBar();
            doSelectChannel(channelId, tr);
        });
        return;
    }
    doSelectChannel(channelId, tr);
}

function doSelectChannel(channelId, tr) {
    // 마스터 행 선택 표시
    document.querySelectorAll('#base-master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentChannelId = channelId;
    currentChannelData = channelDataMap[channelId];

    loadChannelDetail(currentChannelData);
}

// ==================== 정기 목표: 디테일 패널 ====================
async function loadChannelDetail(channel) {
    const yearMonth = document.getElementById('searchYearMonth').value;
    const brandId = document.getElementById('searchBrand').value;

    try {
        // placeholder 숨기고 컨테이너 표시
        document.getElementById('baseDetailPlaceholder').style.display = 'none';
        document.getElementById('baseDetailContainer').style.display = 'flex';

        // 로딩 표시
        baseDetailTableManager.showLoading(baseDetailColumns.length);

        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/base/channel/${channel.ChannelID}/items${queryString}`);
        const items = result.data || [];

        // 아이템 저장 (정렬용)
        currentDetailItems = items;

        // 아이템 수
        document.getElementById('baseItemCount').textContent = `(${items.length}개)`;

        // 요약 렌더링
        renderChannelSummary(channel);

        // 원본 데이터 저장 (dirty 체크용)
        baseOriginalData = {};
        items.forEach(item => {
            baseOriginalData[item.TargetBaseID] = {
                TargetAmount: item.TargetAmount || 0,
                TargetQuantity: item.TargetQuantity || 0,
                Notes: item.Notes || ''
            };
        });

        // dirty 및 선택 초기화
        baseDirtyRows.clear();
        updateSaveBar();
        baseDetailTableManager.clearSelection();
        updateDetailActionButtons([]);

        // TableManager로 렌더링
        baseDetailTableManager.render(items, baseDetailColumns);

    } catch (e) {
        console.error('채널 상세 로드 실패:', e);
        showAlert('채널 상세 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderDetail(sortKey, sortDir) {
    currentDetailItems.sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];

        if (valA == null) valA = '';
        if (valB == null) valB = '';

        if (typeof valA === 'number' && typeof valB === 'number') {
            return sortDir === 'ASC' ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortDir === 'ASC' ? -1 : 1;
        if (strA > strB) return sortDir === 'ASC' ? 1 : -1;
        return 0;
    });

    baseDetailTableManager.clearSelection();
    updateDetailActionButtons([]);
    baseDetailTableManager.render(currentDetailItems, baseDetailColumns);
}

function renderChannelSummary(channel) {
    document.getElementById('baseChannelSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            ${escapeHtml(channel.ChannelName)} 목표 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">품목수</span>
                <span class="summary-value">${channel.ProductCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">목표금액 합계(VAT포함)</span>
                <span class="summary-value">${channel.TotalAmount.toLocaleString()}원</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">목표수량 합계</span>
                <span class="summary-value">${channel.TotalQuantity.toLocaleString()}개</span>
            </div>
        </div>
    `;
}

function resetBaseDetail() {
    currentChannelId = null;
    currentChannelData = null;
    baseOriginalData = {};
    baseDirtyRows.clear();
    currentDetailItems = [];

    document.getElementById('baseDetailPlaceholder').style.display = 'flex';
    document.getElementById('baseDetailContainer').style.display = 'none';
    document.getElementById('baseChannelSummary').innerHTML = '';
    baseDetailTableManager.clearSelection();
    updateDetailActionButtons([]);
    updateSaveBar();
}

// ==================== 정기 목표: 마스터 액션 버튼 ====================
function updateMasterActionButtons(selectedIds) {
    const editDownloadBtn = document.getElementById('masterEditDownloadButton');
    if (!editDownloadBtn) return;

    if (selectedIds.length > 0) {
        editDownloadBtn.classList.remove('btn-disabled');
        editDownloadBtn.disabled = false;
    } else {
        editDownloadBtn.classList.add('btn-disabled');
        editDownloadBtn.disabled = true;
    }
}

function downloadMasterEditForm() {
    const selectedIds = baseMasterTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 채널을 선택해주세요.', 'warning');
        return;
    }

    const yearMonth = document.getElementById('searchYearMonth').value;
    if (!yearMonth) {
        showAlert('년월을 선택해주세요.', 'warning');
        return;
    }

    const params = { year_month: yearMonth, channel_ids: selectedIds.join(',') };
    const brandId = document.getElementById('searchBrand').value;
    if (brandId) params.brand_id = brandId;

    const queryString = api.buildQueryString(params);
    window.location.href = `/api/targets/base/download${queryString}`;
}

// ==================== 정기 목표: 디테일 액션 버튼 ====================
function updateDetailActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('baseDeleteButton');
    const editDownloadBtn = document.getElementById('baseEditDownloadButton');

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

// ==================== 정기 목표: 선택 삭제 ====================
async function bulkDeleteBaseItems() {
    const selectedIds = baseDetailTableManager.getSelectedRows().map(Number);

    if (selectedIds.length === 0) {
        showAlert('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/targets/base/bulk-delete', { ids: selectedIds });

            showAlert(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');

            // 디테일 + 마스터 새로고침
            baseDirtyRows.clear();
            updateSaveBar();
            loadChannelMaster();

            if (currentChannelData) {
                loadChannelDetail(currentChannelData);
            }

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
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
    const original = baseOriginalData[id];
    if (!original) return;

    let currentVal;
    if (field === 'TargetAmount') {
        currentVal = parseFloat(input.value.replace(/,/g, '')) || 0;
    } else if (field === 'TargetQuantity') {
        currentVal = parseInt(input.value.replace(/,/g, '')) || 0;
    } else {
        currentVal = input.value;
    }

    const isDirty = currentVal !== original[field];
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
            if (f === 'TargetAmount') {
                rowData[f] = parseFloat(inp.value.replace(/,/g, '')) || 0;
            } else if (f === 'TargetQuantity') {
                rowData[f] = parseInt(inp.value.replace(/,/g, '')) || 0;
            } else {
                rowData[f] = inp.value;
            }
        });
        baseDirtyRows.set(id, rowData);
    } else {
        baseDirtyRows.delete(id);
    }

    updateSaveBar();
}

function updateSaveBar() {
    const saveBar = document.getElementById('baseSaveBar');
    const countEl = document.getElementById('baseDirtyCount');

    if (!saveBar) return;

    if (baseDirtyRows.size > 0) {
        saveBar.style.display = 'flex';
        countEl.textContent = `${baseDirtyRows.size}건 변경됨`;
    } else {
        saveBar.style.display = 'none';
    }
}

// ==================== 저장 ====================
async function saveChanges() {
    if (baseDirtyRows.size === 0) return;

    const items = [];
    baseDirtyRows.forEach((data, id) => {
        items.push({
            TargetBaseID: id,
            TargetAmount: data.TargetAmount,
            TargetQuantity: data.TargetQuantity,
            Notes: data.Notes
        });
    });

    try {
        const result = await api.put('/api/targets/base/bulk-update', { items });
        showAlert(`${result.updated}건이 저장되었습니다.`, 'success');

        // 원본 데이터 업데이트
        items.forEach(item => {
            baseOriginalData[item.TargetBaseID] = {
                TargetAmount: item.TargetAmount,
                TargetQuantity: item.TargetQuantity,
                Notes: item.Notes
            };
            // currentDetailItems도 동기화
            const detailItem = currentDetailItems.find(d => d.TargetBaseID === item.TargetBaseID);
            if (detailItem) {
                detailItem.TargetAmount = item.TargetAmount;
                detailItem.TargetQuantity = item.TargetQuantity;
                detailItem.Notes = item.Notes;
            }
        });

        // dirty 초기화
        baseDirtyRows.clear();
        updateSaveBar();
        document.querySelectorAll('#base-detail-table .inline-input.dirty').forEach(inp => {
            inp.classList.remove('dirty');
        });

        // 마스터 패널 새로고침 (금액 합계 업데이트)
        loadChannelMaster();

    } catch (e) {
        console.error('저장 실패:', e);
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

// ==================== 공통: 브랜드/채널/년월 로드 ====================
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
        const result = await api.get('/api/targets/base/year-months');
        const yearMonths = result.year_months || [];

        if (yearMonths.length > 0) {
            document.getElementById('searchYearMonth').value = yearMonths[0];
        }
    } catch (e) {
        console.error('년월 목록 로드 실패:', e);
    }
}

async function loadPromotionTypes() {
    try {
        const result = await api.get('/api/targets/promotion/promotion-types');
        const promotionTypes = result.promotion_types || [];

        const select = document.getElementById('searchPromotionType');
        select.innerHTML = '<option value="">전체</option>';

        promotionTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('행사유형 로드 실패:', e);
    }
}

// ==================== 비정기 목표: 데이터 로드 ====================
async function loadData(page = 1, limit = 20) {
    currentPage = page;
    currentLimit = limit;

    try {
        promotionTableManager.showLoading(promotionColumns.length);

        const params = { page, limit, sort_by: currentSortBy, sort_dir: currentSortDir, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/promotion${queryString}`);

        promotionTableManager.render(result.data || [], promotionColumns);

        document.getElementById('promoResultCount').textContent = `(${result.total?.toLocaleString() || 0}건)`;

        paginationManager.render({
            page: result.page,
            limit: result.limit,
            total: result.total,
            total_pages: result.total_pages
        });

    } catch (e) {
        console.error('데이터 로드 실패:', e);
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

// ==================== 필터 ====================
function applyFilters() {
    if (currentTab === 'base' && baseDirtyRows.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 필터를 적용하시겠습니까?', () => {
            baseDirtyRows.clear();
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

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (brandId) currentFilters.brand_id = brandId;

    if (currentTab === 'base') {
        resetBaseDetail();
        loadChannelMaster();
    } else {
        const channelId = document.getElementById('searchChannel').value;
        if (channelId) currentFilters.channel_id = channelId;

        const promotionType = document.getElementById('searchPromotionType').value;
        if (promotionType) currentFilters.promotion_type = promotionType;

        loadData(1, currentLimit);
    }
}

function resetFilters() {
    document.getElementById('searchYearMonth').value = '';
    document.getElementById('searchBrand').value = '';
    document.getElementById('searchChannel').value = '';
    document.getElementById('searchPromotionType').value = '';

    currentFilters = {};

    if (currentTab === 'base') {
        resetBaseDetail();
        loadChannelMaster();
    } else {
        loadData(1, currentLimit);
    }
}

function changeLimit() {
    const limit = parseInt(document.getElementById('promoLimitSelector').value);
    loadData(1, limit);
}

// ==================== 비정기 목표: 액션 버튼 ====================
function updatePromoActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('promoDeleteButton');
    const editDownloadBtn = document.getElementById('promoEditDownloadButton');

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

async function selectAllData() {
    try {
        const params = { page: 1, limit: 100000, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/promotion${queryString}`);
        const data = result.data || [];

        const allIds = data.map(row => row.TargetPromotionID);

        promotionTableManager.selectedRows = new Set(allIds);

        document.querySelectorAll('#promotion-table tbody input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
        });

        const headerCb = document.querySelector('#promotion-table thead input[type="checkbox"]');
        if (headerCb) headerCb.checked = true;

        updatePromoActionButtons(allIds);
        showAlert(`${allIds.length}개 항목이 선택되었습니다.`, 'success');

    } catch (e) {
        console.error('전체 선택 실패:', e);
        showAlert('전체 선택 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    const selectedIds = promotionTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/targets/promotion/bulk-delete', { ids: selectedIds });

            showAlert(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');
            promotionTableManager.clearSelection();
            updatePromoActionButtons([]);
            loadData(currentPage, currentLimit);

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 엑셀 다운로드 ====================
function downloadTemplate() {
    const endpoint = currentTab === 'base'
        ? '/api/targets/base/download'
        : '/api/targets/promotion/download';

    window.location.href = endpoint;
}

function downloadEditForm() {
    const selectedIds = promotionTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 항목을 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/targets/promotion/download${queryString}`;
}

function downloadChannelEditForm() {
    const selectedIds = baseDetailTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 항목을 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/targets/base/download${queryString}`;
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

        const endpoint = currentTab === 'base'
            ? '/api/targets/base/upload'
            : '/api/targets/promotion/upload';

        const token = localStorage.getItem('access_token');
        const response = await fetch(endpoint, {
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
        document.getElementById('uploadInserted').textContent = result.inserted?.toLocaleString() || 0;
        document.getElementById('uploadUpdated').textContent = result.updated?.toLocaleString() || 0;

        uploadResultModal.show();

        // 데이터 새로고침
        if (currentTab === 'base') {
            loadChannelMaster();
            if (currentChannelId && currentChannelData) {
                loadChannelDetail(currentChannelData);
            }
        } else {
            loadData(1, currentLimit);
        }

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

// ==================== 유틸리티 ====================
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
