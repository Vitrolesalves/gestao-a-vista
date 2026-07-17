"""
Middlewares para monitoramento e logging
"""

import json
import time
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .logging_config import (get_client_ip, log_security_event,
                             log_user_activity, logger)

try:
    from prometheus_client import Counter, Gauge, Histogram

    # Métricas Prometheus
    REQUEST_COUNT = Counter(
        "django_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )

    REQUEST_DURATION = Histogram(
        "django_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
    )

    ACTIVE_REQUESTS = Gauge("django_http_requests_active", "Active HTTP requests")

    USER_SESSIONS = Gauge("django_user_sessions_active", "Active user sessions")

    FAILED_LOGINS = Counter(
        "django_failed_logins_total", "Total failed login attempts", ["ip"]
    )

    SUSPICIOUS_REQUESTS = Counter(
        "django_suspicious_requests_total", "Total suspicious requests", ["type", "ip"]
    )

    USER_ACTIVITY = Counter(
        "django_user_activity_total", "Total user activities", ["user", "action"]
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    PROMETHEUS_AVAILABLE = False


class MonitoringMiddleware(MiddlewareMixin):
    """Middleware principal para monitoramento"""

    def process_request(self, request):
        """Processa requisição de entrada"""
        request._monitoring_start_time = time.time()

        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.inc()

        # Log da requisição
        logger.info(
            f"Request started: {request.method} {request.path}",
            method=request.method,
            path=request.path,
            user=str(request.user) if hasattr(request, "user") else "anonymous",
            ip=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

    def process_response(self, request, response):
        """Processa resposta"""
        if hasattr(request, "_monitoring_start_time"):
            duration = time.time() - request._monitoring_start_time

            # Métricas Prometheus
            if PROMETHEUS_AVAILABLE:
                ACTIVE_REQUESTS.dec()

                endpoint = self._get_endpoint_name(request)
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code,
                ).inc()

                REQUEST_DURATION.labels(
                    method=request.method, endpoint=endpoint
                ).observe(duration)

            # Log da resposta
            logger.info(
                f"Request completed: {request.method} {request.path} - {response.status_code}",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration=duration * 1000,  # em ms
                user=str(request.user) if hasattr(request, "user") else "anonymous",
                ip=get_client_ip(request),
            )

            # Log de performance para requisições lentas
            if duration > 2.0:  # > 2 segundos
                logger.warning(
                    f"Slow request detected: {request.method} {request.path}",
                    duration=duration * 1000,
                    threshold=2000,
                    user=str(request.user) if hasattr(request, "user") else "anonymous",
                )

        return response

    def process_exception(self, request, exception):
        """Processa exceções"""
        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.dec()

        # Log da exceção
        logger.error(
            f"Request exception: {request.method} {request.path}",
            exception=str(exception),
            exception_type=type(exception).__name__,
            user=str(request.user) if hasattr(request, "user") else "anonymous",
            ip=get_client_ip(request),
            exc_info=True,
        )

    def _get_endpoint_name(self, request):
        """Obtém nome do endpoint para métricas"""
        try:
            from django.urls import resolve

            resolver_match = resolve(request.path)
            return (
                f"{resolver_match.app_name}:{resolver_match.url_name}"
                if resolver_match.app_name
                else resolver_match.url_name
            )
        except:
            return request.path


class SecurityMiddleware(MiddlewareMixin):
    """Middleware para monitoramento de segurança"""

    SUSPICIOUS_PATTERNS = [
        # SQL Injection
        r"(\bunion\b|\bselect\b|\binsert\b|\bdelete\b|\bdrop\b|\bupdate\b)",
        # XSS
        r"(<script|javascript:|onload=|onerror=)",
        # Path traversal
        r"(\.\./|\.\.\\)",
        # Command injection
        r"(;|\||&|\$\(|\`)",
    ]

    def __init__(self, get_response):
        super().__init__(get_response)
        import re

        self.suspicious_regex = re.compile(
            "|".join(self.SUSPICIOUS_PATTERNS), re.IGNORECASE
        )

    def process_request(self, request):
        """Verifica requisições suspeitas"""
        ip = get_client_ip(request)

        # Verificar rate limiting por IP
        if self._check_rate_limit(ip):
            log_security_event(
                "rate_limit_exceeded",
                f"Rate limit exceeded for IP {ip}",
                request=request,
            )

            if PROMETHEUS_AVAILABLE:
                SUSPICIOUS_REQUESTS.labels(type="rate_limit", ip=ip).inc()

            return JsonResponse({"error": "Rate limit exceeded"}, status=429)

        # Verificar padrões suspeitos
        suspicious_data = self._check_suspicious_patterns(request)
        if suspicious_data:
            log_security_event(
                "suspicious_pattern",
                f"Suspicious pattern detected: {suspicious_data}",
                request=request,
            )

            if PROMETHEUS_AVAILABLE:
                SUSPICIOUS_REQUESTS.labels(type="suspicious_pattern", ip=ip).inc()

        # Verificar user agent suspeito
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if self._is_suspicious_user_agent(user_agent):
            log_security_event(
                "suspicious_user_agent",
                f"Suspicious user agent: {user_agent}",
                request=request,
            )

            if PROMETHEUS_AVAILABLE:
                SUSPICIOUS_REQUESTS.labels(type="suspicious_user_agent", ip=ip).inc()

    def _check_rate_limit(self, ip):
        """Verifica rate limiting por IP"""
        cache_key = f"rate_limit:{ip}"
        requests = cache.get(cache_key, 0)

        if requests >= 100:  # 100 requests por minuto
            return True

        cache.set(cache_key, requests + 1, 60)  # 60 segundos
        return False

    def _check_suspicious_patterns(self, request):
        """Verifica padrões suspeitos na requisição"""
        # Verificar query parameters
        for key, value in request.GET.items():
            if self.suspicious_regex.search(str(value)):
                return f"GET parameter {key}: {value}"

        # Verificar POST data
        if hasattr(request, "POST"):
            for key, value in request.POST.items():
                if self.suspicious_regex.search(str(value)):
                    return f"POST parameter {key}: {value}"

        # Verificar path
        if self.suspicious_regex.search(request.path):
            return f"Path: {request.path}"

        return None

    def _is_suspicious_user_agent(self, user_agent):
        """Verifica se o user agent é suspeito"""
        suspicious_agents = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "zap",
            "burp",
            "w3af",
            "acunetix",
            "nessus",
        ]

        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)


