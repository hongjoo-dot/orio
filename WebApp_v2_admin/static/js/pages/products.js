let masterTableManager, detailTableManager, paginationManager;
let integratedAddModal, addBoxModal, bulkEditProductModal, bulkEditBoxModal, bomAfterCreateModal;
let currentFilters = {};
let currentProductId = null;
let currentSortBy = null;
let currentSortDir = null;
let bomChildRowCounter = 0;
let bulkEditOriginalData = {};
let cachedBrands = [];
let cachedSelectOptions = { TypeERP: [], TypeDB: [], BundleType: [], Status: [] };

// 마스터 테이블 컬럼
const masterColumns = [
    { key: 'ProductID', header: 'ID', sortKey: 'ProductID', render: (row) => row.ProductID },
    { key: 'BrandName', header: '브랜드', sortKey: 'BrandName', render: (row) => row.BrandName || '-' },
    { key: 'Name', header: '제품명', sortKey: 'Name', render: (row) => row.Name || '-' },
    { key: 'UniqueCode', header: '고유코드', sortKey: 'UniqueCode', render: (row) => row.UniqueCode || '-' },
    { key: 'BaseBarcode', header: '바코드', sortKey: 'BaseBarcode', render: (row) => row.BaseBarcode || '-' },
    { key: 'SabangnetCode', header: '사방넷코드', sortKey: 'SabangnetCode', render: (row) => row.SabangnetCode || '-' },
    { key: 'Status', header: '상태', sortKey: 'Status', render: (row) => row.Status || '-' }
];

// 디테일 테이블 컬럼
const detailColumns = [
    { key: 'BoxID', header: 'ID', render: (row) => row.BoxID },
    { key: 'ERPCode', header: 'ERP코드', render: (row) => row.ERPCode || '-' },
    { key: 'QuantityInBox', header: '입수량', render: (row) => row.QuantityInBox || '-' }
];

document.addEventListener('DOMContentLoaded', async function () {
    // 모달 초기화
    integratedAddModal = new ModalManager('integratedAddModal');
    addBoxModal = new ModalManager('addBoxModal');
    bulkEditProductModal = new ModalManager('bulkEditProductModal');
    bulkEditBoxModal = new ModalManager('bulkEditBoxModal');
    bomAfterCreateModal = new ModalManager('bomAfterCreateModal');

    // 테이블 매니저 초기화
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'ProductID',
        onSelectionChange: (selectedIds) => updateActionButtons(selectedIds),
        onRowClick: (row, tr) => selectProduct(row, tr),
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadProducts(1, paginationManager.getLimit());
        },
        emptyMessage: '데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    detailTableManager = new TableManager('detail-table', {
        selectable: true,
        idKey: 'BoxID',
        onSelectionChange: (selectedIds) => updateBoxActionButtons(selectedIds),
        emptyMessage: '박스가 없습니다.'
    });
    detailTableManager.renderHeader(detailColumns);

    // 페이지네이션 매니저 초기화
    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadProducts(page, limit),
        onLimitChange: (page, limit) => loadProducts(page, limit)
    });

    // 초기 데이터 로드
    await Promise.all([
        loadBrands(),
        loadProductMetadata(),
        loadERPCodes()
    ]);

    loadProducts(1, 20);

    // 엔터키 검색 지원
    ['filterBrand', 'filterName', 'filterUniqueCode', 'filterBundleType'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyFilters();
            });
        }
    });
});

async function loadProducts(page = 1, limit = 20) {
    try {
        masterTableManager.showLoading(7);

        const params = { page, limit, sort_by: currentSortBy, sort_dir: currentSortDir, ...currentFilters };
        const queryString = api.buildQueryString(params);
        const res = await api.get(`/api/products${queryString}`);

        // 필터링 카운트 표시
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
        showAlert('제품 로드 실패: ' + e.message, 'error');
        masterTableManager.render([], masterColumns);
    }
}

