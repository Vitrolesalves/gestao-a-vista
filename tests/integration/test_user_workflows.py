"""
Testes de integração para fluxos completos de usuário no sistema Gestão à Vista
"""

import json
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from Gestao_a_Vista.models import (Dashboard, GestaoSala, MonitoramentoLog,
                                   ReservaSala, Service, Unidade, UserActivity)

User = get_user_model()


@pytest.mark.integration
class TestCompleteUserJourney(TransactionTestCase):
    """Testes para jornada completa do usuário"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()

        # Criar usuários com diferentes roles
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )

        self.gerente = User.objects.create_user(
            username="gerente",
            email="gerente@example.com",
            password="gerente123",
            role="gerente",
        )

        self.publico = User.objects.create_user(
            username="publico",
            email="publico@example.com",
            password="publico123",
            role="publico",
        )

    def test_admin_complete_workflow(self):
        """Testa fluxo completo do administrador"""
        # 1. Login
        response = self.client.post(
            "/login/", {"username": "admin", "password": "admin123"}
        )
        self.assertEqual(response.status_code, 302)

        # Verificar se usuário está online
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_online)

        # 2. Acesso à home
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)

        # 3. Acesso ao dashboard
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

        # 4. Criar dashboard
        dashboard_data = {
            "action": "create",
            "nome": "Dashboard Integração",
            "descricao": "Dashboard para teste de integração",
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
            "status": "Sucesso",
        }

        response = self.client.post("/dashboard/", dashboard_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se dashboard foi criado
        self.assertTrue(Dashboard.objects.filter(nome="Dashboard Integração").exists())

        # 5. Acesso ao monitoramento
        response = self.client.get("/monitoramento/")
        self.assertEqual(response.status_code, 200)

        # 6. Acesso ao gerador de QR
        response = self.client.get("/qr-generator/")
        self.assertEqual(response.status_code, 200)

        # 7. Logout
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

        # Verificar se usuário está offline
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_online)

    def test_gerente_workflow_with_permissions(self):
        """Testa fluxo do gerente com verificação de permissões"""
        # 1. Login
        response = self.client.post(
            "/login/", {"username": "gerente", "password": "gerente123"}
        )
        self.assertEqual(response.status_code, 302)

        # 2. Acesso permitido - Dashboard
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

        # 3. Acesso permitido - Monitoramento
        response = self.client.get("/monitoramento/")
        self.assertEqual(response.status_code, 200)

        # 4. Acesso negado - Desativação CR (apenas admin)
        response = self.client.get("/desativacao-cr/")
        self.assertIn(response.status_code, [403, 302])

        # 5. Logout
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

    def test_public_user_limited_workflow(self):
        """Testa fluxo limitado do usuário público"""
        # 1. Login
        response = self.client.post(
            "/login/", {"username": "publico", "password": "publico123"}
        )
        self.assertEqual(response.status_code, 302)

        # 2. Acesso permitido - Dashboard
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

        # 3. Acesso permitido - Portaria Base
        response = self.client.get("/portaria-base/")
        self.assertEqual(response.status_code, 200)

        # 4. Acesso negado - Monitoramento
        response = self.client.get("/monitoramento/")
        self.assertIn(response.status_code, [403, 302])

        # 5. Acesso negado - QR Generator
        response = self.client.get("/qr-generator/")
        self.assertIn(response.status_code, [403, 302])

        # 6. Logout
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user_redirects(self):
        """Testa redirecionamentos para usuário não autenticado"""
        protected_urls = [
            "/home/",
            "/dashboard/",
            "/monitoramento/",
            "/qr-generator/",
            "/portaria-base/",
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login/", response.url)


@pytest.mark.integration
class TestDashboardCRUDWorkflow(TransactionTestCase):
    """Testes para fluxo completo de CRUD de dashboards"""

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

    def test_complete_dashboard_crud_workflow(self):
        """Testa fluxo completo de CRUD para dashboards"""

        # 1. CREATE - Criar dashboard
        create_data = {
            "action": "create",
            "nome": "Dashboard CRUD Test",
            "descricao": "Dashboard para teste de CRUD",
            "cliente": "Cliente CRUD",
            "servico": "Seguranca",
            "url": "https://example.com/dashboard",
            "powerbi_url": "https://app.powerbi.com/test",
            "status": "Sucesso",
        }

        response = self.client.post("/dashboard/", create_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se foi criado
        dashboard = Dashboard.objects.get(nome="Dashboard CRUD Test")
        self.assertEqual(dashboard.cliente, "Cliente CRUD")
        self.assertEqual(dashboard.status, "Sucesso")

        # 2. READ - Verificar se aparece na listagem
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard CRUD Test")

        # 3. UPDATE - Atualizar dashboard
        update_data = {
            "action": "update",
            "dashboard_id": str(dashboard.id),
            "nome": "Dashboard CRUD Updated",
            "descricao": "Dashboard atualizado",
            "cliente": "Cliente Atualizado",
            "servico": "Limpeza",
            "status": "Pendente",
        }

        response = self.client.post("/dashboard/", update_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se foi atualizado
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.nome, "Dashboard CRUD Updated")
        self.assertEqual(dashboard.cliente, "Cliente Atualizado")
        self.assertEqual(dashboard.servico, "Limpeza")
        self.assertEqual(dashboard.status, "Pendente")

        # 4. DELETE - Deletar dashboard
        delete_data = {"action": "delete", "dashboard_id": str(dashboard.id)}

        response = self.client.post("/dashboard/", delete_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se foi deletado
        self.assertFalse(Dashboard.objects.filter(id=dashboard.id).exists())


@pytest.mark.integration
class TestSalaManagementWorkflow(TransactionTestCase):
    """Testes para fluxo de gestão de salas"""

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

        # Criar unidade para testes
        self.unidade = Unidade.objects.create(
            nome="Unidade Teste", endereco="Rua Teste, 123"
        )

    def test_sala_management_workflow(self):
        """Testa fluxo completo de gestão de salas"""

        # 1. Acessar gestão de salas
        response = self.client.get("/gestao-salas/")
        self.assertEqual(response.status_code, 200)

        # 2. Criar nova sala
        response = self.client.get("/gestao-salas/criar/")
        self.assertEqual(response.status_code, 200)

        sala_data = {
            "nome": "Sala Teste",
            "capacidade": 20,
            "unidade": self.unidade.id,
            "disponivel": True,
        }

        response = self.client.post("/gestao-salas/criar/", sala_data)
        self.assertIn(response.status_code, [200, 302])

        # Verificar se sala foi criada
        sala = GestaoSala.objects.get(nome="Sala Teste")
        self.assertEqual(sala.capacidade, 20)
        self.assertTrue(sala.disponivel)

        # 3. Editar sala
        response = self.client.get(f"/gestao-salas/{sala.id_sala}/editar/")
        self.assertEqual(response.status_code, 200)

        update_data = {
            "nome": "Sala Teste Atualizada",
            "capacidade": 30,
            "unidade": self.unidade.id,
            "disponivel": False,
        }

        response = self.client.post(
            f"/gestao-salas/{sala.id_sala}/editar/", update_data
        )
        self.assertIn(response.status_code, [200, 302])

        # Verificar atualização
        sala.refresh_from_db()
        self.assertEqual(sala.nome, "Sala Teste Atualizada")
        self.assertEqual(sala.capacidade, 30)
        self.assertFalse(sala.disponivel)

        # 4. Deletar sala
        response = self.client.get(f"/gestao-salas/{sala.id_sala}/deletar/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/gestao-salas/{sala.id_sala}/deletar/")
        self.assertIn(response.status_code, [200, 302])

        # Verificar se foi deletada
        self.assertFalse(GestaoSala.objects.filter(id_sala=sala.id_sala).exists())


@pytest.mark.integration
class TestAPIIntegrationWorkflow(TransactionTestCase):
    """Testes para fluxos de integração com APIs"""

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
        Service.objects.create(name="Segurança", description="Serviço de segurança")
        Service.objects.create(name="Limpeza", description="Serviço de limpeza")

    def test_api_endpoints_workflow(self):
        """Testa fluxo de APIs do sistema"""

        # 1. API de localizações
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # 2. API de logo de serviço
        response = self.client.get("/api/service-logo/?service=Segurança")
        self.assertEqual(response.status_code, 200)

        # 3. API de geração de QR
        qr_data = {"data": "https://example.com/test", "size": "10"}

        response = self.client.post("/api/generate-qr/", qr_data)
        self.assertIn(response.status_code, [200, 302])

    @patch("Gestao_a_Vista.views.qrcode")
    def test_qr_generation_workflow(self, mock_qrcode):
        """Testa fluxo completo de geração de QR Code"""
        # Mock do qrcode
        mock_qr = Mock()
        mock_qrcode.QRCode.return_value = mock_qr
        mock_qr.make_image.return_value = Mock()

        # 1. Acessar página de geração de QR
        response = self.client.get("/qr-generator/")
        self.assertEqual(response.status_code, 200)

        # 2. Gerar QR Code
        qr_data = {
            "data": "https://example.com/qr-test",
            "size": "10",
            "service": "Segurança",
        }

        response = self.client.post("/api/generate-qr/", qr_data)

        # Verificar se o qrcode foi chamado
        mock_qrcode.QRCode.assert_called()


@pytest.mark.integration
class TestUserActivityTracking(TransactionTestCase):
    """Testes para rastreamento de atividades do usuário"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="test123",
            role="gerente",
        )

    def test_user_activity_tracking_workflow(self):
        """Testa rastreamento de atividades durante navegação"""

        # 1. Login - deve criar atividade
        response = self.client.post(
            "/login/", {"username": "testuser", "password": "test123"}
        )
        self.assertEqual(response.status_code, 302)

        # Verificar se usuário está online
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_online)

        # 2. Navegar por páginas
        pages = ["/home/", "/dashboard/", "/monitoramento/"]

        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)

        # 3. Logout - deve marcar como offline
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

        # Verificar se usuário está offline
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_online)


