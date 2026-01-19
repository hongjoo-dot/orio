let currentPage = 1;
let limit = 20;
let currentFilters = {};
let selectedIds = new Set();
let selectedChildIds = new Set();
let currentParentBoxID = null;
let currentParentERPCode = null;

document.addEventListener('DOMContentLoaded', async function () {
    await loadParents();
    await loadMetadata();
});

async function loadParents() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: limit,
            ...currentFilters
        });

        const res = await api.get(`/api/bom/parents?${params}`);

        const isFiltered = Object.keys(currentFilters).length > 0;
        if (isFiltered) {
            document.getElementById('totalCount').textContent = `전체 ${res.total}개`;
            document.getElementById('filteredCount').textContent = `필터링됨: ${res.data.length}개`;
        } else {
            document.getElementById('totalCount').textContent = `총 ${res.total}개`;
            document.getElementById('filteredCount').textContent = '';
        }

        const tbody = document.getElementById('parentTableBody');
        tbody.innerHTML = '';

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:2rem;color:var(--text-muted);">데이터가 없습니다</td></tr>';
        } else {
            res.data.forEach(parent => {
                const tr = document.createElement('tr');
                if (selectedIds.has(parent.BoxID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedIds.has(parent.BoxID) ? 'checked' : ''} onchange="toggleSelect(${parent.BoxID}, event)"></td>
                    <td>${parent.FirstBOMID || ''}</td>
                    <td>${parent.ERPCode || ''}</td>
                    <td>${parent.Name || ''}</td>
                    <td>${parent.ChildCount || 0}</td>
                `;

                tr.style.cursor = 'pointer';
                tr.onclick = (e) => selectParent(parent.BoxID, parent.ERPCode, e);
                tbody.appendChild(tr);
            });
        }

        renderPagination(res.total, res.page, res.limit);
        updateBulkButtons();
    } catch (e) {
        showAlert('세트 제품 로드 실패: ' + e.message, 'error');
    }
}

function selectParent(boxId, erpCode, event) {
    if (event.target.type === 'checkbox' || event.target.tagName === 'BUTTON' || event.target.tagName === 'I') return;

    currentParentBoxID = boxId;
    currentParentERPCode = erpCode;

    const rows = document.querySelectorAll('#parentTable tbody tr');
    rows.forEach(r => r.style.background = '');
    event.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)';

    loadChildren(boxId);
}

async function loadChildren(parentBoxId) {
    try {
        const res = await api.get(`/api/bom/children/${parentBoxId}`);
        console.log('구성품 로드:', res);

        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('childTableContainer').style.display = 'block';
        document.getElementById('childActionButtons').style.display = 'flex';
        document.getElementById('childCount').style.display = 'block';

        const tbody = document.getElementById('childTableBody');
        tbody.innerHTML = '';
        selectedChildIds.clear();

        document.getElementById('childCount').textContent = `구성품 ${res.data.length}개`;

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:2rem;color:var(--text-muted);">구성품이 없습니다</td></tr>';
        } else {
            res.data.forEach(child => {
                const tr = document.createElement('tr');
                if (selectedChildIds.has(child.BOMID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedChildIds.has(child.BOMID) ? 'checked' : ''} onchange="toggleSelectChild(${child.BOMID}, event)"></td>
                    <td>${child.BOMID || ''}</td>
                    <td>${child.ChildERPCode || ''}</td>
                    <td>${child.ChildName || ''}</td>
                    <td>${child.QuantityRequired || 0}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        updateChildBulkButtons();
    } catch (e) {
        showAlert('구성품 로드 실패: ' + e.message, 'error');
    }
}

function changeLimit() {
    limit = parseInt(document.getElementById('limitSelector').value);
    currentPage = 1;
    loadParents();
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

    currentPage = 1;
    loadParents();
}

function resetFilters() {
    document.getElementById('filterParentERP').value = '';
    document.getElementById('filterParentName').value = '';
    document.getElementById('filterChildERP').value = '';
    document.getElementById('filterChildName').value = '';
    currentFilters = {};
    currentPage = 1;

    // 디테일 영역 초기화
    currentParentBoxID = null;
    currentParentERPCode = null;
    selectedChildIds.clear();
    const placeholder = document.getElementById('detailPlaceholder');
    placeholder.style.display = 'block';
    placeholder.style.textAlign = 'center';
    document.getElementById('childTableContainer').style.display = 'none';
    document.getElementById('childActionButtons').style.display = 'none';
    document.getElementById('childCount').style.display = 'none';

    loadParents();
}

function renderPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const paginationDiv = document.getElementById('pagination');
    paginationDiv.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
    prevBtn.className = 'btn btn-sm btn-secondary';
    prevBtn.disabled = page === 1;
    prevBtn.onclick = () => changePage(page - 1);
    paginationDiv.appendChild(prevBtn);

    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);

    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === page ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
        btn.onclick = () => changePage(i);
        paginationDiv.appendChild(btn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
    nextBtn.className = 'btn btn-sm btn-secondary';
    nextBtn.disabled = page === totalPages || totalPages === 0;
    nextBtn.onclick = () => changePage(page + 1);
    paginationDiv.appendChild(nextBtn);
}

function changePage(page) {
    currentPage = page;
    loadParents();
}

function toggleSelect(id, event) {
    event.stopPropagation();
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    updateBulkButtons();

    const row = Array.from(document.querySelectorAll('#parentTable tbody tr')).find(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        return checkbox && checkbox.onchange && checkbox.onchange.toString().includes(id);
    });
    if (row) {
        row.classList.toggle('selected', selectedIds.has(id));
    }

    const allRows = document.querySelectorAll('#parentTable tbody tr');
    document.getElementById('selectAll').checked = selectedIds.size > 0 && selectedIds.size === allRows.length;
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    const rows = document.querySelectorAll('#parentTable tbody tr');

    rows.forEach(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.onchange) {
            const onchangeStr = checkbox.onchange.toString();
            const match = onchangeStr.match(/toggleSelect\((\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                if (checked) {
                    selectedIds.add(id);
                    r.classList.add('selected');
                    checkbox.checked = true;
                } else {
                    selectedIds.delete(id);
                    r.classList.remove('selected');
                    checkbox.checked = false;
                }
            }
        }
    });

    updateBulkButtons();
}

async function selectAllData() {
    showConfirm('현재 필터 조건의 모든 데이터를 선택하시겠습니까?', async () => {
        try {
            const params = new URLSearchParams({
                limit: 10000,
                ...currentFilters
            });

            const res = await api.get(`/api/bom/parents?${params}`);

            selectedIds.clear();
            res.data.forEach(parent => selectedIds.add(parent.BoxID));

            document.querySelectorAll('#parentTable tbody tr').forEach(r => {
                const checkbox = r.querySelector('input[type="checkbox"]');
                if (checkbox && checkbox.onchange) {
                    const onchangeStr = checkbox.onchange.toString();
                    const match = onchangeStr.match(/toggleSelect\((\d+)/);
                    if (match) {
                        const id = parseInt(match[1]);
                        if (selectedIds.has(id)) {
                            r.classList.add('selected');
                            checkbox.checked = true;
                        }
                    }
                }
            });

            document.getElementById('selectAll').checked = true;
            updateBulkButtons();

            showAlert(`${selectedIds.size}개의 세트 제품이 선택되었습니다.`, 'success');
        } catch (e) {
            showAlert('전체 선택 실패: ' + e.message, 'error');
        }
    });
}

function updateBulkButtons() {
    const hasSelection = selectedIds.size > 0;
    const editBtn = document.getElementById('editButton');
    const deleteBtn = document.getElementById('deleteButton');

    editBtn.disabled = !hasSelection;
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
}

let childRowCounter = 0;

function showAddBOMModal() {
    document.getElementById('bomParentERP').value = '';
    document.getElementById('childRowsContainer').innerHTML = '';
    childRowCounter = 0;

    // 초기 구성품 행 1개 추가
    addChildRow();

    document.getElementById('addBOMModal').classList.add('show');
}

function closeAddBOMModal() {
    document.getElementById('addBOMModal').classList.remove('show');
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

function removeChildRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
    }

    // 최소 1개는 유지
    const container = document.getElementById('childRowsContainer');
    if (container.children.length === 0) {
        addChildRow();
    }
}

async function saveBOM() {
    const parentERP = document.getElementById('bomParentERP').value.trim();

    if (!parentERP) {
        showAlert('부모 품목코드는 필수입니다.', 'error');
        return;
    }

    // 구성품 수집
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

    console.log('BOM 추가 시작:', children);

    let successCount = 0;
    let failCount = 0;
    const errors = [];

    // 각 구성품을 순차적으로 추가하여 개별 결과 확인
    for (let i = 0; i < children.length; i++) {
        const child = children[i];
        try {
            console.log(`[${i + 1}/${children.length}] BOM 추가 시도:`, child);
            const response = await api.post('/api/bom', child);
            console.log(`[${i + 1}/${children.length}] BOM 추가 성공:`, response);
            successCount++;
        } catch (e) {
            console.error(`[${i + 1}/${children.length}] BOM 추가 실패:`, e);
            failCount++;
            errors.push(`${child.ChildERPCode}: ${e.message}`);
        }
    }

    // 결과 표시
    if (successCount > 0) {
        showAlert(`BOM이 추가되었습니다. (성공: ${successCount}개, 실패: ${failCount}개)`, failCount > 0 ? 'warning' : 'success');
        closeAddBOMModal();
        loadParents();
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
    document.getElementById('addChildModal').classList.add('show');
}

function closeAddChildModal() {
    document.getElementById('addChildModal').classList.remove('show');
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
        const response = await api.post('/api/bom', data);
        console.log('BOM 추가 성공:', response);
        showAlert('구성품이 추가되었습니다.', 'success');
        closeAddChildModal();
        loadChildren(currentParentBoxID);
        loadParents(); // Refresh to update child count
    } catch (e) {
        // 에러 메시지를 더 명확하게 표시
        console.error('BOM 추가 실패:', e);
        const errorMessage = e.message || '저장 실패';
        showAlert(errorMessage, 'error');
    }
}

function toggleSelectChild(id, event) {
    event.stopPropagation();
    if (selectedChildIds.has(id)) {
        selectedChildIds.delete(id);
    } else {
        selectedChildIds.add(id);
    }
    updateChildBulkButtons();

    const row = Array.from(document.querySelectorAll('#childTable tbody tr')).find(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        return checkbox && checkbox.onchange && checkbox.onchange.toString().includes(id);
    });
    if (row) {
        row.classList.toggle('selected', selectedChildIds.has(id));
    }

    const allRows = document.querySelectorAll('#childTable tbody tr');
    document.getElementById('selectAllChildren').checked = selectedChildIds.size > 0 && selectedChildIds.size === allRows.length;
}

function toggleSelectAllChildren() {
    const checked = document.getElementById('selectAllChildren').checked;
    const rows = document.querySelectorAll('#childTable tbody tr');

    rows.forEach(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.onchange) {
            const onchangeStr = checkbox.onchange.toString();
            const match = onchangeStr.match(/toggleSelectChild\((\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                if (checked) {
                    selectedChildIds.add(id);
                    r.classList.add('selected');
                    checkbox.checked = true;
                } else {
                    selectedChildIds.delete(id);
                    r.classList.remove('selected');
                    checkbox.checked = false;
                }
            }
        }
    });

    updateChildBulkButtons();
}

function updateChildBulkButtons() {
    const hasSelection = selectedChildIds.size > 0;
    const editBtn = document.getElementById('editChildButton');
    const deleteBtn = document.getElementById('deleteChildButton');

    editBtn.disabled = !hasSelection;
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
}

async function bulkEditChildren() {
    if (selectedChildIds.size === 0) return;

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedChildIds)[0];
    try {
        const bom = await api.get(`/api/bom/${firstId}`);

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditChildCount').textContent = selectedChildIds.size;
        document.getElementById('currentChildERP').textContent = bom.ChildERPCode || '(없음)';
        document.getElementById('currentChildQuantity').textContent = bom.QuantityRequired || '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkChildERP').value = '';
        document.getElementById('bulkChildQuantity').value = '';

        // 모달 열기
        document.getElementById('bulkEditChildModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditChildModal() {
    document.getElementById('bulkEditChildModal').classList.remove('show');
}

async function saveBulkEditChild() {
    const newChildERP = document.getElementById('bulkChildERP').value.trim();
    const newQuantity = document.getElementById('bulkChildQuantity').value;

    // 변경할 값이 없으면 경고
    if (!newChildERP && !newQuantity) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = Array.from(selectedChildIds).map(async bomId => {
            const bom = await api.get(`/api/bom/${bomId}`);
            const updateData = {
                ParentProductBoxID: bom.ParentProductBoxID,
                ChildProductBoxID: bom.ChildProductBoxID,
                QuantityRequired: newQuantity ? parseFloat(newQuantity) : bom.QuantityRequired
            };

            // ChildERPCode가 변경된 경우, 새 ChildProductBoxID를 찾아야 함
            if (newChildERP) {
                // ERPCode로 BoxID 조회
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
        showAlert(`${selectedChildIds.size}개 구성품이 수정되었습니다.`, 'success');
        closeBulkEditChildModal();
        selectedChildIds.clear();
        loadChildren(currentParentBoxID);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDeleteChildren() {
    if (selectedChildIds.size === 0) return;

    showConfirm(`선택한 ${selectedChildIds.size}개의 구성품을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/bom/bulk-delete', { ids: Array.from(selectedChildIds) });
            showAlert(`${selectedChildIds.size}개 구성품이 삭제되었습니다.`, 'success');
            selectedChildIds.clear();
            loadChildren(currentParentBoxID);
            loadParents(); // Refresh to update child count
        } catch (e) {
            showAlert('일괄 삭제 실패: ' + e.message, 'error');
        }
    });
}

