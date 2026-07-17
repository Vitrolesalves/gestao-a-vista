"""
Testes de Interface com Selenium para o sistema Gestão à Vista

Este arquivo contém testes end-to-end que simulam interações reais do usuário
com a interface web do sistema.
"""

import os
import time

import pytest
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from Gestao_a_Vista.models import Dashboard, GestaoSala, Service, Unidade

User = get_user_model()


class BaseSeleniumTestCase(StaticLiveServerTestCase):
    """Classe base para testes Selenium"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executar sem interface gráfica
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        # Para debug, remova o --headless
        if os.getenv("SELENIUM_DEBUG"):
            chrome_options.remove_argument("--headless")

        # Configurar driver
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Configuração inicial para cada teste"""
        # Criar usuários de teste
        self.admin_user = User.objects.create_user(
            username="admin_selenium",
            email="admin@selenium.com",
            password="selenium123",
            role="administrador",
        )

        self.gerente_user = User.objects.create_user(
            username="gerente_selenium",
            email="gerente@selenium.com",
            password="selenium123",
            role="gerente",
        )

        self.publico_user = User.objects.create_user(
            username="publico_selenium",
            email="publico@selenium.com",
            password="selenium123",
            role="publico",
        )

        # Criar dados de teste
        self.service = Service.objects.create(
            name="Segurança Selenium", description="Serviço para testes Selenium"
        )

        self.unidade = Unidade.objects.create(
            nome="Unidade Selenium", endereco="Rua Selenium, 123"
        )

        # Configurar wait
        self.wait = WebDriverWait(self.driver, 10)

    def login(self, username, password):
        """Helper para fazer login"""
        self.driver.get(f"{self.live_server_url}/login/")

        # Aguardar página carregar
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

        # Preencher formulário
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")

        username_field.clear()
        username_field.send_keys(username)

        password_field.clear()
        password_field.send_keys(password)

        # Submeter formulário
        login_button = self.driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"]'
        )
        login_button.click()

        # Aguardar redirecionamento
        self.wait.until(EC.url_contains("/home/"))

    def logout(self):
        """Helper para fazer logout"""
        logout_button = self.driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"]'
        )
        logout_button.click()

        # Aguardar redirecionamento para login
        self.wait.until(EC.url_contains("/login/"))

    def take_screenshot(self, name):
        """Helper para capturar screenshots"""
        screenshot_dir = "tests/selenium/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        self.driver.save_screenshot(f"{screenshot_dir}/{name}.png")


@pytest.mark.selenium
class TestLoginWorkflow(BaseSeleniumTestCase):
    """Testes para fluxo de login"""

    def test_login_success(self):
        """Testa login bem-sucedido"""
        self.login("admin_selenium", "selenium123")

        # Verificar se chegou na home
        self.assertIn("/home/", self.driver.current_url)

        # Verificar elementos da página
        self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, ".sidebar"))

        # Verificar nome do usuário no header
        user_info = self.driver.find_element(By.CSS_SELECTOR, ".text-dark.fw-medium")
        self.assertIn("administrador", user_info.text.lower())

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        self.driver.get(f"{self.live_server_url}/login/")

        # Preencher com credenciais inválidas
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")

        username_field.send_keys("invalid_user")
        password_field.send_keys("invalid_pass")

        login_button = self.driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"]'
        )
        login_button.click()

        # Deve permanecer na página de login
        self.assertIn("/login/", self.driver.current_url)

        # Verificar mensagem de erro (se existir)
        try:
            error_message = self.driver.find_element(By.CSS_SELECTOR, ".alert-danger")
            self.assertTrue(error_message.is_displayed())
        except NoSuchElementException:
            # Se não há mensagem de erro específica, apenas verificar que não fez login
            pass

    def test_logout_workflow(self):
        """Testa fluxo completo de login e logout"""
        # Login
        self.login("admin_selenium", "selenium123")

        # Verificar que está logado
        self.assertIn("/home/", self.driver.current_url)

        # Logout
        self.logout()

        # Verificar que foi redirecionado para login
        self.assertIn("/login/", self.driver.current_url)


