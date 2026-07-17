"""
Validadores para o módulo de geração de QR Codes
"""
import json
import re
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .qr_exceptions import QRCodeValidationError


class QRCodeValidator:
    """Classe para validação de dados de entrada do QR Code"""

    # Constantes de validação
    MAX_CR_NUMBER_LENGTH = 20
    MAX_SERVICE_NAME_LENGTH = 100
    MAX_LOCATION_NAME_LENGTH = 255
    MIN_LOGO_SIZE = 20
    MAX_LOGO_SIZE = 200
    ALLOWED_IMAGE_FORMATS = ["PNG", "JPEG", "JPG", "GIF"]
    MAX_LOCATIONS_PER_REQUEST = 50

    @staticmethod
    def validate_cr_number(cr_number: str) -> str:
        """Valida número do CR"""
        if not cr_number:
            raise QRCodeValidationError("cr_number", "Número do CR é obrigatório")

        # Remove espaços em branco
        cr_number = cr_number.strip()

        if not cr_number:
            raise QRCodeValidationError("cr_number", "Número do CR não pode ser vazio")

        if len(cr_number) > QRCodeValidator.MAX_CR_NUMBER_LENGTH:
            raise QRCodeValidationError(
                "cr_number",
                f"Número do CR deve ter no máximo {QRCodeValidator.MAX_CR_NUMBER_LENGTH} caracteres",
            )

        # Validar formato (apenas alfanuméricos, hífens e underscores)
        if not re.match(r"^[a-zA-Z0-9\-_]+$", cr_number):
            raise QRCodeValidationError(
                "cr_number",
                "Número do CR deve conter apenas letras, números, hífens e underscores",
            )

        return cr_number.upper()

    @staticmethod
    def validate_service_name(service: str) -> str:
        """Valida nome do serviço"""
        if not service:
            raise QRCodeValidationError("service", "Nome do serviço é obrigatório")

        service = service.strip()

        if not service:
            raise QRCodeValidationError("service", "Nome do serviço não pode ser vazio")

        if len(service) > QRCodeValidator.MAX_SERVICE_NAME_LENGTH:
            raise QRCodeValidationError(
                "service",
                f"Nome do serviço deve ter no máximo {QRCodeValidator.MAX_SERVICE_NAME_LENGTH} caracteres",
            )

        # Sanitizar caracteres especiais perigosos
        dangerous_chars = ["<", ">", '"', "'", "&", "\n", "\r", "\t"]
        for char in dangerous_chars:
            if char in service:
                raise QRCodeValidationError(
                    "service", f"Nome do serviço contém caractere não permitido: {char}"
                )

        return service

    @staticmethod
    def validate_locations(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida lista de locais"""
        if not locations:
            raise QRCodeValidationError("locations", "Lista de locais é obrigatória")

        if not isinstance(locations, list):
            raise QRCodeValidationError("locations", "Locais devem ser uma lista")

        if len(locations) == 0:
            raise QRCodeValidationError(
                "locations", "Pelo menos um local deve ser selecionado"
            )

        if len(locations) > QRCodeValidator.MAX_LOCATIONS_PER_REQUEST:
            raise QRCodeValidationError(
                "locations",
                f"Máximo de {QRCodeValidator.MAX_LOCATIONS_PER_REQUEST} locais por requisição",
            )

        validated_locations = []

        for i, location in enumerate(locations):
            if not isinstance(location, dict):
                raise QRCodeValidationError(
                    "locations", f"Local na posição {i} deve ser um objeto"
                )

            # Validar ID do local
            location_id = location.get("id")
            if location_id is None:
                raise QRCodeValidationError(
                    "locations", f"Local na posição {i} deve ter um ID"
                )

            # Converter ID para inteiro se possível
            try:
                location_id = int(location_id)
            except (ValueError, TypeError):
                raise QRCodeValidationError(
                    "locations", f"ID do local na posição {i} deve ser um número válido"
                )

            # Validar nome do local
            display_name = location.get("displayName", "").strip()
            if not display_name:
                raise QRCodeValidationError(
                    "locations", f"Local na posição {i} deve ter um nome (displayName)"
                )

            if len(display_name) > QRCodeValidator.MAX_LOCATION_NAME_LENGTH:
                raise QRCodeValidationError(
                    "locations",
                    f"Nome do local na posição {i} muito longo (máximo {QRCodeValidator.MAX_LOCATION_NAME_LENGTH} caracteres)",
                )

            validated_locations.append(
                {
                    "id": location_id,
                    "displayName": display_name,
                    "ambiente": location.get("ambiente", "").strip(),
                }
            )

        return validated_locations

    @staticmethod
    def validate_logo_size(size: Any, field_name: str = "logo_size") -> int:
        """Valida tamanho do logo"""
        try:
            size = int(size)
        except (ValueError, TypeError):
            raise QRCodeValidationError(
                field_name, "Tamanho do logo deve ser um número"
            )

        if size < QRCodeValidator.MIN_LOGO_SIZE:
            raise QRCodeValidationError(
                field_name,
                f"Tamanho mínimo do logo é {QRCodeValidator.MIN_LOGO_SIZE}px",
            )

        if size > QRCodeValidator.MAX_LOGO_SIZE:
            raise QRCodeValidationError(
                field_name,
                f"Tamanho máximo do logo é {QRCodeValidator.MAX_LOGO_SIZE}px",
            )

        return size

    @staticmethod
    def validate_description_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração de descrição"""
        if not isinstance(config, dict):
            raise QRCodeValidationError(
                "description_config", "Configuração deve ser um objeto"
            )

        mode = config.get("mode", "auto")
        if mode not in ["auto", "custom", "none"]:
            raise QRCodeValidationError(
                "description_config", 'Modo deve ser "auto", "custom" ou "none"'
            )

        if mode == "custom":
            custom_text = config.get("custom_text", "").strip()
            if not custom_text:
                raise QRCodeValidationError(
                    "description_config",
                    'Texto customizado é obrigatório quando modo é "custom"',
                )

            if len(custom_text) > 500:
                raise QRCodeValidationError(
                    "description_config",
                    "Texto customizado deve ter no máximo 500 caracteres",
                )

        return {"mode": mode, "custom_text": config.get("custom_text", "").strip()}

    @staticmethod
    def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida todos os dados da requisição"""
        if not isinstance(data, dict):
            raise QRCodeValidationError(
                "request", "Dados da requisição devem ser um objeto JSON válido"
            )

        # Validar campos obrigatórios
        validated_data = {
            "cr_number": QRCodeValidator.validate_cr_number(data.get("cr_number")),
            "service": QRCodeValidator.validate_service_name(data.get("service")),
            "locations": QRCodeValidator.validate_locations(data.get("locations", [])),
            "logo_size": QRCodeValidator.validate_logo_size(data.get("logo_size", 80)),
            "service_logo_size": QRCodeValidator.validate_logo_size(
                data.get("service_logo_size", 60), "service_logo_size"
            ),
            "description_config": QRCodeValidator.validate_description_config(
                data.get("description_config", {"mode": "auto"})
            ),
        }

        return validated_data

    @staticmethod
    def sanitize_qr_data(qr_data: str) -> str:
        """Sanitiza dados que vão no QR Code"""
        if not isinstance(qr_data, str):
            raise QRCodeValidationError("qr_data", "Dados do QR Code devem ser texto")

        # Remove caracteres de controle
        qr_data = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", qr_data)

        # Limita tamanho (QR Codes têm limite de capacidade)
        if len(qr_data) > 2000:
            raise QRCodeValidationError(
                "qr_data", "Dados do QR Code muito longos (máximo 2000 caracteres)"
            )

        return qr_data.strip()

    @staticmethod
    def validate_url(url: str, field_name: str = "url") -> str:
        """Valida URL"""
        if not url:
            raise QRCodeValidationError(field_name, "URL é obrigatória")

        url = url.strip()

        # Usar validador do Django
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise QRCodeValidationError(field_name, "URL inválida")

        # Verificar protocolos permitidos
        if not url.startswith(("http://", "https://")):
            raise QRCodeValidationError(
                field_name, "URL deve usar protocolo HTTP ou HTTPS"
            )

        return url
