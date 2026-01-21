let masterTableManager, detailTableManager, paginationManager;
let addBOMModal, addChildModal, bulkEditParentModal, bulkEditChildModal;
let currentFilters = {};
let currentParentBoxID = null;
let currentParentERPCode = null;
let childRowCounter = 0;

// 마스터 테이블 컬럼 (세트 제품)
const masterColumns = [
    { key: 'BoxID', header: 'BOMID', render: (row) => row.BoxID }, // BoxID가 BOMID 역할
    { key: 'ERPCode', header: '품목코드', render: (row) => row.ERPCode || '-' },
    { key: 'Name', header: '제품명', render: (row) => row.Name || '-' },
    { key: 'ChildCount', header: '구성품 수', render: (row) => row.ChildCount || 0 }
];

// 디테일 테이블 컬럼 (구성품)
const detailColumns = [
    { key: 'BOMID', header: 'BOMID', render: (row) => row.BOMID },
    { key: 'ChildERPCode', header: '품목코드', render: (row) => row.ChildERPCode || '-' },
    { key: 'ChildName', header: '제품명', render: (row) => row.ChildName || '-' },
    { key: 'QuantityRequired', header: '소요수량', render: (row) => row.QuantityRequired || 0 }
];

document.addEventListener('DOMContentLoaded', async function () {
    // 모달 초기화
    addBOMModal = new ModalManager('addBOMModal');
    addChildModal = new ModalManager('addChildModal');
    bulkEditParentModal = new ModalManager('bulkEditParentModal');
    bulkEditChildModal = new ModalManager('bulkEditChildModal');

    // 테이블 매니저 초기화
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'BoxID',
        onSelectionChange: (selectedIds) => updateActionButtons(selectedIds),
        onRowClick: (row, tr) => selectParent(row, tr),
        emptyMessage: '데이터가 없습니다.'
    });

    detailTableManager = new TableManager('detail-table', {
        selectable: true,
        idKey: 'BOMID',
        onSelectionChange: (selectedIds) => updateChildActionButtons(selectedIds),
        emptyMessage: '구성품이 없습니다.'
    });

    // 페이지네이션 매니저 초기화
    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadParents(page, limit),
        onLimitChange: (page, limit) => loadParents(page, limit)
    });

    // 초기 데이터 로드
    await loadMetadata();
    loadParents(1, 20);

    // 엔터키 검색 지원
    ['filterParentERP', 'filterParentName', 'filterChildERP', 'filterChildName'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyFilters();
            });
        }
    });
});

async function loadParents(page = 1, limit = 20) {
    try {
        masterTableManager.showLoading(5);

        const params = { page, limit, ...currentFilters };
        const queryString = api.buildQueryString(params);
        const res = await api.get(`/api/bom/parents${queryString}`);

        // 필터링 카운트 표시
        const isFiltered = Object.keys(currentFilters).length > 0;
        if (isFiltered) {
            document.getElementById('totalCount').textContent = `전체 ${res.total}개`;
            document.getElementById('filteredCount').textContent = `필터링됨: ${res.data.length}개`;
        } else {
            document.getElementById('totalCount').textContent = `총 ${res.total}개`;
            document.getElementById('filteredCount').textContent = '';
        }

        masterTableManager.render(res.data, masterColumns);

        paginationManager.render({
            page: page,
            limit: limit,
            total: res.total,
            total_pages: Math.ceil(res.total / limit)
        });

    } catch (e) {
        showAlert('세트 제품 로드 실패: ' + e.message, 'error');
        masterTableManager.render([], masterColumns);
    }
}

async function selectParent(row, tr) {
    // 행 선택 스타일 처리
    const rows = document.querySelectorAll('#master-table tbody tr');
    rows.forEach(r => r.classList.remove('selected'));
    tr.classList.add('selected');

    currentParentBoxID = row.BoxID;
    currentParentERPCode = row.ERPCode;
    loadChildren(currentParentBoxID);
}

async function loadChildren(parentBoxId) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('childTableContainer').style.display = 'block';
        document.getElementById('childActionButtons').style.display = 'flex';
        document.getElementById('childCount').style.display = 'block';

        detailTableManager.showLoading(4);
        const res = await api.get(`/api/bom/children/${parentBoxId}`);

        document.getElementById('childCount').textContent = `구성품 ${res.data.length}개`;
        detailTableManager.render(res.data, detailColumns);

    } catch (e) {
        showAlert('구성품 로드 실패: ' + e.message, 'error');
        detailTableManager.render([], detailColumns);
    }
}

