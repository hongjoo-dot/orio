let masterTableManager, paginationManager;
let currentFilters = {};
let currentChannelId = null;
let currentSortBy = null;
let currentSortDir = null;
let detailPage = 1;
let detailLimit = 20;
let selectedDetailIds = new Set();

// 마스터 테이블 컬럼 정의
const masterColumns = [
    { key: 'ChannelID', header: 'ID', sortKey: 'ChannelID', render: (row) => row.ChannelID || '' },
    { key: 'Name', header: '채널명', sortKey: 'Name', render: (row) => row.Name || '' },
    { key: 'Group', header: '그룹', sortKey: 'Group', render: (row) => row.Group || '' },
    { key: 'Type', header: '유형', sortKey: 'Type', render: (row) => row.Type || '' },
    { key: 'ContractType', header: '계약유형', sortKey: 'ContractType', render: (row) => row.ContractType || '' }
];

document.addEventListener('DOMContentLoaded', async function () {
    // 테이블 매니저 초기화
    masterTableManager = new TableManager('channelTable', {
        selectable: true,
        idKey: 'ChannelID',
        onSelectionChange: (selectedIds) => updateBulkButtons(selectedIds),
        onRowClick: (row, tr) => selectChannel(row, tr),
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadChannels(1, paginationManager.getLimit());
        },
        emptyMessage: '데이터가 없습니다'
    });
    masterTableManager.renderHeader(masterColumns);

    // 페이지네이션 매니저 초기화
    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadChannels(page, limit),
        onLimitChange: (page, limit) => loadChannels(page, limit)
    });

    await loadMetadata();
    loadChannels(1, 20);

    // 엔터키 검색 지원
    ['filterName', 'filterDetailName', 'filterGroup'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyFilters();
            });
        }
    });
});

async function loadChannels(page = 1, limit = 20) {
    try {
        masterTableManager.showLoading(masterColumns.length);

        const params = { page, limit, sort_by: currentSortBy, sort_dir: currentSortDir, ...currentFilters };
        const queryString = api.buildQueryString(params);
        const res = await api.get(`/api/channels${queryString}`);

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
        showAlert('채널 로드 실패: ' + e.message, 'error');
        masterTableManager.render([], masterColumns);
    }
}

function selectChannel(row, tr) {
    const rows = document.querySelectorAll('#channelTable tbody tr');
    rows.forEach(r => r.classList.remove('selected'));
    tr.classList.add('selected');

    currentChannelId = row.ChannelID;
    loadDetails(currentChannelId);
}

