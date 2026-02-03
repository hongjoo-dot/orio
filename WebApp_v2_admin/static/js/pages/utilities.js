/**
 * Utilities Page
 * - 피벗 해제 (Unpivot) 도구
 */

let uploadedFile = null;
let currentHeaders = [];

// ========================
// 초기화
// ========================
document.addEventListener('DOMContentLoaded', () => {
    initUploadZone();
});

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

function handleFile(file) {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showAlert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다', 'error');
        return;
    }

    uploadedFile = file;

    // 파일 정보 표시
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('fileName').textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    // 헤더 미리 읽기 (고정칼럼 1로 미리보기 요청)
    loadHeaders();
}

function resetUpload() {
    uploadedFile = null;
    currentHeaders = [];
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
}

// ========================
// 헤더 로드 & 칩 렌더링
// ========================
async function loadHeaders() {
    if (!uploadedFile) return;

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', '1');

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

        // Step 2 표시
        document.getElementById('step2').style.display = 'block';
        document.getElementById('fixedCount').max = currentHeaders.length - 1;

        renderHeaderChips(1);
    } catch (e) {
        showAlert(e.message, 'error');
    }
}

function renderHeaderChips(fixedCount) {
    const container = document.getElementById('headerChips');
    container.innerHTML = '';

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

// fixedCount 입력 변경 시 칩 업데이트
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('fixedCount').addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        if (val >= 1 && val < currentHeaders.length) {
            renderHeaderChips(val);
        }
    });
});

// ========================
// 미리보기
// ========================
async function requestPreview() {
    if (!uploadedFile) {
        showAlert('먼저 파일을 업로드해주세요', 'warning');
        return;
    }

    const fixedCount = parseInt(document.getElementById('fixedCount').value);
    if (isNaN(fixedCount) || fixedCount < 1) {
        showAlert('고정 칼럼 수를 1 이상으로 지정해주세요', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', fixedCount.toString());

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

    const fixedCount = parseInt(document.getElementById('fixedCount').value);

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('fixed_count', fixedCount.toString());

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
