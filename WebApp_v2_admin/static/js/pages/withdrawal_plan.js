/**
 * 불출 계획 페이지 JavaScript
 * - 마스터: 캠페인 그룹 목록
 * - 디테일: 선택된 캠페인의 상품 목록
 */

let currentGroupId = null;
let currentGroupData = null;
let currentFilters = {};
let selectedGroupIds = new Set();  // 선택된 그룹 ID들

let uploadModal, uploadResultModal, confirmModal, alertModal;

/**
 * 페이지 초기화
 */
document.addEventListener('DOMContentLoaded', function() {
    // 모달 초기화
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');
    confirmModal = new ModalManager('confirmModal');
    alertModal = new ModalManager('alertModal');

    // 초기 데이터 로드
    loadTypes();
    loadGroups();

    // Enter 키 검색
    ['filterYearMonth', 'filterType', 'filterTitle'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyFilters();
            });
        }
    });

    // 업로드 존 드래그앤드롭 설정
    setupUploadZone();
});

/**
 * 업로드 존 드래그앤드롭 설정
 */
function setupUploadZone() {
    const uploadZone = document.querySelector('.upload-zone');
    if (!uploadZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

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

/**
 * 사용유형 목록 로드
 */
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

/**
 * 캠페인 그룹 목록 로드 (마스터)
 */
async function loadGroups() {
    try {
        const tbody = document.querySelector('#master-table tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align:center;padding:40px;color:var(--text-muted);">
                    <i class="fa-solid fa-spinner fa-spin"></i> 로딩 중...
                </td>
            </tr>
        `;

        // 선택 초기화
        selectedGroupIds.clear();
        document.getElementById('selectAllGroups').checked = false;

        let params = [];
        if (currentFilters.year_month) params.push(`year_month=${currentFilters.year_month}`);
        if (currentFilters.type) params.push(`type=${encodeURIComponent(currentFilters.type)}`);
        if (currentFilters.title) params.push(`title=${encodeURIComponent(currentFilters.title)}`);

        const queryString = params.length > 0 ? '?' + params.join('&') : '';
        const result = await api.get(`/api/withdrawal-plans/groups${queryString}`);
        const groups = result.data || [];

        document.getElementById('groupCount').textContent = `(${groups.length}건)`;

        if (groups.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align:center;padding:40px;color:var(--text-muted);">
                        <i class="fa-solid fa-inbox" style="font-size:24px;margin-bottom:8px;opacity:0.5;"></i>
                        <p>데이터가 없습니다</p>
                    </td>
                </tr>
            `;
            resetDetail();
            return;
        }

        tbody.innerHTML = '';
        groups.forEach(group => {
            const tr = document.createElement('tr');
            tr.className = 'group-row';
            tr.dataset.groupId = group.GroupID;

            const dateRange = group.StartDate === group.EndDate
                ? group.StartDate
                : `${group.StartDate} ~ ${group.EndDate}`;

            tr.innerHTML = `
                <td style="text-align:center;" onclick="event.stopPropagation();">
                    <input type="checkbox" class="group-checkbox" data-group-id="${group.GroupID}" onchange="toggleGroupSelection(${group.GroupID}, this)">
                </td>
                <td>
                    <div class="group-info">
                        <span class="group-title">${group.Title || '-'}</span>
                        <span class="group-meta">${dateRange} · ${group.ItemCount}개 상품</span>
                    </div>
                </td>
                <td><span class="type-badge ${group.Type}">${group.Type || '-'}</span></td>
                <td style="text-align:right;font-weight:500;">${(group.TotalQty || 0).toLocaleString()}</td>
            `;

            tr.addEventListener('click', () => selectGroup(group, tr));
            tbody.appendChild(tr);
        });

        // 기존 선택 복원 또는 초기화
        if (currentGroupId) {
            const existingRow = document.querySelector(`tr[data-group-id="${currentGroupId}"]`);
            if (existingRow) {
                existingRow.classList.add('selected');
            } else {
                resetDetail();
            }
        }

    } catch (e) {
        console.error('그룹 목록 로드 실패:', e);
        document.querySelector('#master-table tbody').innerHTML = `
            <tr>
                <td colspan="4" style="text-align:center;padding:40px;color:var(--danger);">
                    로드 실패: ${e.message}
                </td>
            </tr>
        `;
    }
}

/**
 * 전체 선택/해제
 */
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.group-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const groupId = parseInt(cb.dataset.groupId);
        if (checkbox.checked) {
            selectedGroupIds.add(groupId);
        } else {
            selectedGroupIds.delete(groupId);
        }
    });
    updateGroupActionButtons();
}

