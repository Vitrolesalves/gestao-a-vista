/**
 * Sistema de Notificações Toast Moderno
 * Compatível com todas as páginas do projeto
 *
 * Uso:
 * showNotification('Mensagem', 'success');
 * showNotification('Erro ao salvar', 'error');
 * showNotification('Aviso importante', 'warning');
 * showNotification('Informação', 'info');
 */

// ========== SISTEMA DE NOTIFICAÇÕES TOAST ==========
function showNotification(message, type = 'info', duration = 5000) {
    // Criar container de notificações se não existir
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }

    // Cores baseadas no tipo
    const colors = {
        success: '#10b981', // verde
        error: '#ef4444',   // vermelho
        info: '#3b82f6',    // azul
        warning: '#f59e0b'  // amarelo
    };

    // Criar notificação
    const notification = document.createElement('div');
    notification.style.cssText = `
        background: white;
        border-left: 4px solid ${colors[type] || colors.info};
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;

    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    messageSpan.style.cssText = 'color: #374151; font-size: 14px; word-break: break-word;';

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: #9ca3af;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        margin-left: 12px;
        flex-shrink: 0;
    `;
    closeBtn.onclick = () => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    };

    notification.appendChild(messageSpan);
    notification.appendChild(closeBtn);
    container.appendChild(notification);

    // Auto-hide
    if (duration > 0) {
        setTimeout(() => {
            if (document.contains(notification)) {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    return notification;
}

// Adicionar estilos de animação
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ========== FIM SISTEMA DE NOTIFICAÇÕES ==========

// Aliases úteis para uso comum
const notify = {
    success: (msg, duration = 5000) => showNotification(msg, 'success', duration),
    error: (msg, duration = 5000) => showNotification(msg, 'error', duration),
    warning: (msg, duration = 5000) => showNotification(msg, 'warning', duration),
    info: (msg, duration = 5000) => showNotification(msg, 'info', duration)
};
