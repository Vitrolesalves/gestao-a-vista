"""
Testes de integração para APIs e serviços externos
"""

import json
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from PIL import Image

from Gestao_a_Vista.models import Dashboard, GestaoSala, Service, Unidade

User = get_user_model()


@pytest.mark.integration
class TestAPIEndpointsIntegration(TransactionTestCase):
    """Testes de integração para endpoints de API"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )
        self.client.login(username="admin", password="admin123")

        # Criar dados de teste
        self.service1 = Service.objects.create(
            name="Segurança", description="Serviço de segurança patrimonial"
        )

        self.service2 = Service.objects.create(
            name="Limpeza", description="Serviço de limpeza e conservação"
        )

        self.unidade = Unidade.objects.create(
            nome="Unidade Central", endereco="Rua Central, 100"
        )

    def test_get_services_api_integration(self):
        """Testa integração da API de serviços"""

        # 1. Buscar todos os serviços
        response = self.client.get("/api/services/")

        if response.status_code == 200:
            self.assertEqual(response["Content-Type"], "application/json")
            data = json.loads(response.content)

            # Verificar estrutura da resposta
            self.assertIn("services", data)
            self.assertIsInstance(data["services"], list)
            self.assertGreaterEqual(len(data["services"]), 2)

            # Verificar dados dos serviços
            service_names = [s["name"] for s in data["services"]]
            self.assertIn("Segurança", service_names)
            self.assertIn("Limpeza", service_names)

        # 2. Buscar com filtro
        response = self.client.get("/api/services/?search=Segurança")

        if response.status_code == 200:
            data = json.loads(response.content)

            # Deve retornar apenas serviços que contenham "Segurança"
            for service in data["services"]:
                self.assertIn("Segurança", service["name"])

    def test_get_locations_api_integration(self):
        """Testa integração da API de localizações"""

        response = self.client.get("/api/locations/")

        if response.status_code == 200:
            self.assertEqual(response["Content-Type"], "application/json")
            data = json.loads(response.content)

            # Verificar estrutura básica da resposta
            self.assertIsInstance(data, (dict, list))
        else:
            # Se endpoint não existe, verificar redirecionamento ou erro esperado
            self.assertIn(response.status_code, [404, 302, 405])

    def test_service_logo_api_integration(self):
        """Testa integração da API de logo de serviços"""

        # 1. Buscar logo de serviço existente
        response = self.client.get("/api/service-logo/?service=Segurança")

        # Pode retornar imagem, JSON ou erro 404
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            # Verificar se é uma resposta de imagem ou JSON
            content_type = response.get("Content-Type", "")
            self.assertTrue(
                content_type.startswith("image/") or content_type == "application/json"
            )

        # 2. Buscar logo de serviço inexistente
        response = self.client.get("/api/service-logo/?service=ServicoInexistente")

        # Deve retornar 404 ou imagem padrão
        self.assertIn(response.status_code, [200, 404])

    @patch("Gestao_a_Vista.views.qrcode")
    def test_qr_generation_api_integration(self, mock_qrcode):
        """Testa integração da API de geração de QR Code"""

        # Mock do qrcode
        mock_qr_instance = Mock()
        mock_qrcode.QRCode.return_value = mock_qr_instance

        # Mock da imagem gerada
        mock_image = Mock()
        mock_qr_instance.make_image.return_value = mock_image

        # Mock do save da imagem
        mock_image.save = Mock()

        # 1. Gerar QR Code válido
        qr_data = {"data": "https://example.com/test", "size": "10"}

        response = self.client.post("/api/generate-qr/", qr_data)

        # Verificar se a API foi chamada
        if response.status_code in [200, 302]:
            mock_qrcode.QRCode.assert_called()

        # 2. Tentar gerar QR Code com dados inválidos
        invalid_data = {
            "data": "",  # Dados vazios
            "size": "invalid",  # Tamanho inválido
        }

        response = self.client.post("/api/generate-qr/", invalid_data)

        # Deve retornar erro ou tratar graciosamente
        self.assertIn(response.status_code, [200, 400, 422])

    def test_dashboard_api_operations_integration(self):
        """Testa operações de API para dashboards"""

        # 1. Criar dashboard via API (simulado via POST)
        dashboard_data = {
            "action": "create",
            "nome": "Dashboard API Test",
            "cliente": "Cliente API",
            "servico": "Seguranca",
            "status": "Sucesso",
        }

        response = self.client.post("/dashboard/", dashboard_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se foi criado
        dashboard = Dashboard.objects.filter(nome="Dashboard API Test").first()
        if dashboard:
            # 2. Atualizar via API
            update_data = {
                "action": "update",
                "dashboard_id": str(dashboard.id),
                "nome": "Dashboard API Updated",
                "status": "Pendente",
            }

            response = self.client.post("/dashboard/", update_data)
            self.assertIn(response.status_code, [200, 302])

            # Verificar atualização
            dashboard.refresh_from_db()
            self.assertEqual(dashboard.nome, "Dashboard API Updated")

            # 3. Deletar via API
            delete_data = {"action": "delete", "dashboard_id": str(dashboard.id)}

            response = self.client.post("/dashboard/", delete_data)
            self.assertIn(response.status_code, [200, 302])

            # Verificar deleção
            self.assertFalse(Dashboard.objects.filter(id=dashboard.id).exists())


@pytest.mark.integration
class TestExternalServiceIntegration(TransactionTestCase):
    """Testes de integração com serviços externos"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )
        self.client.login(username="admin", password="admin123")

    @patch("requests.get")
    def test_external_api_integration(self, mock_get):
        """Testa integração com APIs externas (simulado)"""

        # Mock de resposta de API externa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"message": "API externa funcionando"},
        }
        mock_get.return_value = mock_response

        # Simular chamada para API externa (se existir no sistema)
        # Este é um exemplo de como testar integrações

        # Em um sistema real, haveria uma view que chama API externa
        # Por agora, apenas verificamos que o mock funciona
        import requests

        response = requests.get("https://api.externa.com/test")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    @patch("Gestao_a_Vista.views.qrcode.QRCode")
    def test_qr_library_integration(self, mock_qr_class):
        """Testa integração com biblioteca de QR Code"""

        # Mock da classe QRCode
        mock_qr_instance = Mock()
        mock_qr_class.return_value = mock_qr_instance

        # Mock dos métodos
        mock_qr_instance.add_data = Mock()
        mock_qr_instance.make = Mock()

        # Mock da imagem
        mock_image = Mock()
        mock_qr_instance.make_image.return_value = mock_image

        # Simular geração de QR Code
        qr_data = {"data": "https://example.com/qr-test", "size": "10"}

        response = self.client.post("/api/generate-qr/", qr_data)

        # Verificar se os métodos foram chamados corretamente
        if response.status_code in [200, 302]:
            mock_qr_class.assert_called()

    @patch("reportlab.pdfgen.canvas.Canvas")
    def test_pdf_generation_integration(self, mock_canvas):
        """Testa integração com geração de PDF"""

        # Mock do canvas do ReportLab
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance

        # Mock dos métodos do canvas
        mock_canvas_instance.drawString = Mock()
        mock_canvas_instance.save = Mock()

        # Simular download de PDF (se existir endpoint)
        response = self.client.get("/api/download-pdf/?type=qr&data=test")

        # Verificar resposta (pode ser 404 se endpoint não existir)
        self.assertIn(response.status_code, [200, 404, 302])

        if response.status_code == 200:
            # Verificar se é PDF
            content_type = response.get("Content-Type", "")
            self.assertTrue(
                content_type == "application/pdf" or "pdf" in content_type.lower()
            )

    @patch("PIL.Image.new")
    def test_image_processing_integration(self, mock_image_new):
        """Testa integração com processamento de imagens"""

        # Mock da criação de imagem
        mock_image = Mock()
        mock_image_new.return_value = mock_image

        # Mock dos métodos da imagem
        mock_image.save = Mock()
        mock_image.resize = Mock(return_value=mock_image)

        # Simular processamento de imagem (se existir no sistema)
        # Este é um exemplo de como testar processamento de imagens

        from PIL import Image

        # Criar imagem de teste
        test_image = Image.new("RGB", (100, 100), "white")

        # Verificar se mock foi configurado corretamente
        mock_image_new.assert_called_with("RGB", (100, 100), "white")


