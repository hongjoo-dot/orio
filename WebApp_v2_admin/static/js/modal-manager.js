/**
 * Modal Manager Module
 * - 모달 열기/닫기
 * - 모달 이벤트 관리
 */

class ModalManager {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.closeButtons = this.modal?.querySelectorAll('[data-modal-close]');
        this._initEventListeners();
    }

    /**
     * 이벤트 리스너 초기화
     */
    _initEventListeners() {
        if (!this.modal) return;

        // 닫기 버튼
        this.closeButtons?.forEach(btn => {
            btn.addEventListener('click', () => this.hide());
        });

        // 모달 배경 클릭 시 닫기
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });

        // ESC 키로 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible()) {
                this.hide();
            }
        });
    }

    /**
     * 모달 표시
     */
    show() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
        }
    }

    /**
     * 모달 숨김
     */
    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = ''; // 스크롤 복원
        }
    }

    /**
     * 모달 토글
     */
    toggle() {
        if (this.isVisible()) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * 모달 표시 여부
     */
    isVisible() {
        return this.modal?.style.display === 'flex';
    }

    /**
     * 모달 내용 설정
     */
    setContent(selector, content) {
        const element = this.modal?.querySelector(selector);
        if (element) {
            if (typeof content === 'string') {
                element.innerHTML = content;
            } else {
                element.innerHTML = '';
                element.appendChild(content);
            }
        }
    }

    /**
     * 폼 리셋
     */
    resetForm(formSelector) {
        const form = this.modal?.querySelector(formSelector);
        if (form && form.tagName === 'FORM') {
            form.reset();
        }
    }
}


/**
 * 알림 모달 (간단한 메시지 표시)
 */
function showAlert(message, type = 'info') {
    const alertModal = document.createElement('div');
    alertModal.className = 'modal';
    alertModal.style.display = 'flex';

    const iconMap = {
        success: '<i class="fa-solid fa-circle-check" style="color: var(--success); font-size: 48px;"></i>',
        error: '<i class="fa-solid fa-circle-xmark" style="color: var(--danger); font-size: 48px;"></i>',
        warning: '<i class="fa-solid fa-triangle-exclamation" style="color: var(--warning); font-size: 48px;"></i>',
        info: '<i class="fa-solid fa-circle-info" style="color: var(--accent); font-size: 48px;"></i>'
    };

    alertModal.innerHTML = `
        <div class="modal-content" style="max-width: 400px; text-align: center;">
            <div style="margin-bottom: 20px;">
                ${iconMap[type]}
            </div>
            <div style="font-size: 16px; margin-bottom: 24px; line-height: 1.6;">
                ${message}
            </div>
            <button class="btn btn-primary" onclick="this.closest('.modal').remove(); document.body.style.overflow = '';">
                확인
            </button>
        </div>
    `;

    document.body.appendChild(alertModal);
    document.body.style.overflow = 'hidden';

    // 배경 클릭 시 닫기
    alertModal.addEventListener('click', (e) => {
        if (e.target === alertModal) {
            alertModal.remove();
            document.body.style.overflow = '';
        }
    });
}


/**
 * 확인 모달 (예/아니오)
 */
function showConfirm(message, onConfirm, onCancel = null) {
    const confirmModal = document.createElement('div');
    confirmModal.className = 'modal';
    confirmModal.style.display = 'flex';

    confirmModal.innerHTML = `
        <div class="modal-content" style="max-width: 400px; text-align: center;">
            <div style="margin-bottom: 20px;">
                <i class="fa-solid fa-circle-question" style="color: var(--warning); font-size: 48px;"></i>
            </div>
            <div style="font-size: 16px; margin-bottom: 24px; line-height: 1.6;">
                ${message}
            </div>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button class="btn btn-secondary" id="confirm-cancel">취소</button>
                <button class="btn btn-primary" id="confirm-ok">확인</button>
            </div>
        </div>
    `;

    document.body.appendChild(confirmModal);
    document.body.style.overflow = 'hidden';

    // 확인 버튼
    confirmModal.querySelector('#confirm-ok').addEventListener('click', () => {
        if (onConfirm) onConfirm();
        confirmModal.remove();
        document.body.style.overflow = '';
    });

    // 취소 버튼
    confirmModal.querySelector('#confirm-cancel').addEventListener('click', () => {
        if (onCancel) onCancel();
        confirmModal.remove();
        document.body.style.overflow = '';
    });

    // 배경 클릭 시 취소
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal) {
            if (onCancel) onCancel();
            confirmModal.remove();
            document.body.style.overflow = '';
        }
    });
}
