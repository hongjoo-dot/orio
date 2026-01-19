let masterTableManager, detailTableManager, paginationManager;
let uploadModal, uploadResultModal;
let currentFilters = {};
let selectedPromotionId = null;

// 마스터 테이블 컬럼
const masterColumns = [
    { key: 'PromotionID', header: '행사ID', render: (row) => `<strong>${row.PromotionID}</strong>` },
    { key: 'PromotionName', header: '행사명', render: (row) => row.PromotionName || '-' },
    { key: 'ChannelName', header: '채널', render: (row) => row.ChannelName || '-' },
    {
        key: 'PromotionType',
        header: '행사유형',
        render: (row) => {
            const type = row.PromotionType || '';
            let typeClass = 'default';
            if (type.startsWith('ONLINE')) typeClass = 'online';
            if (type.startsWith('OFFLINE')) typeClass = 'offline';
            return `<span class="badge badge-type-${typeClass}">${row.PromotionTypeDisplay || row.PromotionType || '-'}</span>`;
        }
    },
    {
        key: 'Status',
        header: '상태',
        render: (row) => {
            const status = row.Status || '';
            return `<span class="badge badge-status-${status.toLowerCase()}">${row.StatusDisplay || row.Status || '-'}</span>`;
        }
    },
    {
        key: 'TargetSalesAmount',
        header: '매출목표',
        className: 'text-right',
        render: (row) => `<div style="text-align:right;">${row.TargetSalesAmount?.toLocaleString() || 0}</div>`
    },
    {
        key: 'Period',
        header: '기간',
        render: (row) => `<div style="font-size:13px;">${row.StartDate || ''} ~ ${row.EndDate || ''}</div>`
    }
];

// 디테일 테이블 컬럼
const detailColumns = [
    { key: 'Uniquecode', header: '상품코드', render: (row) => `<strong>${row.Uniquecode || '-'}</strong>` },
    { key: 'ProductName', header: '상품명', render: (row) => row.ProductName || '-' },
    { key: 'SellingPrice', header: '판매가', className: 'text-right', render: (row) => `<div style="text-align:right;">${row.SellingPrice?.toLocaleString() || '-'}</div>` },
    { key: 'PromotionPrice', header: '행사가', className: 'text-right', render: (row) => `<div style="text-align:right;">${row.PromotionPrice?.toLocaleString() || '-'}</div>` },
    { key: 'TargetQuantity', header: '목표수량', className: 'text-right', render: (row) => `<div style="text-align:right;">${row.TargetQuantity?.toLocaleString() || '-'}</div>` },
    { key: 'TargetSalesAmount', header: '목표매출', className: 'text-right', render: (row) => `<div style="text-align:right;">${row.TargetSalesAmount?.toLocaleString() || '-'}</div>` }
];

document.addEventListener('DOMContentLoaded', function () {
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    masterTableManager = new TableManager('master-table', {
        selectable: true,
        onSelectionChange: (selectedIds) => updateActionButtons(selectedIds),
        onRowClick: (row, tr) => showDetail(row, tr),
        emptyMessage: '데이터가 없습니다.'
    });

    detailTableManager = new TableManager('detail-table', {
        selectable: false,
        emptyMessage: '등록된 상품이 없습니다.'
    });

    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadData(page, limit),
        onLimitChange: (page, limit) => loadData(page, limit)
    });

    initYearOptions();
    loadFilterOptions();
    loadData(1, 20);
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

async function loadFilterOptions() {
    try {
        const filterOptions = await api.get('/api/promotions/filter-options');

        // 행사유형
        const typeSelect = document.getElementById('searchPromotionType');
        typeSelect.innerHTML = '<option value="">전체</option>' +
            filterOptions.promotion_types.map(t => `<option value="${t.value}">${t.label}</option>`).join('');

        // 상태
        const statusSelect = document.getElementById('searchStatus');
        statusSelect.innerHTML = '<option value="">전체</option>' +
            filterOptions.statuses.map(s => `<option value="${s.value}">${s.label}</option>`).join('');

        // 채널명
        const channelSelect = document.getElementById('searchChannelName');
        channelSelect.innerHTML = '<option value="">전체</option>' +
            filterOptions.channel_names.map(c => `<option value="${c}">${c}</option>`).join('');
    } catch (e) {
        console.error('필터 옵션 로드 실패:', e);
    }
}

