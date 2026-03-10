/**
 * 예상 판매량 통합 조회 JavaScript
 * - 탭: 통합 조회 / BOM 분해 / SKU 관리
 * - 피벗 테이블: 행(브랜드/채널/상품) × 열(연월별)
 * - SKU 관리: SKU 합산 + 디테일 패널
 */

const API_BASE = '/api/expected-sales-integration';
let currentYearMonths = [];
let currentData = [];
let currentTab = 'integration';
let selectedSkuCode = null;

// Multi-select instances
let msBrand, msChannel, msOwner;

// ==================== 초기화 ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Multi-select 초기화
        msBrand = new MultiSelect('filterBrand', { placeholder: '전체' });
        msChannel = new MultiSelect('filterChannel', { placeholder: '전체' });
        msOwner = new MultiSelect('filterOwner', { placeholder: '전체', onChange: () => onRangeChange() });

        setDefaultRange();
        await loadOwners();
        await onRangeChange();
    } catch (e) {
        console.error('초기화 실패:', e);
        const tbody = document.querySelector('#pivotTable tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:var(--danger);">
            초기화 실패: ${e.message}</td></tr>`;
    }

    // 인라인 편집 이탈 방지
    window.addEventListener('beforeunload', (e) => {
        if (window._skuDirtySet && window._skuDirtySet.size > 0) {
            e.preventDefault();
        }
    });
});

// ==================== 탭 전환 ====================
function switchTab(tab) {
    currentTab = tab;
    document.getElementById('tabIntegration').className =
        tab === 'integration' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabBom').className =
        tab === 'bom' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
    document.getElementById('tabSku').className =
        tab === 'sku' ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';

    // 섹션 표시/숨김
    document.getElementById('pivotSection').style.display = (tab === 'sku') ? 'none' : '';
    document.getElementById('skuSection').style.display = (tab === 'sku') ? '' : 'none';

    if (tab !== 'sku') {
        document.getElementById('tableTitle').textContent =
            tab === 'bom' ? 'BOM 분해 결과' : '통합 조회 결과';
    }

    loadData();
}

// ==================== 기본 연월 범위 설정 ====================
function setDefaultRange() {
    const now = new Date();
    const from = new Date(now.getFullYear(), now.getMonth(), 1);
    const to = new Date(now.getFullYear(), now.getMonth() + 2, 1);

    document.getElementById('filterYearMonthFrom').value = formatMonth(from);
    document.getElementById('filterYearMonthTo').value = formatMonth(to);
}

function formatMonth(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// ==================== 연월 범위 변경 시 ====================
async function onRangeChange() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) return;

    await Promise.all([loadInputMonths(), loadBrands(), loadChannels()]);
    await loadData();
}

function getRangeParams() {
    const p = {
        year_month_from: document.getElementById('filterYearMonthFrom').value,
        year_month_to: document.getElementById('filterYearMonthTo').value
    };
    if (msOwner) {
        const ow = msOwner.getSelectedString();
        if (ow) p.owner = ow;
    }
    return p;
}

// ==================== 입력월 목록 로드 ====================
async function loadInputMonths() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const months = await api.get(`${API_BASE}/input-months${qs}`);
        const sel = document.getElementById('filterInputMonth');
        const cur = sel.value;
        sel.innerHTML = '<option value="">전체</option>';
        months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m; opt.textContent = m;
            sel.appendChild(opt);
        });
        sel.value = cur || '';
    } catch (e) {
        console.error('입력월 로드 실패:', e);
    }
}

// ==================== 브랜드 목록 로드 ====================
async function loadBrands() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const brands = await api.get(`${API_BASE}/brands${qs}`);
        msBrand.setOptions(brands);
    } catch (e) {
        console.error('브랜드 로드 실패:', e);
    }
}

// ==================== 채널 목록 로드 ====================
async function loadChannels() {
    try {
        const qs = api.buildQueryString(getRangeParams());
        const channels = await api.get(`${API_BASE}/channels${qs}`);
        msChannel.setOptions(channels);
    } catch (e) {
        console.error('채널 로드 실패:', e);
    }
}

// ==================== 담당자(Owner) 목록 로드 ====================
async function loadOwners() {
    try {
        const owners = await api.get(`${API_BASE}/owners`);
        msOwner.setOptions(owners);
    } catch (e) {
        console.error('담당자 목록 로드 실패:', e);
    }
}

// ==================== 데이터 로드 ====================
async function loadData() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) {
        showAlert('연월 범위를 설정해주세요.', 'warning');
        return;
    }

    if (currentTab === 'sku') {
        await loadSkuData();
        return;
    }

    const tbody = document.querySelector('#pivotTable tbody');
    tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    try {
        const params = {
            year_month_from: from,
            year_month_to: to,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) params.owner = ow; }
        const qs = api.buildQueryString(params);

        const endpoint = currentTab === 'bom' ? '/bom-data' : '/data';
        const result = await api.get(`${API_BASE}${endpoint}${qs}`);

        currentYearMonths = result.year_months || [];
        currentData = result.data || [];

        if (currentTab === 'bom') {
            renderBomTable(currentYearMonths, currentData);
        } else {
            renderPivotTable(currentYearMonths, currentData);
        }
        document.getElementById('dataCount').textContent = `(${currentData.length}개 상품)`;
    } catch (e) {
        console.error('데이터 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:var(--danger);">
            데이터 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

// ==================== 통합 조회 피벗 테이블 렌더링 ====================
function renderPivotTable(yearMonths, data) {
    const thead = document.querySelector('#pivotTable thead tr');
    const tbody = document.querySelector('#pivotTable tbody');

    thead.innerHTML = '';
    ['브랜드', '채널', '상품명'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const thAmt = document.createElement('th');
        thAmt.textContent = `${ym}(매출)`;
        thAmt.style.textAlign = 'right';
        thead.appendChild(thAmt);

        const thQty = document.createElement('th');
        thQty.textContent = `${ym}(수량)`;
        thQty.style.textAlign = 'right';
        thead.appendChild(thQty);
    });

    ['합계(매출)', '합계(수량)'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        th.style.textAlign = 'right';
        th.style.background = 'rgba(34,197,94,0.1)';
        thead.appendChild(th);
    });

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length * 2 + 2;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${escapeHtml(item.brand)}</td>
            <td>${escapeHtml(item.channel)}</td>
            <td>${escapeHtml(item.name)}</td>
        `;

        yearMonths.forEach(ym => {
            const ymData = item.months[ym] || { amount: 0, quantity: 0 };

            const tdAmt = document.createElement('td');
            tdAmt.className = 'col-amount';
            tdAmt.textContent = ymData.amount ? ymData.amount.toLocaleString() : '-';
            tr.appendChild(tdAmt);

            const tdQty = document.createElement('td');
            tdQty.className = 'col-qty';
            tdQty.textContent = ymData.quantity ? ymData.quantity.toLocaleString() : '-';
            tr.appendChild(tdQty);
        });

        const tdTotalAmt = document.createElement('td');
        tdTotalAmt.className = 'col-total';
        tdTotalAmt.textContent = item.totalAmount ? item.totalAmount.toLocaleString() : '-';
        tr.appendChild(tdTotalAmt);

        const tdTotalQty = document.createElement('td');
        tdTotalQty.className = 'col-total';
        tdTotalQty.textContent = item.totalQuantity ? item.totalQuantity.toLocaleString() : '-';
        tr.appendChild(tdTotalQty);

        tbody.appendChild(tr);
    });
}

