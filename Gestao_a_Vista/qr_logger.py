"""
Sistema de logging estruturado para o módulo de QR Codes
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.conf import settings


class QRCodeLogger:
    """Logger estruturado para operações de QR Code"""

    def __init__(self):
        self.logger = logging.getLogger("qr_code")

        # Configurar handler se não existir
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _log_structured(
        self, level: str, message: str, extra_data: Optional[Dict[str, Any]] = None
    ):
        """Log estruturado com dados extras"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "module": "qr_code",
            "message": message,
        }

        if extra_data:
            log_data.update(extra_data)

        # Log como JSON estruturado
        log_message = json.dumps(log_data, ensure_ascii=False, default=str)

        getattr(self.logger, level.lower())(log_message)

    def info(self, message: str, **kwargs):
        """Log de informação"""
        self._log_structured("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self._log_structured("WARNING", message, kwargs)

    def error(self, message: str, **kwargs):
        """Log de erro"""
        self._log_structured("ERROR", message, kwargs)

    def debug(self, message: str, **kwargs):
        """Log de debug"""
        if settings.DEBUG:
            self._log_structured("DEBUG", message, kwargs)

    def log_request_start(self, user_id: Optional[int], request_data: Dict[str, Any]):
        """Log início de requisição"""
        self.info(
            "QR Code generation request started",
            user_id=user_id,
            cr_number=request_data.get("cr_number"),
            service=request_data.get("service"),
            locations_count=len(request_data.get("locations", [])),
            logo_size=request_data.get("logo_size"),
            service_logo_size=request_data.get("service_logo_size"),
        )

    def log_validation_error(
        self, field: str, error_message: str, user_id: Optional[int] = None
    ):
        """Log erro de validação"""
        self.warning(
            "QR Code validation error",
            user_id=user_id,
            field=field,
            error=error_message,
        )

    def log_generation_success(
        self,
        user_id: Optional[int],
        cr_number: str,
        locations_count: int,
        generation_time: float,
    ):
        """Log sucesso na geração"""
        self.info(
            "QR Code generation completed successfully",
            user_id=user_id,
            cr_number=cr_number,
            locations_count=locations_count,
            generation_time_seconds=round(generation_time, 3),
        )

    def log_generation_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[int] = None,
        **kwargs
    ):
        """Log erro na geração"""
        self.error(
            "QR Code generation failed",
            user_id=user_id,
            error_type=error_type,
            error=error_message,
            **kwargs
        )

    def log_database_query(
        self,
        query_type: str,
        table: str,
        execution_time: float,
        record_count: int = None,
    ):
        """Log query de banco de dados"""
        self.debug(
            "Database query executed",
            query_type=query_type,
            table=table,
            execution_time_seconds=round(execution_time, 4),
            record_count=record_count,
        )

    def log_image_processing(
        self,
        operation: str,
        image_path: Optional[str] = None,
        image_size: Optional[tuple] = None,
        processing_time: float = None,
    ):
        """Log processamento de imagem"""
        self.debug(
            "Image processing operation",
            operation=operation,
            image_path=image_path,
            image_size=image_size,
            processing_time_seconds=round(processing_time, 4)
            if processing_time
            else None,
        )

    def log_configuration_error(self, setting: str, error_message: str):
        """Log erro de configuração"""
        self.error("QR Code configuration error", setting=setting, error=error_message)

    def log_permission_denied(self, user_id: int, action: str, resource: str = None):
        """Log negação de permissão"""
        self.warning(
            "QR Code permission denied",
            user_id=user_id,
            action=action,
            resource=resource,
        )

    def log_performance_metric(
        self, metric_name: str, value: float, unit: str = "seconds"
    ):
        """Log métrica de performance"""
        self.info(
            "QR Code performance metric",
            metric=metric_name,
            value=round(value, 4),
            unit=unit,
        )


# Instância global do logger
qr_logger = QRCodeLogger()
