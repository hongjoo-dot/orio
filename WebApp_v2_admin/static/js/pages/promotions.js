let currentPage = 1, limit = 20, currentFilters = {}, selectedIds = new Set();
let uploadModal, uploadResultModal;
let filterOptions = { promotion_types: [], statuses: [], channel_names: [] };
let selectedPromotionId = null;

document.addEventListener('DOMContentLoaded', function () {
    uploadModal = new ModalManager('uploadModal');
    uploadResultModal = new ModalManager('uploadResultModal');

    initYearOptions();
    loadFilterOptions();
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
        const res = await fetch('/api/promotions/filter-options');
        filterOptions = await res.json();

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

async function loadData() {
    try {
        const params = new URLSearchParams({ page: currentPage, limit, ...currentFilters });
        const res = await fetch(`/api/promotions?${params}`);
        const data = await res.json();

        const tbody = document.getElementById('masterTable');
        tbody.innerHTML = data.data.length === 0
            ? '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted);">데이터가 없습니다.</td></tr>'
            : data.data.map(item => `
                <tr class="master-row ${selectedPromotionId === item.PromotionID ? 'selected' : ''}"
                    onclick="showDetail('${item.PromotionID}', '${item.PromotionName}')"
                    style="cursor:pointer;">
                    <td style="text-align:center;" onclick="event.stopPropagation();">
                        <input type="checkbox" class="row-checkbox" value="${item.PromotionID}" onchange="toggleRowSelect()">
                    </td>
                    <td><strong>${item.PromotionID}</strong></td>
                    <td>${item.PromotionName || '-'}</td>
                    <td>${item.ChannelName || '-'}</td>
                    <td>
                        <span class="badge badge-type-${getTypeClass(item.PromotionType)}">
                            ${item.PromotionTypeDisplay || item.PromotionType || '-'}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-status-${item.Status?.toLowerCase()}">
                            ${item.StatusDisplay || item.Status || '-'}
                        </span>
                    </td>
                    <td style="text-align:right;">${item.TargetSalesAmount?.toLocaleString() || 0}</td>
                    <td style="font-size:13px;">${item.StartDate || ''} ~ ${item.EndDate || ''}</td>
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

function getTypeClass(type) {
    if (!type) return 'default';
    if (type.startsWith('ONLINE')) return 'online';
    if (type.startsWith('OFFLINE')) return 'offline';
    return 'default';
}

async function showDetail(promotionId, promotionName) {
    selectedPromotionId = promotionId;

    // 행 선택 표시 업데이트
    document.querySelectorAll('.master-row').forEach(row => row.classList.remove('selected'));
    event.currentTarget.classList.add('selected');

    document.getElementById('detailTitle').textContent = `${promotionName} - 상품 목록`;
    document.getElementById('detailSection').style.display = 'block';

    try {
        const res = await fetch(`/api/promotions/${promotionId}/products`);
        const result = await res.json();
        const products = result.data || [];

        const tbody = document.getElementById('detailTable');
        tbody.innerHTML = products.length === 0
            ? '<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-muted);">등록된 상품이 없습니다.</td></tr>'
            : products.map(p => `
                <tr>
                    <td><strong>${p.Uniquecode || '-'}</strong></td>
                    <td>${p.ProductName || '-'}</td>
                    <td style="text-align:right;">${p.SellingPrice?.toLocaleString() || '-'}</td>
                    <td style="text-align:right;">${p.PromotionPrice?.toLocaleString() || '-'}</td>
                    <td style="text-align:right;">${p.TargetQuantity?.toLocaleString() || '-'}</td>
                    <td style="text-align:right;">${p.TargetSalesAmount?.toLocaleString() || '-'}</td>
                </tr>
            `).join('');

        // 스크롤 이동
        document.getElementById('detailSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) {
        showAlert('상품 목록 로드 실패: ' + e.message, 'error');
    }
}

function hideDetail() {
    selectedPromotionId = null;
    document.getElementById('detailSection').style.display = 'none';
    document.querySelectorAll('.master-row').forEach(row => row.classList.remove('selected'));
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

    currentPage = 1;
    hideDetail();
    loadData();
}

function resetFilters() {
    document.getElementById('searchYear').value = new Date().getFullYear();
    document.getElementById('searchPromotionType').value = '';
    document.getElementById('searchChannelName').value = '';
    document.getElementById('searchStatus').value = '';
    document.getElementById('searchKeyword').value = '';
    currentFilters = {};
    currentPage = 1;
    hideDetail();

    document.getElementById('masterTable').innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fa-solid fa-search" style="font-size:48px;margin-bottom:16px;opacity:0.5;"></i><p>검색 조건을 입력하고 검색 버튼을 클릭하세요.</p></td></tr>';
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
        if (checked) selectedIds.add(cb.value);
        else selectedIds.delete(cb.value);
    });
    updateActionButtons();
}

function toggleRowSelect() {
    selectedIds.clear();
    document.querySelectorAll('.row-checkbox:checked').forEach(cb => selectedIds.add(cb.value));
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

    showConfirm(`선택한 ${selectedIds.size}개 행사를 삭제하시겠습니까?\n(연관된 상품 정보도 함께 삭제됩니다)`, async () => {
        try {
            const res = await fetch('/api/promotions/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: Array.from(selectedIds) })
            });

            if (res.ok) {
                const result = await res.json();
                showAlert(`삭제 완료: 행사 ${result.deleted_count}건, 상품 ${result.deleted_products}건`, 'success');
                selectedIds.clear();
                updateActionButtons();
                hideDetail();
                loadData();
            } else {
                showAlert('삭제 실패', 'error');
            }
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
