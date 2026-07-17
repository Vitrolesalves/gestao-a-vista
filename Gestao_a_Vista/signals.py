"""
Signal handlers for tracking changes to PlannerProject model
Automatically logs changes to project fields and responsaveis
"""
import logging
import threading
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import PlannerProject, PlannerProjectChangeHistory, PlannerProjectResponsavel

# Thread-local storage for request context
_thread_locals = threading.local()

# Logger configuration
logger = logging.getLogger(__name__)

# Fields to track for changes
TRACKED_FIELDS = [
    'nome',
    'status',
    'prioridade',
    'data_inicial',
    'data_conclusao',
    'observacao',
    'tipo_servico'
]

CustomUser = get_user_model()


def get_current_request():
    """
    Retrieves the current request from thread-local storage
    Returns None if no request is available
    """
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """
    Stores the current request in thread-local storage
    Should be called from middleware
    """
    _thread_locals.request = request


def clear_current_request():
    """
    Clears the current request from thread-local storage
    """
    if hasattr(_thread_locals, 'request'):
        del _thread_locals.request


def get_client_ip(request):
    """
    Extracts the client IP address from the request
    Handles proxy headers (X-Forwarded-For, X-Real-IP)
    """
    if not request:
        return ''

    # Check for proxy headers first
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Check X-Real-IP header
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()

    # Fall back to REMOTE_ADDR
    remote_addr = request.META.get('REMOTE_ADDR', '')
    return remote_addr


def get_field_display_value(instance, field_name):
    """
    Gets the display value for a field, handling foreign keys and choices
    """
    try:
        value = getattr(instance, field_name)

        # Handle None values
        if value is None:
            return 'Nenhum'

        # Handle ForeignKey fields
        if field_name == 'tipo_servico' and value:
            return str(value)

        # Handle choice fields with get_FOO_display()
        if hasattr(instance, f'get_{field_name}_display'):
            return getattr(instance, f'get_{field_name}_display')()

        # Handle date fields
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')

        # Default: convert to string
        return str(value)
    except Exception as e:
        logger.error(f'Error getting display value for field {field_name}: {e}')
        return str(value)


@receiver(pre_save, sender=PlannerProject)
def capture_old_values(sender, instance, **kwargs):
    """
    Signal handler executed BEFORE saving a PlannerProject
    Captures the old values of tracked fields for comparison in post_save
    """
    # Only capture old values if this is an update (not a new instance)
    if instance.pk:
        try:
            # Fetch the current database state
            old_instance = PlannerProject.objects.get(pk=instance.pk)

            # Store old values in a temporary attribute
            instance._old_values = {}
            for field in TRACKED_FIELDS:
                instance._old_values[field] = getattr(old_instance, field)

            logger.debug(f'Captured old values for project {instance.pk}: {instance._old_values}')
        except PlannerProject.DoesNotExist:
            # This shouldn't happen, but handle gracefully
            logger.warning(f'PlannerProject {instance.pk} not found in pre_save')
            instance._old_values = {}
    else:
        # New instance - no old values
        instance._old_values = None


