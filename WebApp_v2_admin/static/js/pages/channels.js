let currentPage = 1;
let limit = 20;
let currentFilters = {};
let selectedIds = new Set();
let selectedDetailIds = new Set();
let currentChannelId = null;
let detailPage = 1;
let detailLimit = 20;
let currentSortBy = null;
let currentSortDir = null;

// 마스터 테이블 정렬용 컬럼 정의
const masterSortColumns = [
    { header: 'ID', sortKey: 'ChannelID' },
    { header: '채널명', sortKey: 'Name' },
    { header: '그룹', sortKey: 'Group' },
    { header: '유형', sortKey: 'Type' },
    { header: '계약유형', sortKey: 'ContractType' }
];

document.addEventListener('DOMContentLoaded', async function () {
    renderSortableHeader();
    await loadChannels();
    await loadMetadata();
});

function renderSortableHeader() {
    const thead = document.querySelector('#channelTable thead tr');
    if (!thead) return;

    // 체크박스 th 유지, 나머지 교체
    const checkboxTh = thead.querySelector('th:first-child');
    thead.innerHTML = '';
    thead.appendChild(checkboxTh);

    masterSortColumns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.header;
        if (col.sortKey) {
            th.setAttribute('data-sortable', col.sortKey);
            if (currentSortBy === col.sortKey) {
                th.classList.add(currentSortDir === 'ASC' ? 'sort-asc' : 'sort-desc');
            }
            th.addEventListener('click', () => {
                if (currentSortBy === col.sortKey) {
                    currentSortDir = currentSortDir === 'DESC' ? 'ASC' : 'DESC';
                } else {
                    currentSortBy = col.sortKey;
                    currentSortDir = 'DESC';
                }
                renderSortableHeader();
                currentPage = 1;
                loadChannels();
            });
        }
        thead.appendChild(th);
    });
}