async function selectProduct(row, tr) {
    // 행 선택 스타일 처리
    const rows = document.querySelectorAll('#master-table tbody tr');
    rows.forEach(r => r.classList.remove('selected'));
    tr.classList.add('selected');

    currentProductId = row.ProductID;
    loadBoxes(currentProductId);
}

async function loadBoxes(productId) {
    try {
        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('boxTableContainer').style.display = 'block';
        document.getElementById('boxActionButtons').style.display = 'flex';
        document.getElementById('boxCount').style.display = 'block';

        detailTableManager.showLoading(3);
        const res = await api.get(`/api/productboxes?product_id=${productId}`);

        document.getElementById('boxCount').textContent = `박스 ${res.data.length}개`;
        detailTableManager.render(res.data, detailColumns);

    } catch (e) {
        showAlert('박스 로드 실패: ' + e.message, 'error');
        detailTableManager.render([], detailColumns);
    }
}

// ... (loadBrands, loadProductTypes 등 기존 로직을 api.get으로 변경) ...

async function loadBrands() {
    try {
        const res = await api.get('/api/brands/all');
        const brands = res.data || [];
        cachedBrands = brands;

        // 필터용
        const uniqueTitles = [...new Set(brands.filter(b => b.Title).map(b => b.Title))];
        const filterOptions = uniqueTitles.sort().map(title => `<option value="${title}">${title}</option>`).join('');
        document.getElementById('filterBrand').innerHTML = '<option value="">전체</option>' + filterOptions;

        // 모달용
        const brandOptions = brands.sort((a, b) => (a.Name || '').localeCompare(b.Name || '')).map(brand => `<option value="${brand.BrandID}">${brand.Name}</option>`).join('');
        document.getElementById('intBrand').innerHTML = '<option value="">선택</option>' + brandOptions;
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

async function loadProductMetadata() {
    try {
        const res = await api.get('/api/products?limit=10000');
        const data = res.data || [];

        // Select 옵션 세팅 (TypeERP, TypeDB, BundleType, Status)
        const setupOptions = (key, elementIds) => {
            const values = [...new Set(data.filter(p => p[key]).map(p => p[key]))].sort();
            const options = values.map(v => `<option value="${v}">${v}</option>`).join('');

            elementIds.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    const defaultText = id.startsWith('filter') ? '전체' : (id.startsWith('bulk') ? '변경하지 않음' : '선택');
                    el.innerHTML = `<option value="">${defaultText}</option>` + options;
                }
            });
        };

        setupOptions('TypeERP', ['intTypeERP']);
        setupOptions('TypeDB', ['intTypeDB']);
        setupOptions('BundleType', ['intBundleType', 'filterBundleType']);
        setupOptions('Status', ['intStatus']);

        // 테이블 수정 모달용 옵션 캐시
        ['TypeERP', 'TypeDB', 'BundleType', 'Status'].forEach(key => {
            cachedSelectOptions[key] = [...new Set(data.filter(p => p[key]).map(p => p[key]))].sort();
        });

        // Datalist 세팅 (CategoryMid, CategorySub, UniqueCode, Name)
        const setupDatalist = (key, listId) => {
            const values = [...new Set(data.filter(p => p[key]).map(p => p[key]))].sort();
            document.getElementById(listId).innerHTML = values.map(v => `<option value="${v}">`).join('');
        };

        setupDatalist('CategoryMid', 'categoryMidList');
        setupDatalist('CategorySub', 'categorySubList');
        setupDatalist('UniqueCode', 'uniqueCodeList');
        setupDatalist('Name', 'nameList');
    } catch (e) {
        console.error('제품 메타데이터 로드 실패:', e);
    }
}

async function loadERPCodes() {
    try {
        const res = await api.get('/api/productboxes?limit=10000');
        const values = [...new Set(res.data.filter(b => b.ERPCode).map(b => b.ERPCode))].sort();
        document.getElementById('erpCodeList').innerHTML = values.map(v => `<option value="${v}">`).join('');
    } catch (e) {
        console.error('ERP코드 로드 실패:', e);
    }
}

