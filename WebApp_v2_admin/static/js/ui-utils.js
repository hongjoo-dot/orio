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
