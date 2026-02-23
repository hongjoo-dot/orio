/**
 * Utilities Page
 * - 피벗 해제 (Unpivot) 도구
 * - BOM 분해 도구
 */

// Unpivot 상태
let uploadedFile = null;
let currentHeaders = [];

// BOM 분해 상태
let bomUploadedFile = null;

// ========================
// 초기화
// ========================
document.addEventListener('DOMContentLoaded', () => {
    initUploadZone();
    initInputListeners();
    initBomUploadZone();
});

// ========================
// 탭 전환
// ========================
function switchUtilityTab(tabName) {
    document.querySelectorAll('.utility-tab').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.utility-tab-content').forEach(content => content.classList.remove('active'));

    document.querySelector(`.utility-tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ========================
// 파일 업로드
// ========================
function initUploadZone() {
    const zone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });
}

function initInputListeners() {
    // fixedCount 입력 변경 시 칩 업데이트
    document.getElementById('fixedCount').addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        if (val >= 1 && val < currentHeaders.length) {
            renderHeaderChips(val);
        }
    });

    // headerRows 변경 시 미리보기 초기화
    document.getElementById('headerRows').addEventListener('change', () => {
        resetPreview();
    });

    // fillMerged 변경 시 미리보기 초기화
    document.getElementById('fillMerged').addEventListener('change', () => {
        resetPreview();
    });
}

function resetPreview() {
    document.getElementById('headerChips').innerHTML = '';
    document.getElementById('originalPreview').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
    currentHeaders = [];
}

function handleFile(file) {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showAlert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다', 'error');
        return;
    }

    uploadedFile = file;

    // 파일 정보 표시
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('fileName').textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    // Step 2 표시
    document.getElementById('step2').style.display = 'block';

    // 헤더 미리 읽기
    loadHeaders();
}

function resetUpload() {
    uploadedFile = null;
    currentHeaders = [];
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
    document.getElementById('headerRows').value = '1';
    document.getElementById('fixedCount').value = '1';
    document.getElementById('fillMerged').checked = false;
}

// ========================
// 헤더 로드 & 칩 렌더링
// ========================
async function loadHeaders() {
    if (!uploadedFile) return;

    const headerRows = parseInt(document.getElementById('headerRows').value) || 1;
    const fixedCount = parseInt(document.getElementById('fixedCount').value) || 1;
    const fillMerged = document.getElementById('fillMerged').checked;

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', fixedCount.toString());
    formData.append('header_rows', headerRows.toString());
    formData.append('fill_merged', fillMerged.toString());

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/utilities/unpivot/preview', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '미리보기 실패');
        }

        const data = await res.json();
        currentHeaders = data.original.headers;

        // 고정칼럼 max 설정
        document.getElementById('fixedCount').max = currentHeaders.length - 1;

        renderHeaderChips(fixedCount);
    } catch (e) {
        showAlert(e.message, 'error');
    }
}

function renderHeaderChips(fixedCount) {
    const container = document.getElementById('headerChips');
    container.innerHTML = '';

    if (currentHeaders.length === 0) return;

    currentHeaders.forEach((header, index) => {
        const chip = document.createElement('span');
        chip.className = `header-chip ${index < fixedCount ? 'fixed' : 'pivot'}`;
        chip.textContent = header;
        chip.title = index < fixedCount ? '고정 칼럼' : '피벗 칼럼 (해제 대상)';

        chip.addEventListener('click', () => {
            const newCount = index + 1;
            if (newCount >= currentHeaders.length) {
                showAlert('마지막 칼럼은 피벗 대상이어야 합니다', 'warning');
                return;
            }
            document.getElementById('fixedCount').value = newCount;
            renderHeaderChips(newCount);
        });

        container.appendChild(chip);
    });
}

// ========================
// 미리보기
// ========================
async function requestPreview() {
    if (!uploadedFile) {
        showAlert('먼저 파일을 업로드해주세요', 'warning');
        return;
    }

    const headerRows = parseInt(document.getElementById('headerRows').value);
    const fixedCount = parseInt(document.getElementById('fixedCount').value);
    const fillMerged = document.getElementById('fillMerged').checked;

    if (isNaN(headerRows) || headerRows < 1) {
        showAlert('헤더 행 수를 1 이상으로 지정해주세요', 'warning');
        return;
    }
    if (isNaN(fixedCount) || fixedCount < 1) {
        showAlert('고정 칼럼 수를 1 이상으로 지정해주세요', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', fixedCount.toString());
    formData.append('header_rows', headerRows.toString());
    formData.append('fill_merged', fillMerged.toString());

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/utilities/unpivot/preview', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '미리보기 실패');
        }

        const data = await res.json();

        // 헤더 업데이트
        currentHeaders = data.original.headers;
        document.getElementById('fixedCount').max = currentHeaders.length - 1;

        // 원본 미리보기
        renderPreviewTable('originalTable', data.original.headers, data.original.preview, fixedCount);
        document.getElementById('originalPreview').style.display = 'block';

        // 변환 미리보기
        renderPreviewTable('convertedTable', data.converted.headers, data.converted.preview, 0);
        document.getElementById('convertInfo').textContent =
            `원본 ${data.original.total_rows}행 x ${data.original.total_cols}열 → 변환 ${data.converted.total_rows}행 x ${data.converted.headers.length}열`;
        document.getElementById('step3').style.display = 'block';

        // 칩 업데이트
        renderHeaderChips(fixedCount);

    } catch (e) {
        showAlert(e.message, 'error');
    }
}

function renderPreviewTable(tableId, headers, rows, fixedCount) {
    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    // 헤더
    thead.innerHTML = '';
    headers.forEach((h, i) => {
        const th = document.createElement('th');
        th.textContent = h;
        if (fixedCount > 0) {
            th.className = i < fixedCount ? 'col-fixed' : 'col-pivot';
        }
        thead.appendChild(th);
    });

    // 데이터
    tbody.innerHTML = '';
    if (rows.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = headers.length;
        td.textContent = '데이터가 없습니다';
        td.style.textAlign = 'center';
        td.style.padding = '20px';
        td.style.color = 'var(--text-muted)';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    rows.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(h => {
            const td = document.createElement('td');
            const val = row[h];
            td.textContent = val !== null && val !== undefined ? val : '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

// ========================
// 다운로드
// ========================
async function downloadResult() {
    if (!uploadedFile) {
        showAlert('먼저 파일을 업로드해주세요', 'warning');
        return;
    }

    const headerRows = parseInt(document.getElementById('headerRows').value);
    const fixedCount = parseInt(document.getElementById('fixedCount').value);
    const fillMerged = document.getElementById('fillMerged').checked;

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', fixedCount.toString());
    formData.append('header_rows', headerRows.toString());
    formData.append('fill_merged', fillMerged.toString());

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/utilities/unpivot/download', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '다운로드 실패');
        }

        // Blob으로 다운로드
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Content-Disposition에서 파일명 추출
        const disposition = res.headers.get('Content-Disposition');
        let filename = 'unpivot_result.xlsx';
        if (disposition) {
            const match = disposition.match(/filename\*=UTF-8''(.+)/);
            if (match) {
                filename = decodeURIComponent(match[1]);
            }
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showAlert('다운로드 완료', 'success');
    } catch (e) {
        showAlert(e.message, 'error');
    }
}

// ============================================================
// BOM 분해
// ============================================================

function initBomUploadZone() {
    const zone = document.getElementById('bomUploadZone');
    const fileInput = document.getElementById('bomFileInput');

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) bomHandleFile(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) bomHandleFile(file);
    });
}

function bomHandleFile(file) {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showAlert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다', 'error');
        return;
    }

    bomUploadedFile = file;

    document.getElementById('bomFileInfo').style.display = 'block';
    document.getElementById('bomFileName').textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    bomRequestPreview();
}

function bomResetUpload() {
    bomUploadedFile = null;
    document.getElementById('bomFileInput').value = '';
    document.getElementById('bomFileInfo').style.display = 'none';
    document.getElementById('bomStep2').style.display = 'none';
}

async function bomRequestPreview() {
    if (!bomUploadedFile) return;

    const formData = new FormData();
    formData.append('file', bomUploadedFile);

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/utilities/bom-decompose/preview', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'BOM 분해 실패');
        }

        const data = await res.json();

        document.getElementById('bomStep2').style.display = 'block';

        if (!data.success) {
            // 검증 실패: 에러 목록 표시
            document.getElementById('bomErrors').style.display = 'block';
            document.getElementById('bomSuccess').style.display = 'none';
            bomRenderErrors(data.errors);
        } else {
            // 검증 통과: 결과 표시
            document.getElementById('bomErrors').style.display = 'none';
            document.getElementById('bomSuccess').style.display = 'block';
            bomRenderSummary(data.summary);

            const headers = [
                '품목코드(품목)', '바코드2(품목)', '상품명(품목)', '수량(품목)',
                '품목코드(구성품)', '바코드2(구성품)', '상품명(구성품)', '수량(구성품)'
            ];
            const rows = data.result.map(r => ({
                '품목코드(품목)': r.parent_erp,
                '바코드2(품목)': r.parent_barcode2,
                '상품명(품목)': r.parent_name,
                '수량(품목)': r.parent_qty,
                '품목코드(구성품)': r.child_erp,
                '바코드2(구성품)': r.child_barcode2,
                '상품명(구성품)': r.child_name,
                '수량(구성품)': r.child_qty
            }));
            renderPreviewTable('bomResultTable', headers, rows, 0);

            document.getElementById('bomResultInfo').textContent =
                `입력 ${data.summary.input_rows}행 → 분해 결과 ${data.summary.output_rows}행`;
        }
    } catch (e) {
        showAlert(e.message, 'error');
    }
}

function bomRenderSummary(summary) {
    const container = document.getElementById('bomSummary');
    container.innerHTML = `
        <div class="bom-summary-item">
            <div class="label">입력 행</div>
            <div class="value">${summary.input_rows}</div>
        </div>
        <div class="bom-summary-item">
            <div class="label">세트/번들 분해</div>
            <div class="value">${summary.sets_decomposed}</div>
        </div>
        <div class="bom-summary-item">
            <div class="label">단품 통과</div>
            <div class="value">${summary.singles_passed}</div>
        </div>
        <div class="bom-summary-item">
            <div class="label">결과 행</div>
            <div class="value">${summary.output_rows}</div>
        </div>
    `;
}

function bomRenderErrors(errors) {
    const container = document.getElementById('bomErrors');
    const rows = errors.map(e =>
        `<tr>
            <td>${e.row}</td>
            <td>${escapeHtml(e.erp_code)}</td>
            <td>${escapeHtml(e.ref_name)}</td>
            <td>${escapeHtml(e.reason)}</td>
        </tr>`
    ).join('');

    container.innerHTML = `
        <div class="bom-error-box">
            <div class="error-title">
                <i class="fa-solid fa-circle-exclamation"></i>
                검증 실패 ${errors.length}건 - 아래 문제를 수정 후 다시 업로드하세요
            </div>
            <table class="bom-error-table">
                <thead>
                    <tr>
                        <th style="width:60px;">행</th>
                        <th style="width:140px;">품목코드</th>
                        <th>상품명(참고)</th>
                        <th>사유</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

async function bomDownloadResult() {
    if (!bomUploadedFile) {
        showAlert('먼저 파일을 업로드해주세요', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', bomUploadedFile);

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/utilities/bom-decompose/download', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '다운로드 실패');
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const disposition = res.headers.get('Content-Disposition');
        let filename = 'bom_decompose_result.xlsx';
        if (disposition) {
            const match = disposition.match(/filename\*=UTF-8''(.+)/);
            if (match) filename = decodeURIComponent(match[1]);
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showAlert('다운로드 완료', 'success');
    } catch (e) {
        showAlert(e.message, 'error');
    }
}
