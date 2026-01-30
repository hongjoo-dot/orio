/**
 * 불출 관리 페이지 JavaScript
 * - 마스터: 불출 계획 목록 (WithdrawalPlan)
 * - 디테일: 불출 상품 (WithdrawalPlanItem) + 상세 정보
 */

let currentPlanId = null;
let currentPlanData = null;

let masterTableManager, detailTableManager;
let paginationManager;

let uploadModal, uploadResultModal, confirmModal, alertModal;

let currentFilters = {};
let currentPage = 1;
let currentLimit = 20;
let currentSortBy = null;
let currentSortDir = null;

const STATUS_LABELS = {
    DRAFT: '임시저장',
    PENDING: '신청',
    APPROVED: '승인',
    REJECTED: '반려'
};

// 마스터 컬럼 정의
const masterColumns = [
    { key: 'PlanID', header: 'ID', sortKey: 'PlanID', render: (row) => row.PlanID || '-' },
    { key: 'OrderNo', header: '주문번호', sortKey: 'OrderNo', render: (row) => row.OrderNo || '-' },
    { key: 'Type', header: '사용유형', sortKey: 'Type', render: (row) => row.Type || '-' },
    {
        key: 'Status',
        header: '상태',
        sortKey: 'Status',
        render: (row) => {
            const status = row.Status || '';
            return `<span class="status-badge status-${status}">${STATUS_LABELS[status] || status}</span>`;
        }
    },
    { key: 'OrdererName', header: '주문자', sortKey: 'OrdererName', render: (row) => row.OrdererName || '-' },
    { key: 'RecipientName', header: '받는분', sortKey: 'RecipientName', render: (row) => row.RecipientName || '-' },
    { key: 'DesiredDate', header: '출고희망일', sortKey: 'DesiredDate', render: (row) => row.DesiredDate || '-' },
    { key: 'CreatedDate', header: '등록일', sortKey: 'CreatedDate', render: (row) => row.CreatedDate ? row.CreatedDate.substring(0, 10) : '-' },
];

// 디테일 컬럼 (상품)
const detailColumns = [
    { key: 'ProductName', header: '상품명', render: (row) => row.ProductName || '-' },
    { key: 'BaseBarcode', header: '바코드', render: (row) => row.BaseBarcode || '-' },
    { key: 'UniqueCode', header: '고유코드', render: (row) => row.UniqueCode || '-' },
    {
        key: 'Quantity',
        header: '수량',
        render: (row) => `<div style="text-align:right;">${(row.Quantity || 0).toLocaleString()}</div>`
    }
];

/**
 * 페이지 초기화
 */
document.addEventListener('DOMContentLoaded', function () {
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');
    confirmModal = new ModalManager('confirmModal');
    alertModal = new ModalManager('alertModal');

    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'PlanID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
        },
        onRowClick: (row, tr) => selectPlan(row, tr),
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadData(1, currentLimit);
        },
        emptyMessage: '불출 계획 데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    detailTableManager = new TableManager('detail-table', {
        selectable: false,
        idKey: 'ItemID',
        emptyMessage: '불출 상품 데이터가 없습니다.'
    });

    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadData(page, limit),
        onLimitChange: (page, limit) => loadData(page, limit)
    });

    loadTypes();
    loadStatuses();
    loadData(1, 20);
});

/**
 * 불출 계획 선택
 */
function selectPlan(row, tr) {
    document.querySelectorAll('#master-table tbody tr').forEach(r => r.classList.remove('selected'));
    tr.classList.add('selected');

    currentPlanId = row.PlanID;
    currentPlanData = row;
    loadDetail(currentPlanId);
}

/**
 * 디테일 로드
 */
async function loadDetail(planId) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailContainer').style.display = 'block';
        document.getElementById('detailActions').style.display = 'flex';
        document.getElementById('detailCount').style.display = 'inline';

        // 계획 상세 정보 표시
        renderPlanInfo(currentPlanData);
        updateWorkflowButtons(currentPlanData);

        // 상품 목록
        detailTableManager.showLoading(detailColumns.length);

        const result = await api.get(`/api/withdrawals/${planId}/items`);
        const data = result.data || [];

        detailTableManager.render(data, detailColumns);
        document.getElementById('detailCount').textContent = `(상품 ${data.length}개)`;

    } catch (e) {
        console.error('불출 상품 로드 실패:', e);
        showAlertModal('불출 상품 로드 실패: ' + e.message, 'error');
        detailTableManager.render([], detailColumns);
    }
}

