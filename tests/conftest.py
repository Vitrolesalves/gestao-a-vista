"""
Configurações e fixtures compartilhadas para todos os testes
"""

import os
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Removido: fixture django_db_setup personalizada
# O pytest-django gerencia automaticamente a configuração do banco


@pytest.fixture
def client():
    """Cliente de teste Django"""
    return Client()


@pytest.fixture
def user_data():
    """Dados básicos para criação de usuário"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def create_user(db, user_data):
    """Fixture para criar um usuário de teste"""

    def _create_user(**kwargs):
        User = get_user_model()
        data = user_data.copy()
        data.update(kwargs)
        return User.objects.create_user(**data)

    return _create_user


@pytest.fixture
def user(create_user):
    """Usuário padrão para testes"""
    return create_user()


@pytest.fixture
def admin_user(db):
    """Usuário administrador para testes"""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def authenticated_client(client, user):
    """Cliente autenticado com usuário padrão"""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Cliente autenticado com usuário administrador"""
    client.force_login(admin_user)
    return client


@pytest.fixture(scope="session")
def chrome_options():
    """Opções do Chrome para testes Selenium"""
    if not SELENIUM_AVAILABLE:
        pytest.skip("selenium not installed")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options


@pytest.fixture(scope="session")
def chrome_driver(chrome_options):
    """Driver do Chrome para testes Selenium"""
    if not SELENIUM_AVAILABLE:
        pytest.skip("selenium not installed")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    yield driver
    driver.quit()


@pytest.fixture
def live_server_url():
    """URL do servidor de teste para Selenium"""
    return "http://localhost:8081"


@pytest.fixture
def temp_media_root():
    """Diretório temporário para arquivos de mídia nos testes"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup é feito automaticamente pelo sistema
