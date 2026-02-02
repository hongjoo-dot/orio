/**
 * Table Manager Module
 * - 테이블 렌더링
 * - 칼럼 헤더 정렬
 * - 행 선택
 */

class TableManager {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.tbody = this.table?.querySelector('tbody');
        this.options = {
            selectable: options.selectable || false,
            idKey: options.idKey || null,
            onRowClick: options.onRowClick || null,
            onSelectionChange: options.onSelectionChange || null,
            onSort: options.onSort || null,
            emptyMessage: options.emptyMessage || '데이터가 없습니다'
        };
        this.selectedRows = new Set();
        this.currentSortKey = null;
        this.currentSortDir = null;
        this._headerRendered = false;
        this._selectAllCheckbox = null;

        // 개별 체크박스 이벤트 (tbody 위임)
        if (this.options.selectable) {
            this.tbody?.addEventListener('change', (e) => {
                if (e.target.classList.contains('row-checkbox')) {
                    this._handleRowSelection(e.target);
                }
            });
        }
    }

    /**
     * 테이블 헤더 렌더링 (정렬 UI 포함)
     */
    renderHeader(columns) {
        const thead = this.table?.querySelector('thead');
        if (!thead) return;

        let headerRow = thead.querySelector('tr');
        if (!headerRow) {
            headerRow = document.createElement('tr');
            thead.appendChild(headerRow);
        }
        headerRow.innerHTML = '';

        // 체크박스 컬럼
        if (this.options.selectable) {
            const th = document.createElement('th');
            th.style.width = '40px';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.addEventListener('change', (e) => {
                this._handleSelectAll(e.target.checked);
            });
            this._selectAllCheckbox = checkbox;
            th.appendChild(checkbox);
            headerRow.appendChild(th);
        }

        // 데이터 컬럼
        columns.forEach(col => {
            const th = document.createElement('th');
            th.style.position = 'relative';
            th.textContent = col.header;

            if (col.align === 'right') {
                th.style.textAlign = 'right';
            }

            if (col.sortKey && this.options.onSort) {
                th.setAttribute('data-sortable', col.sortKey);

                // 현재 정렬 상태 반영
                if (this.currentSortKey === col.sortKey) {
                    th.classList.add(this.currentSortDir === 'ASC' ? 'sort-asc' : 'sort-desc');
                }

                th.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('resize-handle')) {
                        this._handleSortClick(col.sortKey);
                    }
                });
            }

            // 리사이즈 핸들
            const handle = document.createElement('div');
            handle.className = 'resize-handle';
            handle.addEventListener('mousedown', (e) => this._startResize(e, th));
            th.appendChild(handle);

            headerRow.appendChild(th);
        });

        this._headerRendered = true;
    }

    /**
     * 정렬 클릭 처리
     */
    _handleSortClick(sortKey) {
        if (this.currentSortKey === sortKey) {
            this.currentSortDir = this.currentSortDir === 'DESC' ? 'ASC' : 'DESC';
        } else {
            this.currentSortKey = sortKey;
            this.currentSortDir = 'DESC';
        }

        // 헤더 정렬 표시 갱신
        const allTh = this.table.querySelectorAll('thead th[data-sortable]');
        allTh.forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            if (th.getAttribute('data-sortable') === this.currentSortKey) {
                th.classList.add(this.currentSortDir === 'ASC' ? 'sort-asc' : 'sort-desc');
            }
        });

        if (this.options.onSort) {
            this.options.onSort(this.currentSortKey, this.currentSortDir);
        }
    }

    /**
     * 칼럼 리사이즈 시작
     */
    _startResize(e, th) {
        e.preventDefault();
        e.stopPropagation();

        // table-layout: fixed 적용 (최초 리사이즈 시)
        if (!this._layoutFixed) {
            const ths = this.table.querySelectorAll('thead th');
            ths.forEach(t => {
                t.style.width = t.offsetWidth + 'px';
            });
            this.table.style.tableLayout = 'fixed';
            this._layoutFixed = true;
        }

        const startX = e.pageX;
        const startWidth = th.offsetWidth;
        const handle = e.target;
        handle.classList.add('resizing');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';

        const onMouseMove = (moveEvent) => {
            const newWidth = Math.max(40, startWidth + (moveEvent.pageX - startX));
            th.style.width = newWidth + 'px';
        };

        const onMouseUp = () => {
            handle.classList.remove('resizing');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
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
                const content = column.render(rowData, rowData[column.key]);
                if (typeof content === 'string' || typeof content === 'number') {
                    td.innerHTML = content;
                } else if (content instanceof Node) {
                    td.appendChild(content);
                }
            } else {
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
            if (this._selectAllCheckbox) {
                this._selectAllCheckbox.checked = false;
            }
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
        if (this._selectAllCheckbox) {
            this._selectAllCheckbox.checked = false;
        }

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