async function loadChannels() {
    try {
        const filterParams = { ...currentFilters };
        if (currentSortBy) filterParams.sort_by = currentSortBy;
        if (currentSortDir) filterParams.sort_dir = currentSortDir;

        const params = new URLSearchParams({
            page: currentPage,
            limit: limit,
            ...filterParams
        });

        const res = await api.get(`/api/channels?${params}`);

        const isFiltered = Object.keys(currentFilters).length > 0;
        if (isFiltered) {
            document.getElementById('totalCount').textContent = `전체 ${res.total}개`;
            document.getElementById('filteredCount').textContent = `필터링됨: ${res.data.length}개`;
        } else {
            document.getElementById('totalCount').textContent = `총 ${res.total}개`;
            document.getElementById('filteredCount').textContent = '';
        }

        const tbody = document.getElementById('channelTableBody');
        tbody.innerHTML = '';

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted);">데이터가 없습니다</td></tr>';
        } else {
            res.data.forEach(c => {
                const tr = document.createElement('tr');
                if (selectedIds.has(c.ChannelID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedIds.has(c.ChannelID) ? 'checked' : ''} onchange="toggleSelect(${c.ChannelID}, event)"></td>
                    <td>${c.ChannelID || ''}</td>
                    <td>${c.Name || ''}</td>
                    <td>${c.Group || ''}</td>
                    <td>${c.Type || ''}</td>
                    <td>${c.ContractType || ''}</td>
                `;

                tr.style.cursor = 'pointer';
                tr.onclick = (e) => selectChannel(c.ChannelID, e);
                tbody.appendChild(tr);
            });
        }

        renderPagination(res.total, res.page, res.limit);
        updateBulkButtons();
    } catch (e) {
        showAlert('채널 로드 실패: ' + e.message, 'error');
    }
}

function selectChannel(channelId, event) {
    if (event.target.type === 'checkbox' || event.target.tagName === 'BUTTON' || event.target.tagName === 'I') return;

    currentChannelId = channelId;

    const rows = document.querySelectorAll('#channelTable tbody tr');
    rows.forEach(r => r.style.background = '');
    event.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)';

    loadDetails(channelId);
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

        // Add detail_name filter if present
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

function changeLimit() {
    limit = parseInt(document.getElementById('limitSelector').value);
    currentPage = 1;
    loadChannels();
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

    currentPage = 1;
    loadChannels();
}

function resetFilters() {
    document.getElementById('filterName').value = '';
    document.getElementById('filterDetailName').value = '';
    document.getElementById('filterGroup').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterContractType').value = '';
    currentFilters = {};
    currentPage = 1;

    // 디테일 영역 초기화
    currentChannelID = null;
    selectedDetailIds.clear();
    const placeholder = document.getElementById('detailPlaceholder');
    placeholder.style.display = 'block';
    placeholder.style.textAlign = 'center';
    document.getElementById('detailTableContainer').style.display = 'none';
    document.getElementById('detailActionButtons').style.display = 'none';

    loadChannels();
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
    loadChannels();
}

function toggleSelect(id, event) {
    event.stopPropagation();
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    updateBulkButtons();

    const row = Array.from(document.querySelectorAll('#channelTable tbody tr')).find(r =>
        r.querySelector('td:nth-child(2)').textContent == id
    );
    if (row) {
        row.classList.toggle('selected', selectedIds.has(id));
    }

    const allRows = document.querySelectorAll('#channelTable tbody tr');
    document.getElementById('selectAll').checked = selectedIds.size > 0 && selectedIds.size === allRows.length;
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    const rows = document.querySelectorAll('#channelTable tbody tr');

    rows.forEach(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        if (checkbox) {
            const id = parseInt(r.querySelector('td:nth-child(2)').textContent);
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

            const res = await api.get(`/api/channels?${params}`);

            selectedIds.clear();
            res.data.forEach(c => selectedIds.add(c.ChannelID));

            document.querySelectorAll('#channelTable tbody tr').forEach(r => {
                const id = parseInt(r.querySelector('td:nth-child(2)').textContent);
                if (selectedIds.has(id)) {
                    r.classList.add('selected');
                    const checkbox = r.querySelector('input[type="checkbox"]');
                    if (checkbox) checkbox.checked = true;
                }
            });

            document.getElementById('selectAll').checked = true;
            updateBulkButtons();

            showAlert(`${selectedIds.size}개의 채널이 선택되었습니다.`, 'success');
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
        // 통합 엔드포인트 사용 (채널명 중복 허용)
        await api.post('/api/channels/integrated', {
            channel: channelData,
            details: [detailData]
        });

        showAlert('채널과 상세정보가 추가되었습니다.', 'success');
        closeIntegratedAddModal();
        loadChannels();
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

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedDetailIds)[0];
    try {
        const detail = await api.get(`/api/channeldetails/${firstId}`);

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditCount').textContent = selectedDetailIds.size;
        document.getElementById('currentBizNumber').textContent = detail.BizNumber || '(없음)';
        document.getElementById('currentDetailName').textContent = detail.DetailName || '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkBizNumber').value = '';
        document.getElementById('bulkDetailName').value = '';

        // 모달 열기
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

    // 변경할 값이 없으면 경고
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
        loadDetails(currentChannelID);
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
    if (selectedIds.size === 0) return;

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedIds)[0];
    try {
        const channel = await api.get(`/api/channels/${firstId}`);

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditChannelCount').textContent = selectedIds.size;
        document.getElementById('currentName').textContent = channel.Name || '(없음)';
        document.getElementById('currentGroup').textContent = channel.Group || '(없음)';
        document.getElementById('currentType').textContent = channel.Type || '(없음)';
        document.getElementById('currentContractType').textContent = channel.ContractType || '(없음)';
        document.getElementById('currentOwner').textContent = channel.Owner || '(없음)';
        document.getElementById('currentLiveSource').textContent = channel.LiveSource || '(없음)';
        document.getElementById('currentSabangnetMallID').textContent = channel.SabangnetMallID || '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkName').value = '';
        document.getElementById('bulkGroup').value = '';
        document.getElementById('bulkType').value = '';
        document.getElementById('bulkContractType').value = '';
        document.getElementById('bulkOwner').value = '';
        document.getElementById('bulkLiveSource').value = '';
        document.getElementById('bulkSabangnetMallID').value = '';

        // 모달 열기
        document.getElementById('bulkEditChannelModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditChannelModal() {
    document.getElementById('bulkEditChannelModal').classList.remove('show');
}

async function saveBulkEditChannel() {
    const newName = document.getElementById('bulkName').value.trim();
    const newGroup = document.getElementById('bulkGroup').value.trim();
    const newType = document.getElementById('bulkType').value;
    const newContractType = document.getElementById('bulkContractType').value;
    const newOwner = document.getElementById('bulkOwner').value.trim();
    const newLiveSource = document.getElementById('bulkLiveSource').value.trim();
    const newSabangnetMallID = document.getElementById('bulkSabangnetMallID').value.trim();

    // 변경할 값이 없으면 경고
    if (!newName && !newGroup && !newType && !newContractType && !newOwner && !newLiveSource && !newSabangnetMallID) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = Array.from(selectedIds).map(async id => {
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
        showAlert(`${selectedIds.size}개 채널이 수정되었습니다.`, 'success');
        closeBulkEditChannelModal();
        selectedIds.clear();
        loadChannels();
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    if (selectedIds.size === 0) return;

    showConfirm(`선택한 ${selectedIds.size}개의 채널을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/channels/bulk-delete', { ids: Array.from(selectedIds) });
            showAlert('채널이 삭제되었습니다.', 'success');
            selectedIds.clear();
            loadChannels();

            if (selectedIds.has(currentChannelId)) {
                currentChannelId = null;
                document.getElementById('detailPlaceholder').style.display = 'block';
                document.getElementById('detailTableContainer').style.display = 'none';
            }
        } catch (e) {
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

async function loadMetadata() {
    try {
        const res = await api.get('/api/channels/metadata');

        // Name 리스트
        const nameOptions = res.names.map(name => `<option value="${name}">`).join('');
        document.getElementById('nameList').innerHTML = nameOptions;

        // Group 리스트
        const groupOptions = res.groups.map(g => `<option value="${g}">`).join('');
        document.getElementById('groupList').innerHTML = groupOptions;

        // Type 드롭다운
        const typeOptions = res.types.map(t => `<option value="${t}">${t}</option>`).join('');
        document.getElementById('filterType').innerHTML = '<option value="">전체</option>' + typeOptions;
        document.getElementById('intType').innerHTML = '<option value="">선택</option>' + typeOptions;
        document.getElementById('bulkType').innerHTML = '<option value="">변경하지 않음</option>' + typeOptions;

        // ContractType 드롭다운
        const contractTypeOptions = res.contract_types.map(ct => `<option value="${ct}">${ct}</option>`).join('');
        document.getElementById('filterContractType').innerHTML = '<option value="">전체</option>' + contractTypeOptions;
        document.getElementById('intContractType').innerHTML = '<option value="">선택</option>' + contractTypeOptions;
        document.getElementById('bulkContractType').innerHTML = '<option value="">변경하지 않음</option>' + contractTypeOptions;

        // Owner 리스트 (담당자)
        const ownerOptions = res.owners.map(o => `<option value="${o}">`).join('');
        document.getElementById('ownerList').innerHTML = ownerOptions;

        // LiveSource 리스트 (실시간 데이터소스)
        const liveSourceOptions = res.live_sources.map(ls => `<option value="${ls}">`).join('');
        document.getElementById('liveSourceList').innerHTML = liveSourceOptions;

        // SabangnetMallID 리스트
        const sabangnetMallIDOptions = res.sabangnet_mall_ids.map(sm => `<option value="${sm}">`).join('');
        document.getElementById('sabangnetMallIDList').innerHTML = sabangnetMallIDOptions;

        // DetailName 리스트
        const detailNameOptions = res.detail_names.map(dn => `<option value="${dn}">`).join('');
        document.getElementById('detailNameList').innerHTML = detailNameOptions;
    } catch (e) {
        console.error('메타데이터 로드 실패:', e);
    }
}

// Enter key support for filters
['filterName', 'filterDetailName', 'filterGroup'].forEach(id => {
    document.getElementById(id).addEventListener('keypress', e => {
        if (e.key === 'Enter') applyFilters();
    });
});
