"""
Testes unitários para as views do sistema Gestão à Vista
"""

import json
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.test import Client, TestCase
from django.urls import reverse

from Gestao_a_Vista.models import Dashboard, MonitoramentoLog, Service, Unidade

User = get_user_model()


@pytest.mark.views
class TestLoginView(TestCase):
    """Testes para a view de login"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_login_view_get(self):
        """Testa acesso GET à página de login"""
        response = self.client.get("/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "login")

    def test_login_view_authenticated_redirect(self):
        """Testa redirecionamento quando usuário já está autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/login/")

        # Deve redirecionar para home
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_valid_credentials(self):
        """Testa login com credenciais válidas"""
        response = self.client.post(
            "/login/", {"username": "testuser", "password": "testpass123"}
        )

        # Deve redirecionar após login bem-sucedido
        self.assertEqual(response.status_code, 302)

        # Usuário deve estar autenticado
        user = User.objects.get(username="testuser")
        self.assertTrue(user.is_online)

    def test_login_view_post_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        response = self.client.post(
            "/login/", {"username": "testuser", "password": "wrongpassword"}
        )

        # Deve retornar à página de login
        self.assertEqual(response.status_code, 200)

        # Deve mostrar mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("inválidos" in str(m) for m in messages))

    def test_login_view_next_parameter(self):
        """Testa redirecionamento com parâmetro next"""
        response = self.client.post(
            "/login/?next=/dashboard/",
            {"username": "testuser", "password": "testpass123"},
        )

        # Deve redirecionar para a URL especificada em next
        self.assertEqual(response.status_code, 302)


@pytest.mark.views
class TestDashboardView(TestCase):
    """Testes para a view de dashboard"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="administrador",
        )
        self.client.login(username="testuser", password="testpass123")

    def test_dashboard_view_get_authenticated(self):
        """Testa acesso GET à página de dashboard autenticado"""
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dashboard")

    def test_dashboard_view_get_unauthenticated(self):
        """Testa acesso GET à página de dashboard sem autenticação"""
        self.client.logout()
        response = self.client.get("/dashboard/")

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_dashboard_create_post(self):
        """Testa criação de dashboard via POST"""
        dashboard_data = {
            "action": "create",
            "nome": "Dashboard Teste",
            "descricao": "Dashboard para testes",
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
            "url": "https://example.com",
            "powerbi_url": "https://app.powerbi.com/test",
        }

        response = self.client.post("/dashboard/", dashboard_data)

        # Deve criar o dashboard
        self.assertTrue(Dashboard.objects.filter(nome="Dashboard Teste").exists())

        # Deve retornar sucesso (200 ou redirect)
        self.assertIn(response.status_code, [200, 302])

    def test_dashboard_create_post_invalid_data(self):
        """Testa criação de dashboard com dados inválidos"""
        dashboard_data = {
            "action": "create",
            "nome": "",  # Nome obrigatório vazio
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
        }

        response = self.client.post("/dashboard/", dashboard_data)

        # Não deve criar o dashboard
        self.assertFalse(Dashboard.objects.filter(cliente="Cliente Teste").exists())

    def test_dashboard_update_post(self):
        """Testa atualização de dashboard via POST"""
        # Criar dashboard primeiro
        dashboard = Dashboard.objects.create(
            nome="Dashboard Original", cliente="Cliente Original", servico="Seguranca"
        )

        update_data = {
            "action": "update",
            "dashboard_id": str(dashboard.id),
            "nome": "Dashboard Atualizado",
            "cliente": "Cliente Atualizado",
            "servico": "Limpeza",
        }

        response = self.client.post("/dashboard/", update_data)

        # Verificar se foi atualizado
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.nome, "Dashboard Atualizado")
        self.assertEqual(dashboard.cliente, "Cliente Atualizado")

    def test_dashboard_delete_post(self):
        """Testa exclusão de dashboard via POST"""
        # Criar dashboard primeiro
        dashboard = Dashboard.objects.create(
            nome="Dashboard para Deletar", cliente="Cliente", servico="Seguranca"
        )

        delete_data = {"action": "delete", "dashboard_id": str(dashboard.id)}

        response = self.client.post("/dashboard/", delete_data)

        # Verificar se foi deletado
        self.assertFalse(Dashboard.objects.filter(id=dashboard.id).exists())


@pytest.mark.views
class TestHomeView(TestCase):
    """Testes para a view home"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_home_view_authenticated(self):
        """Testa acesso à home autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "home")

    def test_home_view_unauthenticated(self):
        """Testa acesso à home sem autenticação"""
        response = self.client.get("/")

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)

    def test_home_view_context_data(self):
        """Testa dados de contexto da home"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/")

        # Verificar se o usuário está no contexto
        self.assertEqual(response.context["user"], self.user)


