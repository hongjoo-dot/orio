/**
 * Pagination Manager Module
 * - 페이지네이션 UI 관리
 * - 페이지 변경 이벤트
 */

class PaginationManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            onPageChange: options.onPageChange || null,
            onLimitChange: options.onLimitChange || null,
            maxButtons: options.maxButtons || 5
        };
        this.currentPage = 1;
        this.totalPages = 1;
        this.limit = 20;
        this.total = 0;
    }

    /**
     * 페이지네이션 렌더링
     */
    render(paginationData) {
        if (!this.container) {
            console.error('Pagination container not found');
            return;
        }

        this.currentPage = paginationData.page || 1;
        this.totalPages = paginationData.total_pages || 1;
        this.limit = paginationData.limit || 20;
        this.total = paginationData.total || 0;

        this.container.innerHTML = this._buildHTML();
        this._attachEventListeners();
    }

    /**
     * HTML 생성
     */
    _buildHTML() {
        const start = (this.currentPage - 1) * this.limit + 1;
        const end = Math.min(this.currentPage * this.limit, this.total);

        return `
            <div class="pagination">
                <!-- 페이지 정보 -->
                <div class="pagination-info">
                    ${this.total > 0 ? `${start}-${end}` : '0'} / ${this.total}개
                </div>

                <!-- 페이지 버튼 -->
                <div style="display: flex; gap: 8px; align-items: center;">
                    <!-- 첫 페이지 -->
                    <button class="pagination-btn" data-page="1" ${this.currentPage === 1 ? 'disabled' : ''}>
                        <i class="fa-solid fa-angles-left"></i>
                    </button>

                    <!-- 이전 페이지 -->
                    <button class="pagination-btn" data-page="${this.currentPage - 1}" ${this.currentPage === 1 ? 'disabled' : ''}>
                        <i class="fa-solid fa-angle-left"></i>
                    </button>

                    <!-- 페이지 번호 -->
                    ${this._buildPageButtons()}

                    <!-- 다음 페이지 -->
                    <button class="pagination-btn" data-page="${this.currentPage + 1}" ${this.currentPage === this.totalPages ? 'disabled' : ''}>
                        <i class="fa-solid fa-angle-right"></i>
                    </button>

                    <!-- 마지막 페이지 -->
                    <button class="pagination-btn" data-page="${this.totalPages}" ${this.currentPage === this.totalPages ? 'disabled' : ''}>
                        <i class="fa-solid fa-angles-right"></i>
                    </button>
                </div>

                <!-- 페이지당 항목 수 -->
                <div style="display: flex; align-items: center; gap: 8px;">
                    <select id="pagination-limit" class="form-select" style="width: 100px; padding: 6px 10px;">
                        <option value="10" ${this.limit === 10 ? 'selected' : ''}>10개씩</option>
                        <option value="20" ${this.limit === 20 ? 'selected' : ''}>20개씩</option>
                        <option value="50" ${this.limit === 50 ? 'selected' : ''}>50개씩</option>
                        <option value="100" ${this.limit === 100 ? 'selected' : ''}>100개씩</option>
                    </select>
                </div>
            </div>
        `;
    }

    /**
     * 페이지 번호 버튼 생성
     */
    _buildPageButtons() {
        const buttons = [];
        const halfMax = Math.floor(this.options.maxButtons / 2);

        let startPage = Math.max(1, this.currentPage - halfMax);
        let endPage = Math.min(this.totalPages, startPage + this.options.maxButtons - 1);

        // 끝에서 시작할 경우 조정
        if (endPage - startPage < this.options.maxButtons - 1) {
            startPage = Math.max(1, endPage - this.options.maxButtons + 1);
        }

        // 시작 생략 표시
        if (startPage > 1) {
            buttons.push(`
                <button class="pagination-btn" data-page="${startPage - 1}">...</button>
            `);
        }

        // 페이지 번호
        for (let i = startPage; i <= endPage; i++) {
            buttons.push(`
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" data-page="${i}">
                    ${i}
                </button>
            `);
        }

        // 끝 생략 표시
        if (endPage < this.totalPages) {
            buttons.push(`
                <button class="pagination-btn" data-page="${endPage + 1}">...</button>
            `);
        }

        return buttons.join('');
    }

    /**
     * 이벤트 리스너 연결
     */
    _attachEventListeners() {
        // 페이지 버튼 클릭
        this.container.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!btn.disabled) {
                    const page = parseInt(btn.dataset.page);
                    if (page && page !== this.currentPage) {
                        this._changePage(page);
                    }
                }
            });
        });

        // 페이지당 항목 수 변경
        const limitSelect = document.getElementById('pagination-limit');
        if (limitSelect) {
            limitSelect.addEventListener('change', (e) => {
                const newLimit = parseInt(e.target.value);
                this._changeLimit(newLimit);
            });
        }
    }

    /**
     * 페이지 변경
     */
    _changePage(page) {
        if (this.options.onPageChange) {
            this.options.onPageChange(page, this.limit);
        }
    }

    /**
     * 페이지당 항목 수 변경
     */
    _changeLimit(limit) {
        this.limit = limit;
        if (this.options.onLimitChange) {
            this.options.onLimitChange(1, limit); // 첫 페이지로 리셋
        }
    }

    /**
     * 현재 페이지 정보
     */
    getCurrentPage() {
        return this.currentPage;
    }

    /**
     * 현재 limit
     */
    getLimit() {
        return this.limit;
    }
}
