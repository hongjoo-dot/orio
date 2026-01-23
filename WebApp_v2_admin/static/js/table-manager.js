/**
 * Table Manager Module
 * - 테이블 렌더링
 * - 정렬
 * - 행 선택
 */

class TableManager {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.tbody = this.table?.querySelector('tbody');
        this.options = {
            selectable: options.selectable || false,
            idKey: options.idKey || null,  // 명시적 ID 키 지정 (예: 'TargetID', 'ProductID')
            onRowClick: options.onRowClick || null,
            onSelectionChange: options.onSelectionChange || null,
            emptyMessage: options.emptyMessage || '데이터가 없습니다'
        };
        this.selectedRows = new Set();

        if (this.options.selectable) {
            this._initSelection();
        }
    }

    /**
     * 테이블 데이터 렌더링
     */
    render(data, columns) {
        if (!this.tbody) {
            console.error('Table body not found');
            return;
        }

        this.tbody.innerHTML = '';

        if (!data || data.length === 0) {
            this._renderEmpty(columns.length);
            return;
        }

        data.forEach((row, index) => {
            const tr = this._createRow(row, columns, index);
            this.tbody.appendChild(tr);
        });
    }

    /**
     * 행 생성
     */
    _createRow(rowData, columns, index) {
        const tr = document.createElement('tr');
        tr.dataset.index = index;
        // idKey가 명시적으로 지정된 경우 해당 키 사용, 아니면 폴백
        tr.dataset.id = this.options.idKey
            ? (rowData[this.options.idKey] || index)
            : (rowData.id || rowData.IDX || rowData.TargetID || rowData.ProductID || index);

        // 선택 가능한 행
        if (this.options.selectable) {
            const checkCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'row-checkbox';
            checkbox.dataset.id = tr.dataset.id;
            checkCell.appendChild(checkbox);
            tr.appendChild(checkCell);
        }

        // 데이터 셀
        columns.forEach(column => {
            const td = document.createElement('td');

            if (column.render) {
                // 커스텀 렌더러
                const content = column.render(rowData, rowData[column.key]);
                if (typeof content === 'string' || typeof content === 'number') {
                    td.innerHTML = content;
                } else if (content instanceof Node) {
                    td.appendChild(content);
                }
            } else {
                // 기본 렌더링
                td.textContent = rowData[column.key] ?? '-';
            }

            if (column.className) {
                td.className = column.className;
            }

            tr.appendChild(td);
        });

        // 행 클릭 이벤트
        if (this.options.onRowClick) {
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', (e) => {
                if (!e.target.classList.contains('row-checkbox')) {
                    this.options.onRowClick(rowData, tr);
                }
            });
        }

        return tr;
    }

    /**
     * 빈 데이터 렌더링
     */
    _renderEmpty(colspan) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = colspan + (this.options.selectable ? 1 : 0);
        td.textContent = this.options.emptyMessage;
        td.style.textAlign = 'center';
        td.style.padding = '40px';
        td.style.color = 'var(--text-muted)';
        tr.appendChild(td);
        this.tbody.appendChild(tr);
    }

    /**
     * 선택 기능 초기화
     */
    _initSelection() {
        // 전체 선택 체크박스
        const thead = this.table?.querySelector('thead');
        if (thead) {
            const headerRow = thead.querySelector('tr');
            if (headerRow) {
                const th = document.createElement('th');
                th.style.width = '40px';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = 'select-all';
                checkbox.addEventListener('change', (e) => {
                    this._handleSelectAll(e.target.checked);
                });

                th.appendChild(checkbox);
                headerRow.insertBefore(th, headerRow.firstChild);
            }
        }

        // 개별 체크박스 이벤트
        this.tbody?.addEventListener('change', (e) => {
            if (e.target.classList.contains('row-checkbox')) {
                this._handleRowSelection(e.target);
            }
        });
    }

    /**
     * 전체 선택
     */
    _handleSelectAll(checked) {
        const checkboxes = this.tbody.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checked;
            const id = cb.dataset.id;
            if (checked) {
                this.selectedRows.add(id);
            } else {
                this.selectedRows.delete(id);
            }
        });

        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(Array.from(this.selectedRows));
        }
    }

    /**
     * 행 선택
     */
    _handleRowSelection(checkbox) {
        const id = checkbox.dataset.id;

        if (checkbox.checked) {
            this.selectedRows.add(id);
        } else {
            this.selectedRows.delete(id);
            document.getElementById('select-all').checked = false;
        }

        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(Array.from(this.selectedRows));
        }
    }

    /**
     * 선택된 행 가져오기
     */
    getSelectedRows() {
        return Array.from(this.selectedRows);
    }

    /**
     * 선택 초기화
     */
    clearSelection() {
        this.selectedRows.clear();
        const checkboxes = this.tbody.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;

        if (this.options.onSelectionChange) {
            this.options.onSelectionChange([]);
        }
    }

    /**
     * 로딩 상태 표시
     */
    showLoading(colspan) {
        if (!this.tbody) return;

        this.tbody.innerHTML = `
            <tr>
                <td colspan="${colspan + (this.options.selectable ? 1 : 0)}"
                    style="text-align: center; padding: 40px;">
                    <div class="spinner spinner-lg"></div>
                    <div style="margin-top: 12px; color: var(--text-muted);">
                        데이터를 불러오는 중...
                    </div>
                </td>
            </tr>
        `;
    }
}