/**
 * 계획 상세 정보 렌더링
 */
function renderPlanInfo(plan) {
    if (!plan) return;

    const status = plan.Status || '';
    const statusLabel = STATUS_LABELS[status] || status;

    const html = `
        <div style="background:rgba(99,102,241,0.06);border-radius:10px;padding:16px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="font-weight:600;font-size:14px;">계획 #${plan.PlanID}</span>
                <span class="status-badge status-${status}">${statusLabel}</span>
            </div>
            <div class="plan-info-grid">
                <div class="plan-info-item">
                    <span class="plan-info-label">주문번호</span>
                    <span class="plan-info-value">${plan.OrderNo || '-'}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">사용유형</span>
                    <span class="plan-info-value">${plan.Type || '-'}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">주문자</span>
                    <span class="plan-info-value">${plan.OrdererName || '-'}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">받는분</span>
                    <span class="plan-info-value">${plan.RecipientName || '-'}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">전화번호</span>
                    <span class="plan-info-value">${plan.Phone1 || '-'}${plan.Phone2 ? ' / ' + plan.Phone2 : ''}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">배송방식</span>
                    <span class="plan-info-value">${plan.DeliveryMethod || '-'}</span>
                </div>
                <div class="plan-info-item" style="grid-column:1/-1;">
                    <span class="plan-info-label">주소</span>
                    <span class="plan-info-value">${plan.Address1 || ''}${plan.Address2 ? ' ' + plan.Address2 : ''}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">출고희망일</span>
                    <span class="plan-info-value">${plan.DesiredDate || '-'}</span>
                </div>
                <div class="plan-info-item">
                    <span class="plan-info-label">송장번호</span>
                    <span class="plan-info-value">${plan.TrackingNo || '-'}</span>
                </div>
                ${plan.Notes ? `
                <div class="plan-info-item" style="grid-column:1/-1;">
                    <span class="plan-info-label">메모</span>
                    <span class="plan-info-value">${plan.Notes}</span>
                </div>` : ''}
                ${plan.RejectionReason ? `
                <div class="plan-info-item" style="grid-column:1/-1;">
                    <span class="plan-info-label" style="color:var(--danger);">반려사유</span>
                    <span class="plan-info-value" style="color:var(--danger);">${plan.RejectionReason}</span>
                </div>` : ''}
            </div>
        </div>
    `;
    document.getElementById('planInfo').innerHTML = html;
}

/**
 * 워크플로우 버튼 표시
 */
function updateWorkflowButtons(plan) {
    const btnSubmit = document.getElementById('btnSubmit');
    const btnApprove = document.getElementById('btnApprove');
    const btnReject = document.getElementById('btnReject');

    btnSubmit.style.display = 'none';
    btnApprove.style.display = 'none';
    btnReject.style.display = 'none';

    if (!plan) return;

    const status = plan.Status;
    if (status === 'DRAFT' || status === 'REJECTED') {
        btnSubmit.style.display = 'inline-flex';
    }
    if (status === 'PENDING') {
        btnApprove.style.display = 'inline-flex';
        btnReject.style.display = 'inline-flex';
    }
}

/**
 * 디테일 패널 초기화
 */
function resetDetail() {
    currentPlanId = null;
    currentPlanData = null;
    document.getElementById('detailPlaceholder').style.display = 'block';
    document.getElementById('detailContainer').style.display = 'none';
    document.getElementById('detailActions').style.display = 'none';
    document.getElementById('detailCount').style.display = 'none';
    document.getElementById('planInfo').innerHTML = '';
    detailTableManager.render([], detailColumns);
}

// ========== 필터/검색 ==========

