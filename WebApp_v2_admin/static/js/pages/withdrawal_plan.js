/**
 * 불출 계획 페이지 JavaScript
 * - 마스터: 캠페인 그룹 목록 (TableManager)
 * - 디테일: 선택된 캠페인의 상품 목록 (인라인 편집)
 */

// ==================== 상태 변수 ====================
let masterTableManager, detailTableManager;
let uploadModal, uploadResultModal;

// 마스터 데이터
let currentMasterData = [];
let masterDataMap = {};              // {GroupID: row}
let currentGroupId = null;
let currentGroupData = null;

// 디테일 데이터
let currentDetailItems = [];
let originalData = {};               // {PlanID: {PlannedQty, Notes}}
let dirtyRows = new Map();           // Map<PlanID, {PlannedQty, Notes}>

// 필터
let currentFilters = {};

// ==================== 마스터 컬럼 정의 ====================
const masterColumns = [
    {
        key: 'Title',
        header: '캠페인',
        sortKey: 'Title',
        render: (row) => {
            const dateRange = row.StartDate === row.EndDate
                ? row.StartDate
                : `${row.StartDate} ~ ${row.EndDate}`;
            return `<div class="group-info">
                <span class="group-title">${escapeHtml(row.Title)}</span>
                <span class="group-meta">
                    <span class="type-badge ${escapeHtml(row.Type)}">${escapeHtml(row.Type)}</span>
                    <span style="margin-left:4px;">${dateRange} · ${row.ItemCount}개 상품</span>
                </span>
            </div>`;
        }
    },
    {
        key: 'TotalQty',
        header: '총수량',
        sortKey: 'TotalQty',
        render: (row) => `<div style="text-align:right;font-size:13px;">${(row.TotalQty || 0).toLocaleString()}</div>`
    }
];

// ==================== 디테일 컬럼 정의 ====================
const detailColumns = [
    {
        key: 'ProductName',
        header: '상품명',
        sortKey: 'ProductName',
        render: (row) => `<span style="font-size:13px;">${escapeHtml(row.ProductName) || '-'}</span>`
    },
    {
        key: 'UniqueCode',
        header: '고유코드',
        sortKey: 'UniqueCode',
        render: (row) => `<code style="font-size:12px;">${escapeHtml(row.UniqueCode) || '-'}</code>`
    },
    {
        key: 'Date',
        header: '계획일자',
        sortKey: 'Date',
        render: (row) => `<span style="font-size:13px;">${row.Date || '-'}</span>`
    },
    {
        key: 'PlannedQty',
        header: '예정수량',
        sortKey: 'PlannedQty',
        render: (row) => {
            const dirty = dirtyRows.get(row.PlanID);
            const val = dirty && dirty.PlannedQty !== undefined ? dirty.PlannedQty : (row.PlannedQty || 0);
            const orig = originalData[row.PlanID];
            const isDirty = orig && val !== orig.PlannedQty;
            return `<input type="text" class="inline-input amount${isDirty ? ' dirty' : ''}"
                data-id="${row.PlanID}" data-field="PlannedQty"
                value="${val.toLocaleString()}"
                onfocus="onInlineFocus(this)" onblur="onQuantityBlur(this)">`;
        }
    },
    {
        key: 'Notes',
        header: '메모',
        render: (row) => {
            const dirty = dirtyRows.get(row.PlanID);
            const val = dirty && dirty.Notes !== undefined ? dirty.Notes : (row.Notes || '');
            const orig = originalData[row.PlanID];
            const isDirty = orig && val !== (orig.Notes || '');
            return `<input type="text" class="inline-input${isDirty ? ' dirty' : ''}"
                data-id="${row.PlanID}" data-field="Notes"
                value="${escapeHtml(val)}"
                oninput="onNotesInput(this)">`;
        }
    }
];

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async function () {
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 마스터 테이블 매니저
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'GroupID',
        onRowClick: (row, tr) => {
            selectGroup(row.GroupID, tr);
        },
        onSelectionChange: (selectedIds) => {
            updateMasterActionButtons(selectedIds);
        },
        onSort: (sortKey, sortDir) => {
            sortAndRenderMaster(sortKey, sortDir);
        },
        emptyMessage: '캠페인 데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    // 디테일 테이블 매니저
    detailTableManager = new TableManager('detail-table', {
        selectable: false,
        idKey: 'PlanID',
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
        emptyMessage: '상품이 없습니다.'
    });
    detailTableManager.renderHeader(detailColumns);

    // 패널 리사이즈 초기화
    initPanelResize('wpMasterDetail', 'panelResizeHandle');

    // 업로드 존 드래그앤드롭
    setupUploadZone();

    // 사용유형 로드
    loadTypes();

    // Enter 키 검색
    ['filterYearMonth', 'filterType', 'filterTitle'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyFilters();
            });
        }
    });

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

