"""
Testes unitários para os models do sistema Gestão à Vista
"""

import uuid
from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from Gestao_a_Vista.models import (Dashboard, GestaoSala, MonitoramentoLog,
                                   ReservaSala, Script, Service, Unidade,
                                   UserActivity, UserProfile)

User = get_user_model()


@pytest.mark.models
class TestCustomUser(TestCase):
    """Testes para o modelo CustomUser"""

    def setUp(self):
        """Configuração inicial para cada teste"""
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User",
            "role": "publico",
        }

    def test_create_user(self):
        """Testa criação básica de usuário"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.role, "publico")
        self.assertFalse(user.is_online)
        self.assertTrue(user.check_password("testpass123"))
        self.assertIsInstance(user.id, uuid.UUID)

    def test_create_superuser(self):
        """Testa criação de superusuário"""
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, "publico")  # valor padrão

    def test_user_str_representation(self):
        """Testa representação string do usuário"""
        # Com nome
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), "Test User")

        # Sem nome
        user_no_name = User.objects.create_user(
            username="noname", email="noname@example.com", password="pass123"
        )
        self.assertEqual(str(user_no_name), "noname")

    def test_role_choices(self):
        """Testa as opções de role disponíveis"""
        valid_roles = ["administrador", "gerente", "publico", "cliente"]

        for role in valid_roles:
            user = User.objects.create_user(
                username=f"user_{role}",
                email=f"{role}@example.com",
                password="pass123",
                role=role,
            )
            self.assertEqual(user.role, role)

    def test_page_permissions_default(self):
        """Testa permissões padrão de página"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.page_permissions, {})

    def test_has_page_permission_admin(self):
        """Testa permissões de página para administrador"""
        admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role="administrador",
        )

        # Administrador tem acesso a todas as páginas
        self.assertTrue(admin.has_page_permission("dashboard"))
        self.assertTrue(admin.has_page_permission("monitoramento"))
        self.assertTrue(admin.has_page_permission("any_page"))

    def test_has_page_permission_regular_user(self):
        """Testa permissões de página para usuário regular"""
        user = User.objects.create_user(**self.user_data)

        # Usuário sem permissões específicas
        self.assertFalse(user.has_page_permission("dashboard"))

        # Usuário com permissão específica
        user.page_permissions = {"dashboard": True}
        user.save()
        self.assertTrue(user.has_page_permission("dashboard"))
        self.assertFalse(user.has_page_permission("monitoramento"))

    def test_get_default_permissions_admin(self):
        """Testa permissões padrão para administrador"""
        admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass123",
            role="administrador",
        )

        permissions = admin.get_default_permissions()

        # Administrador deve ter todas as permissões
        for page, _ in User.PAGE_PERMISSIONS:
            self.assertTrue(permissions[page])

    def test_get_default_permissions_gerente(self):
        """Testa permissões padrão para gerente"""
        gerente = User.objects.create_user(
            username="gerente",
            email="gerente@example.com",
            password="pass123",
            role="gerente",
        )

        permissions = gerente.get_default_permissions()

        # Gerente deve ter acesso a maioria das páginas
        self.assertTrue(permissions["dashboard"])
        self.assertTrue(permissions["monitoramento"])
        self.assertFalse(permissions["desativacao_cr"])

    def test_get_default_permissions_publico(self):
        """Testa permissões padrão para público"""
        user = User.objects.create_user(**self.user_data)
        permissions = user.get_default_permissions()

        # Público tem acesso limitado
        self.assertTrue(permissions["dashboard"])
        self.assertTrue(permissions["portaria_base"])
        self.assertFalse(permissions["monitoramento"])
        self.assertFalse(permissions["qr_generator"])

    def test_get_default_permissions_cliente(self):
        """Testa permissões padrão para cliente"""
        cliente = User.objects.create_user(
            username="cliente",
            email="cliente@example.com",
            password="pass123",
            role="cliente",
        )

        permissions = cliente.get_default_permissions()

        # Cliente não deve ter acesso a nenhuma página
        for page, _ in User.PAGE_PERMISSIONS:
            self.assertFalse(permissions[page])

    def test_unique_username(self):
        """Testa unicidade do username"""
        User.objects.create_user(**self.user_data)

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="testuser",  # mesmo username
                email="other@example.com",
                password="pass123",
            )


@pytest.mark.models
class TestUserProfile(TestCase):
    """Testes para o modelo UserProfile"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_create_user_profile(self):
        """Testa criação de perfil de usuário"""
        profile = UserProfile.objects.create(
            user=self.user, phone="11999999999", address="Rua Teste, 123"
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone, "11999999999")
        self.assertEqual(profile.address, "Rua Teste, 123")
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_user_profile_str(self):
        """Testa representação string do perfil"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), "Perfil de testuser")

    def test_user_profile_one_to_one(self):
        """Testa relacionamento OneToOne"""
        profile = UserProfile.objects.create(user=self.user)

        # Acesso via related_name
        self.assertEqual(self.user.profile, profile)

        # Não pode criar outro perfil para o mesmo usuário
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)