async function loadDetails(channelId, resetPage = true) {
    if (resetPage) {
        detailPage = 1;
    }

    try {
        const params = new URLSearchParams({
            channel_id: channelId,
            page: detailPage,
            limit: detailLimit
        });

        const detailNameFilter = document.getElementById('filterDetailName').value.trim();
        if (detailNameFilter) {
            params.append('detail_name', detailNameFilter);
        }

        const res = await api.get(`/api/channeldetails?${params}`);

        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailTableContainer').style.display = 'block';
        document.getElementById('detailActionButtons').style.display = 'flex';
        document.getElementById('detailCount').style.display = 'block';
        document.getElementById('detailLimitSelector').style.display = 'block';

        const tbody = document.getElementById('detailTableBody');
        tbody.innerHTML = '';
        selectedDetailIds.clear();

        document.getElementById('detailCount').textContent = `상세 ${res.total}개`;

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:2rem;color:var(--text-muted);">상세정보가 없습니다</td></tr>';
            document.getElementById('detailPagination').style.display = 'none';
        } else {
            res.data.forEach(d => {
                const tr = document.createElement('tr');
                if (selectedDetailIds.has(d.ChannelDetailID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedDetailIds.has(d.ChannelDetailID) ? 'checked' : ''} onchange="toggleSelectDetail(${d.ChannelDetailID}, event)"></td>
                    <td>${d.ChannelDetailID || ''}</td>
                    <td>${d.BizNumber || ''}</td>
                    <td>${d.DetailName || ''}</td>
                `;
                tbody.appendChild(tr);
            });

            renderDetailPagination(res.total, res.page, res.limit);
        }

        updateDetailBulkButtons();
    } catch (e) {
        showAlert('상세정보 로드 실패: ' + e.message, 'error');
    }
}

function changeDetailLimit() {
    detailLimit = parseInt(document.getElementById('detailLimitSelector').value);
    detailPage = 1;
    if (currentChannelId) {
        loadDetails(currentChannelId, false);
    }
}

function renderDetailPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const paginationDiv = document.getElementById('detailPagination');
    paginationDiv.innerHTML = '';
    paginationDiv.style.display = 'flex';

    const prevBtn = document.createElement('button');
    prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
    prevBtn.className = 'btn btn-sm btn-secondary';
    prevBtn.disabled = page === 1;
    prevBtn.onclick = () => changeDetailPage(page - 1);
    paginationDiv.appendChild(prevBtn);

    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);

    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === page ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
        btn.onclick = () => changeDetailPage(i);
        paginationDiv.appendChild(btn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
    nextBtn.className = 'btn btn-sm btn-secondary';
    nextBtn.disabled = page === totalPages || totalPages === 0;
    nextBtn.onclick = () => changeDetailPage(page + 1);
    paginationDiv.appendChild(nextBtn);
}

function changeDetailPage(page) {
    detailPage = page;
    if (currentChannelId) {
        loadDetails(currentChannelId, false);
    }
}

function applyFilters() {
    currentFilters = {};
    const name = document.getElementById('filterName').value.trim();
    const detailName = document.getElementById('filterDetailName').value.trim();
    const group = document.getElementById('filterGroup').value.trim();
    const type = document.getElementById('filterType').value;
    const contractType = document.getElementById('filterContractType').value;

    if (name) currentFilters.name = name;
    if (detailName) currentFilters.detail_name = detailName;
    if (group) currentFilters.group = group;
    if (type) currentFilters.type = type;
    if (contractType) currentFilters.contract_type = contractType;

    loadChannels(1, paginationManager.getLimit());
}

function resetFilters() {
    document.getElementById('filterName').value = '';
    document.getElementById('filterDetailName').value = '';
    document.getElementById('filterGroup').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterContractType').value = '';
    currentFilters = {};

    // 디테일 영역 초기화
    currentChannelId = null;
    selectedDetailIds.clear();
    const placeholder = document.getElementById('detailPlaceholder');
    placeholder.style.display = 'block';
    placeholder.style.textAlign = 'center';
    document.getElementById('detailTableContainer').style.display = 'none';
    document.getElementById('detailActionButtons').style.display = 'none';

    loadChannels(1, paginationManager.getLimit());
}

function updateBulkButtons(selectedIds) {
    const hasSelection = selectedIds && selectedIds.length > 0;
    const editBtn = document.getElementById('editButton');
    const deleteBtn = document.getElementById('deleteButton');

    editBtn.disabled = !hasSelection;
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
}

async function selectAllData() {
    showConfirm('현재 필터 조건의 모든 데이터를 선택하시겠습니까?', async () => {
        try {
            const params = new URLSearchParams({
                limit: 10000,
                ...currentFilters
            });

            const res = await api.get(`/api/channels?${params}`);

            // TableManager의 selectedRows에 직접 추가
            masterTableManager.selectedRows.clear();
            res.data.forEach(c => masterTableManager.selectedRows.add(String(c.ChannelID)));

            // 현재 보이는 행의 체크박스 체크
            const checkboxes = document.querySelectorAll('#channelTable tbody .row-checkbox');
            checkboxes.forEach(cb => {
                if (masterTableManager.selectedRows.has(cb.dataset.id)) {
                    cb.checked = true;
                }
            });

            if (masterTableManager._selectAllCheckbox) {
                masterTableManager._selectAllCheckbox.checked = true;
            }

            updateBulkButtons(masterTableManager.getSelectedRows());
            showAlert(`${masterTableManager.selectedRows.size}개의 채널이 선택되었습니다.`, 'success');
        } catch (e) {
            showAlert('전체 선택 실패: ' + e.message, 'error');
        }
    });
}

function showIntegratedAddModal() {
    document.getElementById('intName').value = '';
    document.getElementById('intGroup').value = '';
    document.getElementById('intType').value = '';
    document.getElementById('intContractType').value = '';
    document.getElementById('intOwner').value = '';
    document.getElementById('intLiveSource').value = '';
    document.getElementById('intSabangnetMallID').value = '';
    document.getElementById('intBizNumber').value = '';
    document.getElementById('intDetailName').value = '';
    document.getElementById('integratedAddModal').classList.add('show');
}

function closeIntegratedAddModal() {
    document.getElementById('integratedAddModal').classList.remove('show');
}

async function saveIntegrated() {
    const name = document.getElementById('intName').value.trim();
    const bizNumber = document.getElementById('intBizNumber').value.trim();
    const detailName = document.getElementById('intDetailName').value.trim();

    if (!name || !bizNumber || !detailName) {
        showAlert('채널명, 사업자번호, 거래처명은 필수입니다.', 'error');
        return;
    }

    const channelData = {
        Name: name,
        Group: document.getElementById('intGroup').value.trim() || null,
        Type: document.getElementById('intType').value.trim() || null,
        ContractType: document.getElementById('intContractType').value || null,
        Owner: document.getElementById('intOwner').value.trim() || null,
        LiveSource: document.getElementById('intLiveSource').value.trim() || null,
        SabangnetMallID: document.getElementById('intSabangnetMallID').value.trim() || null
    };

    const detailData = {
        BizNumber: bizNumber,
        DetailName: detailName
    };

    try {
        await api.post('/api/channels/integrated', {
            channel: channelData,
            details: [detailData]
        });

        showAlert('채널과 상세정보가 추가되었습니다.', 'success');
        closeIntegratedAddModal();
        loadChannels(paginationManager.getCurrentPage(), paginationManager.getLimit());
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function showAddDetailModal() {
    if (!currentChannelId) {
        showAlert('채널을 먼저 선택하세요.', 'warning');
        return;
    }

    document.getElementById('detailBizNumber').value = '';
    document.getElementById('detailDetailName').value = '';
    document.getElementById('addDetailModal').classList.add('show');
}

function closeAddDetailModal() {
    document.getElementById('addDetailModal').classList.remove('show');
}

async function saveDetail() {
    const bizNumber = document.getElementById('detailBizNumber').value.trim();
    const detailName = document.getElementById('detailDetailName').value.trim();

    if (!bizNumber || !detailName) {
        showAlert('사업자번호와 거래처명은 필수입니다.', 'error');
        return;
    }

    const data = {
        ChannelID: currentChannelId,
        BizNumber: bizNumber,
        DetailName: detailName
    };

    try {
        await api.post('/api/channeldetails', data);
        showAlert('상세정보가 추가되었습니다.', 'success');
        closeAddDetailModal();
        loadDetails(currentChannelId);
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function toggleSelectDetail(id, event) {
    event.stopPropagation();
    if (selectedDetailIds.has(id)) {
        selectedDetailIds.delete(id);
    } else {
        selectedDetailIds.add(id);
    }
    updateDetailBulkButtons();

    const row = Array.from(document.querySelectorAll('#detailTable tbody tr')).find(r =>
        r.querySelector('td:nth-child(2)').textContent == id
    );
    if (row) {
        row.classList.toggle('selected', selectedDetailIds.has(id));
    }

    const allRows = document.querySelectorAll('#detailTable tbody tr');
    document.getElementById('selectAllDetails').checked = selectedDetailIds.size > 0 && selectedDetailIds.size === allRows.length;
}

function toggleSelectAllDetails() {
    const checked = document.getElementById('selectAllDetails').checked;
    const rows = document.querySelectorAll('#detailTable tbody tr');

    rows.forEach(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        if (checkbox) {
            const id = parseInt(r.querySelector('td:nth-child(2)').textContent);
            if (checked) {
                selectedDetailIds.add(id);
                r.classList.add('selected');
                checkbox.checked = true;
            } else {
                selectedDetailIds.delete(id);
                r.classList.remove('selected');
                checkbox.checked = false;
            }
        }
    });

    updateDetailBulkButtons();
}

function updateDetailBulkButtons() {
    const hasSelection = selectedDetailIds.size > 0;
    const editBtn = document.getElementById('editDetailButton');
    const deleteBtn = document.getElementById('deleteDetailButton');

    editBtn.disabled = !hasSelection;
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
}

async function bulkEditDetails() {
    if (selectedDetailIds.size === 0) return;

    const firstId = Array.from(selectedDetailIds)[0];
    try {
        const detail = await api.get(`/api/channeldetails/${firstId}`);

        document.getElementById('bulkEditCount').textContent = selectedDetailIds.size;
        document.getElementById('currentBizNumber').textContent = detail.BizNumber || '(없음)';
        document.getElementById('currentDetailName').textContent = detail.DetailName || '(없음)';

        document.getElementById('bulkBizNumber').value = '';
        document.getElementById('bulkDetailName').value = '';

        document.getElementById('bulkEditModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditModal() {
    document.getElementById('bulkEditModal').classList.remove('show');
}

async function saveBulkEdit() {
    const newBizNumber = document.getElementById('bulkBizNumber').value.trim();
    const newDetailName = document.getElementById('bulkDetailName').value.trim();

    if (!newBizNumber && !newDetailName) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = Array.from(selectedDetailIds).map(async id => {
            const detail = await api.get(`/api/channeldetails/${id}`);
            const updateData = {
                ChannelID: detail.ChannelID,
                BizNumber: newBizNumber || detail.BizNumber,
                DetailName: newDetailName || detail.DetailName
            };
            return api.put(`/api/channeldetails/${id}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedDetailIds.size}개 상세정보가 수정되었습니다.`, 'success');
        closeBulkEditModal();
        selectedDetailIds.clear();
        loadDetails(currentChannelId);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDeleteDetails() {
    if (selectedDetailIds.size === 0) return;

    showConfirm(`선택한 ${selectedDetailIds.size}개의 상세정보를 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/channeldetails/bulk-delete', { ids: Array.from(selectedDetailIds) });
            showAlert(`${selectedDetailIds.size}개 상세정보가 삭제되었습니다.`, 'success');
            selectedDetailIds.clear();
            loadDetails(currentChannelId);
        } catch (e) {
            showAlert('일괄 삭제 실패: ' + e.message, 'error');
        }
    });
}