@receiver(post_save, sender=PlannerProject)
def track_project_changes(sender, instance, created, **kwargs):
    """
    Signal handler executed AFTER saving a PlannerProject
    Creates history records for changes detected
    """
    try:
        # Get current request and user
        request = get_current_request()
        usuario = request.user if request and request.user.is_authenticated else None
        ip_address = get_client_ip(request) if request else ''

        # Handle project creation
        if created:
            PlannerProjectChangeHistory.objects.create(
                projeto=instance,
                usuario=usuario,
                tipo_alteracao='criado',
                descricao=f'Projeto "{instance.nome}" criado',
                ip_address=ip_address
            )
            logger.info(f'History record created for new project: {instance.nome}')
            return

        # Handle project updates
        if hasattr(instance, '_old_values') and instance._old_values is not None:
            changes_detected = False

            # Check each tracked field for changes
            for field in TRACKED_FIELDS:
                old_value = instance._old_values.get(field)
                new_value = getattr(instance, field)

                # Detect if value changed
                if old_value != new_value:
                    changes_detected = True

                    # Get display values
                    old_display = get_field_display_value(
                        type('obj', (object,), {field: old_value})(),
                        field
                    )
                    new_display = get_field_display_value(instance, field)

                    # Determine change type
                    if field == 'status':
                        tipo_alteracao = 'status_alterado'
                        descricao = f'Status alterado de "{old_display}" para "{new_display}"'
                    elif field == 'prioridade':
                        tipo_alteracao = 'prioridade_alterada'
                        descricao = f'Prioridade alterada de "{old_display}" para "{new_display}"'
                    else:
                        tipo_alteracao = 'atualizado'
                        descricao = f'Campo "{field}" alterado'

                    # Create history record
                    PlannerProjectChangeHistory.objects.create(
                        projeto=instance,
                        usuario=usuario,
                        tipo_alteracao=tipo_alteracao,
                        campo=field,
                        valor_anterior=str(old_display),
                        valor_novo=str(new_display),
                        descricao=descricao,
                        ip_address=ip_address
                    )

                    logger.info(f'Change tracked for project {instance.nome}: {field} changed from {old_display} to {new_display}')

            if not changes_detected:
                logger.debug(f'No changes detected for project {instance.nome}')

            # Clean up temporary attribute
            delattr(instance, '_old_values')

    except Exception as e:
        logger.error(f'Error tracking project changes for {instance.pk}: {e}', exc_info=True)


@receiver(m2m_changed, sender=PlannerProject.responsaveis.through)
def track_responsavel_changes(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler for m2m changes to responsaveis field
    Tracks when responsaveis are added or removed from projects
    """
    # Only track post_add and post_remove actions
    if action not in ['post_add', 'post_remove']:
        return

    try:
        # Get current request and user
        request = get_current_request()
        usuario = request.user if request and request.user.is_authenticated else None
        ip_address = get_client_ip(request) if request else ''

        # Process each affected user
        if pk_set:
            for user_pk in pk_set:
                try:
                    responsavel = CustomUser.objects.get(pk=user_pk)

                    if action == 'post_add':
                        tipo_alteracao = 'responsavel_adicionado'
                        descricao = f'Responsável "{responsavel.name}" adicionado ao projeto'
                        valor_novo = responsavel.name
                        valor_anterior = None
                    else:  # post_remove
                        tipo_alteracao = 'responsavel_removido'
                        descricao = f'Responsável "{responsavel.name}" removido do projeto'
                        valor_anterior = responsavel.name
                        valor_novo = None

                    # Create history record
                    PlannerProjectChangeHistory.objects.create(
                        projeto=instance,
                        usuario=usuario,
                        tipo_alteracao=tipo_alteracao,
                        campo='responsaveis',
                        valor_anterior=valor_anterior,
                        valor_novo=valor_novo,
                        descricao=descricao,
                        ip_address=ip_address
                    )

                    logger.info(f'Responsavel change tracked for project {instance.nome}: {descricao}')

                except CustomUser.DoesNotExist:
                    logger.warning(f'User {user_pk} not found when tracking responsavel change')

    except Exception as e:
        logger.error(f'Error tracking responsavel changes for project {instance.pk}: {e}', exc_info=True)


# Middleware helper class
class RequestContextMiddleware:
    """
    Middleware to store the current request in thread-local storage
    This allows signals to access the request without it being passed explicitly

    Add this to MIDDLEWARE in settings.py:
    'Gestao_a_Vista.signals.RequestContextMiddleware',
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread-local storage
        set_current_request(request)

        try:
            # Process the request
            response = self.get_response(request)
            return response
        finally:
            # Clean up thread-local storage
            clear_current_request()


import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import GestaoSala # Substitua 'GestaoSala' pelo nome real do model da sua Sala

# 1. Apaga a imagem quando a SALA inteira for deletada
@receiver(post_delete, sender=GestaoSala)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Apaga o arquivo do diretório quando o registro é deletado."""
    if instance.foto: # Substitua 'foto' se o campo tiver outro nome
        if os.path.isfile(instance.foto.path):
            os.remove(instance.foto.path)

# 2. Apaga a imagem ANTIGA quando uma NOVA imagem é enviada (Update)
@receiver(pre_save, sender=GestaoSala)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """Apaga o arquivo antigo do diretório quando a imagem é alterada."""
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).foto
    except sender.DoesNotExist:
        return False

    new_file = instance.foto
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)