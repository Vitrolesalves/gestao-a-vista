"""
Utilitários para sistema de auditoria
"""
from django.utils import timezone
from .models import MonitoramentoLog


def registrar_acao_auditoria(usuario, acao, tipo_item, item_id, detalhes="", status_anterior="", status_novo=""):
    """
    Registra uma ação no sistema de auditoria
    
    Args:
        usuario: Usuário que executou a ação
        acao: Descrição da ação (ex: "criou", "editou", "excluiu")
        tipo_item: Tipo do item (ex: "sala", "reserva", "usuario")
        item_id: ID do item afetado
        detalhes: Detalhes adicionais da ação
        status_anterior: Status anterior do item (opcional)
        status_novo: Novo status do item (opcional)
    """
    try:
        log = MonitoramentoLog.objects.create(
            tipo=f"{acao}_{tipo_item}",
            item_id=item_id,
            status_anterior=status_anterior or "N/A",
            status_novo=status_novo or "N/A",
            observacao=detalhes,
            usuario=usuario,
            created_at=timezone.now()
        )
        return log
    except Exception as e:
        # Em caso de erro, não deve quebrar a aplicação
        print(f"Erro ao registrar auditoria: {e}")
        return None


def buscar_logs_auditoria(tipo_item=None, item_id=None, usuario=None, data_inicio=None, data_fim=None, limit=100):
    """
    Busca logs de auditoria com filtros
    
    Args:
        tipo_item: Filtrar por tipo de item
        item_id: Filtrar por ID específico
        usuario: Filtrar por usuário
        data_inicio: Data inicial
        data_fim: Data final
        limit: Limite de resultados
    
    Returns:
        QuerySet com os logs encontrados
    """
    logs = MonitoramentoLog.objects.all().order_by('-created_at')
    
    if tipo_item:
        logs = logs.filter(tipo__icontains=tipo_item)
    
    if item_id:
        logs = logs.filter(item_id=item_id)
    
    if usuario:
        logs = logs.filter(usuario=usuario)
    
    if data_inicio:
        logs = logs.filter(created_at__gte=data_inicio)
    
    if data_fim:
        logs = logs.filter(created_at__lte=data_fim)
    
    return logs[:limit]


def formatar_log_auditoria(log):
    """
    Formata um log de auditoria para exibição
    
    Args:
        log: Instância de MonitoramentoLog
    
    Returns:
        Dict com dados formatados
    """
    return {
        'id': log.id,
        'data_hora': log.created_at.strftime('%d/%m/%Y %H:%M:%S'),
        'usuario': log.usuario.username if log.usuario else 'Sistema',
        'acao': log.tipo,
        'item_id': log.item_id,
        'status_anterior': log.status_anterior,
        'status_novo': log.status_novo,
        'detalhes': log.observacao,
    }
