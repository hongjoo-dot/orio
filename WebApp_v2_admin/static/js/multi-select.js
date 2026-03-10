/**
 * MultiSelect - 체크박스 기반 다중 선택 드롭다운 컴포넌트
 *
 * Usage:
 *   const ms = new MultiSelect('containerId', {
 *       placeholder: '전체',
 *       searchable: true,       // 검색창 표시 (기본: 항목 8개 이상이면 자동)
 *       sortable: true,         // label 기준 자동 정렬 (기본: true)
 *       onChange: (selectedValues) => { ... }
 *   });
 *   ms.setOptions([{value: 'a', label: 'A'}, ...]);
 *   ms.getSelected();  // ['a', 'b']
 *   ms.reset();
 */
class MultiSelect {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`MultiSelect: container #${containerId} not found`);
            return;
        }
        this.placeholder = options.placeholder || '전체';
        this.onChange = options.onChange || null;
        this.searchable = options.searchable; // undefined = auto
        this.sortable = options.sortable !== false; // default true
        this.options = [];
        this.selected = new Set();
        this._open = false;
        this._searchTerm = '';

        this._build();
        this._bindOutsideClick();
    }

    _build() {
        this.container.classList.add('ms-container');

        // Display button
        this.display = document.createElement('div');
        this.display.className = 'ms-display form-select';
        this.display.innerHTML = `<span class="ms-text">${this.placeholder}</span><span class="ms-arrow">&#9662;</span>`;
        this.display.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // Dropdown panel
        this.panel = document.createElement('div');
        this.panel.className = 'ms-panel';
        this.panel.style.display = 'none';
        this.panel.addEventListener('click', (e) => e.stopPropagation());

        // Search input (created but may be hidden)
        this.searchWrap = document.createElement('div');
        this.searchWrap.className = 'ms-search-wrap';
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.className = 'ms-search';
        this.searchInput.placeholder = '검색...';
        this.searchInput.addEventListener('input', () => {
            this._searchTerm = this.searchInput.value.toLowerCase();
            this._filterList();
        });
        this.searchWrap.appendChild(this.searchInput);
        this.panel.appendChild(this.searchWrap);

        // Select all / deselect
        this.toolbarEl = document.createElement('div');
        this.toolbarEl.className = 'ms-toolbar';

        this.selectAllCb = document.createElement('input');
        this.selectAllCb.type = 'checkbox';
        this.selectAllCb.className = 'ms-select-all-cb';
        this.selectAllCb.addEventListener('change', () => {
            if (this.selectAllCb.checked) {
                this._selectAllVisible();
            } else {
                this._deselectAllVisible();
            }
        });

        const selectAllLabel = document.createElement('label');
        selectAllLabel.className = 'ms-select-all-label';
        selectAllLabel.appendChild(this.selectAllCb);
        const selectAllText = document.createElement('span');
        selectAllText.textContent = '전체 선택';
        selectAllLabel.appendChild(selectAllText);

        this.selectedCountEl = document.createElement('span');
        this.selectedCountEl.className = 'ms-selected-count';

        this.toolbarEl.appendChild(selectAllLabel);
        this.toolbarEl.appendChild(this.selectedCountEl);
        this.panel.appendChild(this.toolbarEl);

        // List
        this.listEl = document.createElement('div');
        this.listEl.className = 'ms-list';
        this.panel.appendChild(this.listEl);

        this.container.appendChild(this.display);
        this.container.appendChild(this.panel);
    }

    _bindOutsideClick() {
        document.addEventListener('click', () => {
            if (this._open) this.close();
        });
    }

    toggle() {
        this._open ? this.close() : this.open();
    }

    open() {
        // Close other multi-selects
        document.querySelectorAll('.ms-panel').forEach(p => {
            if (p !== this.panel) p.style.display = 'none';
        });
        document.querySelectorAll('.ms-container').forEach(c => {
            if (c !== this.container) {
                c.classList.remove('ms-open');
                if (c._msInstance) {
                    c._msInstance._open = false;
                    // Remove elevated z-index from parent card
                    const prevCard = c.closest('.card');
                    if (prevCard) prevCard.classList.remove('ms-card-elevated');
                }
            }
        });
        this.panel.style.display = '';
        this._open = true;
        this.container.classList.add('ms-open');
        // Elevate parent card above sibling cards
        const parentCard = this.container.closest('.card');
        if (parentCard) parentCard.classList.add('ms-card-elevated');
        this.container._msInstance = this;

        // Auto-show search if many options
        const showSearch = this.searchable === true || (this.searchable === undefined && this.options.length >= 8);
        this.searchWrap.style.display = showSearch ? '' : 'none';

        if (showSearch) {
            setTimeout(() => this.searchInput.focus(), 50);
        }
    }

    close() {
        this.panel.style.display = 'none';
        this._open = false;
        this.container.classList.remove('ms-open');
        const parentCard = this.container.closest('.card');
        if (parentCard) parentCard.classList.remove('ms-card-elevated');
        // Clear search on close
        if (this._searchTerm) {
            this._searchTerm = '';
            this.searchInput.value = '';
            this._filterList();
        }
    }

    setOptions(opts) {
        // opts: [{value, label}] or ['string', ...]
        this.options = opts.map(o => {
            if (typeof o === 'string') return { value: o, label: o };
            return o;
        });

        // Sort by label
        if (this.sortable) {
            this.options.sort((a, b) => {
                const la = String(a.label);
                const lb = String(b.label);
                return la.localeCompare(lb, 'ko');
            });
        }

        this._renderList();
        // Keep previously selected items that still exist
        const validValues = new Set(this.options.map(o => String(o.value)));
        const toRemove = [];
        this.selected.forEach(v => { if (!validValues.has(v)) toRemove.push(v); });
        toRemove.forEach(v => this.selected.delete(v));
        this._updateDisplay();
        this._updateToolbar();
    }

    _renderList() {
        this.listEl.innerHTML = '';

        if (this.options.length === 0) {
            this.listEl.innerHTML = '<div class="ms-empty">항목 없음</div>';
            return;
        }

        this.options.forEach(opt => {
            const item = document.createElement('label');
            item.className = 'ms-item';
            item.dataset.label = String(opt.label).toLowerCase();
            item.dataset.value = String(opt.value);

            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = opt.value;
            cb.checked = this.selected.has(String(opt.value));
            cb.addEventListener('change', () => {
                if (cb.checked) {
                    this.selected.add(String(opt.value));
                } else {
                    this.selected.delete(String(opt.value));
                }
                this._updateDisplay();
                this._updateToolbar();
                if (this.onChange) this.onChange(this.getSelected());
            });

            const span = document.createElement('span');
            span.textContent = opt.label;

            item.appendChild(cb);
            item.appendChild(span);
            this.listEl.appendChild(item);
        });
    }

    _filterList() {
        const items = this.listEl.querySelectorAll('.ms-item');
        let visibleCount = 0;
        items.forEach(item => {
            const match = !this._searchTerm || item.dataset.label.includes(this._searchTerm);
            item.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });

        // Update select-all state for visible items
        this._updateToolbar();

        // Show empty message if no matches
        let emptyMsg = this.listEl.querySelector('.ms-no-match');
        if (visibleCount === 0 && this._searchTerm) {
            if (!emptyMsg) {
                emptyMsg = document.createElement('div');
                emptyMsg.className = 'ms-empty ms-no-match';
                emptyMsg.textContent = '검색 결과 없음';
                this.listEl.appendChild(emptyMsg);
            }
            emptyMsg.style.display = '';
        } else if (emptyMsg) {
            emptyMsg.style.display = 'none';
        }
    }

    _selectAllVisible() {
        this.listEl.querySelectorAll('.ms-item').forEach(item => {
            if (item.style.display === 'none') return;
            const cb = item.querySelector('input[type="checkbox"]');
            cb.checked = true;
            this.selected.add(String(cb.value));
        });
        this._updateDisplay();
        this._updateToolbar();
        if (this.onChange) this.onChange(this.getSelected());
    }

    _deselectAllVisible() {
        this.listEl.querySelectorAll('.ms-item').forEach(item => {
            if (item.style.display === 'none') return;
            const cb = item.querySelector('input[type="checkbox"]');
            cb.checked = false;
            this.selected.delete(String(cb.value));
        });
        this._updateDisplay();
        this._updateToolbar();
        if (this.onChange) this.onChange(this.getSelected());
    }

    _updateToolbar() {
        const visible = this.listEl.querySelectorAll('.ms-item:not([style*="display: none"])');
        let checkedCount = 0;
        visible.forEach(item => {
            if (item.querySelector('input[type="checkbox"]').checked) checkedCount++;
        });

        this.selectAllCb.checked = visible.length > 0 && checkedCount === visible.length;
        this.selectAllCb.indeterminate = checkedCount > 0 && checkedCount < visible.length;

        const total = this.selected.size;
        this.selectedCountEl.textContent = total > 0 ? `${total}개 선택됨` : '';
    }

    _updateDisplay() {
        const textEl = this.display.querySelector('.ms-text');
        const count = this.selected.size;

        // Remove existing badges
        this.display.querySelectorAll('.ms-badge').forEach(b => b.remove());

        if (count === 0) {
            textEl.textContent = this.placeholder;
            textEl.style.color = '';
            textEl.style.display = '';
        } else if (count <= 2) {
            // Show as tags
            textEl.textContent = '';
            textEl.style.display = 'none';
            const arr = [...this.selected];
            const frag = document.createDocumentFragment();
            arr.forEach(val => {
                const opt = this.options.find(o => String(o.value) === val);
                const badge = document.createElement('span');
                badge.className = 'ms-badge';
                badge.textContent = opt ? opt.label : val;
                frag.appendChild(badge);
            });
            // Insert badges before arrow
            const arrow = this.display.querySelector('.ms-arrow');
            this.display.insertBefore(frag, arrow);
        } else {
            textEl.style.display = '';
            textEl.textContent = '';
            const badge = document.createElement('span');
            badge.className = 'ms-badge ms-badge-count';
            badge.textContent = `${count}개 선택`;
            const arrow = this.display.querySelector('.ms-arrow');
            this.display.insertBefore(badge, arrow);
        }
    }

    getSelected() {
        return [...this.selected];
    }

    getSelectedString() {
        const arr = this.getSelected();
        return arr.length > 0 ? arr.join(',') : '';
    }

    reset() {
        this.selected.clear();
        this.listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        this._updateDisplay();
        this._updateToolbar();
    }

    setSelected(values) {
        this.selected = new Set(values.map(String));
        this.listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = this.selected.has(String(cb.value));
        });
        this._updateDisplay();
        this._updateToolbar();
    }
}