function applyFilters() {
    currentFilters = {};
    const brand = document.getElementById('filterBrand').value;
    const uniqueCode = document.getElementById('filterUniqueCode').value.trim();
    const name = document.getElementById('filterName').value.trim();
    const bundleType = document.getElementById('filterBundleType').value;

    if (brand) currentFilters.brand = brand;
    if (uniqueCode) currentFilters.unique_code = uniqueCode;
    if (name) currentFilters.name = name;
    if (bundleType) currentFilters.bundle_type = bundleType;

    // 디테일 초기화
    currentProductId = null;
    document.getElementById('detailPlaceholder').style.display = 'block';
    document.getElementById('boxTableContainer').style.display = 'none';
    document.getElementById('boxActionButtons').style.display = 'none';
    document.getElementById('boxCount').style.display = 'none';
    detailTableManager.render([], detailColumns);

    loadProducts(1, paginationManager.getLimit());
}

function resetFilters() {
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterUniqueCode').value = '';
    document.getElementById('filterName').value = '';
    document.getElementById('filterBundleType').value = '';
    currentFilters = {};

    applyFilters();
}

function changeLimit() {
    const limit = parseInt(document.getElementById('limitSelector').value);
    loadProducts(1, limit);
}

function updateActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('editButton');
    const deleteBtn = document.getElementById('deleteButton');

    if (hasSelection) {
        editBtn.classList.remove('btn-disabled');
        deleteBtn.classList.remove('btn-disabled');
        editBtn.disabled = false;
        deleteBtn.disabled = false;
    } else {
        editBtn.classList.add('btn-disabled');
        deleteBtn.classList.add('btn-disabled');
        editBtn.disabled = true;
        deleteBtn.disabled = true;
    }
}

function updateBoxActionButtons(selectedIds) {
    const hasSelection = selectedIds.length > 0;
    const editBtn = document.getElementById('editBoxButton');
    const deleteBtn = document.getElementById('deleteBoxButton');

    if (hasSelection) {
        editBtn.classList.remove('btn-disabled');
        deleteBtn.classList.remove('btn-disabled');
        editBtn.disabled = false;
        deleteBtn.disabled = false;
    } else {
        editBtn.classList.add('btn-disabled');
        deleteBtn.classList.add('btn-disabled');
        editBtn.disabled = true;
        deleteBtn.disabled = true;
    }
}

function selectAllData() {
    showConfirm('현재 필터 조건의 모든 데이터를 선택하시겠습니까?', async () => {
        try {
            const params = { limit: 10000, ...currentFilters };
            const queryString = api.buildQueryString(params);
            const res = await api.get(`/api/products${queryString}`);

            res.data.forEach(p => masterTableManager.selectedRows.add(p.ProductID.toString()));

            // 현재 화면 체크박스 업데이트
            const checkboxes = document.querySelectorAll('#master-table .row-checkbox');
            checkboxes.forEach(cb => {
                if (masterTableManager.selectedRows.has(cb.dataset.id)) {
                    cb.checked = true;
                }
            });

            updateActionButtons(Array.from(masterTableManager.selectedRows));
            showAlert(`${masterTableManager.selectedRows.size}개의 제품이 선택되었습니다.`, 'success');
        } catch (e) {
            showAlert('전체 선택 실패: ' + e.message, 'error');
        }
    });
}

// ========== 모달 관련 함수들 ==========

function showIntegratedAddModal() {
    // 입력 필드 초기화
    const inputs = document.querySelectorAll('#integratedAddModal input, #integratedAddModal select');
    inputs.forEach(input => input.value = '');
    document.getElementById('intQuantityInBox').value = '1';

    integratedAddModal.show();
}

function closeIntegratedAddModal() {
    integratedAddModal.hide();
}