@pytest.mark.models
class TestDashboard(TestCase):
    """Testes para o modelo Dashboard"""

    def setUp(self):
        """Configuração inicial"""
        self.dashboard_data = {
            "nome": "Dashboard Teste",
            "descricao": "Dashboard para testes",
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
            "url": "https://example.com",
            "powerbi_url": "https://app.powerbi.com/test",
            "status": "Sucesso",
        }

    def test_create_dashboard(self):
        """Testa criação de dashboard"""
        dashboard = Dashboard.objects.create(**self.dashboard_data)

        self.assertEqual(dashboard.nome, "Dashboard Teste")
        self.assertEqual(dashboard.cliente, "Cliente Teste")
        self.assertEqual(dashboard.status, "Sucesso")
        self.assertIsInstance(dashboard.id, uuid.UUID)
        self.assertIsNotNone(dashboard.created_at)

    def test_dashboard_str(self):
        """Testa representação string do dashboard"""
        dashboard = Dashboard.objects.create(**self.dashboard_data)
        expected = f"{dashboard.nome} - {dashboard.cliente}"
        self.assertEqual(str(dashboard), expected)

    def test_dashboard_status_choices(self):
        """Testa opções de status do dashboard"""
        valid_statuses = ["Sucesso", "Erro", "Pendente"]

        for status in valid_statuses:
            dashboard = Dashboard.objects.create(
                nome=f"Dashboard {status}",
                cliente="Cliente",
                servico="Servico",
                status=status,
            )
            self.assertEqual(dashboard.status, status)

    def test_dashboard_default_status(self):
        """Testa status padrão do dashboard"""
        dashboard = Dashboard.objects.create(
            nome="Dashboard Padrão", cliente="Cliente", servico="Servico"
        )
        self.assertEqual(dashboard.status, "Sucesso")

    def test_dashboard_url_fields(self):
        """Testa campos de URL do dashboard"""
        dashboard = Dashboard.objects.create(**self.dashboard_data)

        self.assertEqual(dashboard.url, "https://example.com")
        self.assertEqual(dashboard.powerbi_url, "https://app.powerbi.com/test")

    def test_dashboard_optional_fields(self):
        """Testa campos opcionais do dashboard"""
        # Criar dashboard apenas com campos obrigatórios
        dashboard = Dashboard.objects.create(
            nome="Dashboard Mínimo", cliente="Cliente", servico="Servico"
        )

        self.assertEqual(dashboard.descricao, "")
        self.assertEqual(dashboard.url, "")
        self.assertEqual(dashboard.powerbi_url, "")


@pytest.mark.models
class TestUserActivity(TestCase):
    """Testes para o modelo UserActivity"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_create_user_activity(self):
        """Testa criação de atividade do usuário"""
        activity = UserActivity.objects.create(
            user=self.user, action="login", details="Login realizado com sucesso"
        )

        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, "login")
        self.assertEqual(activity.details, "Login realizado com sucesso")
        self.assertIsNotNone(activity.timestamp)

    def test_user_activity_str(self):
        """Testa representação string da atividade"""
        activity = UserActivity.objects.create(user=self.user, action="logout")

        expected = f"{self.user.username} - logout"
        self.assertEqual(str(activity), expected)

    def test_user_activity_default_action(self):
        """Testa ação padrão da atividade"""
        activity = UserActivity.objects.create(user=self.user)
        self.assertEqual(activity.action, "login")

    def test_user_activity_ordering(self):
        """Testa ordenação das atividades por timestamp"""
        # Criar duas atividades
        activity1 = UserActivity.objects.create(user=self.user, action="login")
        activity2 = UserActivity.objects.create(user=self.user, action="logout")

        # A mais recente deve vir primeiro
        activities = UserActivity.objects.all()
        self.assertEqual(activities[0], activity2)
        self.assertEqual(activities[1], activity1)

    def test_user_activity_relationship(self):
        """Testa relacionamento com usuário"""
        activity = UserActivity.objects.create(user=self.user, action="page_view")

        # Acesso via related_name
        self.assertIn(activity, self.user.activities.all())


@pytest.mark.models
class TestService(TestCase):
    """Testes para o modelo Service"""

    def test_create_service(self):
        """Testa criação de serviço"""
        service = Service.objects.create(
            name="Segurança Patrimonial", description="Serviço de segurança"
        )

        self.assertEqual(service.name, "Segurança Patrimonial")
        self.assertEqual(service.description, "Serviço de segurança")

    def test_service_str(self):
        """Testa representação string do serviço"""
        service = Service.objects.create(name="Limpeza")
        self.assertEqual(str(service), "Limpeza")


@pytest.mark.models
class TestUnidade(TestCase):
    """Testes para o modelo Unidade"""

    def test_create_unidade(self):
        """Testa criação de unidade"""
        unidade = Unidade.objects.create(
            nome="Unidade Teste", endereco="Rua Teste, 123", telefone="11999999999"
        )

        self.assertEqual(unidade.nome, "Unidade Teste")
        self.assertEqual(unidade.endereco, "Rua Teste, 123")
        self.assertEqual(unidade.telefone, "11999999999")

    def test_unidade_str(self):
        """Testa representação string da unidade"""
        unidade = Unidade.objects.create(nome="Centro")
        self.assertEqual(str(unidade), "Centro")

    def test_unidade_optional_fields(self):
        """Testa campos opcionais da unidade"""
        unidade = Unidade.objects.create(nome="Mínima")

        self.assertEqual(unidade.endereco, "")
        self.assertEqual(unidade.telefone, "")
        self.assertEqual(unidade.email, "")
        self.assertEqual(unidade.observacoes, "")
