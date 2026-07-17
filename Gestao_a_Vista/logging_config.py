"""
Configurações avançadas de logging para Gestão à Vista
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Diretório base para logs
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configuração de logging estruturado
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
        },
        "security": {
            "format": "SECURITY {asctime} {levelname} {module} {message}",
            "style": "{",
        },
        "audit": {
            "format": "AUDIT {asctime} {user} {action} {resource} {result} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "security_filter": {
            "()": "Gestao_a_Vista.logging_filters.SecurityFilter",
        },
        "performance_filter": {
            "()": "Gestao_a_Vista.logging_filters.PerformanceFilter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django_error.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "file_json": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.json",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "json",
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "security.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 20,
            "formatter": "security",
            "filters": ["security_filter"],
        },
        "audit_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "audit.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 30,
            "formatter": "audit",
        },
        "performance_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "performance.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "json",
            "filters": ["performance_filter"],
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.SentryHandler",
        }
        if "SENTRY_DSN" in os.environ
        else {
            "level": "ERROR",
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file_info", "file_json"],
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_info", "file_error", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "mail_admins", "sentry"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file_info"],
            "level": "DEBUG" if os.environ.get("DEBUG_SQL") == "1" else "INFO",
            "propagate": False,
        },
        "Gestao_a_Vista": {
            "handlers": ["console", "file_info", "file_json", "sentry"],
            "level": "DEBUG",
            "propagate": False,
        },
        "Gestao_a_Vista.security": {
            "handlers": ["security_file", "mail_admins", "sentry"],
            "level": "WARNING",
            "propagate": False,
        },
        "Gestao_a_Vista.audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "Gestao_a_Vista.performance": {
            "handlers": ["performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["file_info", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["file_info"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


class StructuredLogger:
    """Logger estruturado para diferentes tipos de eventos"""

    def __init__(self):
        self.app_logger = logging.getLogger("Gestao_a_Vista")
        self.security_logger = logging.getLogger("Gestao_a_Vista.security")
        self.audit_logger = logging.getLogger("Gestao_a_Vista.audit")
        self.performance_logger = logging.getLogger("Gestao_a_Vista.performance")

    def info(self, message, **kwargs):
        """Log de informação geral"""
        self.app_logger.info(message, extra=kwargs)

    def error(self, message, **kwargs):
        """Log de erro"""
        self.app_logger.error(message, extra=kwargs)

    def warning(self, message, **kwargs):
        """Log de aviso"""
        self.app_logger.warning(message, extra=kwargs)

    def security(self, event_type, message, user=None, ip=None, **kwargs):
        """Log de evento de segurança"""
        extra = {
            "event_type": event_type,
            "user": str(user) if user else "anonymous",
            "ip": ip,
            **kwargs,
        }
        self.security_logger.warning(message, extra=extra)

    def audit(self, user, action, resource, result="success", **kwargs):
        """Log de auditoria"""
        extra = {
            "user": str(user),
            "action": action,
            "resource": resource,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.audit_logger.info(f"{action} on {resource}", extra=extra)

    def performance(self, operation, duration, **kwargs):
        """Log de performance"""
        extra = {
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.performance_logger.info(f"{operation} took {duration}ms", extra=extra)


# Instância global do logger estruturado
logger = StructuredLogger()


def log_user_activity(user, action, resource=None, ip=None, **kwargs):
    """Helper para log de atividade do usuário"""
    logger.audit(
        user=user, action=action, resource=resource or "unknown", ip=ip, **kwargs
    )


def log_security_event(event_type, message, request=None, **kwargs):
    """Helper para log de eventos de segurança"""
    user = getattr(request, "user", None) if request else None
    ip = get_client_ip(request) if request else None

    logger.security(event_type=event_type, message=message, user=user, ip=ip, **kwargs)


def log_performance(operation, start_time, **kwargs):
    """Helper para log de performance"""
    duration = (datetime.now() - start_time).total_seconds() * 1000
    logger.performance(operation=operation, duration=duration, **kwargs)


def get_client_ip(request):
    """Obtém IP do cliente da requisição"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


# Configuração para Sentry (se disponível)
def configure_sentry():
    """Configura Sentry para monitoramento de erros"""
    import os

    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.django import DjangoIntegration
            from sentry_sdk.integrations.redis import RedisIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    DjangoIntegration(
                        transaction_style="url",
                        middleware_spans=True,
                        signals_spans=True,
                    ),
                    CeleryIntegration(monitor_beat_tasks=True),
                    RedisIntegration(),
                ],
                traces_sample_rate=0.1,
                send_default_pii=False,
                environment=os.environ.get("ENVIRONMENT", "development"),
                release=os.environ.get("VERSION", "unknown"),
            )

            logger.info("Sentry configured successfully")

        except ImportError:
            logger.warning("Sentry SDK not installed")
        except Exception as e:
            logger.error(f"Failed to configure Sentry: {e}")


# Configurar Sentry na importação
configure_sentry()
