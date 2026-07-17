/**
 * Bootstrap 5 Custom JavaScript for Gestão à Vista
 * 
 * Este arquivo contém funcionalidades JavaScript customizadas que complementam
 * o Bootstrap 5, incluindo componentes interativos e utilitários específicos.
 */

// Namespace para funcionalidades customizadas
window.GestaoAVista = window.GestaoAVista || {};

(function() {
    'use strict';

    // ===== CONFIGURAÇÕES GLOBAIS =====
    const config = {
        sidebar: {
            storageKey: 'gestao-vista-sidebar-collapsed',
            animationDuration: 300
        },
        notifications: {
            defaultDuration: 5000,
            position: 'top-end'
        },
        theme: {
            storageKey: 'gestao-vista-theme'
        }
    };

    // ===== GERENCIAMENTO DE SIDEBAR =====
    class SidebarManager {
        constructor() {
            this.sidebar = document.querySelector('.sidebar');
            this.mainContent = document.querySelector('.main-content');
            this.toggleBtn = document.querySelector('[data-sidebar-toggle]');
            this.isCollapsed = this.getStoredState();
            
            this.init();
        }

        init() {
            // Aplicar estado inicial
            this.applyState();
            
            // Event listeners
            if (this.toggleBtn) {
                this.toggleBtn.addEventListener('click', () => this.toggle());
            }

            // Listener para tecla de atalho (Ctrl + B)
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'b') {
                    e.preventDefault();
                    this.toggle();
                }
            });

            // Auto-collapse em telas pequenas
            this.handleResize();
            window.addEventListener('resize', () => this.handleResize());
        }

        toggle() {
            this.isCollapsed = !this.isCollapsed;
            this.applyState();
            this.saveState();
            this.triggerEvent();
        }

        collapse() {
            if (!this.isCollapsed) {
                this.toggle();
            }
        }

        expand() {
            if (this.isCollapsed) {
                this.toggle();
            }
        }

        applyState() {
            if (this.sidebar) {
                this.sidebar.classList.toggle('collapsed', this.isCollapsed);
            }
            if (this.mainContent) {
                this.mainContent.classList.toggle('sidebar-collapsed', this.isCollapsed);
            }
        }

        saveState() {
            localStorage.setItem(config.sidebar.storageKey, this.isCollapsed);
        }

        getStoredState() {
            const stored = localStorage.getItem(config.sidebar.storageKey);
            return stored === 'true';
        }

        handleResize() {
            const isMobile = window.innerWidth < 768;
            if (isMobile && !this.isCollapsed) {
                this.collapse();
            }
        }

        triggerEvent() {
            const event = new CustomEvent('sidebar:toggle', {
                detail: { collapsed: this.isCollapsed }
            });
            document.dispatchEvent(event);
        }
    }

    // ===== SISTEMA DE NOTIFICAÇÕES =====
    class NotificationManager {
        constructor() {
            this.container = this.createContainer();
            this.notifications = new Map();
        }

        createContainer() {
            let container = document.getElementById('notification-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'notification-container';
                container.className = 'position-fixed top-0 end-0 p-3';
                container.style.zIndex = '1060';
                document.body.appendChild(container);
            }
            return container;
        }

        show(message, type = 'info', options = {}) {
            const id = this.generateId();
            const notification = this.createNotification(id, message, type, options);
            
            this.container.appendChild(notification);
            this.notifications.set(id, notification);

            // Animar entrada
            setTimeout(() => {
                notification.classList.add('show');
            }, 10);

            // Auto-dismiss
            const duration = options.duration || config.notifications.defaultDuration;
            if (duration > 0) {
                setTimeout(() => this.hide(id), duration);
            }

            return id;
        }

        hide(id) {
            const notification = this.notifications.get(id);
            if (notification) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                    this.notifications.delete(id);
                }, 300);
            }
        }

        createNotification(id, message, type, options) {
            const notification = document.createElement('div');
            notification.className = `toast align-items-center text-white bg-${type} border-0 fade`;
            notification.setAttribute('role', 'alert');
            notification.setAttribute('data-notification-id', id);

            const icon = this.getIcon(type);
            
            notification.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center">
                        ${icon}
                        <span class="ms-2">${message}</span>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;

            // Event listener para fechar
            const closeBtn = notification.querySelector('.btn-close');
            closeBtn.addEventListener('click', () => this.hide(id));

            return notification;
        }

        getIcon(type) {
            const icons = {
                success: '<i class="fas fa-check-circle"></i>',
                danger: '<i class="fas fa-exclamation-triangle"></i>',
                warning: '<i class="fas fa-exclamation-circle"></i>',
                info: '<i class="fas fa-info-circle"></i>',
                primary: '<i class="fas fa-bell"></i>'
            };
            return icons[type] || icons.info;
        }

        generateId() {
            return 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        }

        // Métodos de conveniência
        success(message, options) {
            return this.show(message, 'success', options);
        }

        error(message, options) {
            return this.show(message, 'danger', options);
        }

        warning(message, options) {
            return this.show(message, 'warning', options);
        }

        info(message, options) {
            return this.show(message, 'info', options);
        }
    }

    // ===== GERENCIAMENTO DE FORMULÁRIOS =====
    class FormManager {
        constructor() {
            this.init();
        }

        init() {
            // Auto-validação de formulários
            this.setupFormValidation();
            
            // Loading states em botões
            this.setupButtonLoading();
            
            // Confirmação de ações perigosas
            this.setupDangerousActions();
        }

        setupFormValidation() {
            const forms = document.querySelectorAll('.needs-validation');
            forms.forEach(form => {
                form.addEventListener('submit', (event) => {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                        this.showValidationErrors(form);
                    }
                    form.classList.add('was-validated');
                });
            });
        }

        setupButtonLoading() {
            const buttons = document.querySelectorAll('[data-loading-text]');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    this.setButtonLoading(button, true);
                });
            });
        }

        setupDangerousActions() {
            const dangerousButtons = document.querySelectorAll('[data-confirm]');
            dangerousButtons.forEach(button => {
                button.addEventListener('click', (event) => {
                    const message = button.getAttribute('data-confirm');
                    if (!confirm(message)) {
                        event.preventDefault();
                    }
                });
            });
        }

        setButtonLoading(button, loading) {
            if (loading) {
                button.setAttribute('data-original-text', button.innerHTML);
                const loadingText = button.getAttribute('data-loading-text') || 'Carregando...';
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    ${loadingText}
                `;
                button.disabled = true;
            } else {
                const originalText = button.getAttribute('data-original-text');
                if (originalText) {
                    button.innerHTML = originalText;
                }
                button.disabled = false;
            }
        }

        showValidationErrors(form) {
            const invalidFields = form.querySelectorAll(':invalid');
            if (invalidFields.length > 0) {
                invalidFields[0].focus();
                GestaoAVista.notifications.error('Por favor, corrija os campos destacados.');
            }
        }
    }

    // ===== UTILITÁRIOS DE TABELA =====
    class TableManager {
        constructor() {
            this.init();
        }

        init() {
            this.setupSortable();
            this.setupSearchable();
            this.setupRowActions();
        }

        setupSortable() {
            const sortableHeaders = document.querySelectorAll('[data-sortable]');
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => this.sortTable(header));
            });
        }

        setupSearchable() {
            const searchInputs = document.querySelectorAll('[data-table-search]');
            searchInputs.forEach(input => {
                const tableId = input.getAttribute('data-table-search');
                const table = document.getElementById(tableId);
                if (table) {
                    input.addEventListener('input', () => this.searchTable(input.value, table));
                }
            });
        }

        setupRowActions() {
            const actionButtons = document.querySelectorAll('[data-row-action]');
            actionButtons.forEach(button => {
                button.addEventListener('click', (event) => {
                    const action = button.getAttribute('data-row-action');
                    const rowId = button.getAttribute('data-row-id');
                    this.handleRowAction(action, rowId, button);
                });
            });
        }

        sortTable(header) {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(header.parentNode.children).indexOf(header);
            const isAscending = !header.classList.contains('sort-asc');

            rows.sort((a, b) => {
                const aText = a.children[columnIndex].textContent.trim();
                const bText = b.children[columnIndex].textContent.trim();
                
                // Tentar converter para número
                const aNum = parseFloat(aText);
                const bNum = parseFloat(bText);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? aNum - bNum : bNum - aNum;
                }
                
                return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
            });

            // Remover classes de ordenação de todos os headers
            table.querySelectorAll('[data-sortable]').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Adicionar classe apropriada
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');

            // Reordenar linhas
            rows.forEach(row => tbody.appendChild(row));
        }

        searchTable(query, table) {
            const tbody = table.querySelector('tbody');
            const rows = tbody.querySelectorAll('tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const matches = text.includes(query.toLowerCase());
                row.style.display = matches ? '' : 'none';
            });
        }

        handleRowAction(action, rowId, button) {
            // Implementar ações específicas baseadas no tipo
            console.log('Row action:', action, 'Row ID:', rowId);
        }
    }

    // ===== GERENCIAMENTO DE TEMA =====
    class ThemeManager {
        constructor() {
            this.currentTheme = this.getStoredTheme() || 'light';
            this.init();
        }

        init() {
            this.applyTheme(this.currentTheme);
            this.setupToggle();
        }

        setupToggle() {
            const toggleBtn = document.querySelector('[data-theme-toggle]');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => this.toggle());
            }
        }

        toggle() {
            this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
            this.applyTheme(this.currentTheme);
            this.saveTheme();
        }

        applyTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            
            // Atualizar ícone do botão se existir
            const toggleBtn = document.querySelector('[data-theme-toggle]');
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
                }
            }
        }

        saveTheme() {
            localStorage.setItem(config.theme.storageKey, this.currentTheme);
        }

        getStoredTheme() {
            return localStorage.getItem(config.theme.storageKey);
        }
    }

    // ===== UTILITÁRIOS GERAIS =====
    const Utils = {
        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Throttle function
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Format currency
        formatCurrency(value, currency = 'BRL') {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: currency
            }).format(value);
        },

        // Format date
        formatDate(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            };
            return new Intl.DateTimeFormat('pt-BR', { ...defaultOptions, ...options }).format(new Date(date));
        },

        // Copy to clipboard
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                GestaoAVista.notifications.success('Copiado para a área de transferência!');
                return true;
            } catch (err) {
                console.error('Erro ao copiar:', err);
                GestaoAVista.notifications.error('Erro ao copiar para a área de transferência.');
                return false;
            }
        },

        // Smooth scroll to element
        scrollTo(element, offset = 0) {
            const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
            if (targetElement) {
                const targetPosition = targetElement.offsetTop - offset;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        }
    };

    // ===== INICIALIZAÇÃO =====
    document.addEventListener('DOMContentLoaded', function() {
        // Inicializar componentes
        GestaoAVista.sidebar = new SidebarManager();
        GestaoAVista.notifications = new NotificationManager();
        GestaoAVista.forms = new FormManager();
        GestaoAVista.tables = new TableManager();
        GestaoAVista.theme = new ThemeManager();
        GestaoAVista.utils = Utils;

        // Inicializar tooltips do Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Inicializar popovers do Bootstrap
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });

        // Event listener global para AJAX
        document.addEventListener('ajax:success', function(event) {
            const response = event.detail;
            if (response.message) {
                GestaoAVista.notifications.success(response.message);
            }
        });

        document.addEventListener('ajax:error', function(event) {
            const response = event.detail;
            const message = response.message || 'Ocorreu um erro inesperado.';
            GestaoAVista.notifications.error(message);
        });

        // Marcar como inicializado
        document.body.classList.add('gestao-vista-initialized');
        
        console.log('Gestão à Vista - Sistema inicializado com sucesso!');
    });

    // Expor no escopo global
    window.GestaoAVista = GestaoAVista;

})();
