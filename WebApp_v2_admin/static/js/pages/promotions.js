/**
 * 행사 관리 페이지 JavaScript
 * - 마스터: 행사 목록 (Promotion)
 * - 디테일: 행사 상품 (PromotionProduct) — 행사 클릭 시 표시
 */

// 선택된 행사 ID
let currentPromotionId = null;

// 테이블 및 페이지네이션 매니저
let masterTableManager, detailTableManager;
let paginationManager;

// 모달 매니저
let uploadModal, uploadResultModal, confirmModal, alertModal;

// 현재 필터 및 페이지 정보
let currentFilters = {};
let currentPage = 1;
let currentLimit = 20;
let currentSortBy = null;
let currentSortDir = null;

// 마스터 컬럼 정의 (행사 목록)
const masterColumns = [
    { key: 'PromotionID', header: '행사ID', sortKey: 'PromotionID', render: (row) => row.PromotionID || '-' },
    { key: 'PromotionName', header: '행사명', sortKey: 'PromotionName', render: (row) => row.PromotionName || '-' },
    { key: 'PromotionType', header: '행사유형', sortKey: 'PromotionType', render: (row) => row.PromotionType || '-' },
    {
        key: 'StartDate',
        header: '시작일',
        sortKey: 'StartDate',
        render: (row) => {
            const date = row.StartDate || '';
            const time = row.StartTime || '';
            return time && time !== '00:00:00' ? `${date} ${time}` : date;
        }
    },
    {
        key: 'EndDate',
        header: '종료일',
        sortKey: 'EndDate',
        render: (row) => {
            const date = row.EndDate || '';
            const time = row.EndTime || '';
            return time && time !== '00:00:00' ? `${date} ${time}` : date;
        }
    },
    { key: 'BrandName', header: '브랜드', sortKey: 'BrandName', render: (row) => row.BrandName || '-' },
    { key: 'ChannelName', header: '채널', sortKey: 'ChannelName', render: (row) => row.ChannelName || '-' },
    {
        key: 'Status',
        header: '상태',
        sortKey: 'Status',
        render: (row) => {
            const status = row.Status || '';
            const labels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
            return `<span class="status-badge status-${status}">${labels[status] || status}</span>`;
        }
    },
    {
        key: 'CommissionRate',
        header: '수수료율',
        sortKey: 'CommissionRate',
        align: 'right',
        render: (row) => `<div style="text-align:right;">${row.CommissionRate != null ? row.CommissionRate + '%' : '-'}</div>`
    },
    { key: 'DiscountOwner', header: '할인부담', sortKey: 'DiscountOwner', render: (row) => row.DiscountOwner || '-' },
    {
        key: 'ExpectedSalesAmount',
        header: '예상매출',
        sortKey: 'ExpectedSalesAmount',
        align: 'right',
        render: (row) => `<div style="text-align:right;">${(row.ExpectedSalesAmount || 0).toLocaleString()}</div>`
    },
    {
        key: 'ExpectedQuantity',
        header: '예상수량',
        sortKey: 'ExpectedQuantity',
        align: 'right',
        render: (row) => `<div style="text-align:right;">${(row.ExpectedQuantity || 0).toLocaleString()}</div>`
    }
];

// 디테일 컬럼 정의 (행사 상품 — 상품 고유 정보만)
const detailColumns = [
    { key: 'UniqueCode', header: '상품코드', render: (row) => row.UniqueCode || '-' },
    { key: 'ProductName', header: '상품명', render: (row) => row.ProductName || '-' },
    {
        key: 'SellingPrice',
        header: '판매가',
        render: (row) => `<div style="text-align:right;">${(row.SellingPrice || 0).toLocaleString()}</div>`
    },
    {
        key: 'PromotionPrice',
        header: '행사가',
        render: (row) => `<div style="text-align:right;">${(row.PromotionPrice || 0).toLocaleString()}</div>`
    },
    {
        key: 'SupplyPrice',
        header: '공급가',
        render: (row) => `<div style="text-align:right;">${(row.SupplyPrice || 0).toLocaleString()}</div>`
    },
    {
        key: 'CouponDiscountRate',
        header: '쿠폰할인율',
        render: (row) => `<div style="text-align:right;">${row.CouponDiscountRate != null ? row.CouponDiscountRate + '%' : '-'}</div>`
    },
    {
        key: 'UnitCost',
        header: '원가',
        render: (row) => `<div style="text-align:right;">${(row.UnitCost || 0).toLocaleString()}</div>`
    },
    {
        key: 'LogisticsCost',
        header: '물류비',
        render: (row) => `<div style="text-align:right;">${(row.LogisticsCost || 0).toLocaleString()}</div>`
    },
    {
        key: 'ExpectedSalesAmount',
        header: '예상매출',
        render: (row) => `<div style="text-align:right;">${(row.ExpectedSalesAmount || 0).toLocaleString()}</div>`
    },
    {
        key: 'ExpectedQuantity',
        header: '예상수량',
        render: (row) => `<div style="text-align:right;">${(row.ExpectedQuantity || 0).toLocaleString()}</div>`
    }
];

