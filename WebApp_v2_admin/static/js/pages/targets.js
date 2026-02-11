/**
 * 목표 관리 페이지 JavaScript
 * - 정기 목표: 마스터-디테일 (채널별 인라인 편집)
 * - 비정기 목표: 마스터-디테일 (채널+행사 그룹별 인라인 편집)
 */

// ==================== 공통 상태 ====================
let currentTab = 'base';
let uploadModal, uploadResultModal;
let currentFilters = {};

// ==================== 정기 목표 마스터-디테일 상태 ====================
let baseMasterTableManager;
let baseDetailTableManager;
let channelDataMap = {};
let currentChannels = [];
let currentChannelId = null;
let currentChannelData = null;
let baseOriginalData = {};
let baseDirtyRows = new Map();
let currentDetailItems = [];

// ==================== 비정기 목표 마스터-디테일 상태 ====================
let promoMasterTableManager;
let promoDetailTableManager;
let promoGroupDataMap = {};          // {GroupKey: groupObj}
let currentPromoGroups = [];         // 마스터 데이터 (정렬용)
let currentPromoGroupKey = null;
let currentPromoGroupData = null;
let promoOriginalData = {};          // {TargetPromotionID: {TargetAmount, TargetQuantity, Notes}}
let promoDirtyRows = new Map();      // Map<TargetPromotionID, {TargetAmount, TargetQuantity, Notes}>
let currentPromoDetailItems = [];    // 디테일 데이터 (정렬용)

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
                data-id="${row.TargetBaseID}" data-field="TargetAmount" data-tab="base"
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
                data-id="${row.TargetBaseID}" data-field="TargetQuantity" data-tab="base"
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
                data-id="${row.TargetBaseID}" data-field="Notes" data-tab="base"
                value="${escapeHtml(val)}"
                oninput="onNotesInput(this)">`;
        }
    }
];

// ==================== 비정기 목표 마스터 컬럼 정의 ====================
const promoMasterColumns = [
    {
        key: 'ChannelName',
        header: '채널',
        sortKey: 'ChannelName',
        render: (row) => `<div class="group-info">
            <span class="group-title">${escapeHtml(row.PromotionName)}</span>
            <span class="group-meta">${escapeHtml(row.ChannelName)} · ${escapeHtml(row.PromotionType)}</span>
        </div>`
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

// ==================== 비정기 목표 디테일 컬럼 정의 ====================
const promoDetailColumns = [
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
            const dirty = promoDirtyRows.get(row.TargetPromotionID);
            const val = dirty && dirty.TargetAmount !== undefined ? dirty.TargetAmount : (row.TargetAmount || 0);
            const original = promoOriginalData[row.TargetPromotionID];
            const isDirty = original && val !== original.TargetAmount;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetPromotionID}" data-field="TargetAmount" data-tab="promotion"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onAmountBlur(this)">`;
        }
    },
    {
        key: 'TargetQuantity',
        header: '목표수량',
        sortKey: 'TargetQuantity',
        render: (row) => {
            const dirty = promoDirtyRows.get(row.TargetPromotionID);
            const val = dirty && dirty.TargetQuantity !== undefined ? dirty.TargetQuantity : (row.TargetQuantity || 0);
            const original = promoOriginalData[row.TargetPromotionID];
            const isDirty = original && val !== original.TargetQuantity;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetPromotionID}" data-field="TargetQuantity" data-tab="promotion"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onQuantityBlur(this)">`;
        }
    },
    {
        key: 'Notes',
        header: '비고',
        render: (row) => {
            const dirty = promoDirtyRows.get(row.TargetPromotionID);
            const val = dirty && dirty.Notes !== undefined ? dirty.Notes : (row.Notes || '');
            const original = promoOriginalData[row.TargetPromotionID];
            const isDirty = original && val !== (original.Notes || '');
            return `<input type="text" class="inline-input${isDirty ? ' dirty' : ''}"
                data-id="${row.TargetPromotionID}" data-field="Notes" data-tab="promotion"
                value="${escapeHtml(val)}"
                oninput="onNotesInput(this)">`;
        }
    }
];

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async function () {
    // 모달 초기화
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 정기 목표 마스터 테이블 매니저
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

    // 정기 목표 디테일 테이블 매니저
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
                    updateBaseSaveBar();
                    sortAndRenderDetail(sortKey, sortDir);
                });
                return;
            }
            sortAndRenderDetail(sortKey, sortDir);
        },
        emptyMessage: '상품이 없습니다.'
    });
    baseDetailTableManager.renderHeader(baseDetailColumns);

    // 비정기 목표 마스터 테이블 매니저
    promoMasterTableManager = new TableManager('promo-master-table', {
        selectable: true,
        idKey: 'GroupKey',
        onRowClick: (row, tr) => {
            selectPromoGroup(row.GroupKey, tr);
        },
        onSelectionChange: (selectedIds) => {
            updatePromoMasterActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            sortAndRenderPromoMaster(sortKey, sortDir);
        },
        emptyMessage: '데이터가 없습니다.'
    });
    promoMasterTableManager.renderHeader(promoMasterColumns);

    // 비정기 목표 디테일 테이블 매니저
    promoDetailTableManager = new TableManager('promo-detail-table', {
        selectable: true,
        idKey: 'TargetPromotionID',
        onSelectionChange: (selectedIds) => {
            updatePromoDetailActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            if (promoDirtyRows.size > 0) {
                showConfirm('저장하지 않은 변경사항이 있습니다. 정렬하시겠습니까?', () => {
                    promoDirtyRows.clear();
                    updatePromoSaveBar();
                    sortAndRenderPromoDetail(sortKey, sortDir);
                });
                return;
            }
            sortAndRenderPromoDetail(sortKey, sortDir);
        },
        emptyMessage: '상품이 없습니다.'
    });
    promoDetailTableManager.renderHeader(promoDetailColumns);

    // 패널 리사이즈 초기화
    initPanelResize('baseMasterDetail', 'panelResizeHandle');
    initPanelResize('promoMasterDetail', 'promoResizeHandle');

    // 공통 데이터 로드
    loadBrands();
    loadChannels();
    await loadYearMonths();

    // 정기 목표 마스터 로드
    loadChannelMaster();
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

// ==================== 탭 전환 ====================
function switchTab(tab) {
    if (tab === currentTab) return;

    // 현재 탭의 미저장 변경 확인
    const dirtyMap = currentTab === 'base' ? baseDirtyRows : promoDirtyRows;
    if (dirtyMap.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 탭을 전환하시겠습니까?', () => {
            dirtyMap.clear();
            if (currentTab === 'base') updateBaseSaveBar(); else updatePromoSaveBar();
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
    document.getElementById('promoMasterDetail').style.display = tab === 'promotion' ? 'grid' : 'none';

    // 필터 표시/숨김
    document.getElementById('channelFilterWrap').style.display = tab === 'promotion' ? '' : 'none';
    document.getElementById('promotionFilterWrap').style.display = tab === 'promotion' ? '' : 'none';

    // 업로드 모달 제목
    document.getElementById('uploadModalTitle').textContent =
        tab === 'base' ? '정기 목표 데이터 업로드' : '비정기 목표 데이터 업로드';

    if (tab === 'promotion') {
        loadPromotionTypes();
        loadPromoGroupMaster();
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

        currentChannels = channels;
        channelDataMap = {};
        channels.forEach(ch => channelDataMap[ch.ChannelID] = ch);

        document.getElementById('channelCount').textContent = `(${channels.length}개)`;

        baseMasterTableManager.render(channels, baseMasterColumns);
        applyBaseMasterSelection();

        if (currentChannelId && !channelDataMap[currentChannelId]) {
            resetBaseDetail();
        }

    } catch (e) {
        console.error('채널 목록 로드 실패:', e);
        showAlert('채널 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderMaster(sortKey, sortDir) {
    sortArray(currentChannels, sortKey, sortDir);
    baseMasterTableManager.render(currentChannels, baseMasterColumns);
    applyBaseMasterSelection();
}

function applyBaseMasterSelection() {
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
            updateBaseSaveBar();
            doSelectChannel(channelId, tr);
        });
        return;
    }
    doSelectChannel(channelId, tr);
}

function doSelectChannel(channelId, tr) {
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
        document.getElementById('baseDetailPlaceholder').style.display = 'none';
        document.getElementById('baseDetailContainer').style.display = 'flex';

        baseDetailTableManager.showLoading(baseDetailColumns.length);

        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/base/channel/${channel.ChannelID}/items${queryString}`);
        const items = result.data || [];

        currentDetailItems = items;
        document.getElementById('baseItemCount').textContent = `(${items.length}개)`;

        renderChannelSummary(channel);

        baseOriginalData = {};
        items.forEach(item => {
            baseOriginalData[item.TargetBaseID] = {
                TargetAmount: item.TargetAmount || 0,
                TargetQuantity: item.TargetQuantity || 0,
                Notes: item.Notes || ''
            };
        });

        baseDirtyRows.clear();
        updateBaseSaveBar();
        baseDetailTableManager.clearSelection();
        updateDetailActionButtons([]);

        baseDetailTableManager.render(items, baseDetailColumns);

    } catch (e) {
        console.error('채널 상세 로드 실패:', e);
        showAlert('채널 상세 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderDetail(sortKey, sortDir) {
    sortArray(currentDetailItems, sortKey, sortDir);
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
    updateBaseSaveBar();
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

            baseDirtyRows.clear();
            updateBaseSaveBar();
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

// ==================== 정기 목표: 저장 ====================
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

        items.forEach(item => {
            baseOriginalData[item.TargetBaseID] = {
                TargetAmount: item.TargetAmount,
                TargetQuantity: item.TargetQuantity,
                Notes: item.Notes
            };
            const detailItem = currentDetailItems.find(d => d.TargetBaseID === item.TargetBaseID);
            if (detailItem) {
                detailItem.TargetAmount = item.TargetAmount;
                detailItem.TargetQuantity = item.TargetQuantity;
                detailItem.Notes = item.Notes;
            }
        });

        baseDirtyRows.clear();
        updateBaseSaveBar();
        document.querySelectorAll('#base-detail-table .inline-input.dirty').forEach(inp => {
            inp.classList.remove('dirty');
        });

        loadChannelMaster();

    } catch (e) {
        console.error('저장 실패:', e);
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function updateBaseSaveBar() {
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

// ==================== 비정기 목표: 마스터 패널 ====================
async function loadPromoGroupMaster() {
    const yearMonth = document.getElementById('searchYearMonth').value;
    if (!yearMonth) {
        currentPromoGroups = [];
        promoMasterTableManager.render([], promoMasterColumns);
        document.getElementById('promoGroupCount').textContent = '';
        resetPromoDetail();
        return;
    }

    try {
        const brandId = document.getElementById('searchBrand').value;
        const channelId = document.getElementById('searchChannel').value;
        const promotionType = document.getElementById('searchPromotionType').value;

        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        if (channelId) params.channel_id = channelId;
        if (promotionType) params.promotion_type = promotionType;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/promotion/groups${queryString}`);
        const groups = result.data || [];

        currentPromoGroups = groups;
        promoGroupDataMap = {};
        groups.forEach(g => promoGroupDataMap[g.GroupKey] = g);

        document.getElementById('promoGroupCount').textContent = `(${groups.length}개)`;

        promoMasterTableManager.render(groups, promoMasterColumns);
        applyPromoMasterSelection();

        if (currentPromoGroupKey && !promoGroupDataMap[currentPromoGroupKey]) {
            resetPromoDetail();
        }

    } catch (e) {
        console.error('행사 목록 로드 실패:', e);
        showAlert('행사 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderPromoMaster(sortKey, sortDir) {
    sortArray(currentPromoGroups, sortKey, sortDir);
    promoMasterTableManager.render(currentPromoGroups, promoMasterColumns);
    applyPromoMasterSelection();
}

function applyPromoMasterSelection() {
    if (!currentPromoGroupKey) return;
    document.querySelectorAll('#promo-master-table tbody tr').forEach(tr => {
        if (tr.dataset.id === currentPromoGroupKey) {
            tr.classList.add('selected');
        }
    });
}

// ==================== 비정기 목표: 그룹 선택 ====================
function selectPromoGroup(groupKey, tr) {
    if (promoDirtyRows.size > 0 && groupKey !== currentPromoGroupKey) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 그룹을 전환하시겠습니까?', () => {
            promoDirtyRows.clear();
            updatePromoSaveBar();
            doSelectPromoGroup(groupKey, tr);
        });
        return;
    }
    doSelectPromoGroup(groupKey, tr);
}

function doSelectPromoGroup(groupKey, tr) {
    document.querySelectorAll('#promo-master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentPromoGroupKey = groupKey;
    currentPromoGroupData = promoGroupDataMap[groupKey];

    loadPromoGroupDetail(currentPromoGroupData);
}

// ==================== 비정기 목표: 디테일 패널 ====================
async function loadPromoGroupDetail(group) {
    const yearMonth = document.getElementById('searchYearMonth').value;
    const brandId = document.getElementById('searchBrand').value;

    try {
        document.getElementById('promoDetailPlaceholder').style.display = 'none';
        document.getElementById('promoDetailContainer').style.display = 'flex';

        promoDetailTableManager.showLoading(promoDetailColumns.length);

        const params = {
            channel_id: group.ChannelID,
            promotion_name: group.PromotionName,
            promotion_type: group.PromotionType,
            year_month: yearMonth
        };
        if (brandId) params.brand_id = brandId;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/targets/promotion/group-items${queryString}`);
        const items = result.data || [];

        currentPromoDetailItems = items;
        document.getElementById('promoItemCount').textContent = `(${items.length}개)`;

        renderPromoGroupSummary(group);

        promoOriginalData = {};
        items.forEach(item => {
            promoOriginalData[item.TargetPromotionID] = {
                TargetAmount: item.TargetAmount || 0,
                TargetQuantity: item.TargetQuantity || 0,
                Notes: item.Notes || ''
            };
        });

        promoDirtyRows.clear();
        updatePromoSaveBar();
        promoDetailTableManager.clearSelection();
        updatePromoDetailActionButtons([]);

        promoDetailTableManager.render(items, promoDetailColumns);

    } catch (e) {
        console.error('그룹 상세 로드 실패:', e);
        showAlert('그룹 상세 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderPromoDetail(sortKey, sortDir) {
    sortArray(currentPromoDetailItems, sortKey, sortDir);
    promoDetailTableManager.clearSelection();
    updatePromoDetailActionButtons([]);
    promoDetailTableManager.render(currentPromoDetailItems, promoDetailColumns);
}

function renderPromoGroupSummary(group) {
    const dateRange = (group.StartDate && group.EndDate)
        ? `${group.StartDate} ~ ${group.EndDate}`
        : '-';

    document.getElementById('promoGroupSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            ${escapeHtml(group.ChannelName)} · ${escapeHtml(group.PromotionName)} 목표 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">행사유형</span>
                <span class="summary-value">${escapeHtml(group.PromotionType)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">기간</span>
                <span class="summary-value">${dateRange}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">품목수</span>
                <span class="summary-value">${group.ProductCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">목표금액 합계(VAT포함)</span>
                <span class="summary-value">${group.TotalAmount.toLocaleString()}원</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">목표수량 합계</span>
                <span class="summary-value">${group.TotalQuantity.toLocaleString()}개</span>
            </div>
        </div>
    `;
}

function resetPromoDetail() {
    currentPromoGroupKey = null;
    currentPromoGroupData = null;
    promoOriginalData = {};
    promoDirtyRows.clear();
    currentPromoDetailItems = [];

    document.getElementById('promoDetailPlaceholder').style.display = 'flex';
    document.getElementById('promoDetailContainer').style.display = 'none';
    document.getElementById('promoGroupSummary').innerHTML = '';
    promoDetailTableManager.clearSelection();
    updatePromoDetailActionButtons([]);
    updatePromoSaveBar();
}

// ==================== 비정기 목표: 마스터 액션 버튼 ====================
function updatePromoMasterActionButtons(selectedIds) {
    const editDownloadBtn = document.getElementById('promoMasterEditDownloadButton');
    if (!editDownloadBtn) return;

    if (selectedIds.length > 0) {
        editDownloadBtn.classList.remove('btn-disabled');
        editDownloadBtn.disabled = false;
    } else {
        editDownloadBtn.classList.add('btn-disabled');
        editDownloadBtn.disabled = true;
    }
}

async function downloadPromoMasterEditForm() {
    const selectedGroupKeys = promoMasterTableManager.getSelectedRows();

    if (selectedGroupKeys.length === 0) {
        showAlert('수정할 행사를 선택해주세요.', 'warning');
        return;
    }

    const yearMonth = document.getElementById('searchYearMonth').value;
    if (!yearMonth) {
        showAlert('년월을 선택해주세요.', 'warning');
        return;
    }

    try {
        // 선택된 그룹들의 아이템 ID를 수집
        const brandId = document.getElementById('searchBrand').value;
        const allIds = [];

        for (const groupKey of selectedGroupKeys) {
            const group = promoGroupDataMap[groupKey];
            if (!group) continue;

            const params = {
                channel_id: group.ChannelID,
                promotion_name: group.PromotionName,
                promotion_type: group.PromotionType,
                year_month: yearMonth
            };
            if (brandId) params.brand_id = brandId;
            const queryString = api.buildQueryString(params);

            const result = await api.get(`/api/targets/promotion/group-items${queryString}`);
            const items = result.data || [];
            items.forEach(item => allIds.push(item.TargetPromotionID));
        }

        if (allIds.length === 0) {
            showAlert('선택한 행사에 상품이 없습니다.', 'warning');
            return;
        }

        const params = { ids: allIds.join(',') };
        const queryString = api.buildQueryString(params);
        window.location.href = `/api/targets/promotion/download${queryString}`;

    } catch (e) {
        console.error('수정 양식 다운로드 실패:', e);
        showAlert('수정 양식 다운로드 실패: ' + e.message, 'error');
    }
}

// ==================== 비정기 목표: 디테일 액션 버튼 ====================
function updatePromoDetailActionButtons(selectedIds) {
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

// ==================== 비정기 목표: 선택 삭제 ====================
async function bulkDeletePromoItems() {
    const selectedIds = promoDetailTableManager.getSelectedRows().map(Number);

    if (selectedIds.length === 0) {
        showAlert('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/targets/promotion/bulk-delete', { ids: selectedIds });

            showAlert(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');

            promoDirtyRows.clear();
            updatePromoSaveBar();
            loadPromoGroupMaster();

            if (currentPromoGroupData) {
                loadPromoGroupDetail(currentPromoGroupData);
            }

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 비정기 목표: 저장 ====================
async function savePromoChanges() {
    if (promoDirtyRows.size === 0) return;

    const items = [];
    promoDirtyRows.forEach((data, id) => {
        items.push({
            TargetPromotionID: id,
            TargetAmount: data.TargetAmount,
            TargetQuantity: data.TargetQuantity,
            Notes: data.Notes
        });
    });

    try {
        const result = await api.put('/api/targets/promotion/bulk-update', { items });
        showAlert(`${result.updated}건이 저장되었습니다.`, 'success');

        items.forEach(item => {
            promoOriginalData[item.TargetPromotionID] = {
                TargetAmount: item.TargetAmount,
                TargetQuantity: item.TargetQuantity,
                Notes: item.Notes
            };
            const detailItem = currentPromoDetailItems.find(d => d.TargetPromotionID === item.TargetPromotionID);
            if (detailItem) {
                detailItem.TargetAmount = item.TargetAmount;
                detailItem.TargetQuantity = item.TargetQuantity;
                detailItem.Notes = item.Notes;
            }
        });

        promoDirtyRows.clear();
        updatePromoSaveBar();
        document.querySelectorAll('#promo-detail-table .inline-input.dirty').forEach(inp => {
            inp.classList.remove('dirty');
        });

        loadPromoGroupMaster();

    } catch (e) {
        console.error('저장 실패:', e);
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function updatePromoSaveBar() {
    const saveBar = document.getElementById('promoSaveBar');
    const countEl = document.getElementById('promoDirtyCount');
    if (!saveBar) return;

    if (promoDirtyRows.size > 0) {
        saveBar.style.display = 'flex';
        countEl.textContent = `${promoDirtyRows.size}건 변경됨`;
    } else {
        saveBar.style.display = 'none';
    }
}

// ==================== 공통: 인라인 편집 ====================
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
    const tab = input.dataset.tab;
    const id = parseInt(input.dataset.id);
    const field = input.dataset.field;

    const originalMap = tab === 'base' ? baseOriginalData : promoOriginalData;
    const dirtyMap = tab === 'base' ? baseDirtyRows : promoDirtyRows;
    const original = originalMap[id];
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
        dirtyMap.set(id, rowData);
    } else {
        dirtyMap.delete(id);
    }

    if (tab === 'base') {
        updateBaseSaveBar();
    } else {
        updatePromoSaveBar();
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

// ==================== 필터 ====================
function applyFilters() {
    const dirtyMap = currentTab === 'base' ? baseDirtyRows : promoDirtyRows;
    if (dirtyMap.size > 0) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 필터를 적용하시겠습니까?', () => {
            dirtyMap.clear();
            if (currentTab === 'base') updateBaseSaveBar(); else updatePromoSaveBar();
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
        resetPromoDetail();
        loadPromoGroupMaster();
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
        resetPromoDetail();
        loadPromoGroupMaster();
    }
}

// ==================== 엑셀 다운로드 ====================
function downloadTemplate() {
    const endpoint = currentTab === 'base'
        ? '/api/targets/base/download'
        : '/api/targets/promotion/download';

    window.location.href = endpoint;
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

function downloadPromoDetailEditForm() {
    const selectedIds = promoDetailTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 항목을 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/targets/promotion/download${queryString}`;
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
            loadPromoGroupMaster();
            if (currentPromoGroupKey && currentPromoGroupData) {
                loadPromoGroupDetail(currentPromoGroupData);
            }
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

function sortArray(arr, sortKey, sortDir) {
    arr.sort((a, b) => {
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
}