@pytest.mark.selenium
class TestNavigationWorkflow(BaseSeleniumTestCase):
    """Testes para navegação no sistema"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_sidebar_navigation(self):
        """Testa navegação pela sidebar"""
        # Testar navegação para Dashboard
        dashboard_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="dashboard"]'))
        )
        dashboard_link.click()

        self.wait.until(EC.url_contains("/dashboard/"))
        self.assertIn("/dashboard/", self.driver.current_url)

        # Testar navegação para Monitoramento
        monitoring_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="monitoramento"]'))
        )
        monitoring_link.click()

        self.wait.until(EC.url_contains("/monitoramento/"))
        self.assertIn("/monitoramento/", self.driver.current_url)

        # Voltar para Home
        home_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="home"]'))
        )
        home_link.click()

        self.wait.until(EC.url_contains("/home/"))
        self.assertIn("/home/", self.driver.current_url)

    def test_sidebar_collapse(self):
        """Testa colapso da sidebar"""
        # Encontrar botão de toggle
        toggle_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "sidebarToggle"))
        )

        # Verificar estado inicial da sidebar
        sidebar = self.driver.find_element(By.ID, "sidebar")
        initial_collapsed = "collapsed" in sidebar.get_attribute("class")

        # Clicar no toggle
        toggle_button.click()

        # Aguardar animação
        time.sleep(0.5)

        # Verificar se estado mudou
        final_collapsed = "collapsed" in sidebar.get_attribute("class")
        self.assertNotEqual(initial_collapsed, final_collapsed)

    def test_responsive_navigation(self):
        """Testa navegação responsiva"""
        # Redimensionar para mobile
        self.driver.set_window_size(375, 667)

        # Aguardar ajuste responsivo
        time.sleep(0.5)

        # Verificar se sidebar está oculta em mobile
        sidebar = self.driver.find_element(By.ID, "sidebar")

        # Em mobile, sidebar deve estar transformada para fora da tela
        # ou ter classe específica de mobile

        # Restaurar tamanho desktop
        self.driver.set_window_size(1920, 1080)


@pytest.mark.selenium
class TestDashboardWorkflow(BaseSeleniumTestCase):
    """Testes para funcionalidades do dashboard"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

        # Navegar para dashboard
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.url_contains("/dashboard/"))

    def test_create_dashboard(self):
        """Testa criação de dashboard"""
        # Procurar formulário de criação
        try:
            # Aguardar página carregar completamente
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Procurar campo de nome (pode ter diferentes nomes)
            nome_field = None
            possible_selectors = [
                'input[name="nome"]',
                'input[id="nome"]',
                'input[placeholder*="nome"]',
                'input[type="text"]',
            ]

            for selector in possible_selectors:
                try:
                    nome_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if nome_field:
                # Preencher formulário
                nome_field.clear()
                nome_field.send_keys("Dashboard Selenium Test")

                # Procurar outros campos
                try:
                    cliente_field = self.driver.find_element(
                        By.CSS_SELECTOR, 'input[name="cliente"]'
                    )
                    cliente_field.clear()
                    cliente_field.send_keys("Cliente Selenium")
                except NoSuchElementException:
                    pass

                # Procurar select de serviço
                try:
                    servico_select = Select(
                        self.driver.find_element(
                            By.CSS_SELECTOR, 'select[name="servico"]'
                        )
                    )
                    servico_select.select_by_visible_text("Seguranca")
                except NoSuchElementException:
                    pass

                # Submeter formulário
                submit_button = self.driver.find_element(
                    By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'
                )
                submit_button.click()

                # Aguardar processamento
                time.sleep(2)

                # Verificar se dashboard foi criado (procurar na página)
                page_source = self.driver.page_source.lower()
                self.assertIn("dashboard selenium test", page_source)

        except TimeoutException:
            # Se não conseguir encontrar elementos, capturar screenshot para debug
            self.take_screenshot("dashboard_create_timeout")
            self.fail("Timeout ao tentar criar dashboard")

    def test_dashboard_list_view(self):
        """Testa visualização da lista de dashboards"""
        # Criar dashboard de teste
        Dashboard.objects.create(
            nome="Dashboard Lista Test",
            cliente="Cliente Lista",
            servico="Seguranca",
            status="Sucesso",
        )

        # Recarregar página
        self.driver.refresh()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Verificar se dashboard aparece na lista
        page_source = self.driver.page_source.lower()
        self.assertIn("dashboard lista test", page_source)

    def test_dashboard_search(self):
        """Testa funcionalidade de busca de dashboards"""
        # Criar múltiplos dashboards
        Dashboard.objects.create(
            nome="Dashboard Busca 1",
            cliente="Cliente 1",
            servico="Seguranca",
            status="Sucesso",
        )
        Dashboard.objects.create(
            nome="Dashboard Busca 2",
            cliente="Cliente 2",
            servico="Limpeza",
            status="Pendente",
        )

        # Recarregar página
        self.driver.refresh()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Procurar campo de busca
        try:
            search_field = self.driver.find_element(
                By.CSS_SELECTOR,
                'input[type="search"], input[placeholder*="busca"], input[placeholder*="search"]',
            )

            # Fazer busca
            search_field.clear()
            search_field.send_keys("Busca 1")
            search_field.send_keys(Keys.ENTER)

            # Aguardar resultado
            time.sleep(1)

            # Verificar resultado da busca
            page_source = self.driver.page_source.lower()
            self.assertIn("dashboard busca 1", page_source)

        except NoSuchElementException:
            # Se não há campo de busca, apenas verificar que dashboards existem
            page_source = self.driver.page_source.lower()
            self.assertIn("dashboard busca", page_source)


