/**
 * 사입 예상 매출 관리 페이지 JavaScript
 * - 정기 예상 매출: 마스터-디테일 (채널별 인라인 편집)
 * - 비정기 예상 매출: 마스터-디테일 (비정기별 상품 인라인 편집)
 */

// ==================== 공통 상태 ====================
let currentTab = 'base';
let uploadModal, uploadResultModal;
let msBrand, msChannel, msIrregularType;

// ==================== 정기 상태 ====================
let baseMasterTableManager, baseDetailTableManager;
let channelDataMap = {};
let currentChannels = [];
let currentChannelId = null;
let currentChannelData = null;
let baseOriginalData = {};
let baseDirtyRows = new Map();
let baseDetailItems = [];

// ==================== 비정기 상태 ====================
let irregMasterTableManager, irregDetailTableManager;
let currentIrregMasterData = [];
let irregMasterDataMap = {};
let currentIrregId = null;
let currentIrregData = null;
let currentIrregDetailItems = [];
let irregOriginalData = {};
let irregDirtyRows = new Map();
let irregFiltersLoaded = false;

// ==================== 정기 마스터 컬럼 ====================
const baseMasterColumns = [
    {
        key: 'ChannelName',
        header: '채널',
        sortKey: 'ChannelName',
        render: (row) => `<div class="group-info"><span class="group-title">${escapeHtml(row.ChannelName)}</span></div>`
    },
    {
        key: 'TotalAmount',
        header: '예상금액(VAT포함)',
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

// ==================== 정기 디테일 컬럼 ====================
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
        key: 'ExpectedAmount',
        header: '예상금액(VAT포함)',
        sortKey: 'ExpectedAmount',
        render: (row) => `<span class="col-amount" style="text-align:right">${(row.ExpectedAmount || 0).toLocaleString()}</span>`
    },
    {
        key: 'ExpectedQuantity',
        header: '예상수량',
        sortKey: 'ExpectedQuantity',
        render: (row) => `<span class="col-qty" style="text-align:right">${(row.ExpectedQuantity || 0).toLocaleString()}</span>`
    },
    {
        key: 'Notes',
        header: '비고',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.Notes || '-')}</span>`
    },
    {
        key: 'OliveyoungType',
        header: '올리브영유형',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.OliveyoungType) || '-'}</span>`
    }
];

