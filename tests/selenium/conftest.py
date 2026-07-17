"""
Configurações e fixtures específicas para testes Selenium

Este arquivo contém configurações compartilhadas para todos os testes Selenium,
incluindo fixtures para diferentes navegadores e utilitários de teste.
"""

import os
import tempfile

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


# Configurações de teste para Selenium
@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=["*"],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    MEDIA_ROOT=tempfile.mkdtemp(),
    STATIC_ROOT=tempfile.mkdtemp(),
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",  # Mais rápido para testes
    ],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class SeleniumTestCase(StaticLiveServerTestCase):
    """Classe base para testes Selenium com configurações otimizadas"""

    pass


@pytest.fixture(scope="session")
def selenium_config():
    """Configurações globais para Selenium"""
    return {
        "implicit_wait": 10,
        "page_load_timeout": 30,
        "script_timeout": 30,
        "window_size": (1920, 1080),
        "headless": not os.getenv("SELENIUM_DEBUG", False),
        "screenshot_dir": "tests/selenium/screenshots",
        "downloads_dir": "tests/selenium/downloads",
    }


@pytest.fixture(scope="session")
def chrome_options(selenium_config):
    """Configurações para Chrome WebDriver"""
    options = ChromeOptions()

    if selenium_config["headless"]:
        options.add_argument("--headless")

    # Configurações de performance e estabilidade
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")

    # Configurar tamanho da janela
    width, height = selenium_config["window_size"]
    options.add_argument(f"--window-size={width},{height}")

    # Configurar diretório de downloads
    downloads_dir = os.path.abspath(selenium_config["downloads_dir"])
    os.makedirs(downloads_dir, exist_ok=True)

    prefs = {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    # Configurações para CI/CD
    if os.getenv("CI"):
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")

    return options


@pytest.fixture(scope="session")
def firefox_options(selenium_config):
    """Configurações para Firefox WebDriver"""
    options = FirefoxOptions()

    if selenium_config["headless"]:
        options.add_argument("--headless")

    # Configurações de performance
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("media.volume_scale", "0.0")

    # Configurar downloads
    downloads_dir = os.path.abspath(selenium_config["downloads_dir"])
    os.makedirs(downloads_dir, exist_ok=True)

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", downloads_dir)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/pdf,application/octet-stream",
    )

    return options


@pytest.fixture(scope="session")
def edge_options(selenium_config):
    """Configurações para Edge WebDriver"""
    options = EdgeOptions()

    if selenium_config["headless"]:
        options.add_argument("--headless")

    # Configurações similares ao Chrome
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    width, height = selenium_config["window_size"]
    options.add_argument(f"--window-size={width},{height}")

    return options


@pytest.fixture(params=["chrome"])  # Pode adicionar 'firefox', 'edge'
def driver(request, selenium_config):
    """Fixture para WebDriver com suporte a múltiplos navegadores"""
    browser = request.param

    if browser == "chrome":
        service = ChromeService(ChromeDriverManager().install())
        options = chrome_options(selenium_config)
        driver = webdriver.Chrome(service=service, options=options)
    elif browser == "firefox":
        service = FirefoxService(GeckoDriverManager().install())
        options = firefox_options(selenium_config)
        driver = webdriver.Firefox(service=service, options=options)
    elif browser == "edge":
        service = EdgeService(EdgeChromiumDriverManager().install())
        options = edge_options(selenium_config)
        driver = webdriver.Edge(service=service, options=options)
    else:
        raise ValueError(f"Navegador não suportado: {browser}")

    # Configurar timeouts
    driver.implicitly_wait(selenium_config["implicit_wait"])
    driver.set_page_load_timeout(selenium_config["page_load_timeout"])
    driver.set_script_timeout(selenium_config["script_timeout"])

    # Maximizar janela
    driver.maximize_window()

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture
def chrome_driver(selenium_config, chrome_options):
    """Fixture específica para Chrome"""
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.implicitly_wait(selenium_config["implicit_wait"])
    driver.set_page_load_timeout(selenium_config["page_load_timeout"])
    driver.set_script_timeout(selenium_config["script_timeout"])
    driver.maximize_window()

    yield driver
    driver.quit()