async function loadTypes() {
    try {
        const result = await api.get('/api/withdrawals/types');
        const types = result.types || [];
        const select = document.getElementById('searchType');
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

async function loadStatuses() {
    try {
        const result = await api.get('/api/withdrawals/statuses');
        const statuses = result.statuses || [];
        const select = document.getElementById('searchStatus');
        select.innerHTML = '<option value="">전체</option>';
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = STATUS_LABELS[status] || status;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('상태 로드 실패:', e);
    }
}

function applyFilters() {
    currentFilters = {};
    const yearMonth = document.getElementById('searchYearMonth').value;
    const type = document.getElementById('searchType').value;
    const status = document.getElementById('searchStatus').value;
    const orderNo = document.getElementById('searchOrderNo').value.trim();

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (type) currentFilters.type = type;
    if (status) currentFilters.status = status;
    if (orderNo) currentFilters.order_no = orderNo;

    loadData(1, currentLimit);
}

function resetFilters() {
    document.getElementById('searchYearMonth').value = '';
    document.getElementById('searchType').value = '';
    document.getElementById('searchStatus').value = '';
    document.getElementById('searchOrderNo').value = '';
    currentFilters = {};
    loadData(1, currentLimit);
}

function changeLimit() {
    currentLimit = parseInt(document.getElementById('limitSelector').value);
    loadData(1, currentLimit);
}

// ========== 데이터 로드 ==========

async function loadData(page = 1, limit = 20) {
    try {
        currentPage = page;
        currentLimit = limit;

        masterTableManager.showLoading(masterColumns.length);

        let params = `page=${page}&limit=${limit}`;
        for (const [key, value] of Object.entries(currentFilters)) {
            params += `&${key}=${encodeURIComponent(value)}`;
        }
        if (currentSortBy) params += `&sort_by=${currentSortBy}`;
        if (currentSortDir) params += `&sort_dir=${currentSortDir}`;

        const result = await api.get(`/api/withdrawals?${params}`);
        const data = result.data || [];
        const pagination = result.pagination || {};

        masterTableManager.render(data, masterColumns);

        document.getElementById('resultCount').textContent =
            `(${pagination.total_count || 0}건)`;

        paginationManager.render({
            currentPage: pagination.page || page,
            totalPages: pagination.total_pages || 1,
            totalCount: pagination.total_count || 0,
            limit: pagination.limit || limit
        });

        resetDetail();

    } catch (e) {
        console.error('데이터 로드 실패:', e);
        masterTableManager.render([], masterColumns);
        document.getElementById('resultCount').textContent = '(0건)';
    }
}

// ========== 액션 버튼 ==========

function updateActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('deleteButton');
    if (selectedIds.length > 0) {
        deleteBtn.disabled = false;
        deleteBtn.classList.remove('btn-disabled');
    } else {
        deleteBtn.disabled = true;
        deleteBtn.classList.add('btn-disabled');
    }
}

function selectAllData() {
    masterTableManager.selectAll();
}

// ========== 삭제 ==========

function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedIds();
    if (selectedIds.length === 0) {
        showAlertModal('삭제할 항목을 선택해주세요.');
        return;
    }

    showConfirmModal(
        `선택한 ${selectedIds.length}건의 불출 계획을 삭제하시겠습니까?`,
        async () => {
            try {
                await api.post('/api/withdrawals/bulk-delete', { ids: selectedIds });
                showAlertModal(`${selectedIds.length}건이 삭제되었습니다.`, 'success');
                loadData(currentPage, currentLimit);
            } catch (e) {
                showAlertModal('삭제 실패: ' + e.message, 'error');
            }
        }
    );
}

// ========== 워크플로우 ==========

function submitPlan() {
    if (!currentPlanId) return;
    showConfirmModal(
        '이 불출 계획을 신청하시겠습니까?',
        async () => {
            try {
                await api.put(`/api/withdrawals/${currentPlanId}/status`, { status: 'PENDING' });
                showAlertModal('신청이 완료되었습니다.', 'success');
                loadData(currentPage, currentLimit);
            } catch (e) {
                showAlertModal('신청 실패: ' + e.message, 'error');
            }
        }
    );
}