@pytest.mark.integration
class TestErrorHandlingWorkflow(TransactionTestCase):
    """Testes para tratamento de erros em fluxos"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="test123",
            role="publico",
        )
        self.client.login(username="testuser", password="test123")

    def test_permission_denied_workflow(self):
        """Testa fluxo quando usuário não tem permissão"""

        # Tentar acessar páginas restritas
        restricted_pages = [
            "/monitoramento/",
            "/qr-generator/",
            "/desativacao-cr/",
            "/controle-chips/",
        ]

        for page in restricted_pages:
            response = self.client.get(page)
            # Deve retornar 403 (Forbidden) ou 302 (Redirect)
            self.assertIn(response.status_code, [403, 302])

    def test_invalid_data_workflow(self):
        """Testa fluxo com dados inválidos"""

        # Tentar criar dashboard com dados inválidos
        invalid_data = {
            "action": "create",
            "nome": "",  # Nome vazio
            "cliente": "",  # Cliente vazio
            "servico": "InvalidService",  # Serviço inválido
        }

        response = self.client.post("/dashboard/", invalid_data)
        # Deve retornar erro ou permanecer na página
        self.assertIn(response.status_code, [200, 400])

    def test_nonexistent_resource_workflow(self):
        """Testa fluxo com recursos inexistentes"""

        # Tentar acessar dashboard inexistente
        response = self.client.post(
            "/dashboard/",
            {
                "action": "update",
                "dashboard_id": "00000000-0000-0000-0000-000000000000",
                "nome": "Test",
            },
        )

        # Deve tratar o erro graciosamente
        self.assertIn(response.status_code, [200, 404, 400])


@pytest.mark.integration
class TestSessionManagement(TransactionTestCase):
    """Testes para gerenciamento de sessão"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="sessionuser",
            email="session@example.com",
            password="session123",
            role="gerente",
        )

    def test_session_persistence_workflow(self):
        """Testa persistência de sessão durante navegação"""

        # 1. Login
        response = self.client.post(
            "/login/", {"username": "sessionuser", "password": "session123"}
        )
        self.assertEqual(response.status_code, 302)

        # 2. Navegar por múltiplas páginas mantendo sessão
        pages = ["/home/", "/dashboard/", "/portaria-base/"]

        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)
            # Verificar se usuário ainda está autenticado
            self.assertTrue(response.wsgi_request.user.is_authenticated)

        # 3. Verificar dados de sessão
        session = self.client.session
        self.assertIn("_auth_user_id", session)

    def test_session_timeout_workflow(self):
        """Testa comportamento com timeout de sessão"""

        # 1. Login
        response = self.client.post(
            "/login/", {"username": "sessionuser", "password": "session123"}
        )
        self.assertEqual(response.status_code, 302)

        # 2. Simular expiração de sessão
        self.client.session.flush()

        # 3. Tentar acessar página protegida
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