/**
 * 페이지 초기화
 */
document.addEventListener('DOMContentLoaded', function () {
    // 모달 초기화
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');
    confirmModal = new ModalManager('confirmModal');
    alertModal = new ModalManager('alertModal');

    // 마스터 테이블 매니저
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'PromotionID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
        },
        onRowClick: (row, tr) => selectPromotion(row, tr),
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadData(1, currentLimit);
        },
        emptyMessage: '행사 데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    // 디테일 테이블 매니저
    detailTableManager = new TableManager('detail-table', {
        selectable: true,
        idKey: 'PromotionProductID',
        onSelectionChange: (selectedIds) => {
            updateDetailActionButtons(selectedIds);
        },
        emptyMessage: '행사 상품 데이터가 없습니다.'
    });

    // 페이지네이션 초기화
    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadData(page, limit),
        onLimitChange: (page, limit) => loadData(page, limit)
    });

    // 초기 데이터 로드
    loadBrands();
    loadChannels();
    loadYearMonths();
    loadPromotionTypes();
    loadStatuses();
    loadData(1, 20);
});

/**
 * 행사 선택 (마스터 행 클릭)
 */
function selectPromotion(row, tr) {
    // 이전 선택 행 하이라이트 제거
    document.querySelectorAll('#master-table tbody tr').forEach(r => r.classList.remove('selected'));
    // 현재 행 하이라이트
    tr.classList.add('selected');

    currentPromotionId = row.PromotionID;
    loadDetail(currentPromotionId);
}

/**
 * 디테일 데이터 로드 (행사 상품)
 */
async function loadDetail(promotionId) {
    try {
        // 플레이스홀더 숨기고 디테일 표시
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('detailContainer').style.display = 'block';
        document.getElementById('detailActions').style.display = 'flex';
        document.getElementById('detailCount').style.display = 'inline';

        detailTableManager.showLoading(detailColumns.length);

        const result = await api.get(`/api/promotions/products?promotion_id=${promotionId}&page=1&limit=1000`);
        const data = result.data || [];

        detailTableManager.render(data, detailColumns);
        document.getElementById('detailCount').textContent = `(${data.length}개)`;

    } catch (e) {
        console.error('행사 상품 로드 실패:', e);
        showAlertModal('행사 상품 로드 실패: ' + e.message, 'error');
        detailTableManager.render([], detailColumns);
        document.getElementById('detailCount').textContent = '(0개)';
    }
}

/**
 * 디테일 패널 초기화 (플레이스홀더로 복귀)
 */
function resetDetail() {
    currentPromotionId = null;
    document.getElementById('detailPlaceholder').style.display = 'block';
    document.getElementById('detailContainer').style.display = 'none';
    document.getElementById('detailActions').style.display = 'none';
    document.getElementById('detailCount').style.display = 'none';
    detailTableManager.render([], detailColumns);
    updateDetailActionButtons([]);
}

/**
 * 브랜드 목록 로드
 */
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

/**
 * 채널 목록 로드
 */
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

/**
 * 년월 목록 로드
 */
async function loadYearMonths() {
    try {
        const result = await api.get('/api/promotions/year-months');
        const yearMonths = result.year_months || [];

        if (yearMonths.length > 0) {
            document.getElementById('searchYearMonth').value = yearMonths[0];
        }
    } catch (e) {
        console.error('년월 목록 로드 실패:', e);
    }
}

/**
 * 행사유형 목록 로드
 */
async function loadPromotionTypes() {
    try {
        const result = await api.get('/api/promotions/promotion-types');
        const types = result.promotion_types || [];

        const select = document.getElementById('searchPromotionType');
        select.innerHTML = '<option value="">전체</option>';

        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('행사유형 로드 실패:', e);
    }
}

/**
 * 상태 목록 로드
 */