class UserActivityMiddleware(MiddlewareMixin):
    """Middleware para rastrear atividade do usuário"""

    def process_response(self, request, response):
        """Registra atividade do usuário"""
        if hasattr(request, "user") and request.user.is_authenticated:
            # Atualizar sessões ativas
            if PROMETHEUS_AVAILABLE:
                # Contar sessões ativas (aproximação)
                active_sessions = cache.get("active_sessions_count", 0)
                cache.set("active_sessions_count", active_sessions, 300)  # 5 minutos
                USER_SESSIONS.set(active_sessions)

            # Registrar atividade específica baseada no endpoint
            action = self._get_action_from_request(request)
            if action:
                log_user_activity(
                    user=request.user,
                    action=action,
                    resource=request.path,
                    ip=get_client_ip(request),
                )

                if PROMETHEUS_AVAILABLE:
                    USER_ACTIVITY.labels(user=str(request.user), action=action).inc()

        return response

    def _get_action_from_request(self, request):
        """Determina a ação baseada na requisição"""
        method = request.method
        path = request.path.lower()

        # Mapear endpoints para ações
        if "login" in path and method == "POST":
            return "login"
        elif "logout" in path:
            return "logout"
        elif "dashboard" in path:
            if method == "GET":
                return "dashboard_view"
            elif method == "POST":
                return "dashboard_create"
            elif method in ["PUT", "PATCH"]:
                return "dashboard_update"
            elif method == "DELETE":
                return "dashboard_delete"
        elif "report" in path:
            if method == "GET":
                return "report_view"
            elif method == "POST":
                return "report_generate"
        elif "qr" in path:
            return "qr_generate"
        elif "room" in path or "sala" in path:
            if method == "POST":
                return "room_reserve"
            elif method == "DELETE":
                return "room_cancel"

        return None


class HealthCheckMiddleware(MiddlewareMixin):
    """Middleware para health checks"""

    def process_request(self, request):
        """Processa health checks"""
        if request.path == "/health/":
            return self._health_check_response()
        elif request.path == "/metrics/":
            return self._metrics_response()

    def _health_check_response(self):
        """Resposta do health check"""
        from django.core.cache import cache
        from django.db import connection

        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        # Verificar banco de dados
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            status["checks"]["database"] = "healthy"
        except Exception as e:
            status["checks"]["database"] = f"unhealthy: {str(e)}"
            status["status"] = "unhealthy"

        # Verificar cache
        try:
            cache.set("health_check", "ok", 30)
            cache.get("health_check")
            status["checks"]["cache"] = "healthy"
        except Exception as e:
            status["checks"]["cache"] = f"unhealthy: {str(e)}"
            status["status"] = "unhealthy"

        # Verificar disco
        import shutil

        try:
            disk_usage = shutil.disk_usage("/")
            free_percent = (disk_usage.free / disk_usage.total) * 100
            if free_percent < 10:
                status["checks"]["disk"] = f"warning: {free_percent:.1f}% free"
            else:
                status["checks"]["disk"] = "healthy"
        except Exception as e:
            status["checks"]["disk"] = f"error: {str(e)}"

        http_status = 200 if status["status"] == "healthy" else 503
        return JsonResponse(status, status=http_status)

    def _metrics_response(self):
        """Resposta das métricas Prometheus"""
        if not PROMETHEUS_AVAILABLE:
            return JsonResponse({"error": "Prometheus not available"}, status=503)

        from django.http import HttpResponse
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        metrics_data = generate_latest()
        return HttpResponse(metrics_data, content_type=CONTENT_TYPE_LATEST)


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware para monitoramento de performance"""

    def process_request(self, request):
        """Inicia monitoramento de performance"""
        request._perf_start = time.time()
        request._perf_queries_start = len(connection.queries) if settings.DEBUG else 0

    def process_response(self, request, response):
        """Finaliza monitoramento de performance"""
        if hasattr(request, "_perf_start"):
            duration = time.time() - request._perf_start

            # Contar queries (apenas em debug)
            queries_count = 0
            if settings.DEBUG and hasattr(request, "_perf_queries_start"):
                queries_count = len(connection.queries) - request._perf_queries_start

            # Log de performance
            perf_data = {
                "duration": duration * 1000,  # ms
                "queries_count": queries_count,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
            }

            # Log se performance ruim
            if duration > 1.0 or queries_count > 10:
                logger.warning(
                    f"Performance issue: {request.method} {request.path}", **perf_data
                )

            # Adicionar headers de performance
            response["X-Response-Time"] = f"{duration * 1000:.2f}ms"
            if settings.DEBUG:
                response["X-DB-Queries"] = str(queries_count)

        return response