@pytest.fixture
def firefox_driver(selenium_config, firefox_options):
    """Fixture específica para Firefox"""
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)

    driver.implicitly_wait(selenium_config["implicit_wait"])
    driver.set_page_load_timeout(selenium_config["page_load_timeout"])
    driver.set_script_timeout(selenium_config["script_timeout"])
    driver.maximize_window()

    yield driver
    driver.quit()


@pytest.fixture
def mobile_driver(selenium_config):
    """Fixture para testes mobile (Chrome com user agent mobile)"""
    options = ChromeOptions()

    if selenium_config["headless"]:
        options.add_argument("--headless")

    # Configurações mobile
    mobile_emulation = {
        "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 2.0},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)

    # Outras configurações
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(selenium_config["implicit_wait"])

    yield driver
    driver.quit()


@pytest.fixture
def screenshot_helper(selenium_config):
    """Helper para capturar screenshots"""
    screenshot_dir = selenium_config["screenshot_dir"]
    os.makedirs(screenshot_dir, exist_ok=True)

    def take_screenshot(driver, name, full_page=False):
        """Captura screenshot com nome personalizado"""
        filename = f"{screenshot_dir}/{name}_{driver.name}.png"

        if full_page:
            # Capturar página inteira
            original_size = driver.get_window_size()

            # Obter altura total da página
            total_height = driver.execute_script("return document.body.scrollHeight")

            # Redimensionar para capturar tudo
            driver.set_window_size(original_size["width"], total_height)

            # Capturar screenshot
            driver.save_screenshot(filename)

            # Restaurar tamanho original
            driver.set_window_size(original_size["width"], original_size["height"])
        else:
            driver.save_screenshot(filename)

        return filename

    return take_screenshot


@pytest.fixture
def wait_helper():
    """Helper para waits customizados"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    def wait_for_element(driver, selector, timeout=10, condition="presence"):
        """Aguarda elemento com diferentes condições"""
        wait = WebDriverWait(driver, timeout)

        if condition == "presence":
            return wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        elif condition == "visible":
            return wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
        elif condition == "clickable":
            return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        elif condition == "invisible":
            return wait.until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
            )
        else:
            raise ValueError(f"Condição não suportada: {condition}")

    def wait_for_url_change(driver, current_url, timeout=10):
        """Aguarda mudança de URL"""
        wait = WebDriverWait(driver, timeout)
        return wait.until(lambda d: d.current_url != current_url)

    def wait_for_text_in_element(driver, selector, text, timeout=10):
        """Aguarda texto aparecer em elemento"""
        wait = WebDriverWait(driver, timeout)
        return wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, selector), text)
        )

    return {
        "element": wait_for_element,
        "url_change": wait_for_url_change,
        "text": wait_for_text_in_element,
    }


@pytest.fixture
def test_data_helper():
    """Helper para criar dados de teste"""
    from django.contrib.auth import get_user_model

    from Gestao_a_Vista.models import Dashboard, Service, Unidade

    User = get_user_model()

    def create_test_users():
        """Cria usuários de teste"""
        users = {}

        users["admin"] = User.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="test123",
            role="administrador",
        )

        users["gerente"] = User.objects.create_user(
            username="gerente_test",
            email="gerente@test.com",
            password="test123",
            role="gerente",
        )

        users["publico"] = User.objects.create_user(
            username="publico_test",
            email="publico@test.com",
            password="test123",
            role="publico",
        )

        return users

    def create_test_data():
        """Cria dados de teste completos"""
        # Criar serviços
        services = []
        for name in ["Segurança", "Limpeza", "Manutenção"]:
            service, created = Service.objects.get_or_create(
                name=name, defaults={"description": f"Serviço de {name.lower()}"}
            )
            services.append(service)

        # Criar unidades
        unidades = []
        for i in range(3):
            unidade, created = Unidade.objects.get_or_create(
                nome=f"Unidade {i+1}", defaults={"endereco": f"Rua Teste {i+1}, 123"}
            )
            unidades.append(unidade)

        # Criar dashboards
        dashboards = []
        for i in range(5):
            dashboard, created = Dashboard.objects.get_or_create(
                nome=f"Dashboard {i+1}",
                defaults={
                    "cliente": f"Cliente {i+1}",
                    "servico": "Seguranca",
                    "status": "Sucesso" if i % 2 == 0 else "Pendente",
                },
            )
            dashboards.append(dashboard)

        return {"services": services, "unidades": unidades, "dashboards": dashboards}

    return {"users": create_test_users, "data": create_test_data}


@pytest.fixture
def performance_helper():
    """Helper para testes de performance"""
    import time

    def measure_page_load(driver, url):
        """Mede tempo de carregamento da página"""
        start_time = time.time()
        driver.get(url)

        # Aguardar página carregar completamente
        driver.execute_script("return document.readyState") == "complete"

        end_time = time.time()
        return end_time - start_time

    def measure_element_load(driver, selector, timeout=10):
        """Mede tempo até elemento aparecer"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        start_time = time.time()

        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

        end_time = time.time()
        return end_time - start_time

    def get_page_metrics(driver):
        """Obtém métricas de performance da página"""
        return driver.execute_script(
            """
            var performance = window.performance;
            var timing = performance.timing;
            
            return {
                'loadTime': timing.loadEventEnd - timing.navigationStart,
                'domReady': timing.domContentLoadedEventEnd - timing.navigationStart,
                'firstPaint': performance.getEntriesByType('paint')[0]?.startTime || 0,
                'resources': performance.getEntriesByType('resource').length
            };
        """
        )

    return {
        "page_load": measure_page_load,
        "element_load": measure_element_load,
        "metrics": get_page_metrics,
    }


# Configurações de marcadores pytest
def pytest_configure(config):
    """Configuração de marcadores pytest"""
    config.addinivalue_line("markers", "selenium: marca testes que usam Selenium")
    config.addinivalue_line("markers", "slow: marca testes lentos")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "ui: marca testes de interface")
    config.addinivalue_line("markers", "mobile: marca testes mobile")
    config.addinivalue_line("markers", "performance: marca testes de performance")