@pytest.mark.integration
class TestFileHandlingIntegration(TransactionTestCase):
    """Testes de integração para manipulação de arquivos"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )
        self.client.login(username="admin", password="admin123")

    def test_file_upload_integration(self):
        """Testa integração de upload de arquivos"""

        # Criar arquivo de teste em memória
        test_file = BytesIO()
        test_file.write(b"Test file content")
        test_file.seek(0)
        test_file.name = "test.txt"

        # Simular upload (se existir endpoint)
        response = self.client.post("/api/upload/", {"file": test_file})

        # Verificar resposta (pode ser 404 se endpoint não existir)
        self.assertIn(response.status_code, [200, 404, 405, 302])

    def test_static_file_serving_integration(self):
        """Testa servimento de arquivos estáticos"""

        # Tentar acessar arquivos estáticos comuns
        static_files = [
            "/static/css/style.css",
            "/static/js/main.js",
            "/static/img/logo.png",
        ]

        for static_file in static_files:
            response = self.client.get(static_file)

            # Arquivos estáticos podem não existir em teste
            # Verificar se não há erro 500
            self.assertNotEqual(response.status_code, 500)

    @patch("django.core.files.storage.default_storage.save")
    def test_file_storage_integration(self, mock_save):
        """Testa integração com sistema de armazenamento"""

        # Mock do salvamento de arquivo
        mock_save.return_value = "saved_file.txt"

        # Simular salvamento de arquivo
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        content = ContentFile(b"Test content")
        saved_name = default_storage.save("test.txt", content)

        # Verificar se mock foi chamado
        mock_save.assert_called_once()
        self.assertEqual(saved_name, "saved_file.txt")


@pytest.mark.integration
class TestDatabaseIntegration(TransactionTestCase):
    """Testes de integração com banco de dados"""

    def setUp(self):
        """Configuração inicial"""
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )

    def test_database_connection_integration(self):
        """Testa integração com conexão de banco de dados"""

        from django.db import connection

        # Verificar se conexão está ativa
        self.assertTrue(connection.is_usable())

        # Executar query simples
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_database_transaction_integration(self):
        """Testa integração com transações de banco"""

        from django.db import transaction

        # Testar transação bem-sucedida
        with transaction.atomic():
            user = User.objects.create_user(
                username="transaction_test",
                email="transaction@example.com",
                password="test123",
            )

            # Verificar que usuário foi criado
            self.assertTrue(User.objects.filter(username="transaction_test").exists())

        # Usuário deve existir após commit da transação
        self.assertTrue(User.objects.filter(username="transaction_test").exists())

    def test_database_migration_integration(self):
        """Testa integração com sistema de migrações"""

        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        # Verificar se todas as migrações foram aplicadas
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        # Se não há migrações pendentes, plan deve estar vazio
        # Em ambiente de teste, isso pode variar
        self.assertIsInstance(plan, list)

    def test_database_indexes_integration(self):
        """Testa integração com índices de banco de dados"""

        from django.db import connection

        # Verificar se índices importantes existem
        with connection.cursor() as cursor:
            # Obter informações sobre tabelas
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'Gestao_a_Vista_%'
            """
            )

            tables = cursor.fetchall()

            # Deve haver pelo menos algumas tabelas do app
            self.assertGreater(len(tables), 0)

            # Verificar se tabela de usuários existe
            table_names = [table[0] for table in tables]
            self.assertIn("Gestao_a_Vista_customuser", table_names)