async function bulkEdit() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    const firstId = selectedIds[0];
    try {
        const channel = await api.get(`/api/channels/${firstId}`);

        document.getElementById('bulkEditChannelCount').textContent = selectedIds.length;
        document.getElementById('currentName').textContent = channel.Name || '(없음)';
        document.getElementById('currentGroup').textContent = channel.Group || '(없음)';
        document.getElementById('currentType').textContent = channel.Type || '(없음)';
        document.getElementById('currentContractType').textContent = channel.ContractType || '(없음)';
        document.getElementById('currentOwner').textContent = channel.Owner || '(없음)';
        document.getElementById('currentLiveSource').textContent = channel.LiveSource || '(없음)';
        document.getElementById('currentSabangnetMallID').textContent = channel.SabangnetMallID || '(없음)';

        document.getElementById('bulkName').value = '';
        document.getElementById('bulkGroup').value = '';
        document.getElementById('bulkType').value = '';
        document.getElementById('bulkContractType').value = '';
        document.getElementById('bulkOwner').value = '';
        document.getElementById('bulkLiveSource').value = '';
        document.getElementById('bulkSabangnetMallID').value = '';

        document.getElementById('bulkEditChannelModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditChannelModal() {
    document.getElementById('bulkEditChannelModal').classList.remove('show');
}

async function saveBulkEditChannel() {
    const selectedIds = masterTableManager.getSelectedRows();
    const newName = document.getElementById('bulkName').value.trim();
    const newGroup = document.getElementById('bulkGroup').value.trim();
    const newType = document.getElementById('bulkType').value;
    const newContractType = document.getElementById('bulkContractType').value;
    const newOwner = document.getElementById('bulkOwner').value.trim();
    const newLiveSource = document.getElementById('bulkLiveSource').value.trim();
    const newSabangnetMallID = document.getElementById('bulkSabangnetMallID').value.trim();

    if (!newName && !newGroup && !newType && !newContractType && !newOwner && !newLiveSource && !newSabangnetMallID) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = selectedIds.map(async id => {
            const channel = await api.get(`/api/channels/${id}`);
            const updateData = {
                Name: newName || channel.Name,
                Group: newGroup || channel.Group,
                Type: newType || channel.Type,
                ContractType: newContractType || channel.ContractType,
                Owner: newOwner || channel.Owner,
                LiveSource: newLiveSource || channel.LiveSource,
                SabangnetMallID: newSabangnetMallID || channel.SabangnetMallID
            };
            return api.put(`/api/channels/${id}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedIds.length}개 채널이 수정되었습니다.`, 'success');
        closeBulkEditChannelModal();
        masterTableManager.clearSelection();
        loadChannels(paginationManager.getCurrentPage(), paginationManager.getLimit());
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개의 채널을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/channels/bulk-delete', { ids: selectedIds.map(id => parseInt(id)) });
            showAlert('채널이 삭제되었습니다.', 'success');

            if (selectedIds.includes(String(currentChannelId))) {
                currentChannelId = null;
                document.getElementById('detailPlaceholder').style.display = 'block';
                document.getElementById('detailTableContainer').style.display = 'none';
            }

            masterTableManager.clearSelection();
            loadChannels(paginationManager.getCurrentPage(), paginationManager.getLimit());
        } catch (e) {
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

async function loadMetadata() {
    try {
        const res = await api.get('/api/channels/metadata');

        const nameOptions = res.names.map(name => `<option value="${name}">`).join('');
        document.getElementById('nameList').innerHTML = nameOptions;

        const groupOptions = res.groups.map(g => `<option value="${g}">`).join('');
        document.getElementById('groupList').innerHTML = groupOptions;

        const typeOptions = res.types.map(t => `<option value="${t}">${t}</option>`).join('');
        document.getElementById('filterType').innerHTML = '<option value="">전체</option>' + typeOptions;
        document.getElementById('intType').innerHTML = '<option value="">선택</option>' + typeOptions;
        document.getElementById('bulkType').innerHTML = '<option value="">변경하지 않음</option>' + typeOptions;

        const contractTypeOptions = res.contract_types.map(ct => `<option value="${ct}">${ct}</option>`).join('');
        document.getElementById('filterContractType').innerHTML = '<option value="">전체</option>' + contractTypeOptions;
        document.getElementById('intContractType').innerHTML = '<option value="">선택</option>' + contractTypeOptions;
        document.getElementById('bulkContractType').innerHTML = '<option value="">변경하지 않음</option>' + contractTypeOptions;

        const ownerOptions = res.owners.map(o => `<option value="${o}">`).join('');
        document.getElementById('ownerList').innerHTML = ownerOptions;

        const liveSourceOptions = res.live_sources.map(ls => `<option value="${ls}">`).join('');
        document.getElementById('liveSourceList').innerHTML = liveSourceOptions;

        const sabangnetMallIDOptions = res.sabangnet_mall_ids.map(sm => `<option value="${sm}">`).join('');
        document.getElementById('sabangnetMallIDList').innerHTML = sabangnetMallIDOptions;

        const detailNameOptions = res.detail_names.map(dn => `<option value="${dn}">`).join('');
        document.getElementById('detailNameList').innerHTML = detailNameOptions;
    } catch (e) {
        console.error('메타데이터 로드 실패:', e);
    }
}