async function loadData(page = 1, limit = 20) {
    try {
        masterTableManager.showLoading(7);

        const params = { page, limit, ...currentFilters };
        const queryString = api.buildQueryString(params);
        const data = await api.get(`/api/promotions${queryString}`);

        masterTableManager.render(data.data, masterColumns);

        paginationManager.render({
            page: page,
            limit: limit,
            total: data.total,
            total_pages: Math.ceil(data.total / limit)
        });

        document.getElementById('resultCount').textContent = `(총 ${data.total.toLocaleString()}건)`;

    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
        masterTableManager.render([], masterColumns);
    }
}

async function showDetail(row, tr) {
    // 행 선택 스타일 처리 (TableManager는 체크박스 선택만 관리하므로, 클릭 선택 스타일은 별도 처리 필요)
    // 하지만 TableManager.js를 보면 onRowClick 시 별도 스타일 처리는 안 함.
    // 기존 CSS .master-row.selected를 활용하려면 여기서 클래스를 토글해야 함.

    // 모든 행의 selected 클래스 제거
    const rows = document.querySelectorAll('#master-table tbody tr');
    rows.forEach(r => r.classList.remove('selected'));

    // 현재 행에 selected 클래스 추가
    tr.classList.add('selected');
    tr.classList.add('master-row'); // CSS 적용을 위해

    selectedPromotionId = row.PromotionID;
    document.getElementById('detailTitle').textContent = `${row.PromotionName} - 상품 목록`;
    document.getElementById('detailSection').style.display = 'block';

    try {
        detailTableManager.showLoading(6);
        const result = await api.get(`/api/promotions/${row.PromotionID}/products`);
        detailTableManager.render(result.data || [], detailColumns);

        // 스크롤 이동
        document.getElementById('detailSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) {
        showAlert('상품 목록 로드 실패: ' + e.message, 'error');
        detailTableManager.render([], detailColumns);
    }
}

function hideDetail() {
    selectedPromotionId = null;
    document.getElementById('detailSection').style.display = 'none';
    const rows = document.querySelectorAll('#master-table tbody tr');
    rows.forEach(r => r.classList.remove('selected'));
}

function applyFilters() {
    currentFilters = {};
    const year = document.getElementById('searchYear').value;
    const promotionType = document.getElementById('searchPromotionType').value;
    const channelName = document.getElementById('searchChannelName').value;
    const status = document.getElementById('searchStatus').value;
    const search = document.getElementById('searchKeyword').value.trim();

    if (year) currentFilters.year = year;
    if (promotionType) currentFilters.promotion_type = promotionType;
    if (channelName) currentFilters.channel_name = channelName;
    if (status) currentFilters.status = status;
    if (search) currentFilters.search = search;

    hideDetail();
    loadData(1, paginationManager.getLimit());
}

function resetFilters() {
    document.getElementById('searchYear').value = new Date().getFullYear();
    document.getElementById('searchPromotionType').value = '';
    document.getElementById('searchChannelName').value = '';
    document.getElementById('searchStatus').value = '';
    document.getElementById('searchKeyword').value = '';
    currentFilters = {};

    hideDetail();
    loadData(1, paginationManager.getLimit());
}

function changeLimit() {
    const limit = parseInt(document.getElementById('limitSelector').value);
    loadData(1, limit);
}

function selectAllVisible() {
    // TableManager는 현재 페이지의 모든 행을 선택하는 기능을 제공하지 않음 (UI 상의 selectAll 체크박스 제외).
    // 하지만 UI 상의 selectAll 체크박스를 클릭하게 하거나, 내부 메서드를 호출할 수 있음.
    // TableManager의 _handleSelectAll(true)를 호출하면 됨.
    // 하지만 _handleSelectAll은 private 메서드임.
    // TableManager에 selectAll() 메서드를 추가하거나, 여기서 직접 DOM 조작.

    // 가장 쉬운 방법: 헤더의 체크박스를 클릭하게 함.
    const selectAllCb = document.getElementById('select-all');
    if (selectAllCb && !selectAllCb.checked) {
        selectAllCb.click();
    }
}

function updateActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const deleteBtn = document.getElementById('deleteButton');
    if (hasSelection) {
        deleteBtn.classList.remove('btn-disabled');
    } else {
        deleteBtn.classList.add('btn-disabled');
    }
}

