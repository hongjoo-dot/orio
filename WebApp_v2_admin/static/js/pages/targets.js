/**
 * 목표 관리 페이지 JavaScript
 * - 기본 목표 (TargetBaseProduct)
 * - 행사 목표 (TargetPromotionProduct)
 */

// 현재 활성 탭
let currentTab = 'base';

// 테이블 및 페이지네이션 매니저
let baseTableManager, promotionTableManager;
let paginationManager;

// 모달 매니저
let uploadModal, uploadResultModal;

// 현재 필터
let currentFilters = {};

// 현재 페이지 정보
let currentPage = 1;
let currentLimit = 20;

// 기본 목표 컬럼 정의
const baseColumns = [
    { key: 'Date', header: '날짜', render: (row) => row.Date || '-' },
    { key: 'BrandName', header: '브랜드', render: (row) => row.BrandName || '-' },
    { key: 'ChannelName', header: '채널', render: (row) => row.ChannelName || '-' },
    { key: 'UniqueCode', header: '상품코드', render: (row) => row.UniqueCode || '-' },
    { key: 'ProductName', header: '상품명', render: (row) => row.ProductName || '-' },
    {
        key: 'TargetAmount',
        header: '목표금액',
        render: (row) => `<div style="text-align:right;">${(row.TargetAmount || 0).toLocaleString()}</div>`
    },
    {
        key: 'TargetQuantity',
        header: '목표수량',
        render: (row) => `<div style="text-align:right;">${(row.TargetQuantity || 0).toLocaleString()}</div>`
    }
];

// 행사 목표 컬럼 정의
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
    { key: 'UniqueCode', header: '상품코드', render: (row) => row.UniqueCode || '-' },
    {
        key: 'TargetAmount',
        header: '목표금액',
        render: (row) => `<div style="text-align:right;">${(row.TargetAmount || 0).toLocaleString()}</div>`
    },
    {
        key: 'TargetQuantity',
        header: '목표수량',
        render: (row) => `<div style="text-align:right;">${(row.TargetQuantity || 0).toLocaleString()}</div>`
    }
];

/**
 * 페이지 초기화
 */
