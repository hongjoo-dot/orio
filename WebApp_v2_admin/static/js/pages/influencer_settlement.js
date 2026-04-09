/**
 * 인플루언서 광고비 정산 페이지
 * 검색어별 > UTM Content별 > 상품별 3단 Depth
 * - 요율은 검색어(인플루언서)별로 적용
 * - 합계 행 클릭 시 인플루언서 전체 상품 합산 표시
 */

let currentData = [];
let currentStartDate = null;
let currentEndDate = null;

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];

    document.getElementById('influencerInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') search();
    });
});

// ──────────────────────────────────────
// 검색
// ──────────────────────────────────────
async function search() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const influencers = document.getElementById('influencerInput').value.trim();

    if (!startDate || !endDate) return showAlert('기간을 선택해주세요.', 'warning');
    if (!influencers) return showAlert('인플루언서 이름을 입력해주세요.', 'warning');

    currentStartDate = startDate;
    currentEndDate = endDate;

    try {
        const params = new URLSearchParams({ start_date: startDate, end_date: endDate, influencers });
        const res = await api.get(`/api/influencer-settlement/summary?${params}`);

        currentData = res.data;
        renderSummary(res.data);
        resetDetailPanel();

    } catch (err) {
        showAlert('검색 중 오류가 발생했습니다.', 'error');
        console.error(err);
    }
}

// ──────────────────────────────────────
// 좌측 테이블: 검색어별 > UTM별
// ──────────────────────────────────────
function renderSummary(data) {
    const tbody = document.getElementById('summaryBody');
    const infoEl = document.getElementById('summaryInfo');

    const totalInfluencers = data.length;
    const totalUtms = data.reduce((s, d) => s + d.details.length, 0);
    infoEl.textContent = `(${totalInfluencers}명, UTM ${totalUtms}건)`;

    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="inf-empty-msg">검색 결과가 없습니다.</td></tr>';
        return;
    }

    let html = '';

    data.forEach((group, gIdx) => {
        const infEscaped = group.influencer.replace(/'/g, "\\'").replace(/"/g, '&quot;');

        // 검색어 합계 행 (클릭 가능 + 요율 입력)
        html += `
            <tr class="inf-group-row inf-clickable-row" data-gidx="${gIdx}"
                onclick="selectInfluencer('${infEscaped}', this)">
                <td>${group.influencer}</td>
                <td>합계</td>
                <td style="text-align:right">${group.total_order_count.toLocaleString()}</td>
                <td style="text-align:right">${group.total_payment.toLocaleString()}원</td>
                <td style="text-align:center">
                    <input type="number" class="rate-input" value="" placeholder="0"
                           onclick="event.stopPropagation()"
                           oninput="calcGroupSettlement(${gIdx}, this.value)">
                </td>
                <td style="text-align:right">
                    <span class="settlement-amount" id="stl-group-${gIdx}">-</span>
                </td>
            </tr>`;

        // UTM Content별 행
        group.details.forEach((detail, dIdx) => {
            const uid = `${gIdx}-${dIdx}`;
            const contentEscaped = detail.content.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            html += `
                <tr class="inf-utm-row" data-uid="${uid}" data-gidx="${gIdx}"
                    onclick="selectUtm('${contentEscaped}', this)">
                    <td></td>
                    <td style="padding-left:24px;font-size:12px;">${detail.content || '(없음)'}</td>
                    <td style="text-align:right">${detail.order_count.toLocaleString()}</td>
                    <td style="text-align:right">${detail.payment.toLocaleString()}원</td>
                    <td style="text-align:center;color:var(--text-muted);font-size:11px;">-</td>
                    <td style="text-align:right;color:var(--text-muted);font-size:11px;">-</td>
                </tr>`;
        });
    });

    // 전체 합계 행
    const grandOrders = data.reduce((s, g) => s + g.total_order_count, 0);
    const grandPayment = data.reduce((s, g) => s + g.total_payment, 0);
    html += `
        <tr class="inf-grand-total">
            <td colspan="2">전체 합계</td>
            <td style="text-align:right">${grandOrders.toLocaleString()}</td>
            <td style="text-align:right">${grandPayment.toLocaleString()}원</td>
            <td style="text-align:center">-</td>
            <td style="text-align:right"><span class="settlement-amount" id="stl-grand">-</span></td>
        </tr>`;

    tbody.innerHTML = html;
}

