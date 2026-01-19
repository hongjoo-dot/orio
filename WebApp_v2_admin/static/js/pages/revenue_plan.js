let currentPage = 1, limit = 20, currentFilters = {}, selectedIds = new Set();
let uploadModal, editModal, uploadResultModal;
let brandsData = [], channelsData = [];

document.addEventListener('DOMContentLoaded', function () {
    uploadModal = new ModalManager('uploadModal');
    editModal = new ModalManager('editModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    initYearOptions();
    loadBrands();
    loadChannels();
});

function initYearOptions() {
    const select = document.getElementById('searchYear');
    const currentYear = new Date().getFullYear();
    for (let y = currentYear + 1; y >= currentYear - 2; y--) {
        const option = document.createElement('option');
        option.value = y;
        option.textContent = y + '년';
        if (y === currentYear) option.selected = true;
        select.appendChild(option);
    }
}

async function loadBrands() {
    try {
        const res = await fetch('/api/brands/all');
        const result = await res.json();
        brandsData = result.data || [];

        const options = brandsData.map(b => `<option value="${b.BrandID}">${b.Name}</option>`).join('');
        document.getElementById('searchBrand').innerHTML = '<option value="">전체</option>' + options;
        document.getElementById('editBrand').innerHTML = options;
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

async function loadChannels() {
    try {
        const res = await fetch('/api/channels?limit=500');
        const result = await res.json();
        channelsData = result.data || [];

        const options = channelsData.map(c => `<option value="${c.ChannelID}">${c.Name}</option>`).join('');
        document.getElementById('searchChannel').innerHTML = '<option value="">전체</option>' + options;
        document.getElementById('editChannel').innerHTML = options;
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

async function loadData() {
    try {
        const params = new URLSearchParams({ page: currentPage, limit, ...currentFilters });
        const res = await fetch(`/api/revenue-plan?${params}`);
        const data = await res.json();

        const tbody = document.getElementById('dataTable');
        tbody.innerHTML = data.data.length === 0
            ? '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted);">데이터가 없습니다.</td></tr>'
            : data.data.map(item => `
                <tr>
                    <td style="text-align:center;">
                        <input type="checkbox" class="row-checkbox" value="${item.PlanID}" onchange="toggleRowSelect()">
                    </td>
                    <td>${item.Date || '-'}</td>
                    <td>${item.BrandName || '-'}</td>
                    <td>${item.ChannelName || '-'}</td>
                    <td>
                        <span class="badge ${item.PlanType === 'TARGET' ? 'badge-primary' : 'badge-success'}">
                            ${item.PlanType === 'TARGET' ? '목표' : '예상'}
                        </span>
                    </td>
                    <td style="text-align:right;">${item.Amount?.toLocaleString() || 0}</td>
                    <td style="text-align:center;">
                        <button class="btn btn-sm btn-secondary" onclick="showEditModal(${item.PlanID})" title="수정">
                            <i class="fa-solid fa-edit"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

        document.getElementById('resultCount').textContent = `(총 ${data.total.toLocaleString()}건)`;

        const totalPages = Math.ceil(data.total / limit);
        document.getElementById('pagination').innerHTML =
            (currentPage > 1 ? `<button class="btn btn-sm btn-secondary" onclick="changePage(${currentPage - 1})">이전</button>` : '') +
            `<span style="padding:0 16px;">${currentPage} / ${totalPages || 1}</span>` +
            (currentPage < totalPages ? `<button class="btn btn-sm btn-secondary" onclick="changePage(${currentPage + 1})">다음</button>` : '');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function applyFilters() {
    currentFilters = {};
    const year = document.getElementById('searchYear').value;
    const month = document.getElementById('searchMonth').value;
    const brandId = document.getElementById('searchBrand').value;
    const channelId = document.getElementById('searchChannel').value;
    const planType = document.getElementById('searchPlanType').value;

    if (year) currentFilters.year = year;
    if (month) currentFilters.month = month;
    if (brandId) currentFilters.brand_id = brandId;
    if (channelId) currentFilters.channel_id = channelId;
    if (planType) currentFilters.plan_type = planType;

    currentPage = 1;
    loadData();
}

function resetFilters() {
    document.getElementById('searchYear').value = new Date().getFullYear();
    document.getElementById('searchMonth').value = '';
    document.getElementById('searchBrand').value = '';
    document.getElementById('searchChannel').value = '';
    document.getElementById('searchPlanType').value = '';
    currentFilters = {};
    currentPage = 1;

    document.getElementById('dataTable').innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fa-solid fa-search" style="font-size:48px;margin-bottom:16px;opacity:0.5;"></i><p>검색 조건을 입력하고 검색 버튼을 클릭하세요.</p></td></tr>';
    document.getElementById('resultCount').textContent = '';
    document.getElementById('pagination').innerHTML = '';
}

function changePage(page) {
    currentPage = page;
    loadData();
}

function changeLimit() {
    limit = parseInt(document.getElementById('limitSelector').value);
    currentPage = 1;
    loadData();
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.row-checkbox').forEach(cb => {
        cb.checked = checked;
        if (checked) selectedIds.add(parseInt(cb.value));
        else selectedIds.delete(parseInt(cb.value));
    });
    updateActionButtons();
}

function toggleRowSelect() {
    selectedIds.clear();
    document.querySelectorAll('.row-checkbox:checked').forEach(cb => selectedIds.add(parseInt(cb.value)));
    document.getElementById('selectAll').checked = document.querySelectorAll('.row-checkbox').length === selectedIds.size;
    updateActionButtons();
}

function selectAllVisible() {
    document.getElementById('selectAll').checked = true;
    toggleSelectAll();
}

function updateActionButtons() {
    const hasSelection = selectedIds.size > 0;
    const deleteBtn = document.getElementById('deleteButton');
    if (hasSelection) {
        deleteBtn.classList.remove('btn-disabled');
    } else {
        deleteBtn.classList.add('btn-disabled');
    }
}

async function bulkDelete() {
    if (selectedIds.size === 0) return;

    showConfirm(`선택한 ${selectedIds.size}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const res = await fetch('/api/revenue-plan/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: Array.from(selectedIds) })
            });

            if (res.ok) {
                showAlert('삭제되었습니다.', 'success');
                selectedIds.clear();
                updateActionButtons();
                loadData();
            } else {
                showAlert('삭제 실패', 'error');
            }
        } catch (e) {
            showAlert('오류: ' + e.message, 'error');
        }
    });
}

async function showEditModal(planId) {
    try {
        const res = await fetch(`/api/revenue-plan/${planId}`);
        if (!res.ok) throw new Error('데이터 로드 실패');
        const item = await res.json();

        document.getElementById('editPlanId').value = item.PlanID;
        document.getElementById('editDate').value = item.Date;
        document.getElementById('editBrand').value = item.BrandID;
        document.getElementById('editChannel').value = item.ChannelID;
        document.getElementById('editPlanType').value = item.PlanType;
        document.getElementById('editAmount').value = item.Amount;

        editModal.show();
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

async function saveEdit() {
    const planId = document.getElementById('editPlanId').value;
    const data = {
        Date: document.getElementById('editDate').value,
        BrandID: parseInt(document.getElementById('editBrand').value),
        ChannelID: parseInt(document.getElementById('editChannel').value),
        PlanType: document.getElementById('editPlanType').value,
        Amount: parseFloat(document.getElementById('editAmount').value)
    };

    try {
        const res = await fetch(`/api/revenue-plan/${planId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            showAlert('수정되었습니다.', 'success');
            editModal.hide();
            loadData();
        } else {
            const error = await res.json();
            showAlert('수정 실패: ' + (error.detail || '알 수 없는 오류'), 'error');
        }
    } catch (e) {
        showAlert('오류: ' + e.message, 'error');
    }
}

function downloadTemplate() {
    window.location.href = '/api/revenue-plan/download/template';
}

function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
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
    if (!fileInput.files[0]) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('uploadButton').disabled = true;
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '업로드 중...';

    try {
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                document.getElementById('progressBar').style.width = progress + '%';
                document.getElementById('progressText').textContent = progress + '%';
            }
        }, 100);

        const res = await fetch('/api/revenue-plan/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        if (res.ok) {
            const result = await res.json();

            document.getElementById('uploadTotalRows').textContent = result.total_rows?.toLocaleString() || 0;
            document.getElementById('uploadInserted').textContent = result.inserted?.toLocaleString() || 0;
            document.getElementById('uploadUpdated').textContent = result.updated?.toLocaleString() || 0;

            const warnings = [];
            if (result.unmapped_brands > 0) {
                const brandList = result.unmapped_brands_list?.slice(0, 10).map(b => `<span style="color:var(--danger);font-weight:600;">${b}</span>`).join(', ');
                warnings.push(`<strong>브랜드 매핑 실패 ${result.unmapped_brands}건:</strong><br><span style="margin-left:8px;">${brandList}</span>`);
            }
            if (result.unmapped_channels > 0) {
                const channelList = result.unmapped_channels_list?.slice(0, 10).map(c => `<span style="color:var(--danger);font-weight:600;">${c}</span>`).join(', ');
                warnings.push(`<strong>채널 매핑 실패 ${result.unmapped_channels}건:</strong><br><span style="margin-left:8px;">${channelList}</span>`);
            }

            if (warnings.length > 0) {
                document.getElementById('uploadWarnings').style.display = 'block';
                document.getElementById('uploadWarningContent').innerHTML = warnings.map(w => `<div style="margin-bottom:12px;line-height:1.6;">• ${w}</div>`).join('');
            } else {
                document.getElementById('uploadWarnings').style.display = 'none';
            }

            uploadModal.hide();
            uploadResultModal.show();

            if (Object.keys(currentFilters).length > 0) {
                loadData();
            }
        } else {
            const error = await res.json();
            showAlert('업로드 실패: ' + (error.detail || '알 수 없는 오류'), 'error');
        }
    } catch (e) {
        showAlert('업로드 오류: ' + e.message, 'error');
    } finally {
        document.getElementById('uploadButton').disabled = false;
        document.getElementById('uploadProgress').style.display = 'none';
    }
}