@pytest.mark.views
class TestLogoutView(TestCase):
    """Testes para a view de logout"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_logout_view(self):
        """Testa logout do usuário"""
        # Fazer login primeiro
        self.client.login(username="testuser", password="testpass123")
        self.user.is_online = True
        self.user.save()

        # Fazer logout
        response = self.client.get("/logout/")

        # Deve redirecionar
        self.assertEqual(response.status_code, 302)

        # Usuário deve estar offline
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_online)


@pytest.mark.views
class TestGetServicesView(TestCase):
    """Testes para a view get_services (API)"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Criar alguns serviços de teste
        Service.objects.create(name="Segurança", description="Serviço de segurança")
        Service.objects.create(name="Limpeza", description="Serviço de limpeza")

    def test_get_services_authenticated(self):
        """Testa busca de serviços autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/get-services/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Verificar se retorna os serviços
        data = json.loads(response.content)
        self.assertIn("services", data)
        self.assertEqual(len(data["services"]), 2)

    def test_get_services_unauthenticated(self):
        """Testa busca de serviços sem autenticação"""
        response = self.client.get("/get-services/")

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)

    def test_get_services_with_search(self):
        """Testa busca de serviços com filtro"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/get-services/?search=Segurança")

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data["services"]), 1)
        self.assertEqual(data["services"][0]["name"], "Segurança")


@pytest.mark.views
class TestQRGeneratorView(TestCase):
    """Testes para a view de geração de QR Code"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="administrador",
        )

    def test_qr_generator_view_get(self):
        """Testa acesso GET à página de geração de QR"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/qr-generator/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "qr")

    def test_qr_generator_view_permission_required(self):
        """Testa que a view requer permissão adequada"""
        # Usuário sem permissão
        user_no_permission = User.objects.create_user(
            username="noperm",
            email="noperm@example.com",
            password="pass123",
            role="publico",
        )

        self.client.login(username="noperm", password="pass123")
        response = self.client.get("/qr-generator/")

        # Deve negar acesso ou redirecionar
        self.assertIn(response.status_code, [403, 302])

    @patch("Gestao_a_Vista.views.qrcode")
    def test_generate_qr_post(self, mock_qrcode):
        """Testa geração de QR Code via POST"""
        # Mock do qrcode
        mock_qr = Mock()
        mock_qrcode.QRCode.return_value = mock_qr

        self.client.login(username="testuser", password="testpass123")

        qr_data = {"data": "https://example.com", "size": "10"}

        response = self.client.post("/generate-qr/", qr_data)

        # Verificar se o qrcode foi chamado
        mock_qrcode.QRCode.assert_called_once()


@pytest.mark.views
class TestMonitoramentoView(TestCase):
    """Testes para a view de monitoramento"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="administrador",
        )

    def test_monitoramento_view_get(self):
        """Testa acesso GET à página de monitoramento"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/monitoramento/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "monitoramento")

    def test_monitoramento_view_with_logs(self):
        """Testa view de monitoramento com logs existentes"""
        # Criar alguns logs de teste
        MonitoramentoLog.objects.create(
            tipo="INFO", mensagem="Log de teste", detalhes="Detalhes do log"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/monitoramento/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log de teste")

    def test_monitoramento_view_permission_required(self):
        """Testa que monitoramento requer permissão"""
        # Usuário público não deve ter acesso
        user_public = User.objects.create_user(
            username="public",
            email="public@example.com",
            password="pass123",
            role="publico",
        )

        self.client.login(username="public", password="pass123")
        response = self.client.get("/monitoramento/")

        # Deve negar acesso
        self.assertIn(response.status_code, [403, 302])


@pytest.mark.views
class TestViewPermissions(TestCase):
    """Testes para permissões das views"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()

        # Criar usuários com diferentes roles
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role="administrador",
        )

        self.gerente = User.objects.create_user(
            username="gerente",
            email="gerente@example.com",
            password="pass123",
            role="gerente",
        )

        self.publico = User.objects.create_user(
            username="publico",
            email="publico@example.com",
            password="pass123",
            role="publico",
        )

    def test_admin_access_all_pages(self):
        """Testa que administrador tem acesso a todas as páginas"""
        self.client.login(username="admin", password="pass123")

        # Lista de URLs que admin deve ter acesso
        admin_urls = [
            "/dashboard/",
            "/monitoramento/",
            "/qr-generator/",
        ]

        for url in admin_urls:
            response = self.client.get(url)
            self.assertIn(
                response.status_code, [200, 302], f"Admin deveria ter acesso a {url}"
            )

    def test_public_limited_access(self):
        """Testa que usuário público tem acesso limitado"""
        self.client.login(username="publico", password="pass123")

        # URLs que público deve ter acesso
        public_allowed = ["/dashboard/"]

        # URLs que público NÃO deve ter acesso
        public_denied = ["/monitoramento/", "/qr-generator/"]

        for url in public_allowed:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"Público deveria ter acesso a {url}"
            )

        for url in public_denied:
            response = self.client.get(url)
            self.assertIn(
                response.status_code,
                [403, 302],
                f"Público NÃO deveria ter acesso a {url}",
            )

    def test_gerente_intermediate_access(self):
        """Testa que gerente tem acesso intermediário"""
        self.client.login(username="gerente", password="pass123")

        # Gerente deve ter mais acesso que público, menos que admin
        gerente_urls = ["/dashboard/", "/monitoramento/"]

        for url in gerente_urls:
            response = self.client.get(url)
            self.assertIn(
                response.status_code, [200, 302], f"Gerente deveria ter acesso a {url}"
            )