async function saveIntegrated() {
    const uniqueCode = document.getElementById('intUniqueCode').value.trim();
    const name = document.getElementById('intName').value.trim();
    const typeERP = document.getElementById('intTypeERP').value.trim();
    const typeDB = document.getElementById('intTypeDB').value.trim();
    const erpCode = document.getElementById('intERPCode').value.trim();

    if (!uniqueCode || !name || !typeERP || !typeDB || !erpCode) {
        showAlert('UniqueCode, Name, TypeERP, TypeDB, ERPCode는 필수입니다.', 'error');
        return;
    }

    const brandID = document.getElementById('intBrand').value;

    const productData = {
        BrandID: brandID ? parseInt(brandID) : null,
        UniqueCode: uniqueCode,
        Name: name,
        TypeERP: typeERP,
        TypeDB: typeDB,
        BaseBarcode: document.getElementById('intBaseBarcode').value.trim() || null,
        Barcode2: document.getElementById('intBarcode2').value.trim() || null,
        SabangnetCode: document.getElementById('intSabangnetCode').value.trim() || null,
        SabangnetUniqueCode: document.getElementById('intSabangnetUniqueCode').value.trim() || null,
        BundleType: document.getElementById('intBundleType').value || null,
        CategoryMid: document.getElementById('intCategoryMid').value.trim() || null,
        CategorySub: document.getElementById('intCategorySub').value.trim() || null,
        Status: document.getElementById('intStatus').value || null,
        ReleaseDate: document.getElementById('intReleaseDate').value || null
    };

    const boxData = {
        ERPCode: erpCode,
        QuantityInBox: parseInt(document.getElementById('intQuantityInBox').value) || 1
    };

    const bundleType = document.getElementById('intBundleType').value;

    try {
        await api.post('/api/products/integrated', { product: productData, box: boxData });
        closeIntegratedAddModal();

        if (bundleType === 'SET') {
            await showBOMAfterCreateModal(erpCode);
        } else {
            showAlert('제품과 박스가 추가되었습니다.', 'success');
            loadProducts(1, paginationManager.getLimit());
        }
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

function showAddBoxModal() {
    if (!currentProductId) {
        showAlert('제품을 먼저 선택하세요.', 'warning');
        return;
    }
    document.getElementById('boxERPCode').value = '';
    document.getElementById('boxQuantityInBox').value = '1';
    addBoxModal.show();
}

function closeAddBoxModal() {
    addBoxModal.hide();
}

async function saveBox() {
    const erpCode = document.getElementById('boxERPCode').value.trim();
    if (!erpCode) {
        showAlert('품목코드(ERPCode)는 필수입니다.', 'error');
        return;
    }

    const data = {
        ProductID: currentProductId,
        ERPCode: erpCode,
        QuantityInBox: parseInt(document.getElementById('boxQuantityInBox').value) || 1
    };

    try {
        await api.post('/api/productboxes', data);
        showAlert('박스가 추가되었습니다.', 'success');
        closeAddBoxModal();
        loadBoxes(currentProductId);
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

async function bulkEdit() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('수정할 제품을 선택하세요.', 'warning');
        return;
    }

    try {
        const products = await Promise.all(selectedIds.map(id => api.get(`/api/products/${id}`)));
        document.getElementById('bulkEditProductCount').textContent = products.length;

        bulkEditOriginalData = {};
        const tbody = document.getElementById('bulkEditTableBody');
        tbody.innerHTML = '';

        const brandOpts = cachedBrands.sort((a, b) => (a.Name || '').localeCompare(b.Name || '')).map(b => `<option value="${b.BrandID}">${b.Name}</option>`).join('');
        const selectOptHtml = (key, currentVal) => {
            return cachedSelectOptions[key].map(v => `<option value="${v}" ${v === currentVal ? 'selected' : ''}>${v}</option>`).join('');
        };

        for (const p of products) {
            const id = p.ProductID;
            bulkEditOriginalData[id] = {
                BrandID: p.BrandID ? String(p.BrandID) : '',
                UniqueCode: p.UniqueCode || '',
                Name: p.Name || '',
                TypeERP: p.TypeERP || '',
                TypeDB: p.TypeDB || '',
                BaseBarcode: p.BaseBarcode || '',
                Barcode2: p.Barcode2 || '',
                SabangnetCode: p.SabangnetCode || '',
                SabangnetUniqueCode: p.SabangnetUniqueCode || '',
                BundleType: p.BundleType || '',
                CategoryMid: p.CategoryMid || '',
                CategorySub: p.CategorySub || '',
                Status: p.Status || '',
                ReleaseDate: p.ReleaseDate ? p.ReleaseDate.split('T')[0] : ''
            };

            const tr = document.createElement('tr');
            tr.dataset.productId = id;
            tr.innerHTML = `
                <td class="sticky-col"><span class="cell-id">${id}</span></td>
                <td><select class="cell-select" data-field="BrandID" data-original="${p.BrandID || ''}">
                    <option value="">-</option>${brandOpts}
                </select></td>
                <td><input class="cell-input" data-field="UniqueCode" value="${p.UniqueCode || ''}" list="uniqueCodeList"></td>
                <td><input class="cell-input" data-field="Name" value="${p.Name || ''}" style="min-width:160px;" list="nameList"></td>
                <td><select class="cell-select" data-field="TypeERP">
                    <option value="">-</option>${selectOptHtml('TypeERP', p.TypeERP)}
                </select></td>
                <td><select class="cell-select" data-field="TypeDB">
                    <option value="">-</option>${selectOptHtml('TypeDB', p.TypeDB)}
                </select></td>
                <td><input class="cell-input" data-field="BaseBarcode" value="${p.BaseBarcode || ''}"></td>
                <td><input class="cell-input" data-field="Barcode2" value="${p.Barcode2 || ''}"></td>
                <td><input class="cell-input" data-field="SabangnetCode" value="${p.SabangnetCode || ''}"></td>
                <td><input class="cell-input" data-field="SabangnetUniqueCode" value="${p.SabangnetUniqueCode || ''}"></td>
                <td><select class="cell-select" data-field="BundleType">
                    <option value="">-</option>${selectOptHtml('BundleType', p.BundleType)}
                </select></td>
                <td><input class="cell-input" data-field="CategoryMid" value="${p.CategoryMid || ''}" list="categoryMidList"></td>
                <td><input class="cell-input" data-field="CategorySub" value="${p.CategorySub || ''}" list="categorySubList"></td>
                <td><select class="cell-select" data-field="Status">
                    <option value="">-</option>${selectOptHtml('Status', p.Status)}
                </select></td>
                <td><input class="cell-input" type="date" data-field="ReleaseDate" value="${p.ReleaseDate ? p.ReleaseDate.split('T')[0] : ''}"></td>
            `;

            // 브랜드 select 초기값 설정
            const brandSelect = tr.querySelector('[data-field="BrandID"]');
            if (p.BrandID) brandSelect.value = String(p.BrandID);

            tbody.appendChild(tr);
        }

        // 변경 감지 이벤트
        tbody.addEventListener('input', handleBulkEditCellChange);
        tbody.addEventListener('change', handleBulkEditCellChange);

        bulkEditProductModal.show();
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function handleBulkEditCellChange(e) {
    const el = e.target;
    const field = el.dataset.field;
    if (!field) return;

    const tr = el.closest('tr');
    const productId = tr.dataset.productId;
    const original = bulkEditOriginalData[productId];
    if (!original) return;

    const currentVal = el.value;
    const originalVal = original[field];

    if (currentVal !== originalVal) {
        el.classList.add('cell-changed');
    } else {
        el.classList.remove('cell-changed');
    }
}

function closeBulkEditProductModal() {
    bulkEditProductModal.hide();
    bulkEditOriginalData = {};
}

async function saveBulkEditProduct() {
    const tbody = document.getElementById('bulkEditTableBody');
    const rows = tbody.querySelectorAll('tr');
    const updates = [];

    for (const tr of rows) {
        const productId = tr.dataset.productId;
        const original = bulkEditOriginalData[productId];
        if (!original) continue;

        const updateData = {};
        const cells = tr.querySelectorAll('.cell-input, .cell-select');

        for (const cell of cells) {
            const field = cell.dataset.field;
            const currentVal = cell.value;
            const originalVal = original[field];

            if (currentVal !== originalVal) {
                if (field === 'BrandID') {
                    updateData[field] = currentVal ? parseInt(currentVal) : null;
                } else {
                    updateData[field] = currentVal || null;
                }
            }
        }

        if (Object.keys(updateData).length > 0) {
            updates.push({ id: productId, data: updateData });
        }
    }

    if (updates.length === 0) {
        showAlert('변경된 항목이 없습니다.', 'warning');
        return;
    }

    try {
        const promises = updates.map(u => api.put(`/api/products/${u.id}`, u.data));
        await Promise.all(promises);
        showAlert(`${updates.length}개 제품이 수정되었습니다.`, 'success');
        closeBulkEditProductModal();
        masterTableManager.clearSelection();
        loadProducts(paginationManager.getCurrentPage(), paginationManager.getLimit());
    } catch (e) {
        showAlert('수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    const selectedIds = masterTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개의 제품을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/products/bulk-delete', { ids: selectedIds.map(id => parseInt(id)) });
            showAlert('제품이 삭제되었습니다.', 'success');
            masterTableManager.clearSelection();
            loadProducts(paginationManager.getCurrentPage(), paginationManager.getLimit());

            if (selectedIds.includes(currentProductId?.toString())) {
                currentProductId = null;
                document.getElementById('detailPlaceholder').style.display = 'block';
                document.getElementById('boxTableContainer').style.display = 'none';
            }
        } catch (e) {
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

async function bulkEditBoxes() {
    const selectedIds = detailTableManager.getSelectedRows();
    if (selectedIds.length === 0) {
        showAlert('수정할 박스를 선택하세요.', 'warning');
        return;
    }

    document.getElementById('bulkEditBoxCount').textContent = selectedIds.length;
    bulkEditBoxModal.show();
}

function closeBulkEditBoxModal() {
    bulkEditBoxModal.hide();
}

async function saveBulkEditBox() {
    const selectedIds = detailTableManager.getSelectedRows();
    const newERPCode = document.getElementById('bulkERPCode').value.trim();
    const newQuantityInBox = document.getElementById('bulkQuantityInBox').value;

    if (!newERPCode && !newQuantityInBox) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = selectedIds.map(async id => {
            const box = await api.get(`/api/productboxes/${id}`);
            const updateData = {
                ProductID: box.ProductID,
                ERPCode: newERPCode || box.ERPCode,
                QuantityInBox: newQuantityInBox ? parseInt(newQuantityInBox) : box.QuantityInBox
            };
            return api.put(`/api/productboxes/${id}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedIds.length}개 박스가 수정되었습니다.`, 'success');
        closeBulkEditBoxModal();
        detailTableManager.clearSelection();
        loadBoxes(currentProductId);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDeleteBoxes() {
    const selectedIds = detailTableManager.getSelectedRows();
    if (selectedIds.length === 0) return;

    showConfirm(`선택한 ${selectedIds.length}개의 박스를 삭제하시겠습니까?`, async () => {
        try {
            const promises = selectedIds.map(id => api.delete(`/api/productboxes/${id}`));
            await Promise.all(promises);
            showAlert(`${selectedIds.length}개 박스가 삭제되었습니다.`, 'success');
            detailTableManager.clearSelection();
            loadBoxes(currentProductId);
        } catch (e) {
            showAlert('일괄 삭제 실패: ' + e.message, 'error');
        }
    });
}

function downloadExcel() {
    const params = { ...currentFilters };
    const queryString = api.buildQueryString(params);
    const downloadUrl = `/api/products/download/excel${queryString}`;
    window.location.href = downloadUrl;
    showAlert('엑셀 파일 다운로드를 시작합니다.', 'success');
}

// ========== BOM 연계 함수들 (SET 상품 등록 후) ==========

async function showBOMAfterCreateModal(parentERPCode) {
    document.getElementById('bomParentERPCode').value = parentERPCode;
    document.getElementById('bomChildRowsContainer').innerHTML = '';
    bomChildRowCounter = 0;

    // 구성품 품목코드 자동완성 로드
    try {
        const res = await api.get('/api/bom/metadata');
        const items = res.child_erp_codes || [];
        document.getElementById('bomChildERPList').innerHTML = items.map(v => `<option value="${v}">`).join('');
    } catch (e) {
        console.error('BOM 메타데이터 로드 실패:', e);
    }

    addBOMChildRow();
    bomAfterCreateModal.show();
}

function addBOMChildRow() {
    const container = document.getElementById('bomChildRowsContainer');
    const rowId = `bomChildRow_${bomChildRowCounter++}`;

    const rowDiv = document.createElement('div');
    rowDiv.id = rowId;
    rowDiv.className = 'form-group';
    rowDiv.style.cssText = 'display:grid;grid-template-columns:1fr 120px 40px;gap:12px;align-items:end;padding:12px;background:rgba(0,0,0,0.02);border-radius:8px;margin-bottom:12px;';

    rowDiv.innerHTML = `
        <div>
            <label class="form-label required">구성품 품목코드</label>
            <input type="text" class="form-input bom-child-erp" list="bomChildERPList" placeholder="예: PART-001" required>
        </div>
        <div>
            <label class="form-label">소요수량</label>
            <input type="number" class="form-input bom-child-quantity" value="1" step="0.01" min="0.01">
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeBOMChildRow('${rowId}')" style="height:38px;">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;

    container.appendChild(rowDiv);
}

window.addBOMChildRow = addBOMChildRow;
window.removeBOMChildRow = function (rowId) {
    const row = document.getElementById(rowId);
    if (row) row.remove();
    const container = document.getElementById('bomChildRowsContainer');
    if (container.children.length === 0) addBOMChildRow();
};

async function saveBOMAfterCreate() {
    const parentERP = document.getElementById('bomParentERPCode').value.trim();
    const childERPs = document.querySelectorAll('.bom-child-erp');
    const childQuantities = document.querySelectorAll('.bom-child-quantity');
    const children = [];

    for (let i = 0; i < childERPs.length; i++) {
        const childERP = childERPs[i].value.trim();
        const quantity = parseFloat(childQuantities[i].value) || 1;

        if (!childERP) {
            showAlert(`${i + 1}번째 구성품의 품목코드를 입력하세요.`, 'error');
            return;
        }

        children.push({
            ParentERPCode: parentERP,
            ChildERPCode: childERP,
            QuantityRequired: quantity
        });
    }

    if (children.length === 0) {
        showAlert('최소 1개 이상의 구성품이 필요합니다.', 'error');
        return;
    }

    let successCount = 0;
    let failCount = 0;
    const errors = [];

    for (const child of children) {
        try {
            await api.post('/api/bom', child);
            successCount++;
        } catch (e) {
            failCount++;
            errors.push(`${child.ChildERPCode}: ${e.message}`);
        }
    }

    if (successCount > 0) {
        showAlert(`BOM이 추가되었습니다. (성공: ${successCount}개, 실패: ${failCount}개)`, failCount > 0 ? 'warning' : 'success');
    } else {
        showAlert(`BOM 추가 실패:\n${errors.join('\n')}`, 'error');
    }

    bomAfterCreateModal.hide();
    loadProducts(1, paginationManager.getLimit());
}

function skipBOMAfterCreate() {
    bomAfterCreateModal.hide();
    loadProducts(1, paginationManager.getLimit());
}