async function loadStatuses() {
    try {
        const result = await api.get('/api/promotions/statuses');
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

/**
 * 마스터 데이터 로드 (행사 목록)
 */
async function loadData(page = 1, limit = 20) {
    currentPage = page;
    currentLimit = limit;

    try {
        masterTableManager.showLoading(masterColumns.length);

        const params = { page, limit, sort_by: currentSortBy, sort_dir: currentSortDir, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/promotions${queryString}`);

        masterTableManager.render(result.data || [], masterColumns);

        document.getElementById('resultCount').textContent = `(${result.total?.toLocaleString() || 0}건)`;

        paginationManager.render({
            page: result.page,
            limit: result.limit,
            total: result.total,
            total_pages: result.total_pages
        });

    } catch (e) {
        console.error('데이터 로드 실패:', e);
        showAlertModal('데이터 로드 실패: ' + e.message, 'error');
    }
}

/**
 * 필터 적용
 */
function applyFilters() {
    currentFilters = {};

    const yearMonth = document.getElementById('searchYearMonth').value;
    const brandId = document.getElementById('searchBrand').value;
    const channelId = document.getElementById('searchChannel').value;
    const promotionType = document.getElementById('searchPromotionType').value;
    const status = document.getElementById('searchStatus').value;

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (brandId) currentFilters.brand_id = brandId;
    if (channelId) currentFilters.channel_id = channelId;
    if (promotionType) currentFilters.promotion_type = promotionType;
    if (status) currentFilters.status = status;

    // 디테일 패널 초기화
    resetDetail();
    loadData(1, currentLimit);
}

/**
 * 필터 초기화
 */
function resetFilters() {
    document.getElementById('searchYearMonth').value = '';
    document.getElementById('searchBrand').value = '';
    document.getElementById('searchChannel').value = '';
    document.getElementById('searchPromotionType').value = '';
    document.getElementById('searchStatus').value = '';

    currentFilters = {};
    resetDetail();
    loadData(1, currentLimit);
}

/**
 * 페이지 크기 변경
 */
function changeLimit() {
    const limit = parseInt(document.getElementById('limitSelector').value);
    loadData(1, limit);
}

/**
 * 마스터 액션 버튼 상태 업데이트
 */
function updateActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('deleteButton');

    if (selectedIds.length > 0) {
        deleteBtn.classList.remove('btn-disabled');
        deleteBtn.disabled = false;
    } else {
        deleteBtn.classList.add('btn-disabled');
        deleteBtn.disabled = true;
    }
}

/**
 * 디테일 액션 버튼 상태 업데이트
 */
function updateDetailActionButtons(selectedIds) {
    const deleteBtn = document.getElementById('detailDeleteButton');

    if (selectedIds.length > 0) {
        deleteBtn.classList.remove('btn-disabled');
        deleteBtn.disabled = false;
    } else {
        deleteBtn.classList.add('btn-disabled');
        deleteBtn.disabled = true;
    }
}

/**
 * 마스터 전체 선택
 */
async function selectAllData() {
    try {
        const params = { page: 1, limit: 100000, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`/api/promotions${queryString}`);
        const data = result.data || [];

        const allIds = data.map(row => row.PromotionID);

        masterTableManager.selectedRows = new Set(allIds);

        document.querySelectorAll('#master-table tbody input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
        });

        const headerCb = document.querySelector('#master-table thead input[type="checkbox"]');
        if (headerCb) headerCb.checked = true;

        updateActionButtons(allIds);
        showAlertModal(`${allIds.length}개 행사가 선택되었습니다.`, 'success');

    } catch (e) {
        console.error('전체 선택 실패:', e);
        showAlertModal('전체 선택 실패: ' + e.message, 'error');
    }
}

/**
 * 디테일 전체 선택
 */
function selectAllDetail() {
    const allIds = detailTableManager.getAllIds ? detailTableManager.getAllIds() : [];

    // 테이블에서 직접 수집
    const checkboxes = document.querySelectorAll('#detail-table tbody input[type="checkbox"]');
    const ids = [];
    checkboxes.forEach(cb => {
        cb.checked = true;
        if (cb.value) ids.push(parseInt(cb.value) || cb.value);
    });

    if (ids.length > 0) {
        detailTableManager.selectedRows = new Set(ids);
    }

    const headerCb = document.querySelector('#detail-table thead input[type="checkbox"]');
    if (headerCb) headerCb.checked = true;

    updateDetailActionButtons(ids);
    showAlertModal(`${ids.length}개 상품이 선택되었습니다.`, 'success');
}

/**
 * 마스터 선택 삭제 (행사 삭제)
 */
async function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlertModal('삭제할 행사를 선택해주세요.', 'warning');
        return;
    }

    showConfirmModal(`${selectedIds.length}개 행사를 삭제하시겠습니까?\n(해당 행사의 상품도 함께 삭제됩니다)`, async () => {
        try {
            const result = await api.post('/api/promotions/bulk-delete', { ids: selectedIds });

            showAlertModal(`${result.deleted_count}개 행사가 삭제되었습니다.`, 'success');
            masterTableManager.clearSelection();
            updateActionButtons([]);
            resetDetail();
            loadData(currentPage, currentLimit);

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlertModal('삭제 실패: ' + e.message, 'error');
        }
    });
}

/**
 * 디테일 선택 삭제 (행사 상품 삭제)
 */
async function bulkDeleteDetail() {
    const selectedIds = detailTableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlertModal('삭제할 상품을 선택해주세요.', 'warning');
        return;
    }

    showConfirmModal(`${selectedIds.length}개 상품을 삭제하시겠습니까?`, async () => {
        try {
            const result = await api.post('/api/promotions/products/bulk-delete', { ids: selectedIds });

            showAlertModal(`${result.deleted_count}개 상품이 삭제되었습니다.`, 'success');
            detailTableManager.clearSelection();
            updateDetailActionButtons([]);

            // 디테일 새로고침
            if (currentPromotionId) {
                loadDetail(currentPromotionId);
            }

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlertModal('삭제 실패: ' + e.message, 'error');
        }
    });
}

/**
 * 엑셀 양식 다운로드
 */
function downloadExcel() {
    const endpoint = '/api/promotions/download';

    const selectedIds = masterTableManager.getSelectedRows();
    const params = { ...currentFilters };

    if (selectedIds.length > 0) {
        params.ids = selectedIds.join(',');
    }

    const queryString = api.buildQueryString(params);
    window.location.href = `${endpoint}${queryString}`;
}

/**
 * 업로드 모달 표시
 */
function showUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('uploadButton').disabled = true;

    uploadModal.show();
}

/**
 * 파일 선택 핸들러
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileInfo').style.display = 'block';
        document.getElementById('uploadButton').disabled = false;
    }
}

/**
 * 파일 업로드
 */
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        showAlertModal('파일을 선택해주세요.', 'warning');
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
        const response = await fetch('/api/promotions/upload', {
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
        document.getElementById('promoInserted').textContent = result.promotion_inserted?.toLocaleString() || 0;
        document.getElementById('promoUpdated').textContent = result.promotion_updated?.toLocaleString() || 0;
        document.getElementById('prodInserted').textContent = result.product_inserted?.toLocaleString() || 0;
        document.getElementById('prodUpdated').textContent = result.product_updated?.toLocaleString() || 0;

        uploadResultModal.show();

        // 마스터 새로고침 + 디테일 초기화
        resetDetail();
        loadData(1, currentLimit);

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

/**
 * 알림 모달 표시
 */
function showAlertModal(message, type = 'info') {
    if (typeof showAlert === 'function') {
        showAlert(message, type);
        return;
    }

    const icons = {
        success: 'fa-circle-check',
        error: 'fa-circle-xmark',
        warning: 'fa-triangle-exclamation',
        info: 'fa-circle-info'
    };
    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--accent)'
    };

    const iconEl = document.getElementById('alertIcon');
    if (iconEl) {
        iconEl.className = `fa-solid ${icons[type] || icons.info}`;
        iconEl.style.color = colors[type] || colors.info;
    }

    const titleEl = document.getElementById('alertTitle');
    if (titleEl) {
        const titles = { success: '성공', error: '오류', warning: '경고', info: '알림' };
        titleEl.textContent = titles[type] || '알림';
    }

    document.getElementById('alertMessage').textContent = message;
    alertModal.show();
}

/**
 * 확인 모달 표시
 */
function showConfirmModal(message, onConfirm) {
    if (typeof showConfirm === 'function') {
        showConfirm(message, onConfirm);
        return;
    }

    document.getElementById('confirmMessage').textContent = message;

    const okBtn = document.getElementById('confirmOkButton');
    const newBtn = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newBtn, okBtn);

    newBtn.addEventListener('click', () => {
        confirmModal.hide();
        onConfirm();
    });

    confirmModal.show();
}