document.addEventListener('DOMContentLoaded', function () {
    // 모달 초기화
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    // 테이블 매니저 초기화 - 기본 목표
    baseTableManager = new TableManager('base-table', {
        selectable: true,
        idKey: 'TargetBaseID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
        },
        emptyMessage: '목표 데이터가 없습니다.'
    });

    // 테이블 매니저 초기화 - 행사 목표
    promotionTableManager = new TableManager('promotion-table', {
        selectable: true,
        idKey: 'TargetPromotionID',
        onSelectionChange: (selectedIds) => {
            updateActionButtons(selectedIds);
        },
        emptyMessage: '목표 데이터가 없습니다.'
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
    document.getElementById('base-table').style.display = tab === 'base' ? '' : 'none';
    document.getElementById('promotion-table').style.display = tab === 'promotion' ? '' : 'none';

    // 행사 필터 표시/숨김
    document.getElementById('promotionFilterWrap').style.display = tab === 'promotion' ? '' : 'none';

    // 테이블 제목 변경
    document.getElementById('tableTitle').textContent = tab === 'base' ? '기본 목표' : '행사 목표';

    // 업로드 모달 제목 변경
    document.getElementById('uploadModalTitle').textContent =
        tab === 'base' ? '기본 목표 데이터 업로드' : '행사 목표 데이터 업로드';

    // 행사 목표 탭이면 행사유형 목록 로드
    if (tab === 'promotion') {
        loadPromotionTypes();
    }

    // 선택 해제 및 데이터 새로고침
    getActiveTableManager().clearSelection();
    updateActionButtons([]);
    loadData(1, currentLimit);
}

/**
 * 현재 활성 테이블 매니저 반환
 */
function getActiveTableManager() {
    return currentTab === 'base' ? baseTableManager : promotionTableManager;
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
        const endpoint = currentTab === 'base'
            ? '/api/targets/base/year-months'
            : '/api/targets/promotion/year-months';

        const result = await api.get(endpoint);
        const yearMonths = result.year_months || [];

        // 년월 입력 필드에 기본값 설정 (최신 년월)
        if (yearMonths.length > 0) {
            document.getElementById('searchYearMonth').value = yearMonths[0];
        }
    } catch (e) {
        console.error('년월 목록 로드 실패:', e);
    }
}

/**
 * 행사유형 목록 로드 (행사 목표 탭용)
 */
async function loadPromotionTypes() {
    try {
        const result = await api.get('/api/targets/promotion/promotion-types');
        const promotionTypes = result.promotion_types || [];

        const select = document.getElementById('searchPromotionType');
        select.innerHTML = '<option value="">전체</option>';

        promotionTypes.forEach(type => {
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
 * 데이터 로드
 */
async function loadData(page = 1, limit = 20) {
    currentPage = page;
    currentLimit = limit;

    const tableManager = getActiveTableManager();
    const columns = currentTab === 'base' ? baseColumns : promotionColumns;

    try {
        tableManager.showLoading(columns.length);

        // API 엔드포인트 결정
        const endpoint = currentTab === 'base'
            ? '/api/targets/base'
            : '/api/targets/promotion';

        // 쿼리 파라미터 구성
        const params = { page, limit, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`${endpoint}${queryString}`);

        // 테이블 렌더링
        tableManager.render(result.data || [], columns);

        // 결과 카운트 표시
        document.getElementById('resultCount').textContent = `(${result.total?.toLocaleString() || 0}건)`;

        // 페이지네이션 렌더링
        paginationManager.render({
            page: result.page,
            limit: result.limit,
            total: result.total,
            total_pages: result.total_pages
        });

    } catch (e) {
        console.error('데이터 로드 실패:', e);
        showAlert('데이터 로드 실패: ' + e.message, 'error');
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

    if (yearMonth) currentFilters.year_month = yearMonth;
    if (brandId) currentFilters.brand_id = brandId;
    if (channelId) currentFilters.channel_id = channelId;

    // 행사 목표 탭인 경우 행사유형 필터 추가
    if (currentTab === 'promotion') {
        const promotionType = document.getElementById('searchPromotionType').value;
        if (promotionType) currentFilters.promotion_type = promotionType;
    }

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
 * 전체 선택 (현재 필터 조건의 모든 데이터)
 */
async function selectAllData() {
    try {
        const endpoint = currentTab === 'base'
            ? '/api/targets/base'
            : '/api/targets/promotion';

        const params = { page: 1, limit: 100000, ...currentFilters };
        const queryString = api.buildQueryString(params);

        const result = await api.get(`${endpoint}${queryString}`);
        const data = result.data || [];

        const tableManager = getActiveTableManager();
        const idKey = currentTab === 'base' ? 'TargetBaseID' : 'TargetPromotionID';

        const allIds = data.map(row => row[idKey]);

        // 테이블 매니저의 선택 상태 업데이트
        tableManager.selectedRows = new Set(allIds);

        // 체크박스 UI 업데이트
        document.querySelectorAll(`#${currentTab}-table tbody input[type="checkbox"]`).forEach(cb => {
            cb.checked = true;
        });

        // 헤더 체크박스도 체크
        const headerCb = document.querySelector(`#${currentTab}-table thead input[type="checkbox"]`);
        if (headerCb) headerCb.checked = true;

        updateActionButtons(allIds);
        showAlert(`${allIds.length}개 항목이 선택되었습니다.`, 'success');

    } catch (e) {
        console.error('전체 선택 실패:', e);
        showAlert('전체 선택 실패: ' + e.message, 'error');
    }
}

/**
 * 선택 삭제
 */
async function bulkDelete() {
    const tableManager = getActiveTableManager();
    const selectedIds = tableManager.getSelectedRows();

    if (selectedIds.length === 0) {
        showAlert('삭제할 항목을 선택해주세요.', 'warning');
        return;
    }

    showConfirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`, async () => {
        try {
            const endpoint = currentTab === 'base'
                ? '/api/targets/base/bulk-delete'
                : '/api/targets/promotion/bulk-delete';

            const result = await api.post(endpoint, { ids: selectedIds });

            showAlert(`${result.deleted_count}개 항목이 삭제되었습니다.`, 'success');
            tableManager.clearSelection();
            updateActionButtons([]);
            loadData(currentPage, currentLimit);

        } catch (e) {
            console.error('삭제 실패:', e);
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

/**
 * 엑셀 양식 다운로드 (신규/수정 통합)
 * - 필터나 선택이 없으면: 빈 양식 (신규 등록용)
 * - 필터가 있거나 선택된 항목이 있으면: 해당 데이터 포함 (수정용)
 */
function downloadExcel() {
    const endpoint = currentTab === 'base'
        ? '/api/targets/base/download'
        : '/api/targets/promotion/download';

    const tableManager = getActiveTableManager();
    const selectedIds = tableManager.getSelectedRows();

    const params = { ...currentFilters };

    // 선택된 항목이 있으면 해당 ID들만 다운로드
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
    // 파일 입력 초기화
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
        showAlert('파일을 선택해주세요.', 'warning');
        return;
    }

    try {
        // 진행률 표시
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

        // FormData로 파일 전송
        const formData = new FormData();
        formData.append('file', file);

        const endpoint = currentTab === 'base'
            ? '/api/targets/base/upload'
            : '/api/targets/promotion/upload';

        const token = localStorage.getItem('access_token');
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        // 업로드 모달 닫기
        uploadModal.hide();

        if (!response.ok) {
            const error = await response.json();
            // 에러 모달 표시
            document.getElementById('uploadSuccessSection').style.display = 'none';
            document.getElementById('uploadErrorSection').style.display = 'block';
            document.getElementById('uploadResultTitle').textContent = '업로드 실패';
            document.getElementById('uploadErrorMessage').textContent = error.detail || '업로드 중 오류가 발생했습니다.';
            uploadResultModal.show();
            return;
        }

        const result = await response.json();

        // 성공 모달 표시
        document.getElementById('uploadSuccessSection').style.display = 'block';
        document.getElementById('uploadErrorSection').style.display = 'none';
        document.getElementById('uploadResultTitle').textContent = '업로드 결과';
        document.getElementById('uploadTotalRows').textContent = result.total_rows?.toLocaleString() || 0;
        document.getElementById('uploadInserted').textContent = result.inserted?.toLocaleString() || 0;
        document.getElementById('uploadUpdated').textContent = result.updated?.toLocaleString() || 0;

        uploadResultModal.show();

        // 데이터 새로고침
        loadData(1, currentLimit);

    } catch (e) {
        console.error('업로드 실패:', e);

        // 업로드 모달 닫기
        uploadModal.hide();

        // 에러 모달 표시
        document.getElementById('uploadSuccessSection').style.display = 'none';
        document.getElementById('uploadErrorSection').style.display = 'block';
        document.getElementById('uploadResultTitle').textContent = '업로드 실패';
        document.getElementById('uploadErrorMessage').textContent = e.message || '업로드 중 오류가 발생했습니다.';
        uploadResultModal.show();
    }
}