# Hook para capturar screenshots em falhas
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura screenshot quando teste falha"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        # Verificar se é teste Selenium
        if hasattr(item, "funcargs") and "driver" in item.funcargs:
            driver = item.funcargs["driver"]

            # Criar diretório de screenshots
            screenshot_dir = "tests/selenium/screenshots/failures"
            os.makedirs(screenshot_dir, exist_ok=True)

            # Capturar screenshot
            test_name = item.name.replace("/", "_").replace(":", "_")
            screenshot_path = f"{screenshot_dir}/FAILED_{test_name}.png"

            try:
                driver.save_screenshot(screenshot_path)
                print(f"\nScreenshot salvo: {screenshot_path}")
            except Exception as e:
                print(f"\nErro ao capturar screenshot: {e}")


# Configurações de timeout para diferentes tipos de teste
@pytest.fixture(autouse=True)
def configure_timeouts(request):
    """Configura timeouts baseado nos marcadores do teste"""
    if request.node.get_closest_marker("slow"):
        # Testes lentos têm timeout maior
        request.node.timeout = 300  # 5 minutos
    elif request.node.get_closest_marker("selenium"):
        # Testes Selenium têm timeout médio
        request.node.timeout = 120  # 2 minutos
    else:
        # Testes normais têm timeout padrão
        request.node.timeout = 60  # 1 minuto