// ==================== BOM 분해 테이블 렌더링 ====================
function renderBomTable(yearMonths, data) {
    const thead = document.querySelector('#pivotTable thead tr');
    const tbody = document.querySelector('#pivotTable tbody');

    thead.innerHTML = '';
    ['브랜드', '채널', '상품명'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        thead.appendChild(th);
    });

    yearMonths.forEach(ym => {
        const th = document.createElement('th');
        th.textContent = `${ym}(수량)`;
        th.style.textAlign = 'right';
        thead.appendChild(th);
    });

    const thTotal = document.createElement('th');
    thTotal.textContent = '합계(수량)';
    thTotal.style.textAlign = 'right';
    thTotal.style.background = 'rgba(34,197,94,0.1)';
    thead.appendChild(thTotal);

    tbody.innerHTML = '';
    const totalCols = 3 + yearMonths.length + 1;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${escapeHtml(item.brand)}</td>
            <td>${escapeHtml(item.channel)}</td>
            <td>${escapeHtml(item.name)}</td>
        `;

        yearMonths.forEach(ym => {
            const qty = item.months[ym] || 0;
            const td = document.createElement('td');
            td.className = 'col-qty';
            td.textContent = qty ? qty.toLocaleString() : '-';
            tr.appendChild(td);
        });

        const tdTotal = document.createElement('td');
        tdTotal.className = 'col-total';
        tdTotal.textContent = item.totalQuantity ? item.totalQuantity.toLocaleString() : '-';
        tr.appendChild(tdTotal);

        tbody.appendChild(tr);
    });
}

// ==================== SKU 데이터 로드 ====================
async function loadSkuData(keepDetail = false) {
    const tbody = document.querySelector('#skuTable tbody');
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;">
        <div class="spinner spinner-lg"></div>
        <div style="margin-top:12px;color:var(--text-muted);">데이터를 불러오는 중...</div>
    </td></tr>`;

    // 디테일 모달 숨김 (keepDetail이면 유지)
    if (!keepDetail) {
        closeSkuDetail();
    }

    try {
        const params = {
            year_month_from: document.getElementById('filterYearMonthFrom').value,
            year_month_to: document.getElementById('filterYearMonthTo').value,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) params.owner = ow; }
        const qs = api.buildQueryString(params);

        const result = await api.get(`${API_BASE}/sku-data${qs}`);
        renderSkuTable(result.data, result.summary);
    } catch (e) {
        console.error('SKU 데이터 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--danger);">
            데이터 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

// ==================== SKU 테이블 렌더링 ====================
function renderSkuTable(data, summary) {
    // 요약 카드 업데이트
    document.getElementById('skuTotalAmount').textContent =
        summary.totalAmount ? Math.round(summary.totalAmount / 1.1).toLocaleString() : '-';
    document.getElementById('skuTotalQty').textContent =
        summary.totalQuantity ? summary.totalQuantity.toLocaleString() : '-';
    document.getElementById('skuProductCount').textContent =
        summary.productCount ? summary.productCount.toLocaleString() : '-';
    const tbody = document.querySelector('#skuTable tbody');
    tbody.innerHTML = '';

    document.getElementById('skuDataCount').textContent = `(${data.length}개 SKU)`;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--text-muted);">
            데이터가 없습니다</td></tr>`;
        return;
    }

    // SKU 데이터를 전역 배열에 저장 (inline onclick에서 참조)
    window._skuItems = data;

    tbody.innerHTML = data.map((item, idx) => `
        <tr style="cursor:pointer" onclick="onSkuRowClick(${idx}, this)">
            <td>${escapeHtml(item.code)}</td>
            <td>${escapeHtml(item.name)}</td>
            <td class="col-amount">${item.totalAmount ? item.totalAmount.toLocaleString() : '-'}</td>
            <td class="col-qty">${item.totalQuantity ? item.totalQuantity.toLocaleString() : '-'}</td>
            <td style="text-align:center;"><button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); onSkuRowClick(${idx}, this.closest('tr'));" style="padding:2px 10px;font-size:11px;">상세</button></td>
        </tr>
    `).join('');
}

// ==================== SKU 행 클릭 핸들러 ====================
function onSkuRowClick(idx, trEl) {
    const item = window._skuItems[idx];
    if (!item) return;
    selectSku(item.code, item.name, trEl);
}

// ==================== SKU 디테일 모달 ====================
let skuDetailModal = null;

function getSkuDetailModal() {
    if (!skuDetailModal) {
        skuDetailModal = new ModalManager('skuDetailModal');
        // hide() 오버라이드: 미저장 변경사항 확인
        const originalHide = skuDetailModal.hide.bind(skuDetailModal);
        skuDetailModal.hide = function() {
            if (window._skuDirtySet && window._skuDirtySet.size > 0) {
                showConfirm('저장하지 않은 변경사항이 있습니다. 닫으시겠습니까?', () => {
                    window._skuDirtySet = new Set();
                    originalHide();
                    selectedSkuCode = null;
                    document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
                });
                return;
            }
            originalHide();
            selectedSkuCode = null;
            document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
        };
    }
    return skuDetailModal;
}

// ==================== SKU 선택 (디테일 로드) ====================
async function selectSku(code, name, rowEl) {
    // 수정사항 있을 때 다른 SKU 선택 시 확인
    if (window._skuDirtySet && window._skuDirtySet.size > 0 && selectedSkuCode && selectedSkuCode !== code) {
        showConfirm('저장하지 않은 변경사항이 있습니다. 다른 SKU를 선택하시겠습니까?', () => {
            window._skuDirtySet = new Set();
            _doSelectSku(code, name, rowEl);
        });
        return;
    }
    await _doSelectSku(code, name, rowEl);
}

async function _doSelectSku(code, name, rowEl) {
    selectedSkuCode = code;

    // 활성 행 표시
    document.querySelectorAll('#skuTable tbody tr').forEach(tr => tr.classList.remove('active'));
    if (rowEl) rowEl.classList.add('active');

    // 모달 표시
    document.getElementById('skuDetailTitle').textContent = `${code} - ${name}`;
    const tbody = document.querySelector('#skuDetailTable tbody');
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:30px;">
        <div class="spinner"></div></td></tr>`;
    getSkuDetailModal().show();

    try {
        const detailParams = {
            unique_code: code,
            year_month_from: document.getElementById('filterYearMonthFrom').value,
            year_month_to: document.getElementById('filterYearMonthTo').value,
            input_month: document.getElementById('filterInputMonth').value,
            brand: msBrand.getSelectedString(),
            channel: msChannel.getSelectedString()
        };
        { const ow = msOwner.getSelectedString(); if (ow) detailParams.owner = ow; }
        const qs = api.buildQueryString(detailParams);

        const detailData = await api.get(`${API_BASE}/sku-detail${qs}`);
        renderSkuDetail(detailData);
    } catch (e) {
        console.error('SKU 디테일 로드 실패:', e);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:30px;color:var(--danger);">
            디테일 로드 실패: ${escapeHtml(e.message)}</td></tr>`;
    }
}

// ==================== SKU 디테일 렌더링 (인라인 편집) ====================
function renderSkuDetail(detailData) {
    const tbody = document.querySelector('#skuDetailTable tbody');
    const footer = document.getElementById('skuDetailFooter');
    tbody.innerHTML = '';

    // dirty 상태 초기화
    window._skuDetailItems = detailData;
    window._skuDirtySet = new Set();
    if (footer) footer.style.display = 'none';

    if (detailData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:30px;color:var(--text-muted);">
            상세 데이터가 없습니다</td></tr>`;
        return;
    }

    let prevChannel = null;
    let prevSource = null;

    detailData.forEach((item, idx) => {
        const tr = document.createElement('tr');
        tr.id = `skuDetail-${idx}`;

        const channelChanged = item.channel !== prevChannel;
        const sourceChanged = item.sourceType !== prevSource || channelChanged;
        const isWithdrawal = item.sourceType === '불출';

        tr.innerHTML = `
            <td style="${channelChanged ? 'font-weight:600;' : 'color:var(--text-muted);'}">${channelChanged ? escapeHtml(item.channel) : ''}</td>
            <td>${sourceChanged ? escapeHtml(item.sourceType) : ''}</td>
            <td>${escapeHtml(item.yearMonth)}</td>
            <td style="text-align:right;">
                <input type="number" class="form-input" style="width:110px;text-align:right;padding:4px 8px;font-size:13px;"
                       value="${item.amount || 0}" data-idx="${idx}" data-field="amount"
                       onchange="onSkuDetailInput(${idx})" ${isWithdrawal ? 'disabled' : ''}>
            </td>
            <td style="text-align:right;">
                <input type="number" class="form-input" style="width:90px;text-align:right;padding:4px 8px;font-size:13px;"
                       value="${item.quantity || 0}" data-idx="${idx}" data-field="quantity"
                       onchange="onSkuDetailInput(${idx})">
            </td>
        `;

        if (channelChanged) {
            tr.style.borderTop = '2px solid var(--border)';
        }

        tbody.appendChild(tr);
        prevChannel = item.channel;
        prevSource = item.sourceType;
    });
}