// ──────────────────────────────────────
// 정산금 계산 (검색어/인플루언서별)
// ──────────────────────────────────────
function calcGroupSettlement(gIdx, rateStr) {
    const rate = parseFloat(rateStr) || 0;
    const group = currentData[gIdx];
    const settlement = Math.round(group.total_payment * rate / 100);
    document.getElementById(`stl-group-${gIdx}`).textContent = settlement.toLocaleString() + '원';

    // 전체 합계 갱신
    let grandTotal = 0;
    currentData.forEach((_, i) => {
        const text = document.getElementById(`stl-group-${i}`).textContent.replace(/[^0-9-]/g, '');
        grandTotal += parseInt(text) || 0;
    });
    document.getElementById('stl-grand').textContent = grandTotal.toLocaleString() + '원';
}

// ──────────────────────────────────────
// 합계 행 클릭 → 인플루언서 전체 상품 합산
// ──────────────────────────────────────
async function selectInfluencer(influencer, trEl) {
    // 행 선택 표시
    document.querySelectorAll('.inf-utm-row, .inf-group-row').forEach(tr => tr.classList.remove('selected-row'));
    if (trEl) trEl.classList.add('selected-row');

    document.getElementById('emptyDetailCard').style.display = 'none';

    try {
        const params = new URLSearchParams({
            start_date: currentStartDate,
            end_date: currentEndDate,
            influencer: influencer
        });
        const res = await api.get(`/api/influencer-settlement/influencer-items?${params}`);

        renderItems(`${influencer} 전체`, res.data);

    } catch (err) {
        showAlert('상품 내역 조회 중 오류가 발생했습니다.', 'error');
        console.error(err);
    }
}

// ──────────────────────────────────────
// UTM 행 클릭 → 해당 Content 상품별 상세
// ──────────────────────────────────────
async function selectUtm(content, trEl) {
    // 행 선택 표시
    document.querySelectorAll('.inf-utm-row, .inf-group-row').forEach(tr => tr.classList.remove('selected-row'));
    if (trEl) trEl.classList.add('selected-row');

    document.getElementById('emptyDetailCard').style.display = 'none';

    try {
        const params = new URLSearchParams({
            start_date: currentStartDate,
            end_date: currentEndDate,
            content: content
        });
        const res = await api.get(`/api/influencer-settlement/content-items?${params}`);

        renderItems(content, res.data);

    } catch (err) {
        showAlert('상품 내역 조회 중 오류가 발생했습니다.', 'error');
        console.error(err);
    }
}

// ──────────────────────────────────────
// 우측 상품 렌더링 (공통)
// ──────────────────────────────────────
function renderItems(title, items) {
    const card = document.getElementById('itemsCard');
    const contentEl = document.getElementById('itemsContent');

    document.getElementById('itemsTitle').textContent = title || '(없음)';
    document.getElementById('itemsCount').textContent = items.length;
    card.style.display = '';

    if (!items.length) {
        contentEl.innerHTML = '<div class="inf-empty">상품 데이터가 없습니다.</div>';
        return;
    }

    let html = '';
    items.forEach(item => {
        html += `
            <div class="inf-item-row">
                <div class="inf-item-info">
                    <div class="inf-item-name">${item.product_name}</div>
                    ${item.option_value ? `<div class="inf-item-option">${item.option_value}</div>` : ''}
                </div>
                <div class="inf-item-qty">${item.total_quantity}개</div>
                <div class="inf-item-amount">${item.total_payment.toLocaleString()}원</div>
            </div>`;
    });

    // 상품 합계
    const totalQty = items.reduce((s, i) => s + i.total_quantity, 0);
    const totalAmt = items.reduce((s, i) => s + i.total_payment, 0);
    html += `
        <div class="inf-item-row" style="border-top:2px solid var(--border);font-weight:700;margin-top:4px;padding-top:10px;">
            <div class="inf-item-info"><div class="inf-item-name">합계</div></div>
            <div class="inf-item-qty">${totalQty}개</div>
            <div class="inf-item-amount">${totalAmt.toLocaleString()}원</div>
        </div>`;

    contentEl.innerHTML = html;
}

// ──────────────────────────────────────
// 우측 패널 초기화
// ──────────────────────────────────────
function resetDetailPanel() {
    document.getElementById('itemsCard').style.display = 'none';
    document.getElementById('emptyDetailCard').style.display = '';
}
