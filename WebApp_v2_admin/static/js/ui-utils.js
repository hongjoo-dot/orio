/**
 * UI Utilities Module
 * - 알림 메시지 (Toast)
 * - 확인 대화상자 (Confirm)
 */

/**
 * 알림 메시지 표시
 * @param {string} message - 메시지 내용
 * @param {string} type - 알림 타입 ('success', 'error', 'warning', 'info')
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <i class="fa-solid fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    // 스타일 설정 (CSS에 .alert 클래스가 없다면 기본 스타일 적용)
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.padding = '12px 20px';
    alertDiv.style.borderRadius = '8px';
    alertDiv.style.color = 'white';
    alertDiv.style.fontWeight = '500';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    alertDiv.style.display = 'flex';
    alertDiv.style.alignItems = 'center';
    alertDiv.style.gap = '10px';
    alertDiv.style.opacity = '0';
    alertDiv.style.transform = 'translateY(-20px)';
    alertDiv.style.transition = 'all 0.3s ease';

    // 타입별 색상
    switch (type) {
        case 'success': alertDiv.style.backgroundColor = '#10B981'; break;
        case 'error': alertDiv.style.backgroundColor = '#EF4444'; break;
        case 'warning': alertDiv.style.backgroundColor = '#F59E0B'; break;
        default: alertDiv.style.backgroundColor = '#3B82F6';
    }

    document.body.appendChild(alertDiv);

    // 애니메이션
    requestAnimationFrame(() => {
        alertDiv.style.opacity = '1';
        alertDiv.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-20px)';
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

/**
 * 확인 대화상자 표시
 * @param {string} message - 질문 내용
 * @param {function} onConfirm - 확인 시 실행할 콜백 함수
 */
function showConfirm(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}

/**
 * HTML 특수문자 이스케이프
 * @param {string} str - 이스케이프할 문자열
 * @returns {string} 이스케이프된 문자열
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * 배열 정렬 (오름차순/내림차순)
 * @param {Array} arr - 정렬할 배열
 * @param {string} sortKey - 정렬 기준 키
 * @param {string} sortDir - 정렬 방향 ('ASC' | 'DESC')
 */
function sortArray(arr, sortKey, sortDir) {
    arr.sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];

        if (valA == null) valA = '';
        if (valB == null) valB = '';

        if (typeof valA === 'number' && typeof valB === 'number') {
            return sortDir === 'ASC' ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortDir === 'ASC' ? -1 : 1;
        if (strA > strB) return sortDir === 'ASC' ? 1 : -1;
        return 0;
    });
}