function approvePlan() {
    if (!currentPlanId) return;
    showConfirmModal(
        '이 불출 계획을 승인하시겠습니까?',
        async () => {
            try {
                await api.put(`/api/withdrawals/${currentPlanId}/status`, { status: 'APPROVED' });
                showAlertModal('승인이 완료되었습니다.', 'success');
                loadData(currentPage, currentLimit);
            } catch (e) {
                showAlertModal('승인 실패: ' + e.message, 'error');
            }
        }
    );
}

function rejectPlan() {
    if (!currentPlanId) return;
    // 반려 사유 입력 표시
    document.getElementById('rejectReasonContainer').style.display = 'block';
    document.getElementById('rejectReason').value = '';

    showConfirmModal(
        '이 불출 계획을 반려하시겠습니까?',
        async () => {
            try {
                const reason = document.getElementById('rejectReason').value.trim();
                await api.put(`/api/withdrawals/${currentPlanId}/status`, {
                    status: 'REJECTED',
                    rejection_reason: reason || null
                });
                document.getElementById('rejectReasonContainer').style.display = 'none';
                showAlertModal('반려가 완료되었습니다.', 'success');
                loadData(currentPage, currentLimit);
            } catch (e) {
                showAlertModal('반려 실패: ' + e.message, 'error');
            }
        },
        true
    );
}

// ========== 엑셀 다운로드/업로드 ==========

async function downloadExcel() {
    try {
        let params = '';
        const parts = [];
        for (const [key, value] of Object.entries(currentFilters)) {
            parts.push(`${key}=${encodeURIComponent(value)}`);
        }

        // 선택된 ID가 있으면 해당 데이터만
        const selectedIds = masterTableManager.getSelectedIds();
        if (selectedIds.length > 0) {
            parts.push(`ids=${selectedIds.join(',')}`);
        }

        if (parts.length > 0) params = '?' + parts.join('&');

        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/withdrawals/download${params}`, {
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
        a.download = `withdrawals_${new Date().toISOString().slice(0, 10)}.xlsx`;
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
    document.getElementById('uploadButton').disabled = true;
    uploadModal.open();
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
    document.getElementById('progressText').textContent = '업로드 중...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/withdrawals/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '처리 완료';

        const result = await response.json();

        uploadModal.close();

        if (response.ok) {
            // 성공
            document.getElementById('uploadSuccessSection').style.display = 'block';
            document.getElementById('uploadErrorSection').style.display = 'none';
            document.getElementById('uploadResultTitle').textContent = '업로드 완료';
            document.getElementById('planInserted').textContent = result.plan_inserted || 0;
            document.getElementById('planUpdated').textContent = result.plan_updated || 0;
            document.getElementById('itemsInserted').textContent = result.items_inserted || 0;
            document.getElementById('uploadTotalRows').textContent = result.total_rows || 0;
        } else {
            // 실패
            document.getElementById('uploadSuccessSection').style.display = 'none';
            document.getElementById('uploadErrorSection').style.display = 'block';
            document.getElementById('uploadResultTitle').textContent = '업로드 실패';
            document.getElementById('uploadErrorMessage').textContent = result.detail || '알 수 없는 오류';
        }

        uploadResultModal.open();
        loadData(currentPage, currentLimit);

    } catch (e) {
        uploadModal.close();
        document.getElementById('uploadSuccessSection').style.display = 'none';
        document.getElementById('uploadErrorSection').style.display = 'block';
        document.getElementById('uploadResultTitle').textContent = '업로드 실패';
        document.getElementById('uploadErrorMessage').textContent = e.message;
        uploadResultModal.open();
    } finally {
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fa-solid fa-upload"></i> 업로드';
    }
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
    } else {
        icon.className = 'fa-solid fa-circle-info';
        icon.style.color = 'var(--accent)';
    }
    document.getElementById('alertMessage').textContent = message;
    alertModal.open();
}

function showConfirmModal(message, onConfirm, showRejectReason = false) {
    document.getElementById('confirmMessage').textContent = message;

    if (!showRejectReason) {
        document.getElementById('rejectReasonContainer').style.display = 'none';
    }

    const okBtn = document.getElementById('confirmOkButton');
    const newBtn = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newBtn, okBtn);

    newBtn.addEventListener('click', async () => {
        confirmModal.close();
        if (onConfirm) await onConfirm();
    });

    confirmModal.open();
}