/**
 * 행사 관리 페이지 JavaScript
 * - 행사 목록 (Promotion)
 * - 행사 상품 (PromotionProduct)
 */

// 현재 활성 탭
let currentTab = 'promotion';

// 테이블 및 페이지네이션 매니저
let promotionTableManager, productTableManager;
let paginationManager;

// 모달 매니저
let uploadModal, uploadResultModal, confirmModal, alertModal;

// 현재 필터 및 페이지 정보
let currentFilters = {};
let currentPage = 1;
let currentLimit = 20;

// 행사 목록 컬럼 정의
const promotionColumns = [
    { key: 'PromotionID', header: '행사ID', render: (row) => row.PromotionID || '-' },
    { key: 'PromotionName', header: '행사명', render: (row) => row.PromotionName || '-' },
    { key: 'PromotionType', header: '행사유형', render: (row) => row.PromotionType || '-' },
    {
        key: 'StartDate',
        header: '시작일',
        render: (row) => {
            const date = row.StartDate || '';
            const time = row.StartTime || '';
            return time && time !== '00:00:00' ? `${date} ${time}` : date;
        }
    },
    {
        key: 'EndDate',
        header: '종료일',
        render: (row) => {
            const date = row.EndDate || '';
            const time = row.EndTime || '';
            return time && time !== '00:00:00' ? `${date} ${time}` : date;
        }
    },
    { key: 'BrandName', header: '브랜드', render: (row) => row.BrandName || '-' },
    { key: 'ChannelName', header: '채널', render: (row) => row.ChannelName || '-' },
    {
        key: 'Status',
        header: '상태',
        render: (row) => {
            const status = row.Status || '';
            const labels = { SCHEDULED: '예정', ACTIVE: '진행중', ENDED: '종료', CANCELLED: '취소' };
            return `<span class="status-badge status-${status}">${labels[status] || status}</span>`;
        }
    },
    {
        key: 'CommissionRate',
        header: '수수료율',
        render: (row) => `<div style="text-align:right;">${row.CommissionRate != null ? row.CommissionRate + '%' : '-'}</div>`
    },
    { key: 'DiscountOwner', header: '할인부담', render: (row) => row.DiscountOwner || '-' },
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

// 행사 상품 컬럼 정의
const productColumns = [
    { key: 'PromotionID', header: '행사ID', render: (row) => row.PromotionID || '-' },
    { key: 'PromotionName', header: '행사명', render: (row) => row.PromotionName || '-' },
    { key: 'PromotionType', header: '행사유형', render: (row) => row.PromotionType || '-' },
    { key: 'BrandName', header: '브랜드', render: (row) => row.BrandName || '-' },
    { key: 'ChannelName', header: '채널', render: (row) => row.ChannelName || '-' },
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

    // 테이블 매니저 초기화 - 행사 목록
    promotionTableManager = new TableManager('promotion-table', {
        selectable: true,
        idKey: 'PromotionID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
        },
        emptyMessage: '행사 데이터가 없습니다.'
    });

    // 테이블 매니저 초기화 - 행사 상품
    productTableManager = new TableManager('product-table', {
        selectable: true,
        idKey: 'PromotionProductID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
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
 * 탭 전환
 */
function switchTab(tab) {
    currentTab = tab;

    // 탭 버튼 스타일 변경
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });

    // 테이블 표시 전환
    document.getElementById('promotion-table').style.display = tab === 'promotion' ? '' : 'none';
    document.getElementById('product-table').style.display = tab === 'product' ? '' : 'none';

    // 테이블 제목 변경
    document.getElementById('tableTitle').textContent = tab === 'promotion' ? '행사' : '행사 상품';

    // 선택 해제 및 데이터 새로고침
    getActiveTableManager().clearSelection();
    updateActionButtons([]);
    loadData(1, currentLimit);
}

/**
 * 현재 활성 테이블 매니저 반환
 */
function getActiveTableManager() {
    return currentTab === 'promotion' ? promotionTableManager : productTableManager;
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
 * 데이터 로드
 */
async function loadData(page = 1, limit = 20) {
    currentPage = page;
    currentLimit = limit;

    const tableManager = getActiveTableManager();
    const columns = currentTab === 'promotion' ? promotionColumns : productColumns;

    try {
        tableManager.showLoading(columns.length);

        const endpoint = currentTab === 'promotion'
            ? '/api/promotions'
            : '/api/promotions/products';

        const params = { page, limit, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`${endpoint}${queryString}`);

        tableManager.render(result.data || [], columns);

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
 * 액션 버튼 상태 업데이트
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
 * 전체 선택
 */
async function selectAllData() {
    try {
        const endpoint = currentTab === 'promotion'
            ? '/api/promotions'
            : '/api/promotions/products';

        const params = { page: 1, limit: 100000, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`${endpoint}${queryString}`);
        const data = result.data || [];

        const tableManager = getActiveTableManager();
        const idKey = currentTab === 'promotion' ? 'PromotionID' : 'PromotionProductID';

        const allIds = data.map(row => row[idKey]);

        tableManager.selectedRows = new Set(allIds);

        const tableId = currentTab === 'promotion' ? 'promotion-table' : 'product-table';
        document.querySelectorAll(`#${tableId} tbody input[type="checkbox"]`).forEach(cb => {
            cb.checked = true;
        });

        const headerCb = document.querySelector(`#${tableId} thead input[type="checkbox"]`);
        if (headerCb) headerCb.checked = true;

        updateActionButtons(allIds);
        showAlertModal(`${allIds.length}개 항목이 선택되었습니다.`, 'success');

    } catch (e) {
        console.error('전체 선택 실패:', e);
        showAlertModal('전체 선택 실패: ' + e.message, 'error');
    }
}

/**
 * 선택 삭제
 */
async function bulkDelete() {
    const tableManager = getActiveTableManager();
    const selectedIds = tableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlertModal('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirmModal(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const endpoint = currentTab === 'promotion'
                ? '/api/promotions/bulk-delete'
                : '/api/promotions/products/bulk-delete';

            const result = await api.post(endpoint, { ids: selectedIds });

            showAlertModal(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');
            tableManager.clearSelection();
            updateActionButtons([]);
            loadData(currentPage, currentLimit);

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

    const tableManager = getActiveTableManager();
    const selectedIds = tableManager.getSelectedRows();

    const params = { ...currentFilters };

    if (selectedIds.length > 0) {
        if (currentTab === 'promotion') {
            params.ids = selectedIds.join(',');
        } else {
            params.product_ids = selectedIds.join(',');
        }
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
    // showAlert가 전역에 있으면 사용, 없으면 자체 모달 사용
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
    // showConfirm이 전역에 있으면 사용
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