// ==================== SKU 디테일 인라인 편집 ====================
function onSkuDetailInput(idx) {
    const item = window._skuDetailItems[idx];
    const tr = document.getElementById(`skuDetail-${idx}`);
    const inputs = tr.querySelectorAll('input[type="number"]');

    const newAmount = parseFloat(inputs[0].value) || 0;
    const newQty = parseInt(inputs[1].value) || 0;
    const origAmount = item.amount || 0;
    const origQty = item.quantity || 0;

    if (newAmount !== origAmount || newQty !== origQty) {
        window._skuDirtySet.add(idx);
        tr.style.background = 'rgba(245,158,11,0.08)';
    } else {
        window._skuDirtySet.delete(idx);
        tr.style.background = '';
    }
    updateSkuDetailFooter();
}

function updateSkuDetailFooter() {
    const footer = document.getElementById('skuDetailFooter');
    if (!footer) return;
    const count = window._skuDirtySet ? window._skuDirtySet.size : 0;
    if (count > 0) {
        footer.style.display = '';
        document.getElementById('skuDirtyCount').textContent = `수정된 항목: ${count}건`;
    } else {
        footer.style.display = 'none';
    }
}

async function saveSkuDetail() {
    if (!window._skuDirtySet || window._skuDirtySet.size === 0) return;

    const items = [];
    window._skuDirtySet.forEach(idx => {
        const item = window._skuDetailItems[idx];
        const tr = document.getElementById(`skuDetail-${idx}`);
        const inputs = tr.querySelectorAll('input[type="number"]');

        items.push({
            recordId: item.recordId,
            sourceType: item.sourceType,
            amount: parseFloat(inputs[0].value) || 0,
            quantity: parseInt(inputs[1].value) || 0
        });
    });

    try {
        const result = await api.put(`${API_BASE}/sku-inline-update`, { items });
        showAlert(result.message, 'success');

        // 로컬 데이터 업데이트 & dirty 초기화
        window._skuDirtySet.forEach(idx => {
            const tr = document.getElementById(`skuDetail-${idx}`);
            const inputs = tr.querySelectorAll('input[type="number"]');
            window._skuDetailItems[idx].amount = parseFloat(inputs[0].value) || 0;
            window._skuDetailItems[idx].quantity = parseInt(inputs[1].value) || 0;
            tr.style.background = '';
        });
        window._skuDirtySet.clear();
        updateSkuDetailFooter();

        // SKU 합산 테이블 새로고침 (모달 유지)
        loadSkuData(true);
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

// ==================== SKU 디테일 닫기 ====================
function closeSkuDetail() {
    if (skuDetailModal) skuDetailModal.hide();
}

// ==================== 필터 초기화 ====================
function resetFilters() {
    document.getElementById('filterInputMonth').value = '';
    msBrand.reset();
    msChannel.reset();
    msOwner.reset();
    setDefaultRange();
    onRangeChange();
}

// ==================== 엑셀 다운로드 ====================
function downloadExcel() {
    const from = document.getElementById('filterYearMonthFrom').value;
    const to = document.getElementById('filterYearMonthTo').value;
    if (!from || !to) {
        showAlert('연월 범위를 설정해주세요.', 'warning');
        return;
    }

    const token = localStorage.getItem('access_token');
    const dlParams = {
        year_month_from: from,
        year_month_to: to,
        input_month: document.getElementById('filterInputMonth').value,
        brand: msBrand.getSelectedString(),
        channel: msChannel.getSelectedString()
    };
    { const ow = msOwner.getSelectedString(); if (ow) dlParams.owner = ow; }
    const qs = api.buildQueryString(dlParams);

    const endpoint = currentTab === 'bom' ? '/bom-download' : '/download';
    const filePrefix = currentTab === 'bom' ? 'BOM분해' : '예상판매량_통합';

    fetch(`${API_BASE}${endpoint}${qs}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(resp => {
        if (!resp.ok) throw new Error('다운로드 실패');
        return resp.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filePrefix}_${from}~${to}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(e => {
        console.error('엑셀 다운로드 실패:', e);
        showAlert('엑셀 다운로드에 실패했습니다.', 'error');
    });
}