/**
 * 개별 그룹 선택/해제
 */
function toggleGroupSelection(groupId, checkbox) {
    if (checkbox.checked) {
        selectedGroupIds.add(groupId);
    } else {
        selectedGroupIds.delete(groupId);
    }

    // 전체 선택 체크박스 상태 업데이트
    const allCheckboxes = document.querySelectorAll('.group-checkbox');
    const checkedCount = document.querySelectorAll('.group-checkbox:checked').length;
    document.getElementById('selectAllGroups').checked = (allCheckboxes.length > 0 && checkedCount === allCheckboxes.length);
    updateGroupActionButtons();
}

/**
 * 그룹 선택에 따른 수정 양식 버튼 상태 업데이트
 */
function updateGroupActionButtons() {
    const editDownloadBtn = document.getElementById('editDownloadButton');
    if (selectedGroupIds.size > 0) {
        editDownloadBtn.classList.remove('btn-disabled');
        editDownloadBtn.disabled = false;
    } else {
        editDownloadBtn.classList.add('btn-disabled');
        editDownloadBtn.disabled = true;
    }
}

/**
 * 캠페인 그룹 선택
 */
function selectGroup(group, tr) {
    // 기존 선택 해제
    document.querySelectorAll('#master-table tbody tr').forEach(r => r.classList.remove('selected'));
    tr.classList.add('selected');

    currentGroupId = group.GroupID;
    currentGroupData = group;

    loadGroupDetail(group);
}

/**
 * 그룹 상세 로드 (디테일)
 */
async function loadGroupDetail(group) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailContainer').style.display = 'flex';

        // 그룹 요약
        renderGroupSummary(group);

        // 상품 테이블 로딩
        const tbody = document.querySelector('#detail-table tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align:center;padding:20px;color:var(--text-muted);">
                    <i class="fa-solid fa-spinner fa-spin"></i> 로딩 중...
                </td>
            </tr>
        `;

        const result = await api.get(`/api/withdrawal-plans/groups/${group.GroupID}/items`);
        const items = result.data || [];

        document.getElementById('itemCount').textContent = `(${items.length}건)`;

        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center;padding:20px;color:var(--text-muted);">
                        상품이 없습니다
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.ProductName || '-'}</td>
                <td><code style="font-size:12px;">${item.UniqueCode || '-'}</code></td>
                <td>${item.Date || '-'}</td>
                <td style="text-align:right;font-weight:500;">${(item.PlannedQty || 0).toLocaleString()}</td>
                <td style="color:var(--text-muted);font-size:13px;">${item.Notes || '-'}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (e) {
        console.error('그룹 상세 로드 실패:', e);
        showAlertModal('상품 목록 로드 실패: ' + e.message, 'error');
    }
}

/**
 * 그룹 요약 렌더링
 */
function renderGroupSummary(group) {
    const html = `
        <div class="group-summary-title">
            <span class="type-badge ${group.Type}">${group.Type}</span>
            ${group.Title}
        </div>
        <div class="group-summary-grid">
            <div class="summary-item">
                <span class="summary-label">그룹ID</span>
                <span class="summary-value">${group.GroupID}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">기간</span>
                <span class="summary-value">${group.StartDate === group.EndDate ? group.StartDate : group.StartDate + ' ~ ' + group.EndDate}</span>
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
    document.getElementById('groupSummary').innerHTML = html;
}

/**
 * 디테일 패널 초기화
 */
function resetDetail() {
    currentGroupId = null;
    currentGroupData = null;
    document.getElementById('detailPlaceholder').style.display = 'flex';
    document.getElementById('detailContainer').style.display = 'none';
}

// ========== 필터 ==========

function applyFilters() {
    currentFilters = {};

    const yearMonth = document.getElementById('filterYearMonth').value;
    const type = document.getElementById('filterType').value;
    const title = document.getElementById('filterTitle').value.trim();

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (type) currentFilters.type = type;
    if (title) currentFilters.title = title;

    resetDetail();
    loadGroups();
}

function resetFilters() {
    document.getElementById('filterYearMonth').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterTitle').value = '';
    currentFilters = {};
    resetDetail();
    loadGroups();
}

// ========== 엑셀 다운로드/업로드 ==========