// ==================== 업로드 존 드래그앤드롭 ====================
function setupUploadZone() {
    const uploadZone = document.querySelector('.upload-zone');
    if (!uploadZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.style.borderColor = 'var(--accent)';
            uploadZone.style.background = 'rgba(99, 102, 241, 0.05)';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.style.borderColor = 'var(--border)';
            uploadZone.style.background = 'transparent';
        });
    });

    uploadZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = document.getElementById('fileInput');
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    });
}

// ==================== 마스터 패널 ====================
async function loadMasterData() {
    try {
        masterTableManager.showLoading(masterColumns.length);

        const params = { ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/withdrawal-plans/groups${queryString}`);
        const data = result.data || [];

        currentMasterData = data;
        masterDataMap = {};
        data.forEach(row => masterDataMap[row.GroupID] = row);

        document.getElementById('masterCount').textContent = `(${data.length}건)`;

        masterTableManager.render(data, masterColumns);
        applyMasterSelection();

        if (currentGroupId && !masterDataMap[currentGroupId]) {
            resetDetail();
        }

    } catch (e) {
        console.error('캠페인 목록 로드 실패:', e);
        showAlert('캠페인 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderMaster(sortKey, sortDir) {
    sortArray(currentMasterData, sortKey, sortDir);
    masterTableManager.render(currentMasterData, masterColumns);
    applyMasterSelection();
}

function applyMasterSelection() {
    if (!currentGroupId) return;
    document.querySelectorAll('#master-table tbody tr').forEach(tr => {
        if (tr.dataset.id == currentGroupId) {
            tr.classList.add('selected');
        }
    });
}

// ==================== 캠페인 선택 (마스터 행 클릭) ====================
function selectGroup(groupId, tr) {
    if (dirtyRows.size > 0 && groupId !== currentGroupId) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 캠페인을 전환하시겠습니까?', () => {
            dirtyRows.clear();
            updateSaveBar();
            doSelectGroup(groupId, tr);
        });
        return;
    }
    doSelectGroup(groupId, tr);
}

function doSelectGroup(groupId, tr) {
    document.querySelectorAll('#master-table tbody tr').forEach(r => r.classList.remove('selected'));
    if (tr) tr.classList.add('selected');

    currentGroupId = groupId;
    currentGroupData = masterDataMap[groupId];

    loadDetailData(currentGroupData);
}

// ==================== 디테일 패널 ====================
async function loadDetailData(group) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailContainer').style.display = 'flex';

        detailTableManager.showLoading(detailColumns.length);

        const result = await api.get(`/api/withdrawal-plans/groups/${group.GroupID}/items`);
        const items = result.data || [];

        currentDetailItems = items;
        document.getElementById('detailItemCount').textContent = `(${items.length}건)`;

        renderGroupSummary(group);

        // 원본 데이터 저장
        originalData = {};
        items.forEach(item => {
            originalData[item.PlanID] = {
                PlannedQty: item.PlannedQty || 0,
                Notes: item.Notes || ''
            };
        });

        dirtyRows.clear();
        updateSaveBar();

        detailTableManager.render(items, detailColumns);

    } catch (e) {
        console.error('상품 목록 로드 실패:', e);
        showAlert('상품 목록 로드 실패: ' + e.message, 'error');
    }
}

function sortAndRenderDetail(sortKey, sortDir) {
    sortArray(currentDetailItems, sortKey, sortDir);
    detailTableManager.render(currentDetailItems, detailColumns);
}

function renderGroupSummary(group) {
    const dateRange = group.StartDate === group.EndDate
        ? group.StartDate
        : `${group.StartDate} ~ ${group.EndDate}`;

    document.getElementById('groupSummary').innerHTML = `
        <div class="group-summary-title">
            <i class="fa-solid fa-chart-bar" style="color:var(--accent);"></i>
            <span class="type-badge ${escapeHtml(group.Type)}">${escapeHtml(group.Type)}</span>
            ${escapeHtml(group.Title)} 요약
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">그룹ID</span>
                <span class="summary-value">${group.GroupID}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">기간</span>
                <span class="summary-value">${dateRange}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">상품 수</span>
                <span class="summary-value">${group.ItemCount}개</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">총 수량</span>
                <span class="summary-value">${(group.TotalQty || 0).toLocaleString()}</span>
            </div>
        </div>
    `;
}

function resetDetail() {
    currentGroupId = null;
    currentGroupData = null;
    originalData = {};
    dirtyRows.clear();
    currentDetailItems = [];

    document.getElementById('detailPlaceholder').style.display = 'flex';
    document.getElementById('detailContainer').style.display = 'none';
    document.getElementById('groupSummary').innerHTML = '';
    updateSaveBar();
}

// ==================== 인라인 편집 ====================
function onInlineFocus(input) {
    const raw = input.value.replace(/,/g, '');
    input.value = raw;
    input.select();
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
    if (field === 'PlannedQty') {
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
            if (f === 'PlannedQty') {
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
            PlanID: id,
            PlannedQty: data.PlannedQty,
            Notes: data.Notes
        });
    });

    try {
        const result = await api.put('/api/withdrawal-plans/bulk-update', { items });
        showAlert(`${result.updated}건이 저장되었습니다.`, 'success');

        // 원본 데이터 업데이트
        items.forEach(item => {
            originalData[item.PlanID] = {
                PlannedQty: item.PlannedQty,
                Notes: item.Notes
            };
            const detailItem = currentDetailItems.find(d => d.PlanID === item.PlanID);
            if (detailItem) {
                detailItem.PlannedQty = item.PlannedQty;
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

    const yearMonth = document.getElementById('filterYearMonth').value;
    const type = document.getElementById('filterType').value;
    const title = document.getElementById('filterTitle').value.trim();

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (type) currentFilters.type = type;
    if (title) currentFilters.title = title;

    resetDetail();
    loadMasterData();
}

function resetFilters() {
    document.getElementById('filterYearMonth').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterTitle').value = '';

    currentFilters = {};
    resetDetail();
    loadMasterData();
}

// ==================== 사용유형 로드 ====================
async function loadTypes() {
    try {
        const result = await api.get('/api/withdrawal-plans/types');
        const types = result.types || [];
        const select = document.getElementById('filterType');
        select.innerHTML = '<option value="">전체</option>';
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('사용유형 로드 실패:', e);
    }
}

// ==================== 캠페인 삭제 ====================
function deleteGroup() {
    if (!currentGroupId || !currentGroupData) {
        showAlert('삭제할 캠페인을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(
        `"${currentGroupData.Title}" 캠페인의 모든 상품(${currentGroupData.ItemCount}건)을 삭제하시겠습니까?`,
        async () => {
            try {
                await api.post('/api/withdrawal-plans/groups/delete', { group_id: currentGroupId });
                showAlert('삭제 완료', 'success');
                resetDetail();
                loadMasterData();
            } catch (e) {
                showAlert('삭제 실패: ' + e.message, 'error');
            }
        }
    );
}

// ==================== 엑셀 다운로드 ====================
function downloadTemplate() {
    window.location.href = '/api/withdrawal-plans/download';
}

function downloadEditForm() {
    const selectedIds = masterTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('수정할 캠페인을 선택해주세요.', 'warning');
        return;
    }

    const params = { group_ids: selectedIds.join(',') };
    const queryString = api.buildQueryString(params);
    window.location.href = `/api/withdrawal-plans/download${queryString}`;
}

// ==================== 업로드 ====================
function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('uploadButton').disabled = true;

    const uploadZone = document.querySelector('.upload-zone');
    if (uploadZone) {
        uploadZone.style.borderColor = 'var(--border)';
        uploadZone.style.background = 'transparent';
    }

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
        const response = await fetch('/api/withdrawal-plans/upload', {
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
        document.getElementById('uploadTotalRows').textContent = result.total_rows || 0;
        document.getElementById('resultInserted').textContent = result.inserted || 0;
        document.getElementById('resultUpdated').textContent = result.updated || 0;

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
    } finally {
        document.getElementById('uploadButton').disabled = false;
    }
}