async function loadMetadata() {
    try {
        const res = await api.get('/api/bom/metadata');

        const setupDatalist = (listId, items) => {
            const el = document.getElementById(listId);
            if (el) {
                el.innerHTML = items.map(item => `<option value="${item}">`).join('');
            }
        };

        setupDatalist('parentERPList', res.parent_erp_codes);
        setupDatalist('parentNameList', res.parent_names);
        setupDatalist('childERPList', res.child_erp_codes);
        setupDatalist('childNameList', res.child_names);

    } catch (e) {
        console.error('메타데이터 로드 실패:', e);
    }
}

function applyFilters() {
    currentFilters = {};
    const parentERP = document.getElementById('filterParentERP').value.trim();
    const parentName = document.getElementById('filterParentName').value.trim();
    const childERP = document.getElementById('filterChildERP').value.trim();
    const childName = document.getElementById('filterChildName').value.trim();

    if (parentERP) currentFilters.parent_erp = parentERP;
    if (parentName) currentFilters.parent_name = parentName;
    if (childERP) currentFilters.child_erp = childERP;
    if (childName) currentFilters.child_name = childName;

    // 디테일 초기화
    currentParentBoxID = null;
    currentParentERPCode = null;
    document.getElementById('detailPlaceholder').style.display = 'block';
    document.getElementById('childTableContainer').style.display = 'none';
    document.getElementById('childActionButtons').style.display = 'none';
    document.getElementById('childCount').style.display = 'none';
    detailTableManager.render([], detailColumns);

    loadParents(1, paginationManager.getLimit());
}

function resetFilters() {
    document.getElementById('filterParentERP').value = '';
    document.getElementById('filterParentName').value = '';
    document.getElementById('filterChildERP').value = '';
    document.getElementById('filterChildName').value = '';
    currentFilters = {};

    applyFilters();
}

function updateActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('editButton');
    const deleteBtn = document.getElementById('deleteButton');

    if (hasSelection) {
        editBtn.classList.remove('btn-disabled');
        deleteBtn.classList.remove('btn-disabled');
        editBtn.disabled = false;
        deleteBtn.disabled = false;
    } else {
        editBtn.classList.add('btn-disabled');
        deleteBtn.classList.add('btn-disabled');
        editBtn.disabled = true;
        deleteBtn.disabled = true;
    }
}

function updateChildActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('editChildButton');
    const deleteBtn = document.getElementById('deleteChildButton');

    if (hasSelection) {
        editBtn.classList.remove('btn-disabled');
        deleteBtn.classList.remove('btn-disabled');
        editBtn.disabled = false;
        deleteBtn.disabled = false;
    } else {
        editBtn.classList.add('btn-disabled');
        deleteBtn.classList.add('btn-disabled');
        editBtn.disabled = true;
        deleteBtn.disabled = true;
    }
}

function selectAllData() {
    showConfirm('현재 필터 조건의 모든 데이터를 선택하시겠습니까?', async () => {
        try {
            const params = { limit: 10000, ...currentFilters };
            const queryString = api.buildQueryString(params);
            const res = await api.get(`/api/bom/parents${queryString}`);

            res.data.forEach(p => masterTableManager.selectedRows.add(p.BoxID.toString()));

            // 현재 화면 체크박스 업데이트
            const checkboxes = document.querySelectorAll('#master-table .row-checkbox');
            checkboxes.forEach(cb => {
                if (masterTableManager.selectedRows.has(cb.dataset.id)) {
                    cb.checked = true;
                }
            });

            updateActionButtons(Array.from(masterTableManager.selectedRows));
            showAlert(`${masterTableManager.selectedRows.size}개의 세트 제품이 선택되었습니다.`, 'success');
        } catch (e) {
            showAlert('전체 선택 실패: ' + e.message, 'error');
        }
    });
}

// ========== 모달 관련 함수들 ==========

function showAddBOMModal() {
    document.getElementById('bomParentERP').value = '';
    document.getElementById('childRowsContainer').innerHTML = '';
    childRowCounter = 0;
    addChildRow();
    addBOMModal.show();
}

function closeAddBOMModal() {
    addBOMModal.hide();
}

