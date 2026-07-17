"""
Context processors para Gestão à Vista
Adiciona variáveis globais aos templates
"""


def user_permissions(request):
    """
    Adiciona as permissões do usuário ao contexto de todos os templates
    """
    if request.user.is_authenticated:
        # Se for administrador, todas as permissões são True
        if request.user.role == "administrador":
            return {
                'user_has_permissions': {
                    "controle_acessos": True,  # Controle de Usuários (apenas admin)
                    "dashboard": True,
                    "monitoramento": True,
                    "qr_generator": True,
                    "etiquetas_generator": True,
                    "desativacao_cr": True,
                    "controle_chips": True,
                    "implantacoes_opsvista": True,
                    "implantacoes_fluxo": True,
                    "desmobilizacoes_fluxo": True,
                    "portaria_base": True,
                    "gestao_salas": True,
                    "reserva_salas": True,
                    "calendario_reservas": True,
                    "livro_ata": True,
                    "planner": True,
                    "explorer": True,
                    "torre_controle": True,
                    "relatorios": True,
                    "gestao_qualidade": True,
                    "calendario_2026": True,
                    "psicossocial": True,
                    "financeiro": True,
                    "cmo_efetivo": True,
                    "cmo_efetivo_torre": True,
                    "cmo_efetivo_cmo": True,
                    "links_importantes": True,
                    "controle_ordens": True,
                }
            }

        # Para outros usuários, usa as permissões armazenadas
        permissions = request.user.page_permissions.copy()

        # Controle de Usuários é apenas para administradores
        permissions['controle_acessos'] = False

        return {
            'user_has_permissions': permissions
        }

    # Usuário não autenticado - sem permissões
    return {
        'user_has_permissions': {}
    }


def created_regionais_processor(request):
    """
    Adiciona a lista de regionais criadas no banco de dados ao contexto,
    para o filtro regional do Administrador Supremo. Lista cada Regional
    individualmente (não só estados únicos), já que pode haver mais de uma
    Regional no mesmo estado, cada uma com seu próprio banco de dados.
    """
    if request.user.is_authenticated and getattr(request.user, 'is_global_admin', False):
        from .models import Regional

        regionais = Regional.objects.all().order_by('estado', 'nome')
        regionais_dropdown = [
            {
                'id': str(reg.id),
                'nome': f"{reg.nome} ({reg.estado})",
                'db_slug': reg.db_slug,
            }
            for reg in regionais
        ]

        return {
            'global_regionais_dropdown': regionais_dropdown
        }
    return {
        'global_regionais_dropdown': []
    }

