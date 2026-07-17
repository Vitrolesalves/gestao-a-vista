"""
Testes para o módulo de geração de QR Codes refatorado
"""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from Gestao_a_Vista.models import Estrutura
from Gestao_a_Vista.qr_code_service import (QRCodeService,
                                            generate_qr_code_improved)
from Gestao_a_Vista.qr_exceptions import (QRCodeDatabaseError,
                                          QRCodeGenerationError,
                                          QRCodeValidationError)
from Gestao_a_Vista.qr_validators import QRCodeValidator

User = get_user_model()


@pytest.mark.django_db
class TestQRCodeValidator:
    """Testes para o validador de QR Codes"""

    def test_validate_cr_number_success(self):
        """Teste validação de CR number válido"""
        validator = QRCodeValidator()
        result = validator.validate_cr_number("CR-12345")
        assert result == "CR-12345"

    def test_validate_cr_number_empty(self):
        """Teste validação de CR number vazio"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_cr_number("")
        assert exc_info.value.field == "cr_number"
        assert "obrigatório" in exc_info.value.message

    def test_validate_cr_number_invalid_chars(self):
        """Teste validação de CR number com caracteres inválidos"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_cr_number("CR@123!")
        assert exc_info.value.field == "cr_number"
        assert "apenas letras" in exc_info.value.message

    def test_validate_service_name_success(self):
        """Teste validação de nome de serviço válido"""
        validator = QRCodeValidator()
        result = validator.validate_service_name("Vigilância")
        assert result == "Vigilância"

    def test_validate_service_name_dangerous_chars(self):
        """Teste validação de nome de serviço com caracteres perigosos"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_service_name("Service<script>")
        assert exc_info.value.field == "service"
        assert "caractere não permitido" in exc_info.value.message

    def test_validate_locations_success(self):
        """Teste validação de locais válidos"""
        validator = QRCodeValidator()
        locations = [
            {"id": 1, "displayName": "Local 1"},
            {"id": 2, "displayName": "Local 2"},
        ]
        result = validator.validate_locations(locations)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["displayName"] == "Local 1"

    def test_validate_locations_empty(self):
        """Teste validação de lista de locais vazia"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_locations([])
        assert exc_info.value.field == "locations"
        assert "pelo menos um local" in exc_info.value.message

    def test_validate_locations_invalid_id(self):
        """Teste validação de local com ID inválido"""
        validator = QRCodeValidator()
        locations = [{"id": "invalid", "displayName": "Local 1"}]
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_locations(locations)
        assert exc_info.value.field == "locations"
        assert "número válido" in exc_info.value.message

    def test_validate_logo_size_success(self):
        """Teste validação de tamanho de logo válido"""
        validator = QRCodeValidator()
        result = validator.validate_logo_size(80)
        assert result == 80

    def test_validate_logo_size_too_small(self):
        """Teste validação de tamanho de logo muito pequeno"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_logo_size(10)
        assert "Tamanho mínimo" in exc_info.value.message

    def test_validate_logo_size_too_large(self):
        """Teste validação de tamanho de logo muito grande"""
        validator = QRCodeValidator()
        with pytest.raises(QRCodeValidationError) as exc_info:
            validator.validate_logo_size(300)
        assert "Tamanho máximo" in exc_info.value.message

    def test_sanitize_qr_data_success(self):
        """Teste sanitização de dados do QR Code"""
        validator = QRCodeValidator()
        result = validator.sanitize_qr_data("CR: 12345 | Local: Test")
        assert result == "CR: 12345 | Local: Test"

    def test_sanitize_qr_data_control_chars(self):
        """Teste sanitização removendo caracteres de controle"""
        validator = QRCodeValidator()
        result = validator.sanitize_qr_data("CR: 12345\x00\x1f | Local: Test")
        assert result == "CR: 12345 | Local: Test"


@pytest.mark.django_db
class TestQRCodeService:
    """Testes para o serviço de QR Codes"""

    def setup_method(self):
        """Setup para cada teste"""
        self.service = QRCodeService()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Criar estrutura de teste
        self.estrutura = Estrutura.objects.create(
            id=1, descricao="Local Teste", nivel=1, qrcode="https://example.com/qr/1"
        )

    def test_validate_request_data_success(self):
        """Teste validação de dados de requisição válidos"""
        data = {
            "cr_number": "CR-12345",
            "service": "Vigilância",
            "locations": [{"id": 1, "displayName": "Local 1"}],
            "logo_size": 80,
            "service_logo_size": 60,
            "description_config": {"mode": "auto"},
        }

        result = self.service._validate_request_data(data)
        assert result["cr_number"] == "CR-12345"
        assert result["service"] == "Vigilância"
        assert len(result["locations"]) == 1

    def test_validate_request_data_invalid(self):
        """Teste validação de dados de requisição inválidos"""
        data = {
            "cr_number": "",  # Inválido
            "service": "Vigilância",
            "locations": [{"id": 1, "displayName": "Local 1"}],
        }

        with pytest.raises(QRCodeValidationError):
            self.service._validate_request_data(data)

    def test_fetch_estruturas_success(self):
        """Teste busca de estruturas com sucesso"""
        locations = [{"id": 1, "displayName": "Local Teste"}]

        result = self.service._fetch_estruturas(locations)

        assert 1 in result
        assert result[1] == self.estrutura

    def test_fetch_estruturas_not_found(self):
        """Teste busca de estruturas não encontradas"""
        locations = [{"id": 999, "displayName": "Local Inexistente"}]

        result = self.service._fetch_estruturas(locations)

        assert 999 in result
        assert result[999] is None

    @patch("Gestao_a_Vista.qr_code_service.qrcode.QRCode")
    def test_create_qr_image_success(self, mock_qr_class):
        """Teste criação de imagem QR com sucesso"""
        # Mock do QR Code
        mock_qr = Mock()
        mock_qr_class.return_value = mock_qr

        mock_image = Mock()
        mock_qr.make_image.return_value = mock_image

        result = self.service._create_qr_image("Test content")

        assert result == mock_image
        mock_qr.add_data.assert_called_once_with("Test content")
        mock_qr.make.assert_called_once_with(fit=True)

    def test_build_qr_content_with_estrutura(self):
        """Teste construção de conteúdo QR com estrutura existente"""
        location = {"id": 1, "displayName": "Local Teste"}
        validated_data = {"cr_number": "CR-12345", "service": "Vigilância"}

        result = self.service._build_qr_content(
            location, validated_data, self.estrutura
        )

        assert result == "https://example.com/qr/1"

    def test_build_qr_content_without_estrutura(self):
        """Teste construção de conteúdo QR sem estrutura"""
        location = {"id": 999, "displayName": "Local Novo"}
        validated_data = {"cr_number": "CR-12345", "service": "Vigilância"}

        result = self.service._build_qr_content(location, validated_data, None)

        expected = "CR: CR-12345 | Serviço: Vigilância | Local: Local Novo"
        assert result == expected

    @patch("Gestao_a_Vista.qr_code_service.Image")
    def test_image_to_base64_success(self, mock_image_class):
        """Teste conversão de imagem para base64"""
        # Mock da imagem
        mock_image = Mock()
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b"fake_image_data"

        with patch("Gestao_a_Vista.qr_code_service.BytesIO", return_value=mock_buffer):
            with patch("base64.b64encode", return_value=b"ZmFrZV9pbWFnZV9kYXRh"):
                result = self.service._image_to_base64(mock_image)

                assert result == "ZmFrZV9pbWFnZV9kYXRh"
                mock_image.save.assert_called_once()


@pytest.mark.django_db
class TestQRCodeEndpoint:
    """Testes para o endpoint de geração de QR Codes"""

    def setup_method(self):
        """Setup para cada teste"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_generate_qr_code_improved_success(self):
        """Teste endpoint com dados válidos"""
        data = {
            "cr_number": "CR-12345",
            "service": "Vigilância",
            "locations": [{"id": 1, "displayName": "Local 1"}],
            "logo_size": 80,
            "service_logo_size": 60,
        }

        request = self.factory.post(
            "/api/generate-qr-v2/",
            data=json.dumps(data),
            content_type="application/json",
        )
        request.user = self.user

        with patch(
            "Gestao_a_Vista.qr_code_service.qr_service.generate_qr_codes"
        ) as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "qr_codes": [{"location_id": 1, "image": "base64data"}],
                "generation_time": 0.5,
                "total_codes": 1,
            }

            response = generate_qr_code_improved(request)

            assert response.status_code == 200
            response_data = json.loads(response.content)
            assert response_data["success"] is True
            assert len(response_data["qr_codes"]) == 1

    def test_generate_qr_code_improved_validation_error(self):
        """Teste endpoint com dados inválidos"""
        data = {
            "cr_number": "",  # Inválido
            "service": "Vigilância",
            "locations": [{"id": 1, "displayName": "Local 1"}],
        }

        request = self.factory.post(
            "/api/generate-qr-v2/",
            data=json.dumps(data),
            content_type="application/json",
        )
        request.user = self.user

        response = generate_qr_code_improved(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error_type"] == "validation_error"

    def test_generate_qr_code_improved_invalid_json(self):
        """Teste endpoint com JSON inválido"""
        request = self.factory.post(
            "/api/generate-qr-v2/", data="invalid json", content_type="application/json"
        )
        request.user = self.user

        response = generate_qr_code_improved(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error_type"] == "invalid_json"

    def test_generate_qr_code_improved_method_not_allowed(self):
        """Teste endpoint com método não permitido"""
        request = self.factory.get("/api/generate-qr-v2/")
        request.user = self.user

        response = generate_qr_code_improved(request)

        assert response.status_code == 405
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error_type"] == "method_not_allowed"


class TestQRCodeExceptions:
    """Testes para as exceções customizadas"""

    def test_qr_code_validation_error(self):
        """Teste exceção de validação"""
        error = QRCodeValidationError("test_field", "Test message")
        assert error.field == "test_field"
        assert error.message == "Test message"
        assert str(error) == "Erro de validação no campo 'test_field': Test message"

    def test_qr_code_generation_error(self):
        """Teste exceção de geração"""
        original_error = ValueError("Original error")
        error = QRCodeGenerationError("Test message", original_error)
        assert error.original_error == original_error
        assert str(error) == "Erro na geração do QR Code: Test message"

    def test_qr_code_database_error(self):
        """Teste exceção de banco de dados"""
        error = QRCodeDatabaseError("Database error", "SELECT * FROM test")
        assert error.query == "SELECT * FROM test"
        assert str(error) == "Erro de banco de dados: Database error"