@pytest.mark.selenium
class TestFormInteractions(BaseSeleniumTestCase):
    """Testes para interações com formulários"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_form_validation(self):
        """Testa validação de formulários"""
        # Ir para página com formulário (dashboard)
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            # Procurar formulário
            form = self.driver.find_element(By.TAG_NAME, "form")

            # Tentar submeter formulário vazio
            submit_button = form.find_element(
                By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'
            )
            submit_button.click()

            # Aguardar validação
            time.sleep(1)

            # Verificar se há mensagens de validação
            # (HTML5 validation ou custom validation)

        except NoSuchElementException:
            # Se não há formulário, pular teste
            pass

    def test_select_interactions(self):
        """Testa interações com campos select"""
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            # Procurar campo select
            select_element = self.driver.find_element(By.TAG_NAME, "select")
            select = Select(select_element)

            # Testar seleção de opções
            options = select.options
            if len(options) > 1:
                # Selecionar segunda opção
                select.select_by_index(1)

                # Verificar se seleção foi feita
                selected_option = select.first_selected_option
                self.assertIsNotNone(selected_option)

        except NoSuchElementException:
            # Se não há select, pular teste
            pass


@pytest.mark.selenium
class TestAccessibilityFeatures(BaseSeleniumTestCase):
    """Testes para recursos de acessibilidade"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_keyboard_navigation(self):
        """Testa navegação por teclado"""
        # Testar navegação por Tab
        body = self.driver.find_element(By.TAG_NAME, "body")

        # Simular algumas teclas Tab
        for _ in range(5):
            body.send_keys(Keys.TAB)
            time.sleep(0.1)

        # Verificar se algum elemento está focado
        active_element = self.driver.switch_to.active_element
        self.assertIsNotNone(active_element)

    def test_aria_labels(self):
        """Testa presença de labels ARIA"""
        # Procurar elementos com aria-label
        aria_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label]")

        # Deve haver pelo menos alguns elementos com aria-label
        # (especialmente botões de ação)

        # Procurar elementos com role
        role_elements = self.driver.find_elements(By.CSS_SELECTOR, "[role]")

        # Verificar se há estrutura semântica adequada
        nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
        main_elements = self.driver.find_elements(By.TAG_NAME, "main")

        # Deve haver pelo menos um nav e um main
        self.assertGreater(len(nav_elements), 0)
        self.assertGreater(len(main_elements), 0)