function addChildRow() {
    const container = document.getElementById('childRowsContainer');
    const rowId = `childRow_${childRowCounter++}`;

    const rowDiv = document.createElement('div');
    rowDiv.id = rowId;
    rowDiv.className = 'form-group';
    rowDiv.style.cssText = 'display:grid;grid-template-columns:1fr 120px 40px;gap:12px;align-items:end;padding:12px;background:rgba(0,0,0,0.02);border-radius:8px;margin-bottom:12px;';

    rowDiv.innerHTML = `
        <div>
            <label class="form-label required">자식 품목코드</label>
            <input type="text" class="form-input child-erp" list="childERPList" placeholder="예: PART-001" required>
        </div>
        <div>
            <label class="form-label">소요수량</label>
            <input type="number" class="form-input child-quantity" value="1" step="0.01" min="0.01">
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeChildRow('${rowId}')" style="height:38px;">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;

    container.appendChild(rowDiv);
}

// window 객체에 할당해야 HTML onclick에서 접근 가능 (모듈 스코프 문제 해결)
window.addChildRow = addChildRow;
window.removeChildRow = function (rowId) {
    const row = document.getElementById(rowId);
    if (row) row.remove();
    const container = document.getElementById('childRowsContainer');
    if (container.children.length === 0) addChildRow();
};

async function saveBOM() {
    const parentERP = document.getElementById('bomParentERP').value.trim();
    if (!parentERP) {
        showAlert('부모 품목코드는 필수입니다.', 'error');
        return;
    }

    const childERPs = document.querySelectorAll('.child-erp');
    const childQuantities = document.querySelectorAll('.child-quantity');
    const children = [];

    for (let i = 0; i < childERPs.length; i++) {
        const childERP = childERPs[i].value.trim();
        const quantity = parseFloat(childQuantities[i].value) || 1;

        if (!childERP) {
            showAlert(`${i + 1}번째 구성품의 품목코드를 입력하세요.`, 'error');
            return;
        }

        children.push({
            ParentERPCode: parentERP,
            ChildERPCode: childERP,
            QuantityRequired: quantity
        });
    }

    if (children.length === 0) {
        showAlert('최소 1개 이상의 구성품이 필요합니다.', 'error');
        return;
    }

    let successCount = 0;
    let failCount = 0;
    const errors = [];

    for (let i = 0; i < children.length; i++) {
        const child = children[i];
        try {
            await api.post('/api/bom', child);
            successCount++;
        } catch (e) {
            failCount++;
            errors.push(`${child.ChildERPCode}: ${e.message}`);
        }
    }

    if (successCount > 0) {
        showAlert(`BOM이 추가되었습니다. (성공: ${successCount}개, 실패: ${failCount}개)`, failCount > 0 ? 'warning' : 'success');
        closeAddBOMModal();
        loadParents(paginationManager.getCurrentPage(), paginationManager.getLimit());
    } else {
        showAlert(`BOM 추가 실패:\n${errors.join('\n')}`, 'error');
    }
}

function showAddChildModal() {
    if (!currentParentBoxID) {
        showAlert('세트 제품을 먼저 선택하세요.', 'warning');
        return;
    }
    document.getElementById('childERP').value = '';
    document.getElementById('childQuantity').value = '1';
    addChildModal.show();
}

function closeAddChildModal() {
    addChildModal.hide();
}

async function saveChild() {
    const childERP = document.getElementById('childERP').value.trim();
    if (!childERP) {
        showAlert('자식 품목코드는 필수입니다.', 'error');
        return;
    }

    const data = {
        ParentERPCode: currentParentERPCode,
        ChildERPCode: childERP,
        QuantityRequired: parseFloat(document.getElementById('childQuantity').value) || 1
    };

    try {
        await api.post('/api/bom', data);
        showAlert('구성품이 추가되었습니다.', 'success');
        closeAddChildModal();
        loadChildren(currentParentBoxID);
        loadParents(paginationManager.getCurrentPage(), paginationManager.getLimit()); // 자식 수 업데이트
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

async function bulkEdit() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    // 첫 번째 선택된 항목의 자식 정보를 가져와서 현재 값 표시 (대표값)
    const firstId = selectedIds[0];
    try {
        const res = await api.get(`/api/bom/children/${firstId}`);
        const firstChild = res.data[0];

        document.getElementById('bulkEditParentCount').textContent = selectedIds.length;
        document.getElementById('currentParentQuantity').textContent = firstChild ? firstChild.QuantityRequired : '(없음)';
        document.getElementById('bulkParentQuantity').value = '';

        bulkEditParentModal.show();
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditParentModal() {
    bulkEditParentModal.hide();
}

async function saveBulkEditParent() {
    const newQuantity = document.getElementById('bulkParentQuantity').value;
    if (!newQuantity) {
        showAlert('소요수량을 입력하세요.', 'warning');
        return;
    }

    const quantity = parseFloat(newQuantity);
    if (isNaN(quantity) || quantity <= 0) {
        showAlert('올바른 숫자를 입력하세요.', 'error');
        return;
    }

    const selectedIds = masterTableManager.getSelectedRows();
    try {
        const updatePromises = [];
        for (const boxId of selectedIds) {
            const res = await api.get(`/api/bom/children/${boxId}`);
            const bomIds = res.data.map(child => child.BOMID);
            bomIds.forEach(bomId => {
                updatePromises.push(api.put(`/api/bom/${bomId}`, { QuantityRequired: quantity }));
            });
        }

        await Promise.all(updatePromises);
        showAlert(`${selectedIds.length}개 세트 제품의 구성품 소요수량이 변경되었습니다.`, 'success');
        closeBulkEditParentModal();
        masterTableManager.clearSelection();
        loadParents(paginationManager.getCurrentPage(), paginationManager.getLimit());
        if (currentParentBoxID) loadChildren(currentParentBoxID);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개 세트 제품의 모든 BOM을 삭제하시겠습니까?`, async () => {
        try {
            const deletePromises = [];
            for (const boxId of selectedIds) {
                const res = await api.get(`/api/bom/children/${boxId}`);
                const bomIds = res.data.map(child => child.BOMID);
                if (bomIds.length > 0) {
                    deletePromises.push(api.post('/api/bom/bulk-delete', { ids: bomIds }));
                }
            }

            await Promise.all(deletePromises);
            showAlert('선택한 세트 제품의 BOM이 삭제되었습니다.', 'success');
            masterTableManager.clearSelection();
            loadParents(paginationManager.getCurrentPage(), paginationManager.getLimit());

            if (selectedIds.includes(currentParentBoxID?.toString())) {
                currentParentBoxID = null;
                currentParentERPCode = null;
                document.getElementById('detailPlaceholder').style.display = 'block';
                document.getElementById('childTableContainer').style.display = 'none';
            }
        } catch (e) {
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

async function bulkEditChildren() {
    const selectedIds = detailTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    const firstId = selectedIds[0];
    try {
        const bom = await api.get(`/api/bom/${firstId}`);
        document.getElementById('bulkEditChildCount').textContent = selectedIds.length;
        document.getElementById('currentChildERP').textContent = bom.ChildERPCode || '(없음)';
        document.getElementById('currentChildQuantity').textContent = bom.QuantityRequired || '(없음)';
        document.getElementById('bulkChildERP').value = '';
        document.getElementById('bulkChildQuantity').value = '';

        bulkEditChildModal.show();
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditChildModal() {
    bulkEditChildModal.hide();
}

async function saveBulkEditChild() {
    const selectedIds = detailTableManager.getSelectedRows();
    const newChildERP = document.getElementById('bulkChildERP').value.trim();
    const newQuantity = document.getElementById('bulkChildQuantity').value;

    if (!newChildERP && !newQuantity) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = selectedIds.map(async bomId => {
            const bom = await api.get(`/api/bom/${bomId}`);
            const updateData = {
                ParentProductBoxID: bom.ParentProductBoxID,
                ChildProductBoxID: bom.ChildProductBoxID,
                QuantityRequired: newQuantity ? parseFloat(newQuantity) : bom.QuantityRequired
            };

            if (newChildERP) {
                const boxRes = await api.get(`/api/productboxes?erp_code=${newChildERP}`);
                if (boxRes.data && boxRes.data.length > 0) {
                    updateData.ChildProductBoxID = boxRes.data[0].BoxID;
                } else {
                    throw new Error(`품목코드를 찾을 수 없습니다: ${newChildERP}`);
                }
            }

            return api.put(`/api/bom/${bomId}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedIds.length}개 구성품이 수정되었습니다.`, 'success');
        closeBulkEditChildModal();
        detailTableManager.clearSelection();
        loadChildren(currentParentBoxID);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDeleteChildren() {
    const selectedIds = detailTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개의 구성품을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/bom/bulk-delete', { ids: selectedIds.map(id => parseInt(id)) });
            showAlert(`${selectedIds.length}개 구성품이 삭제되었습니다.`, 'success');
            detailTableManager.clearSelection();
            loadChildren(currentParentBoxID);
            loadParents(paginationManager.getCurrentPage(), paginationManager.getLimit());
        } catch (e) {
            showAlert('일괄 삭제 실패: ' + e.message, 'error');
        }
    });
}