async function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개 행사를 삭제하시겠습니까?\n(연관된 상품 정보도 함께 삭제됩니다)`, async () => {
        try {
            await api.post('/api/promotions/bulk-delete', { ids: selectedIds });

            showAlert(`삭제 완료되었습니다.`, 'success');
            masterTableManager.clearSelection();
            updateActionButtons([]);
            hideDetail();
            loadData(paginationManager.getCurrentPage(), paginationManager.getLimit());
        } catch (e) {
            showAlert('오류: ' + e.message, 'error');
        }
    });
}

function downloadTemplate() {
    window.location.href = '/api/promotions/download/template';
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

        const res = await fetch('/api/promotions/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';

        if (res.ok) {
            const result = await res.json();

            // Promotion 통계
            document.getElementById('uploadPromotionTotal').textContent = result.promotion?.total_rows?.toLocaleString() || 0;
            document.getElementById('uploadPromotionInserted').textContent = result.promotion?.inserted?.toLocaleString() || 0;
            document.getElementById('uploadPromotionUpdated').textContent = result.promotion?.updated?.toLocaleString() || 0;

            // PromotionProduct 통계
            document.getElementById('uploadProductTotal').textContent = result.promotion_product?.total_rows?.toLocaleString() || 0;
            document.getElementById('uploadProductInserted').textContent = result.promotion_product?.inserted?.toLocaleString() || 0;
            document.getElementById('uploadProductUpdated').textContent = result.promotion_product?.updated?.toLocaleString() || 0;

            // 경고 메시지
            const warnings = [];
            if (result.warnings?.unmapped_brands?.count > 0) {
                const brandList = result.warnings.unmapped_brands.items?.slice(0, 10).map(b => `<span style="color:var(--danger);font-weight:600;">${b}</span>`).join(', ');
                const more = result.warnings.unmapped_brands.count > 10 ? ` 외 ${result.warnings.unmapped_brands.count - 10}건` : '';
                warnings.push(`<strong>브랜드 매핑 실패 ${result.warnings.unmapped_brands.count}건:</strong><br><span style="margin-left:8px;">${brandList}${more}</span>`);
            }
            if (result.warnings?.unmapped_channels?.count > 0) {
                const channelList = result.warnings.unmapped_channels.items?.slice(0, 10).map(c => `<span style="color:var(--danger);font-weight:600;">${c}</span>`).join(', ');
                const more = result.warnings.unmapped_channels.count > 10 ? ` 외 ${result.warnings.unmapped_channels.count - 10}건` : '';
                warnings.push(`<strong>채널 매핑 실패 ${result.warnings.unmapped_channels.count}건:</strong><br><span style="margin-left:8px;">${channelList}${more}</span>`);
            }
            if (result.warnings?.unmapped_products?.count > 0) {
                const productList = result.warnings.unmapped_products.items?.slice(0, 10).map(p => `<span style="color:var(--danger);font-weight:600;">${p}</span>`).join(', ');
                const more = result.warnings.unmapped_products.count > 10 ? ` 외 ${result.warnings.unmapped_products.count - 10}건` : '';
                warnings.push(`<strong>상품코드 매핑 실패 ${result.warnings.unmapped_products.count}건:</strong><br><span style="margin-left:8px;">${productList}${more}</span>`);
            }

            if (warnings.length > 0) {
                document.getElementById('uploadWarnings').style.display = 'block';
                document.getElementById('uploadWarningContent').innerHTML = warnings.map(w => `<div style="margin-bottom:12px;line-height:1.6;">• ${w}</div>`).join('');
            } else {
                document.getElementById('uploadWarnings').style.display = 'none';
            }

            uploadModal.hide();
            uploadResultModal.show();

            // 채널명 옵션 새로고침
            loadFilterOptions();

            if (Object.keys(currentFilters).length > 0) {
                loadData(1, paginationManager.getLimit());
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
