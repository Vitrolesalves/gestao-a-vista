"""
Testes básicos para verificar se a configuração de testes está funcionando
"""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase


class TestBasicSetup(TestCase):
    """Testes básicos de configuração"""

    def test_django_settings(self):
        """Testa se as configurações do Django estão corretas"""
        self.assertTrue(settings.TESTING)
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3"
        )
        self.assertEqual(settings.DATABASES["default"]["NAME"], ":memory:")

    def test_user_model(self):
        """Testa se o modelo de usuário está funcionando"""
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_database_connection(self):
        """Testa se a conexão com o banco de dados está funcionando"""
        User = get_user_model()
        # Testa se conseguimos criar e consultar dados
        initial_count = User.objects.count()
        User.objects.create_user(username="dbtest", password="pass123")
        final_count = User.objects.count()
        self.assertEqual(final_count, initial_count + 1)


@pytest.mark.unit
def test_pytest_working():
    """Teste simples para verificar se o pytest está funcionando"""
    assert True


@pytest.mark.unit
def test_fixtures_working(user):
    """Testa se as fixtures estão funcionando"""
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.unit
def test_client_fixture(client):
    """Testa se o fixture do client está funcionando"""
    response = client.get("/")
    # Esperamos um redirect ou 404, não um erro 500
    assert response.status_code in [200, 302, 404]
