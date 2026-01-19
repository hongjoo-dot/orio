let currentPage = 1;
let limit = 20;
let currentFilters = {};
let selectedIds = new Set();
let selectedBoxIds = new Set();
let currentProductId = null;

document.addEventListener('DOMContentLoaded', async function () {
    await loadProducts();
    await loadBrands();
    await loadProductTypes();
    await loadCategories();
    await loadERPCodes();
    await loadUniqueCodes();
    await loadProductNames();
});

async function loadProducts() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: limit,
            ...currentFilters
        });

        const res = await api.get(`/api/products?${params}`);

        // 필터링 여부 확인
        const isFiltered = Object.keys(currentFilters).length > 0;
        if (isFiltered) {
            document.getElementById('totalCount').textContent = `전체 ${res.total}개`;
            document.getElementById('filteredCount').textContent = `필터링됨: ${res.data.length}개`;
        } else {
            document.getElementById('totalCount').textContent = `총 ${res.total}개`;
            document.getElementById('filteredCount').textContent = '';
        }

        const tbody = document.getElementById('productTableBody');
        tbody.innerHTML = '';

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--text-muted);">데이터가 없습니다</td></tr>';
        } else {
            res.data.forEach(p => {
                const tr = document.createElement('tr');
                if (selectedIds.has(p.ProductID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedIds.has(p.ProductID) ? 'checked' : ''} onchange="toggleSelect(${p.ProductID}, event)"></td>
                    <td>${p.ProductID || ''}</td>
                    <td>${p.BrandName || ''}</td>
                    <td>${p.Name || ''}</td>
                    <td>${p.UniqueCode || ''}</td>
                    <td>${p.BaseBarcode || ''}</td>
                    <td>${p.SabangnetCode || ''}</td>
                    <td>${p.Status || ''}</td>
                `;

                tr.style.cursor = 'pointer';
                tr.onclick = (e) => selectProduct(p.ProductID, e);
                tbody.appendChild(tr);
            });
        }

        renderPagination(res.total, res.page, res.limit);
        updateBulkButtons();
    } catch (e) {
        showAlert('제품 로드 실패: ' + e.message, 'error');
    }
}

function selectProduct(productId, event) {
    if (event.target.type === 'checkbox' || event.target.tagName === 'BUTTON' || event.target.tagName === 'I') return;

    currentProductId = productId;

    const rows = document.querySelectorAll('#productTable tbody tr');
    rows.forEach(r => r.style.background = '');
    event.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)';

    loadBoxes(productId);
}

async function loadBoxes(productId) {
    try {
        const res = await api.get(`/api/productboxes?product_id=${productId}`);

        document.getElementById('detailPlaceholder').style.display = 'none';
        document.getElementById('boxTableContainer').style.display = 'block';
        document.getElementById('boxActionButtons').style.display = 'flex';
        document.getElementById('boxCount').style.display = 'block';

        const tbody = document.getElementById('boxTableBody');
        tbody.innerHTML = '';
        selectedBoxIds.clear();

        document.getElementById('boxCount').textContent = `박스 ${res.data.length}개`;

        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:2rem;color:var(--text-muted);">박스가 없습니다</td></tr>';
        } else {
            res.data.forEach(b => {
                const tr = document.createElement('tr');
                if (selectedBoxIds.has(b.BoxID)) tr.classList.add('selected');

                tr.innerHTML = `
                    <td><input type="checkbox" ${selectedBoxIds.has(b.BoxID) ? 'checked' : ''} onchange="toggleSelectBox(${b.BoxID}, event)"></td>
                    <td>${b.BoxID || ''}</td>
                    <td>${b.ERPCode || ''}</td>
                    <td>${b.QuantityInBox || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        updateBoxBulkButtons();
    } catch (e) {
        showAlert('박스 로드 실패: ' + e.message, 'error');
    }
}

async function loadBrands() {
    try {
        const res = await api.get('/api/brands/all');
        const brands = res.data || [];

        // 필터용 - Title 사용
        const uniqueTitles = [...new Set(brands.filter(b => b.Title).map(b => b.Title))];
        const filterOptions = uniqueTitles
            .sort()
            .map(title => `<option value="${title}">${title}</option>`)
            .join('');
        document.getElementById('filterBrand').innerHTML = '<option value="">전체</option>' + filterOptions;

        // 통합 추가 모달용 - BrandID를 value로, Name을 표시
        const brandOptions = brands
            .sort((a, b) => (a.Name || '').localeCompare(b.Name || ''))
            .map(brand => `<option value="${brand.BrandID}">${brand.Name}</option>`)
            .join('');
        document.getElementById('intBrand').innerHTML = '<option value="">선택</option>' + brandOptions;

        // 선택 수정 모달용 - BrandID 사용
        document.getElementById('bulkBrand').innerHTML = '<option value="">변경하지 않음</option>' + brandOptions;

        // 편집 모달용 - BrandID 사용
        document.getElementById('editBrand').innerHTML = '<option value="">선택</option>' + brandOptions;
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

async function loadProductTypes() {
    try {
        const res = await api.get('/api/products?limit=10000');

        // TypeERP
        const typeERPs = [...new Set(res.data.filter(p => p.TypeERP).map(p => p.TypeERP))];
        const typeERPOptions = typeERPs.sort().map(type => `<option value="${type}">${type}</option>`).join('');
        document.getElementById('intTypeERP').innerHTML = '<option value="">선택</option>' + typeERPOptions;
        document.getElementById('bulkTypeERP').innerHTML = '<option value="">변경하지 않음</option>' + typeERPOptions;
        document.getElementById('editTypeERP').innerHTML = '<option value="">선택</option>' + typeERPOptions;

        // TypeDB
        const typeDBs = [...new Set(res.data.filter(p => p.TypeDB).map(p => p.TypeDB))];
        const typeDBOptions = typeDBs.sort().map(type => `<option value="${type}">${type}</option>`).join('');
        document.getElementById('intTypeDB').innerHTML = '<option value="">선택</option>' + typeDBOptions;
        document.getElementById('bulkTypeDB').innerHTML = '<option value="">변경하지 않음</option>' + typeDBOptions;
        document.getElementById('editTypeDB').innerHTML = '<option value="">선택</option>' + typeDBOptions;

        // BundleType
        const bundleTypes = [...new Set(res.data.filter(p => p.BundleType).map(p => p.BundleType))];
        const bundleTypeOptions = bundleTypes.sort().map(type => `<option value="${type}">${type}</option>`).join('');
        document.getElementById('intBundleType').innerHTML = '<option value="">선택</option>' + bundleTypeOptions;
        document.getElementById('bulkBundleType').innerHTML = '<option value="">변경하지 않음</option>' + bundleTypeOptions;
        document.getElementById('filterBundleType').innerHTML = '<option value="">전체</option>' + bundleTypeOptions;
        document.getElementById('editBundleType').innerHTML = '<option value="">선택</option>' + bundleTypeOptions;

        // Status
        const statuses = [...new Set(res.data.filter(p => p.Status).map(p => p.Status))];
        const statusOptions = statuses.sort().map(status => `<option value="${status}">${status}</option>`).join('');
        document.getElementById('intStatus').innerHTML = '<option value="">선택</option>' + statusOptions;
        document.getElementById('bulkStatus').innerHTML = '<option value="">변경하지 않음</option>' + statusOptions;
        document.getElementById('editStatus').innerHTML = '<option value="">선택</option>' + statusOptions;
    } catch (e) {
        console.error('제품 타입 로드 실패:', e);
    }
}

async function loadCategories() {
    try {
        const res = await api.get('/api/products?limit=10000');

        // CategoryMid
        const categoryMids = [...new Set(res.data.filter(p => p.CategoryMid).map(p => p.CategoryMid))];
        const categoryMidOptions = categoryMids.sort().map(cat => `<option value="${cat}">`).join('');
        document.getElementById('categoryMidList').innerHTML = categoryMidOptions;

        // CategorySub
        const categorySubs = [...new Set(res.data.filter(p => p.CategorySub).map(p => p.CategorySub))];
        const categorySubOptions = categorySubs.sort().map(cat => `<option value="${cat}">`).join('');
        document.getElementById('categorySubList').innerHTML = categorySubOptions;
    } catch (e) {
        console.error('카테고리 로드 실패:', e);
    }
}

async function loadERPCodes() {
    try {
        const res = await api.get('/api/productboxes?limit=10000');
        const erpCodes = [...new Set(res.data.filter(b => b.ERPCode).map(b => b.ERPCode))];
        const options = erpCodes.sort().map(code => `<option value="${code}">`).join('');
        document.getElementById('erpCodeList').innerHTML = options;
    } catch (e) {
        console.error('ERP코드 로드 실패:', e);
    }
}

async function loadUniqueCodes() {
    try {
        const res = await api.get('/api/products?limit=10000');
        const uniqueCodes = [...new Set(res.data.filter(p => p.UniqueCode).map(p => p.UniqueCode))];
        const options = uniqueCodes.sort().map(code => `<option value="${code}">`).join('');
        document.getElementById('uniqueCodeList').innerHTML = options;
    } catch (e) {
        console.error('고유코드 로드 실패:', e);
    }
}

async function loadProductNames() {
    try {
        const res = await api.get('/api/products?limit=10000');
        const names = [...new Set(res.data.filter(p => p.Name).map(p => p.Name))];
        const options = names.sort().map(name => `<option value="${name}">`).join('');
        document.getElementById('nameList').innerHTML = options;
    } catch (e) {
        console.error('상품명 로드 실패:', e);
    }
}

function changeLimit() {
    limit = parseInt(document.getElementById('limitSelector').value);
    currentPage = 1;
    loadProducts();
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

    currentPage = 1;
    loadProducts();
}

function resetFilters() {
    document.getElementById('filterBrand').value = '';
    document.getElementById('filterUniqueCode').value = '';
    document.getElementById('filterName').value = '';
    document.getElementById('filterBundleType').value = '';
    currentFilters = {};
    currentPage = 1;

    // 디테일 영역 초기화
    currentBoxID = null;
    selectedBoxIds.clear();
    const placeholder = document.getElementById('detailPlaceholder');
    placeholder.style.display = 'block';
    placeholder.style.textAlign = 'center';
    document.getElementById('boxTableContainer').style.display = 'none';
    document.getElementById('boxActionButtons').style.display = 'none';

    loadProducts();
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
    loadProducts();
}

function toggleSelect(id, event) {
    event.stopPropagation();
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    updateBulkButtons();

    const row = Array.from(document.querySelectorAll('#productTable tbody tr')).find(r =>
        r.querySelector('td:nth-child(2)').textContent == id
    );
    if (row) {
        row.classList.toggle('selected', selectedIds.has(id));
    }

    const allRows = document.querySelectorAll('#productTable tbody tr');
    const totalCheckboxes = allRows.length;
    document.getElementById('selectAll').checked = selectedIds.size > 0 && selectedIds.size === totalCheckboxes;
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    const rows = document.querySelectorAll('#productTable tbody tr');

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

            const res = await api.get(`/api/products?${params}`);

            selectedIds.clear();
            res.data.forEach(p => selectedIds.add(p.ProductID));

            document.querySelectorAll('#productTable tbody tr').forEach(r => {
                const id = parseInt(r.querySelector('td:nth-child(2)').textContent);
                if (selectedIds.has(id)) {
                    r.classList.add('selected');
                    const checkbox = r.querySelector('input[type="checkbox"]');
                    if (checkbox) checkbox.checked = true;
                }
            });

            document.getElementById('selectAll').checked = true;
            updateBulkButtons();

            showAlert(`${selectedIds.size}개의 제품이 선택되었습니다.`, 'success');
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
    document.getElementById('intBrand').value = '';
    document.getElementById('intUniqueCode').value = '';
    document.getElementById('intName').value = '';
    document.getElementById('intTypeERP').value = '';
    document.getElementById('intTypeDB').value = '';
    document.getElementById('intBaseBarcode').value = '';
    document.getElementById('intBarcode2').value = '';
    document.getElementById('intSabangnetCode').value = '';
    document.getElementById('intSabangnetUniqueCode').value = '';
    document.getElementById('intBundleType').value = '';
    document.getElementById('intCategoryMid').value = '';
    document.getElementById('intCategorySub').value = '';
    document.getElementById('intStatus').value = '';
    document.getElementById('intReleaseDate').value = '';
    document.getElementById('intERPCode').value = '';
    document.getElementById('intQuantityInBox').value = '1';
    document.getElementById('integratedAddModal').classList.add('show');
}

function closeIntegratedAddModal() {
    document.getElementById('integratedAddModal').classList.remove('show');
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

    try {
        await api.post('/api/products/integrated', { product: productData, box: boxData });
        showAlert('제품과 박스가 추가되었습니다.', 'success');
        closeIntegratedAddModal();
        loadProducts();
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
    document.getElementById('addBoxModal').classList.add('show');
}

function closeAddBoxModal() {
    document.getElementById('addBoxModal').classList.remove('show');
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

function toggleSelectBox(id, event) {
    event.stopPropagation();
    if (selectedBoxIds.has(id)) {
        selectedBoxIds.delete(id);
    } else {
        selectedBoxIds.add(id);
    }
    updateBoxBulkButtons();

    const row = Array.from(document.querySelectorAll('#boxTable tbody tr')).find(r =>
        r.querySelector('td:nth-child(2)').textContent == id
    );
    if (row) {
        row.classList.toggle('selected', selectedBoxIds.has(id));
    }

    const allRows = document.querySelectorAll('#boxTable tbody tr');
    document.getElementById('selectAllBoxes').checked = selectedBoxIds.size > 0 && selectedBoxIds.size === allRows.length;
}

function toggleSelectAllBoxes() {
    const checked = document.getElementById('selectAllBoxes').checked;
    const rows = document.querySelectorAll('#boxTable tbody tr');

    rows.forEach(r => {
        const checkbox = r.querySelector('input[type="checkbox"]');
        if (checkbox) {
            const id = parseInt(r.querySelector('td:nth-child(2)').textContent);
            if (checked) {
                selectedBoxIds.add(id);
                r.classList.add('selected');
                checkbox.checked = true;
            } else {
                selectedBoxIds.delete(id);
                r.classList.remove('selected');
                checkbox.checked = false;
            }
        }
    });

    updateBoxBulkButtons();
}

function updateBoxBulkButtons() {
    const hasSelection = selectedBoxIds.size > 0;
    const editBtn = document.getElementById('editBoxButton');
    const deleteBtn = document.getElementById('deleteBoxButton');

    editBtn.disabled = !hasSelection;
    deleteBtn.disabled = !hasSelection;
    editBtn.classList.toggle('btn-disabled', !hasSelection);
    deleteBtn.classList.toggle('btn-disabled', !hasSelection);
}

async function bulkEditBoxes() {
    if (selectedBoxIds.size === 0) {
        showAlert('수정할 박스를 선택하세요.', 'warning');
        return;
    }

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedBoxIds)[0];
    try {
        const box = await api.get(`/api/productboxes/${firstId}`);

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditBoxCount').textContent = selectedBoxIds.size;
        document.getElementById('currentERPCode').textContent = box.ERPCode || '(없음)';
        document.getElementById('currentQuantityInBox').textContent = box.QuantityInBox || '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkERPCode').value = '';
        document.getElementById('bulkQuantityInBox').value = '';

        // 모달 열기
        document.getElementById('bulkEditBoxModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditBoxModal() {
    document.getElementById('bulkEditBoxModal').classList.remove('show');
}

async function saveBulkEditBox() {
    const newERPCode = document.getElementById('bulkERPCode').value.trim();
    const newQuantityInBox = document.getElementById('bulkQuantityInBox').value;

    // 변경할 값이 없으면 경고
    if (!newERPCode && !newQuantityInBox) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = Array.from(selectedBoxIds).map(async id => {
            const box = await api.get(`/api/productboxes/${id}`);
            const updateData = {
                ProductID: box.ProductID,
                ERPCode: newERPCode || box.ERPCode,
                QuantityInBox: newQuantityInBox ? parseInt(newQuantityInBox) : box.QuantityInBox
            };
            return api.put(`/api/productboxes/${id}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedBoxIds.size}개 박스가 수정되었습니다.`, 'success');
        closeBulkEditBoxModal();
        selectedBoxIds.clear();
        loadBoxes(currentProductId);
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

async function bulkDeleteBoxes() {
    if (selectedBoxIds.size === 0) return;

    showConfirm(`선택한 ${selectedBoxIds.size}개의 박스를 삭제하시겠습니까?`, async () => {
        try {
            const promises = Array.from(selectedBoxIds).map(id =>
                api.delete(`/api/productboxes/${id}`)
            );

            await Promise.all(promises);
            showAlert(`${selectedBoxIds.size}개 박스가 삭제되었습니다.`, 'success');
            selectedBoxIds.clear();
            loadBoxes(currentProductId);
        } catch (e) {
            showAlert('일괄 삭제 실패: ' + e.message, 'error');
        }
    });
}

async function bulkEdit() {
    if (selectedIds.size === 0) {
        showAlert('수정할 제품을 선택하세요.', 'warning');
        return;
    }

    // 첫 번째 선택된 항목의 데이터를 가져와서 현재 값 표시
    const firstId = Array.from(selectedIds)[0];
    try {
        const product = await api.get(`/api/products/${firstId}`);

        // 모달에 선택 개수와 현재 값 표시
        document.getElementById('bulkEditProductCount').textContent = selectedIds.size;
        document.getElementById('currentBrand').textContent = product.BrandName || '(없음)';
        document.getElementById('currentUniqueCode').textContent = product.UniqueCode || '(없음)';
        document.getElementById('currentProductName').textContent = product.Name || '(없음)';
        document.getElementById('currentTypeERP').textContent = product.TypeERP || '(없음)';
        document.getElementById('currentTypeDB').textContent = product.TypeDB || '(없음)';
        document.getElementById('currentBaseBarcode').textContent = product.BaseBarcode || '(없음)';
        document.getElementById('currentBarcode2').textContent = product.Barcode2 || '(없음)';
        document.getElementById('currentSabangnetCode').textContent = product.SabangnetCode || '(없음)';
        document.getElementById('currentSabangnetUniqueCode').textContent = product.SabangnetUniqueCode || '(없음)';
        document.getElementById('currentBundleType').textContent = product.BundleType || '(없음)';
        document.getElementById('currentCategoryMid').textContent = product.CategoryMid || '(없음)';
        document.getElementById('currentCategorySub').textContent = product.CategorySub || '(없음)';
        document.getElementById('currentStatus').textContent = product.Status || '(없음)';
        document.getElementById('currentReleaseDate').textContent = product.ReleaseDate || '(없음)';

        // 입력 필드 초기화
        document.getElementById('bulkBrand').value = '';
        document.getElementById('bulkUniqueCode').value = '';
        document.getElementById('bulkProductName').value = '';
        document.getElementById('bulkTypeERP').value = '';
        document.getElementById('bulkTypeDB').value = '';
        document.getElementById('bulkBaseBarcode').value = '';
        document.getElementById('bulkBarcode2').value = '';
        document.getElementById('bulkSabangnetCode').value = '';
        document.getElementById('bulkSabangnetUniqueCode').value = '';
        document.getElementById('bulkBundleType').value = '';
        document.getElementById('bulkCategoryMid').value = '';
        document.getElementById('bulkCategorySub').value = '';
        document.getElementById('bulkStatus').value = '';
        document.getElementById('bulkReleaseDate').value = '';

        // 모달 열기
        document.getElementById('bulkEditProductModal').classList.add('show');
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
    }
}

function closeBulkEditProductModal() {
    document.getElementById('bulkEditProductModal').classList.remove('show');
}

async function saveBulkEditProduct() {
    const newBrand = document.getElementById('bulkBrand').value;
    const newUniqueCode = document.getElementById('bulkUniqueCode').value.trim();
    const newName = document.getElementById('bulkProductName').value.trim();
    const newTypeERP = document.getElementById('bulkTypeERP').value;
    const newTypeDB = document.getElementById('bulkTypeDB').value;
    const newBaseBarcode = document.getElementById('bulkBaseBarcode').value.trim();
    const newBarcode2 = document.getElementById('bulkBarcode2').value.trim();
    const newSabangnetCode = document.getElementById('bulkSabangnetCode').value.trim();
    const newSabangnetUniqueCode = document.getElementById('bulkSabangnetUniqueCode').value.trim();
    const newBundleType = document.getElementById('bulkBundleType').value;
    const newCategoryMid = document.getElementById('bulkCategoryMid').value.trim();
    const newCategorySub = document.getElementById('bulkCategorySub').value.trim();
    const newStatus = document.getElementById('bulkStatus').value;
    const newReleaseDate = document.getElementById('bulkReleaseDate').value;

    // 변경할 값이 없으면 경고
    if (!newBrand && !newUniqueCode && !newName && !newTypeERP && !newTypeDB &&
        !newBaseBarcode && !newBarcode2 && !newSabangnetCode && !newSabangnetUniqueCode &&
        !newBundleType && !newCategoryMid && !newCategorySub && !newStatus && !newReleaseDate) {
        showAlert('변경할 값을 입력하세요.', 'warning');
        return;
    }

    try {
        const promises = Array.from(selectedIds).map(async id => {
            const product = await api.get(`/api/products/${id}`);
            const updateData = {
                BrandID: newBrand || product.BrandID,
                UniqueCode: newUniqueCode || product.UniqueCode,
                Name: newName || product.Name,
                TypeERP: newTypeERP || product.TypeERP,
                TypeDB: newTypeDB || product.TypeDB,
                BaseBarcode: newBaseBarcode || product.BaseBarcode,
                Barcode2: newBarcode2 || product.Barcode2,
                SabangnetCode: newSabangnetCode || product.SabangnetCode,
                SabangnetUniqueCode: newSabangnetUniqueCode || product.SabangnetUniqueCode,
                BundleType: newBundleType || product.BundleType,
                CategoryMid: newCategoryMid || product.CategoryMid,
                CategorySub: newCategorySub || product.CategorySub,
                Status: newStatus || product.Status,
                ReleaseDate: newReleaseDate || product.ReleaseDate
            };
            return api.put(`/api/products/${id}`, updateData);
        });

        await Promise.all(promises);
        showAlert(`${selectedIds.size}개 제품이 수정되었습니다.`, 'success');
        closeBulkEditProductModal();
        selectedIds.clear();
        loadProducts();
    } catch (e) {
        showAlert('일괄 수정 실패: ' + e.message, 'error');
    }
}

function showEditProductModal(product) {
    document.getElementById('editProductId').value = product.ProductID;
    document.getElementById('editBrand').value = product.BrandID || '';
    document.getElementById('editUniqueCode').value = product.UniqueCode || '';
    document.getElementById('editName').value = product.Name || '';
    document.getElementById('editTypeERP').value = product.TypeERP || '';
    document.getElementById('editTypeDB').value = product.TypeDB || '';
    document.getElementById('editBaseBarcode').value = product.BaseBarcode || '';
    document.getElementById('editBarcode2').value = product.Barcode2 || '';
    document.getElementById('editSabangnetCode').value = product.SabangnetCode || '';
    document.getElementById('editSabangnetUniqueCode').value = product.SabangnetUniqueCode || '';
    document.getElementById('editBundleType').value = product.BundleType || '';
    document.getElementById('editCategoryMid').value = product.CategoryMid || '';
    document.getElementById('editCategorySub').value = product.CategorySub || '';
    document.getElementById('editStatus').value = product.Status || '';
    document.getElementById('editReleaseDate').value = product.ReleaseDate || '';
    document.getElementById('editProductModal').classList.add('show');
}

function closeEditProductModal() {
    document.getElementById('editProductModal').classList.remove('show');
}

async function updateProduct() {
    const productId = document.getElementById('editProductId').value;
    const uniqueCode = document.getElementById('editUniqueCode').value.trim();
    const name = document.getElementById('editName').value.trim();
    const typeERP = document.getElementById('editTypeERP').value.trim();
    const typeDB = document.getElementById('editTypeDB').value.trim();

    if (!uniqueCode || !name || !typeERP || !typeDB) {
        showAlert('UniqueCode, Name, TypeERP, TypeDB는 필수입니다.', 'error');
        return;
    }

    const data = {
        BrandID: document.getElementById('editBrand').value ? parseInt(document.getElementById('editBrand').value) : null,
        UniqueCode: uniqueCode,
        Name: name,
        TypeERP: typeERP,
        TypeDB: typeDB,
        BaseBarcode: document.getElementById('editBaseBarcode').value.trim() || null,
        Barcode2: document.getElementById('editBarcode2').value.trim() || null,
        SabangnetCode: document.getElementById('editSabangnetCode').value.trim() || null,
        SabangnetUniqueCode: document.getElementById('editSabangnetUniqueCode').value.trim() || null,
        BundleType: document.getElementById('editBundleType').value || null,
        CategoryMid: document.getElementById('editCategoryMid').value.trim() || null,
        CategorySub: document.getElementById('editCategorySub').value.trim() || null,
        Status: document.getElementById('editStatus').value || null,
        ReleaseDate: document.getElementById('editReleaseDate').value || null
    };

    try {
        await api.put(`/api/products/${productId}`, data);
        showAlert('제품이 수정되었습니다.', 'success');
        closeEditProductModal();
        selectedIds.clear();
        loadProducts();
    } catch (e) {
        showAlert('수정 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    if (selectedIds.size === 0) return;

    showConfirm(`선택한 ${selectedIds.size}개의 제품을 삭제하시겠습니까?`, async () => {
        try {
            await api.post('/api/products/bulk-delete', { ids: Array.from(selectedIds) });
            showAlert('제품이 삭제되었습니다.', 'success');
            selectedIds.clear();
            loadProducts();

            if (selectedIds.has(currentProductId)) {
                currentProductId = null;
                document.getElementById('detailPlaceholder').style.display = 'block';
                document.getElementById('boxTableContainer').style.display = 'none';
            }
        } catch (e) {
            showAlert('삭제 실패: ' + e.message, 'error');
        }
    });
}

// Excel download function
function downloadExcel() {
    // 현재 필터 조건을 query parameter로 변환
    const params = new URLSearchParams();
    if (currentFilters.brand) params.append('brand', currentFilters.brand);
    if (currentFilters.unique_code) params.append('unique_code', currentFilters.unique_code);
    if (currentFilters.name) params.append('name', currentFilters.name);
    if (currentFilters.bundle_type) params.append('bundle_type', currentFilters.bundle_type);

    // 엑셀 다운로드 URL
    const downloadUrl = `/api/products/download/excel?${params.toString()}`;

    // 다운로드 실행
    window.location.href = downloadUrl;

    // 사용자 피드백
    showAlert('엑셀 파일 다운로드를 시작합니다.', 'success');
}

// Enter key support for filters
['filterBrand', 'filterName', 'filterUniqueCode', 'filterBundleType'].forEach(id => {
    document.getElementById(id).addEventListener('keypress', e => {
        if (e.key === 'Enter') applyFilters();
    });
});