/**
 * 엑셀 양식 다운로드 (빈 양식 - 신규 등록용)
 */
async function downloadTemplate() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/withdrawal-plans/download', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '다운로드 실패');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `withdrawal_plan_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        showAlertModal('다운로드 실패: ' + e.message, 'error');
    }
}

/**
 * 수정 양식 다운로드 (선택된 그룹 데이터 포함)
 */
async function downloadEditForm() {
    if (selectedGroupIds.size === 0) {
        showAlertModal('수정할 캠페인을 선택해주세요.', 'warning');
        return;
    }

    try {
        const groupIdsArray = Array.from(selectedGroupIds);
        const queryString = `?group_ids=${groupIdsArray.join(',')}`;

        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/withdrawal-plans/download${queryString}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '다운로드 실패');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `withdrawal_plan_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        showAlertModal('다운로드 실패: ' + e.message, 'error');
    }
}

function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('uploadButton').disabled = true;

    // 업로드 존 스타일 초기화
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
    if (!file) return;

    const uploadButton = document.getElementById('uploadButton');
    uploadButton.disabled = true;
    uploadButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 업로드 중...';

    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('progressBar').style.width = '50%';
    document.getElementById('progressText').textContent = '50%';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/withdrawal-plans/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        const result = await response.json();

        uploadModal.hide();

        if (response.ok) {
            document.getElementById('uploadSuccessSection').style.display = 'block';
            document.getElementById('uploadErrorSection').style.display = 'none';
            document.getElementById('uploadResultTitle').textContent = '업로드 결과';
            document.getElementById('uploadTotalRows').textContent = result.total_rows || 0;
            document.getElementById('resultInserted').textContent = result.inserted || 0;
            document.getElementById('resultUpdated').textContent = result.updated || 0;
        } else {
            document.getElementById('uploadSuccessSection').style.display = 'none';
            document.getElementById('uploadErrorSection').style.display = 'block';
            document.getElementById('uploadResultTitle').textContent = '업로드 실패';
            document.getElementById('uploadErrorMessage').textContent = result.detail || '알 수 없는 오류';
        }

        uploadResultModal.show();
        loadGroups();

    } catch (e) {
        uploadModal.hide();
        document.getElementById('uploadSuccessSection').style.display = 'none';
        document.getElementById('uploadErrorSection').style.display = 'block';
        document.getElementById('uploadResultTitle').textContent = '업로드 실패';
        document.getElementById('uploadErrorMessage').textContent = e.message;
        uploadResultModal.show();
    } finally {
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fa-solid fa-upload"></i> 업로드';
    }
}

// ========== 삭제 ==========

function deleteGroup() {
    if (!currentGroupId || !currentGroupData) {
        showAlertModal('삭제할 캠페인을 선택해주세요.', 'warning');
        return;
    }

    showConfirmModal(
        `"${currentGroupData.Title}" 캠페인의 모든 상품(${currentGroupData.ItemCount}건)을 삭제하시겠습니까?`,
        async () => {
            try {
                await api.post('/api/withdrawal-plans/groups/delete', { group_id: currentGroupId });
                showAlertModal('삭제 완료', 'success');
                resetDetail();
                loadGroups();
            } catch (e) {
                showAlertModal('삭제 실패: ' + e.message, 'error');
            }
        }
    );
}

// ========== 모달 헬퍼 ==========

function showAlertModal(message, type = 'info') {
    const icon = document.getElementById('alertIcon');
    if (type === 'success') {
        icon.className = 'fa-solid fa-circle-check';
        icon.style.color = 'var(--success)';
    } else if (type === 'error') {
        icon.className = 'fa-solid fa-circle-xmark';
        icon.style.color = 'var(--danger)';
    } else if (type === 'warning') {
        icon.className = 'fa-solid fa-triangle-exclamation';
        icon.style.color = 'var(--warning)';
    } else {
        icon.className = 'fa-solid fa-circle-info';
        icon.style.color = 'var(--accent)';
    }
    document.getElementById('alertMessage').textContent = message;
    alertModal.show();
}

function showConfirmModal(message, onConfirm) {
    document.getElementById('confirmMessage').textContent = message;

    const okBtn = document.getElementById('confirmOkButton');
    const newBtn = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newBtn, okBtn);

    newBtn.addEventListener('click', async () => {
        confirmModal.hide();
        if (onConfirm) await onConfirm();
    });

    confirmModal.show();
}