// ==================== 비정기 마스터 컬럼 ====================
const irregMasterColumns = [
    {
        key: 'IrregularName',
        header: '비정기',
        sortKey: 'IrregularName',
        render: (row) => {
            const statusLabels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
            const statusLabel = statusLabels[row.Status] || row.Status;
            const dateRange = (row.StartDate && row.EndDate) ? `${row.StartDate} ~ ${row.EndDate}` : '';
            return `<div class="group-info">
                <span class="group-title">${escapeHtml(row.IrregularName)}</span>
                <span class="group-meta">
                    ${escapeHtml(row.ChannelName)} · ${escapeHtml(row.IrregularType)}
                    <span class="status-badge status-${row.Status}" style="margin-left:4px;">${statusLabel}</span>
                </span>
                ${dateRange ? `<span class="group-meta">${dateRange}</span>` : ''}
            </div>`;
        }
    },
    {
        key: 'OliveyoungType',
        header: '올리브영유형',
        render: (row) => `<div style="font-size:13px;">${escapeHtml(row.OliveyoungType) || '-'}</div>`
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

// ==================== 비정기 디테일 컬럼 ====================
const irregDetailColumns = [
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
        key: 'IrregularPrice',
        header: '비정기가',
        sortKey: 'IrregularPrice',
        render: (row) => `<span class="col-amount" style="text-align:right">${(row.IrregularPrice || 0).toLocaleString()}</span>`
    },
    {
        key: 'ExpectedSalesAmount',
        header: '예상매출',
        sortKey: 'ExpectedSalesAmount',
        render: (row) => `<span class="col-amount" style="text-align:right">${(row.ExpectedSalesAmount || 0).toLocaleString()}</span>`
    },
    {
        key: 'ExpectedQuantity',
        header: '예상수량',
        sortKey: 'ExpectedQuantity',
        render: (row) => `<span class="col-qty" style="text-align:right">${(row.ExpectedQuantity || 0).toLocaleString()}</span>`
    },
    {
        key: 'Notes',
        header: '비고',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.Notes || '-')}</span>`
    }
];

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async function () {
    // 바깥 클릭 시 드롭다운 닫기
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-dropdown')) closeAllDropdowns();
    });

    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 정기 테이블 매니저
    baseMasterTableManager = new TableManager('base-master-table', {
        selectable: true,
        idKey: 'ChannelID',
        onRowClick: (row, tr) => selectChannel(row.ChannelID, tr),
        onSelectionChange: (ids) => updateBaseMasterActionButtons(ids),
        onSort: (sortKey, sortDir) => sortAndRenderBaseMaster(sortKey, sortDir),
        emptyMessage: '데이터가 없습니다.'
    });
    baseMasterTableManager.renderHeader(baseMasterColumns);

    baseDetailTableManager = new TableManager('base-detail-table', {
        selectable: true,
        idKey: 'Expected1PRegularID',
        onSelectionChange: (ids) => updateBaseDetailActionButtons(ids),
        onSort: (sortKey, sortDir) => sortAndRenderBaseDetail(sortKey, sortDir),
        emptyMessage: '상품이 없습니다.'
    });
    baseDetailTableManager.renderHeader(baseDetailColumns);

    // 비정기 테이블 매니저
    irregMasterTableManager = new TableManager('irreg-master-table', {
        selectable: true,
        idKey: 'Expected1PIrregularID',
        onRowClick: (row, tr) => selectIrregular(row.Expected1PIrregularID, tr),
        onSelectionChange: (ids) => updateIrregMasterActionButtons(ids),
        onSort: (sortKey, sortDir) => sortAndRenderIrregMaster(sortKey, sortDir),
        emptyMessage: '비정기 데이터가 없습니다.'
    });
    irregMasterTableManager.renderHeader(irregMasterColumns);

    irregDetailTableManager = new TableManager('irreg-detail-table', {
        selectable: true,
        idKey: 'Expected1PIrregularProductID',
        onSelectionChange: (ids) => updateIrregDetailActionButtons(ids),
        onSort: (sortKey, sortDir) => sortAndRenderIrregDetail(sortKey, sortDir),
        emptyMessage: '비정기 상품이 없습니다.'
    });
    irregDetailTableManager.renderHeader(irregDetailColumns);

    // 패널 리사이즈
    initPanelResize('baseMasterDetail', 'baseResizeHandle');
    initPanelResize('irregMasterDetail', 'irregResizeHandle');

    // MultiSelect 초기화
    msBrand = new MultiSelect('searchBrand', { placeholder: '전체' });
    msChannel = new MultiSelect('searchChannel', { placeholder: '전체' });
    msIrregularType = new MultiSelect('searchIrregularType', { placeholder: '전체' });

    // 공통 데이터
    loadBrands();
    loadChannels();
    await loadYearMonths();
    await loadInputMonths();

    // 년월 변경 시 입력월 목록 갱신
    document.getElementById('searchYearMonth').addEventListener('change', async () => {
        await loadInputMonths();
    });

    // 정기 마스터 로드
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
    doSwitchTab(tab);
}

function doSwitchTab(tab) {
    currentTab = tab;

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    document.getElementById('baseMasterDetail').style.display = tab === 'base' ? 'grid' : 'none';
    document.getElementById('irregMasterDetail').style.display = tab === 'irregular' ? 'grid' : 'none';

    // 비정기 전용 필터 표시/숨김
    document.getElementById('channelFilterWrap').style.display = tab === 'irregular' ? '' : 'none';
    document.getElementById('irregularTypeFilterWrap').style.display = tab === 'irregular' ? '' : 'none';
    document.getElementById('statusFilterWrap').style.display = tab === 'irregular' ? '' : 'none';

    if (tab === 'irregular' && !irregFiltersLoaded) {
        irregFiltersLoaded = true;
        loadIrregularTypes();
        loadStatuses();
    }

    // 탭 전환 시 입력월 목록 갱신
    loadInputMonths();

    if (tab === 'irregular') {
        loadIrregMaster();
    }
}

// ================================================================
//  정기 예상 매출
// ================================================================

// ==================== 정기: 마스터 ====================
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
        const brandId = msBrand.getSelectedString();
        const inputMonth = document.getElementById('searchInputMonth').value;
        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        if (inputMonth) params.input_month = inputMonth;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/expected/1p/regular/channels${queryString}`);
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