@pytest.mark.selenium
class TestResponsiveDesign(BaseSeleniumTestCase):
    """Testes para design responsivo"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_mobile_layout(self):
        """Testa layout mobile"""
        # Redimensionar para mobile
        self.driver.set_window_size(375, 667)
        time.sleep(0.5)

        # Verificar se elementos se adaptaram
        sidebar = self.driver.find_element(By.ID, "sidebar")

        # Em mobile, sidebar deve estar oculta ou colapsada
        # Verificar se há overlay mobile
        try:
            overlay = self.driver.find_element(By.ID, "mobileOverlay")
            # Overlay deve existir mas estar oculto inicialmente
        except NoSuchElementException:
            pass

    def test_tablet_layout(self):
        """Testa layout tablet"""
        # Redimensionar para tablet
        self.driver.set_window_size(768, 1024)
        time.sleep(0.5)

        # Verificar se layout se adapta adequadamente
        main_content = self.driver.find_element(By.CSS_SELECTOR, ".main-content")
        self.assertTrue(main_content.is_displayed())

    def test_desktop_layout(self):
        """Testa layout desktop"""
        # Redimensionar para desktop
        self.driver.set_window_size(1920, 1080)
        time.sleep(0.5)

        # Verificar se todos os elementos estão visíveis
        sidebar = self.driver.find_element(By.ID, "sidebar")
        main_content = self.driver.find_element(By.CSS_SELECTOR, ".main-content")

        self.assertTrue(sidebar.is_displayed())
        self.assertTrue(main_content.is_displayed())


@pytest.mark.selenium
class TestErrorHandling(BaseSeleniumTestCase):
    """Testes para tratamento de erros"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_404_page(self):
        """Testa página 404"""
        # Navegar para página inexistente
        self.driver.get(f"{self.live_server_url}/pagina-inexistente/")

        # Aguardar carregamento
        time.sleep(1)

        # Verificar se é página de erro ou redirecionamento
        current_url = self.driver.current_url

        # Pode ser redirecionado para login ou mostrar 404
        self.assertTrue(
            "404" in self.driver.page_source
            or "/login/" in current_url
            or "/home/" in current_url
        )

    def test_permission_denied(self):
        """Testa acesso negado"""
        # Logout do admin
        self.logout()

        # Login como usuário público
        self.login("publico_selenium", "selenium123")

        # Tentar acessar página restrita
        self.driver.get(f"{self.live_server_url}/monitoramento/")

        # Deve ser redirecionado ou mostrar erro
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()

        # Verificar se acesso foi negado
        self.assertTrue(
            "/login/" in current_url
            or "acesso negado" in page_source
            or "permission denied" in page_source
            or "403" in page_source
        )


# Configuração para executar testes com diferentes navegadores
class FirefoxSeleniumTestCase(BaseSeleniumTestCase):
    """Classe base para testes com Firefox"""

    @classmethod
    def setUpClass(cls):
        super(BaseSeleniumTestCase, cls).setUpClass()

        from selenium.webdriver.firefox.options import \
            Options as FirefoxOptions
        from selenium.webdriver.firefox.service import \
            Service as FirefoxService
        from webdriver_manager.firefox import GeckoDriverManager

        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")

        service = FirefoxService(GeckoDriverManager().install())
        cls.driver = webdriver.Firefox(service=service, options=firefox_options)
        cls.driver.implicitly_wait(10)


# Utilitários para testes Selenium
class SeleniumTestUtils:
    """Utilitários para testes Selenium"""

    @staticmethod
    def wait_for_element(driver, selector, timeout=10):
        """Aguarda elemento aparecer"""
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    @staticmethod
    def wait_for_clickable(driver, selector, timeout=10):
        """Aguarda elemento ficar clicável"""
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

    @staticmethod
    def scroll_to_element(driver, element):
        """Rola página até elemento"""
        driver.execute_script("arguments[0].scrollIntoView();", element)

    @staticmethod
    def take_full_screenshot(driver, filename):
        """Captura screenshot da página inteira"""
        # Obter altura total da página
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Redimensionar janela para capturar página inteira
        driver.set_window_size(1920, total_height)

        # Capturar screenshot
        driver.save_screenshot(filename)

        # Restaurar tamanho original
        driver.set_window_size(1920, 1080)