async function bulkEdit() {
    if (selectedIds.size === 0) return;

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedIds)[0];
    try {
        const res = await api.get(`/api/bom/children/${firstId}`);
        const firstChild = res.data[0];

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditParentCount').textContent = selectedIds.size;
        document.getElementById('currentParentQuantity').textContent = firstChild ? firstChild.QuantityRequired : '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkParentQuantity').value = '';

        // 모달 열기
        document.getElementById('bulkEditParentModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditParentModal() {
    document.getElementById('bulkEditParentModal').classList.remove('show');
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

    try {
        // For each selected parent, get all child BOMIDs and update them
        const updatePromises = [];
        for (const boxId of selectedIds) {
            const res = await api.get(`/api/bom/children/${boxId}`);
            const bomIds = res.data.map(child => child.BOMID);

            bomIds.forEach(bomId => {
                updatePromises.push(
                    api.put(`/api/bom/${bomId}`, { QuantityRequired: quantity })
                );
            });
        }

        await Promise.all(updatePromises);
        showAlert(`${selectedIds.size}개 세트 제품의 구성품 소요수량이 변경되었습니다.`, 'success');

        closeBulkEditParentModal();
        selectedIds.clear();
        loadParents();

        // 현재 선택된 세트의 구성품도 새로고침
        if (currentParentBoxID) {
            loadChildren(currentParentBoxID);
        }
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    if (selectedIds.size === 0) return;

    showConfirm(`선택한 ${selectedIds.size}개 세트 제품의 모든 BOM을 삭제하시겠습니까?`, async () => {
        try {
            // For each selected parent, get all child BOMIDs and delete them
            const deletePromises = [];
            for (const boxId of selectedIds) {
                const res = await api.get(`/api/bom/children/${boxId}`);
                const bomIds = res.data.map(child => child.BOMID);

                if (bomIds.length > 0) {
                    deletePromises.push(
                        api.post('/api/bom/bulk-delete', { ids: bomIds })
                    );
                }
            }

            await Promise.all(deletePromises);
            showAlert('선택한 세트 제품의 BOM이 삭제되었습니다.', 'success');

            selectedIds.clear();
            loadParents();

            if (selectedIds.has(currentParentBoxID)) {
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

async function loadMetadata() {
    try {
        const res = await api.get('/api/bom/metadata');

        // Parent ERP Codes
        const parentERPOptions = res.parent_erp_codes.map(erp => `<option value="${erp}">`).join('');
        document.getElementById('parentERPList').innerHTML = parentERPOptions;

        // Parent Names
        const parentNameOptions = res.parent_names.map(name => `<option value="${name}">`).join('');
        document.getElementById('parentNameList').innerHTML = parentNameOptions;

        // Child ERP Codes
        const childERPOptions = res.child_erp_codes.map(erp => `<option value="${erp}">`).join('');
        document.getElementById('childERPList').innerHTML = childERPOptions;

        // Child Names
        const childNameOptions = res.child_names.map(name => `<option value="${name}">`).join('');
        document.getElementById('childNameList').innerHTML = childNameOptions;
    } catch (e) {
        console.error('메타데이터 로드 실패:', e);
    }
}

// Enter key support for filters
['filterParentERP', 'filterParentName', 'filterChildERP', 'filterChildName'].forEach(id => {
    document.getElementById(id).addEventListener('keypress', e => {
        if (e.key === 'Enter') applyFilters();
    });
});