function sortAndRenderBaseMaster(sortKey, sortDir) {
    sortArray(currentChannels, sortKey, sortDir);
    baseMasterTableManager.render(currentChannels, baseMasterColumns);
    applyBaseMasterSelection();
}

function applyBaseMasterSelection() {
    if (!currentChannelId) return;
    document.querySelectorAll('#base-master-table tbody tr').forEach(tr => {
        if (tr.dataset.id == currentChannelId) tr.classList.add('selected');
    });
}

// ==================== 정기: 채널 선택 ====================
function selectChannel(channelId, tr) {
    doSelectChannel(channelId, tr);
}

function doSelectChannel(channelId, tr) {
    document.querySelectorAll('#base-master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentChannelId = channelId;
    currentChannelData = channelDataMap[channelId];
    loadChannelDetail(currentChannelData);
}

// ==================== 정기: 디테일 ====================
async function loadChannelDetail(channel) {
    const yearMonth = document.getElementById('searchYearMonth').value;
    const brandId = msBrand.getSelectedString();
    const inputMonth = document.getElementById('searchInputMonth').value;

    try {
        document.getElementById('baseDetailPlaceholder').style.display = 'none';
        document.getElementById('baseDetailContainer').style.display = 'flex';
        baseDetailTableManager.showLoading(baseDetailColumns.length);

        const params = { year_month: yearMonth };
        if (brandId) params.brand_id = brandId;
        if (inputMonth) params.input_month = inputMonth;
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/expected/1p/regular/channel/${channel.ChannelID}/items${queryString}`);
        const items = result.data || [];

        baseDetailItems = items;
        document.getElementById('baseItemCount').textContent = `(${items.length}개)`;
        renderChannelSummary(channel);

        baseDetailTableManager.clearSelection();
        updateBaseDetailActionButtons([]);
        baseDetailTableManager.render(items, baseDetailColumns);
    } catch (e) {
        console.error('채널 상세 로드 실패:', e);
        showAlert('채널 상세 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderBaseDetail(sortKey, sortDir) {
    sortArray(baseDetailItems, sortKey, sortDir);
    baseDetailTableManager.clearSelection();
    updateBaseDetailActionButtons([]);
    baseDetailTableManager.render(baseDetailItems, baseDetailColumns);
}

function renderChannelSummary(channel) {
    document.getElementById('baseChannelSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            ${escapeHtml(channel.ChannelName)} 예상 매출 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">품목수</span>
                <span class="summary-value">${channel.ProductCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상금액 합계(VAT포함)</span>
                <span class="summary-value">${channel.TotalAmount.toLocaleString()}원</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상수량 합계</span>
                <span class="summary-value">${channel.TotalQuantity.toLocaleString()}개</span>
            </div>
        </div>
    `;
}

function resetBaseDetail() {
    currentChannelId = null;
    currentChannelData = null;
    baseDetailItems = [];

    document.getElementById('baseDetailPlaceholder').style.display = 'flex';
    document.getElementById('baseDetailContainer').style.display = 'none';
    document.getElementById('baseChannelSummary').innerHTML = '';
    baseDetailTableManager.clearSelection();
    updateBaseDetailActionButtons([]);
}

// ==================== 정기: 액션 버튼 ====================
function updateBaseMasterActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('masterEditDownloadButton');
    const deleteBtn = document.getElementById('baseMasterDeleteButton');
    if (editBtn) { editBtn.classList.toggle('btn-disabled', !hasSelection); editBtn.disabled = !hasSelection; }
    if (deleteBtn) { deleteBtn.classList.toggle('btn-disabled', !hasSelection); deleteBtn.disabled = !hasSelection; }
}

function updateBaseDetailActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('baseDeleteButton');
    const editBtn = document.getElementById('baseEditDownloadButton');

    const hasSelection = selectedIds.length > 0;
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    editBtn.disabled = !hasSelection;
}

