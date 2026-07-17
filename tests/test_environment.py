"""
Testes para verificar se o ambiente de testes está configurado corretamente
"""

import pytest
from django.conf import settings


@pytest.mark.unit
def test_pytest_working():
    """Teste simples para verificar se o pytest está funcionando"""
    assert True


@pytest.mark.unit
def test_django_settings():
    """Testa se as configurações do Django estão corretas"""
    assert settings.TESTING is True
    assert settings.DEBUG is False
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    # O pytest-django pode modificar o nome do banco para compartilhamento
    assert (
        ":memory:" in settings.DATABASES["default"]["NAME"]
        or settings.DATABASES["default"]["NAME"] == ":memory:"
    )


@pytest.mark.unit
def test_coverage_working():
    """Teste para verificar se o coverage está funcionando"""

    def dummy_function():
        return "coverage test"

    result = dummy_function()
    assert result == "coverage test"


@pytest.mark.unit
def test_client_fixture(client):
    """Testa se o fixture do client está funcionando"""
    # Teste simples que não acessa o banco de dados
    assert client is not None
    assert hasattr(client, "get")
    assert hasattr(client, "post")
