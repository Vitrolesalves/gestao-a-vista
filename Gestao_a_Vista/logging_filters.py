"""
Filtros customizados para logging
"""

import logging
import re
from datetime import datetime


class SecurityFilter(logging.Filter):
    """Filtro para eventos de segurança"""

    SECURITY_KEYWORDS = [
        "login",
        "logout",
        "authentication",
        "authorization",
        "permission",
        "access",
        "forbidden",
        "unauthorized",
        "csrf",
        "xss",
        "injection",
        "attack",
        "suspicious",
        "failed",
        "blocked",
        "banned",
    ]

    def filter(self, record):
        """Filtra apenas logs relacionados à segurança"""
        message = record.getMessage().lower()

        # Verificar se contém palavras-chave de segurança
        for keyword in self.SECURITY_KEYWORDS:
            if keyword in message:
                return True

        # Verificar se é um log de erro HTTP relacionado à segurança
        if hasattr(record, "status_code"):
            if record.status_code in [401, 403, 429]:
                return True

        return False


class PerformanceFilter(logging.Filter):
    """Filtro para logs de performance"""

    def filter(self, record):
        """Filtra apenas logs de performance"""
        # Verificar se tem informações de timing
        if hasattr(record, "duration"):
            return True

        # Verificar se é um log de query lenta
        message = record.getMessage().lower()
        if "slow" in message or "performance" in message or "duration" in message:
            return True

        return False


class SensitiveDataFilter(logging.Filter):
    """Filtro para remover dados sensíveis dos logs"""

    SENSITIVE_PATTERNS = [
        # Senhas
        (
            re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE),
            "password=***",
        ),
        # Tokens
        (
            re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE),
            "token=***",
        ),
        # API Keys
        (
            re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE),
            "api_key=***",
        ),
        # CPF/CNPJ
        (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "***.***.***-**"),
        (re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"), "**.***.***/****-**"),
        # Cartão de crédito
        (
            re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "**** **** **** ****",
        ),
        # Email (parcial)
        (
            re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"),
            r"\1***@\2",
        ),
    ]

    def filter(self, record):
        """Remove dados sensíveis da mensagem de log"""
        if hasattr(record, "msg"):
            message = str(record.msg)

            # Aplicar todos os padrões de limpeza
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)

            record.msg = message

        return True


class RateLimitFilter(logging.Filter):
    """Filtro para rate limiting de logs"""

    def __init__(self, rate_limit=100, time_window=60):
        super().__init__()
        self.rate_limit = rate_limit  # Máximo de logs por janela
        self.time_window = time_window  # Janela de tempo em segundos
        self.log_counts = {}
        self.last_reset = datetime.now()

    def filter(self, record):
        """Aplica rate limiting baseado no tipo de log"""
        now = datetime.now()

        # Reset contadores a cada janela de tempo
        if (now - self.last_reset).seconds >= self.time_window:
            self.log_counts.clear()
            self.last_reset = now

        # Identificar tipo de log
        log_key = f"{record.levelname}:{record.module}"

        # Contar logs
        self.log_counts[log_key] = self.log_counts.get(log_key, 0) + 1

        # Verificar se excedeu o limite
        if self.log_counts[log_key] > self.rate_limit:
            # Permitir apenas uma mensagem de aviso sobre rate limit
            if self.log_counts[log_key] == self.rate_limit + 1:
                record.msg = (
                    f"Rate limit exceeded for {log_key}. Suppressing further logs."
                )
                return True
            return False

        return True


class StructuredLogFilter(logging.Filter):
    """Filtro para adicionar informações estruturadas aos logs"""

    def filter(self, record):
        """Adiciona campos estruturados ao log"""
        # Adicionar timestamp ISO
        record.timestamp = datetime.now().isoformat()

        # Adicionar informações do ambiente
        record.environment = getattr(record, "environment", "unknown")
        record.service = "gestao-a-vista"
        record.version = getattr(record, "version", "1.0.0")

        # Adicionar contexto da requisição se disponível
        if hasattr(record, "request"):
            request = record.request
            record.user_id = (
                getattr(request.user, "id", None) if hasattr(request, "user") else None
            )
            record.session_key = getattr(request, "session", {}).get("session_key")
            record.user_agent = request.META.get("HTTP_USER_AGENT", "")
            record.remote_addr = self._get_client_ip(request)

        return True

    def _get_client_ip(self, request):
        """Obtém IP do cliente"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class ErrorContextFilter(logging.Filter):
    """Filtro para adicionar contexto adicional aos logs de erro"""

    def filter(self, record):
        """Adiciona contexto aos logs de erro"""
        if record.levelno >= logging.ERROR:
            # Adicionar stack trace se disponível
            if record.exc_info:
                record.error_type = (
                    record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
                )
                record.error_message = (
                    str(record.exc_info[1]) if record.exc_info[1] else "No message"
                )

            # Adicionar informações do sistema
            import os

            import psutil

            try:
                process = psutil.Process(os.getpid())
                record.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                record.cpu_percent = process.cpu_percent()
            except:
                record.memory_usage = 0
                record.cpu_percent = 0

        return True


class BusinessMetricsFilter(logging.Filter):
    """Filtro para logs de métricas de negócio"""

    BUSINESS_EVENTS = [
        "user_login",
        "user_logout",
        "user_registration",
        "dashboard_created",
        "dashboard_viewed",
        "dashboard_shared",
        "report_generated",
        "report_downloaded",
        "room_reserved",
        "room_cancelled",
        "qr_generated",
        "qr_scanned",
    ]

    def filter(self, record):
        """Filtra logs de métricas de negócio"""
        message = record.getMessage().lower()

        # Verificar se é um evento de negócio
        for event in self.BUSINESS_EVENTS:
            if event in message:
                record.business_event = event
                return True

        # Verificar se tem marcador de métrica
        if hasattr(record, "metric_type"):
            return True

        return False