// ==================== 정기: 마스터 삭제 ====================
async function bulkDeleteBaseMasterItems() {
    const selectedIds = baseMasterTableManager.getSelectedRows().map(Number);
    if (selectedIds.length === 0) {
        showAlert('삭제할 채널을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`선택한 ${selectedIds.length}개 채널의 모든 상품을 삭제하시겠습니까?`, async () => {
        try {
            const yearMonth = document.getElementById('searchYearMonth').value;
            const inputMonth = document.getElementById('searchInputMonth').value;
            const deletePromises = selectedIds.map(channelId =>
                api.post('/api/expected/1p/regular/filter-delete', {
                    year_month: yearMonth,
                    channel_id: channelId,
                    input_month: inputMonth || null
                })
            );
            const results = await Promise.all(deletePromises);
            const totalDeleted = results.reduce((sum, r) => sum + (r.deleted_count || 0), 0);
            showAlert(`${totalDeleted}개 항목이 삭제되었습니다.`, 'success');

            loadChannelMaster();
            document.getElementById('baseDetailContainer').style.display = 'none';
            document.getElementById('baseDetailPlaceholder').style.display = '';
        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 정기: 디테일 삭제 ====================
async function bulkDeleteBaseItems() {
    const selectedIds = baseDetailTableManager.getSelectedRows().map(Number);
    if (selectedIds.length === 0) {
        showAlert('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/expected/1p/regular/bulk-delete', { ids: selectedIds });
            showAlert(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');

            loadChannelMaster();
            if (currentChannelData) loadChannelDetail(currentChannelData);
        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 정기: 저장 (인라인 편집 제거됨) ====================
function saveBaseChanges() { /* removed - upload only */ }
function updateBaseSaveBar() { /* removed - upload only */ }

// ================================================================
//  비정기 예상 매출
// ================================================================

// ==================== 비정기: 마스터 ====================
async function loadIrregMaster() {
    try {
        irregMasterTableManager.showLoading(irregMasterColumns.length);

        const params = {};
        const yearMonth = document.getElementById('searchYearMonth').value;
        const brandId = msBrand.getSelectedString();
        const channelId = msChannel.getSelectedString();
        const irregularType = msIrregularType.getSelectedString();
        const status = document.getElementById('searchStatus').value;
        const inputMonth = document.getElementById('searchInputMonth').value;

        if (yearMonth) params.year_month = yearMonth;
        if (brandId) params.brand_id = brandId;
        if (channelId) params.channel_id = channelId;
        if (irregularType) params.irregular_type = irregularType;
        if (status) params.status = status;
        if (inputMonth) params.input_month = inputMonth;

        const queryString = api.buildQueryString(params);
        const result = await api.get(`/api/expected/1p/irregular/master-summary${queryString}`);
        const data = result.data || [];

        currentIrregMasterData = data;
        irregMasterDataMap = {};
        data.forEach(row => irregMasterDataMap[row.Expected1PIrregularID] = row);

        document.getElementById('irregMasterCount').textContent = `(${data.length}개)`;
        irregMasterTableManager.render(data, irregMasterColumns);
        applyIrregMasterSelection();

        if (currentIrregId && !irregMasterDataMap[currentIrregId]) {
            resetIrregDetail();
        }
    } catch (e) {
        console.error('비정기 목록 로드 실패:', e);
        showAlert('비정기 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderIrregMaster(sortKey, sortDir) {
    sortArray(currentIrregMasterData, sortKey, sortDir);
    irregMasterTableManager.render(currentIrregMasterData, irregMasterColumns);
    applyIrregMasterSelection();
}

function applyIrregMasterSelection() {
    if (!currentIrregId) return;
    document.querySelectorAll('#irreg-master-table tbody tr').forEach(tr => {
        if (tr.dataset.id === currentIrregId) tr.classList.add('selected');
    });
}

// ==================== 비정기: 선택 ====================
function selectIrregular(irregularId, tr) {
    doSelectIrregular(irregularId, tr);
}

function doSelectIrregular(irregularId, tr) {
    document.querySelectorAll('#irreg-master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentIrregId = irregularId;
    currentIrregData = irregMasterDataMap[irregularId];
    loadIrregDetail(currentIrregData);
}

// ==================== 비정기: 디테일 ====================
async function loadIrregDetail(irreg) {
    try {
        document.getElementById('irregDetailPlaceholder').style.display = 'none';
        document.getElementById('irregDetailContainer').style.display = 'flex';
        irregDetailTableManager.showLoading(irregDetailColumns.length);

        const result = await api.get(`/api/expected/1p/irregular/products?expected_1p_irregular_id=${irreg.Expected1PIrregularID}&page=1&limit=10000`);
        const items = result.data || [];

        currentIrregDetailItems = items;
        document.getElementById('irregDetailItemCount').textContent = `(${items.length}개)`;
        renderIrregSummary(irreg);

        irregDetailTableManager.clearSelection();
        updateIrregDetailActionButtons([]);
        irregDetailTableManager.render(items, irregDetailColumns);
    } catch (e) {
        console.error('비정기 상품 로드 실패:', e);
        showAlert('비정기 상품 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderIrregDetail(sortKey, sortDir) {
    sortArray(currentIrregDetailItems, sortKey, sortDir);
    irregDetailTableManager.clearSelection();
    updateIrregDetailActionButtons([]);
    irregDetailTableManager.render(currentIrregDetailItems, irregDetailColumns);
}

function renderIrregSummary(irreg) {
    const statusLabels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
    const statusLabel = statusLabels[irreg.Status] || irreg.Status;
    const dateRange = (irreg.StartDate && irreg.EndDate) ? `${irreg.StartDate} ~ ${irreg.EndDate}` : '-';

    document.getElementById('irregSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            ${escapeHtml(irreg.IrregularName)} 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">채널</span>
                <span class="summary-value">${escapeHtml(irreg.ChannelName)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">유형</span>
                <span class="summary-value">${escapeHtml(irreg.IrregularType)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">상태</span>
                <span class="summary-value"><span class="status-badge status-${irreg.Status}">${statusLabel}</span></span>
            </div>
            <div class="summary-item">
                <span class="summary-label">기간</span>
                <span class="summary-value">${dateRange}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">상품수</span>
                <span class="summary-value">${irreg.ProductCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상매출 합계</span>
                <span class="summary-value">${irreg.TotalSalesAmount.toLocaleString()}원</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">예상수량 합계</span>
                <span class="summary-value">${irreg.TotalQuantity.toLocaleString()}개</span>
            </div>
        </div>
    `;
}

function resetIrregDetail() {
    currentIrregId = null;
    currentIrregData = null;
    currentIrregDetailItems = [];

    document.getElementById('irregDetailPlaceholder').style.display = 'flex';
    document.getElementById('irregDetailContainer').style.display = 'none';
    document.getElementById('irregSummary').innerHTML = '';
    irregDetailTableManager.clearSelection();
    updateIrregDetailActionButtons([]);
}

// ==================== 비정기: 액션 버튼 ====================
function updateIrregMasterActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('irregEditDownloadButton');
    const deleteBtn = document.getElementById('irregMasterDeleteButton');
    if (editBtn) { editBtn.classList.toggle('btn-disabled', !hasSelection); editBtn.disabled = !hasSelection; }
    if (deleteBtn) { deleteBtn.classList.toggle('btn-disabled', !hasSelection); deleteBtn.disabled = !hasSelection; }
}

function updateIrregDetailActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('irregDeleteButton');
    const editBtn = document.getElementById('irregDetailEditDownloadButton');

    const hasSelection = selectedIds.length > 0;
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    editBtn.disabled = !hasSelection;
}

// ==================== 비정기: 마스터 삭제 ====================
async function bulkDeleteIrregMasterItems() {
    const selectedIds = irregMasterTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('삭제할 행사를 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`선택한 ${selectedIds.length}개 행사를 삭제하시겠습니까?\n(포함된 상품도 함께 삭제됩니다)`, async () => {
        try {
            const result = await api.post('/api/expected/1p/irregular/bulk-delete', { ids: selectedIds });
            showAlert(`${result.deleted_count}개 행사가 삭제되었습니다.`, 'success');

            loadIrregMaster();
            document.getElementById('irregDetailContainer').style.display = 'none';
            document.getElementById('irregDetailPlaceholder').style.display = '';
        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 비정기: 디테일 삭제 ====================
async function bulkDeleteIrregItems() {
    const selectedIds = irregDetailTableManager.getSelectedRows().map(Number);
    if (selectedIds.length === 0) {
        showAlert('삭제할 상품을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 상품을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/expected/1p/irregular/products/bulk-delete', { ids: selectedIds });
            showAlert(`${result.deleted_count}개 상품이 삭제되었습니다.`, 'success');

            loadIrregMaster();
            if (currentIrregData) loadIrregDetail(currentIrregData);
        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// ==================== 비정기: 저장 (인라인 편집 제거됨) ====================
function saveIrregChanges() { /* removed - upload only */ }
function updateIrregSaveBar() { /* removed - upload only */ }

// ================================================================
//  공통 기능
// ================================================================

// ==================== 인라인 편집 (제거됨 - 업로드 전용) ====================
function onInlineFocus(input) { /* removed */ }
function onAmountBlur(input) { /* removed */ }
function onQuantityBlur(input) { /* removed */ }
function onNotesInput(input) { /* removed */ }
function checkDirty(input) { /* removed */ }

// ==================== 공통 데이터 로드 ====================
async function loadBrands() {
    try {
        const result = await api.get('/api/brands/all');
        const brands = result.data || [];

        msBrand.setOptions(brands.map(b => ({ value: b.BrandID, label: b.Name })));
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

async function loadChannels() {
    try {
        // 1P, 2P 채널 모두 로드
        const [result1p, result2p] = await Promise.all([
            api.get('/api/channels/list?contract_type=1P'),
            api.get('/api/channels/list?contract_type=2P')
        ]);
        const channels1p = result1p.data || result1p || [];
        const channels2p = result2p.data || result2p || [];
        const channels = [...channels1p, ...channels2p];

        msChannel.setOptions(channels.map(ch => ({ value: ch.ChannelID, label: ch.Name })));
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

async function loadYearMonths() {
    try {
        const result = await api.get('/api/expected/1p/regular/year-months');
        const yearMonths = result.year_months || [];

        if (yearMonths.length > 0) {
            document.getElementById('searchYearMonth').value = yearMonths[0];
        }
    } catch (e) {
        console.error('년월 목록 로드 실패:', e);
    }
}

async function loadInputMonths() {
    try {
        const yearMonth = document.getElementById('searchYearMonth').value;
        const params = {};
        if (yearMonth) params.year_month = yearMonth;
        const queryString = api.buildQueryString(params);

        const endpoint = currentTab === 'irregular'
            ? '/api/expected/1p/irregular/input-months'
            : '/api/expected/1p/regular/input-months';
        const result = await api.get(`${endpoint}${queryString}`);
        const inputMonths = result.input_months || [];

        const select = document.getElementById('searchInputMonth');
        select.innerHTML = '<option value="">전체</option>';

        inputMonths.forEach(im => {
            const option = document.createElement('option');
            option.value = im;
            option.textContent = im;
            select.appendChild(option);
        });

        // 가장 최근 입력월을 기본 선택
        if (inputMonths.length > 0) {
            select.value = inputMonths[0];
        }
    } catch (e) {
        console.error('입력월 목록 로드 실패:', e);
    }
}

async function loadIrregularTypes() {
    try {
        const result = await api.get('/api/expected/1p/irregular/irregular-types');
        const types = result.irregular_types || [];

        msIrregularType.setOptions(types.map(t => ({ value: t, label: t })));
    } catch (e) {
        console.error('비정기유형 로드 실패:', e);
    }
}

async function loadStatuses() {
    try {
        const result = await api.get('/api/expected/1p/irregular/statuses');
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

// ==================== 필터 ====================
function applyFilters() {
    doApplyFilters();
}

function doApplyFilters() {
    if (currentTab === 'base') {
        resetBaseDetail();
        loadChannelMaster();
    } else {
        resetIrregDetail();
        loadIrregMaster();
    }
}

function resetFilters() {
    document.getElementById('searchYearMonth').value = '';
    document.getElementById('searchInputMonth').value = '';
    document.getElementById('searchInputMonth').innerHTML = '<option value="">전체</option>';
    msBrand.reset();
    msChannel.reset();
    msIrregularType.reset();
    document.getElementById('searchStatus').value = '';

    if (currentTab === 'base') {
        resetBaseDetail();
        loadChannelMaster();
    } else {
        resetIrregDetail();
        loadIrregMaster();
    }
}

// ==================== 엑셀 다운로드 ====================
function downloadTemplate(formatType) {
    const endpoint = currentTab === 'base'
        ? `/api/expected/1p/regular/download?format_type=${formatType}`
        : `/api/expected/1p/irregular/download?format_type=${formatType}`;
    window.location.href = endpoint;
    closeAllDropdowns();
}

function toggleTemplateDropdown(btn) {
    const dropdown = btn.closest('.btn-dropdown');
    const isOpen = dropdown.classList.contains('open');
    closeAllDropdowns();
    if (!isOpen) dropdown.classList.add('open');
}

function closeAllDropdowns() {
    document.querySelectorAll('.btn-dropdown.open').forEach(d => d.classList.remove('open'));
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
    const brandId = msBrand.getSelectedString();
    const inputMonth = document.getElementById('searchInputMonth').value;
    if (brandId) params.brand_id = brandId;
    if (inputMonth) params.input_month = inputMonth;

    const queryString = api.buildQueryString(params);
    window.location.href = `/api/expected/1p/regular/download${queryString}`;
}

function downloadChannelEditForm() {
    const selectedIds = baseDetailTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('수정할 항목을 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/expected/1p/regular/download${queryString}`;
}

function downloadIrregEditForm() {
    const selectedIds = irregMasterTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('수정할 비정기를 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/expected/1p/irregular/download${queryString}`;
}

function downloadIrregDetailEditForm() {
    const selectedIds = irregDetailTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('수정할 상품을 선택해주세요.', 'warning');
        return;
    }

    const params = { ids: currentIrregId };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/expected/1p/irregular/download${queryString}`;
}

// ==================== 업로드 ====================
function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('uploadButton').disabled = true;

    document.getElementById('uploadModalTitle').textContent =
        currentTab === 'base' ? '정기 예상 매출 데이터 업로드' : '비정기 데이터 업로드';

    // 입력월: 기본값 없이 직접 선택 필수
    document.getElementById('uploadInputMonth').value = '';

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

        // 입력월(Round) 필수
        const uploadInputMonth = document.getElementById('uploadInputMonth').value;
        if (!uploadInputMonth) {
            showAlert('입력월을 선택해주세요.', 'warning');
            document.getElementById('uploadProgress').style.display = 'none';
            document.getElementById('uploadButton').disabled = false;
            return;
        }
        formData.append('input_month', uploadInputMonth);

        const endpoint = currentTab === 'base'
            ? '/api/expected/1p/regular/upload'
            : '/api/expected/1p/irregular/upload';

        const token = localStorage.getItem('access_token');
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        uploadModal.hide();

        if (!response.ok) {
            const error = await response.json();
            showUploadError(error.detail || '업로드 중 오류가 발생했습니다.');
            return;
        }

        const result = await response.json();
        showUploadSuccess(result);

        // 데이터 새로고침
        if (currentTab === 'base') {
            loadChannelMaster();
            if (currentChannelId && currentChannelData) loadChannelDetail(currentChannelData);
        } else {
            resetIrregDetail();
            loadIrregMaster();
        }

    } catch (e) {
        console.error('업로드 실패:', e);
        uploadModal.hide();
        showUploadError(e.message || '업로드 중 오류가 발생했습니다.');
    }
}

function showUploadSuccess(result) {
    document.getElementById('uploadSuccessSection').style.display = 'block';
    document.getElementById('uploadErrorSection').style.display = 'none';
    document.getElementById('uploadResultTitle').textContent = '업로드 결과';

    if (currentTab === 'base') {
        document.getElementById('uploadRegularStats').style.display = 'block';
        document.getElementById('uploadIrregularStats').style.display = 'none';
        document.getElementById('regTotalRows').textContent = result.total_rows?.toLocaleString() || 0;
        document.getElementById('regInserted').textContent = result.inserted?.toLocaleString() || 0;
        document.getElementById('regUpdated').textContent = result.updated?.toLocaleString() || 0;
    } else {
        document.getElementById('uploadRegularStats').style.display = 'none';
        document.getElementById('uploadIrregularStats').style.display = 'block';
        document.getElementById('irregTotalRows').textContent = result.total_rows?.toLocaleString() || 0;
        document.getElementById('irregInserted').textContent = result.irregular_inserted?.toLocaleString() || 0;
        document.getElementById('irregUpdated').textContent = result.irregular_updated?.toLocaleString() || 0;
        document.getElementById('irregProdInserted').textContent = result.product_inserted?.toLocaleString() || 0;
        document.getElementById('irregProdUpdated').textContent = result.product_updated?.toLocaleString() || 0;
    }

    uploadResultModal.show();
}

function showUploadError(message) {
    document.getElementById('uploadSuccessSection').style.display = 'none';
    document.getElementById('uploadErrorSection').style.display = 'block';
    document.getElementById('uploadResultTitle').textContent = '업로드 실패';
    document.getElementById('uploadErrorMessage').textContent = message;
    uploadResultModal.show();
}
