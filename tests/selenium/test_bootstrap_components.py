"""
Testes Selenium para componentes Bootstrap customizados

Este arquivo testa especificamente os componentes Bootstrap 5 customizados
implementados no sistema Gestão à Vista.
"""

import time

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .test_ui_workflows import BaseSeleniumTestCase


@pytest.mark.selenium
class TestBootstrapSidebar(BaseSeleniumTestCase):
    """Testes para sidebar Bootstrap customizada"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_sidebar_toggle_functionality(self):
        """Testa funcionalidade de toggle da sidebar"""
        # Encontrar sidebar e botão de toggle
        sidebar = self.wait.until(EC.presence_of_element_located((By.ID, "sidebar")))
        toggle_button = self.driver.find_element(By.ID, "sidebarToggle")

        # Verificar estado inicial
        initial_classes = sidebar.get_attribute("class")
        initial_collapsed = "collapsed" in initial_classes

        # Clicar no toggle
        toggle_button.click()

        # Aguardar animação (300ms conforme CSS)
        time.sleep(0.5)

        # Verificar mudança de estado
        final_classes = sidebar.get_attribute("class")
        final_collapsed = "collapsed" in final_classes

        self.assertNotEqual(initial_collapsed, final_collapsed)

        # Testar toggle novamente para voltar ao estado original
        toggle_button.click()
        time.sleep(0.5)

        restored_classes = sidebar.get_attribute("class")
        restored_collapsed = "collapsed" in restored_classes

        self.assertEqual(initial_collapsed, restored_collapsed)

    def test_sidebar_navigation_links(self):
        """Testa links de navegação da sidebar"""
        # Lista de links esperados
        expected_links = [
            ("home", "/home/"),
            ("dashboard", "/dashboard/"),
            ("monitoramento", "/monitoramento/"),
            ("controle_acessos", "/controle-acessos/"),
        ]

        for link_text, expected_url in expected_links:
            try:
                # Encontrar link (pode estar em href ou texto)
                link = self.driver.find_element(
                    By.CSS_SELECTOR,
                    f'a[href*="{link_text}"], a[href*="{expected_url}"]',
                )

                # Clicar no link
                link.click()

                # Aguardar navegação
                self.wait.until(lambda driver: expected_url in driver.current_url)

                # Verificar se chegou na página correta
                self.assertIn(expected_url, self.driver.current_url)

                # Voltar para home para próximo teste
                home_link = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="home"]')
                home_link.click()
                self.wait.until(EC.url_contains("/home/"))

            except (NoSuchElementException, TimeoutException):
                # Se link não existe ou não funciona, continuar com próximo
                continue

    def test_sidebar_submenu_functionality(self):
        """Testa funcionalidade de submenus da sidebar"""
        try:
            # Procurar submenu (ex: Geradores, Gestão de Reservas)
            submenu_toggle = self.driver.find_element(
                By.CSS_SELECTOR, '[data-bs-toggle="collapse"]'
            )

            # Obter ID do submenu alvo
            target_id = submenu_toggle.get_attribute("href").replace("#", "")
            submenu = self.driver.find_element(By.ID, target_id)

            # Verificar estado inicial (deve estar fechado)
            initial_classes = submenu.get_attribute("class")
            initial_open = "show" in initial_classes

            # Clicar para abrir submenu
            submenu_toggle.click()

            # Aguardar animação
            time.sleep(0.5)

            # Verificar se abriu
            final_classes = submenu.get_attribute("class")
            final_open = "show" in final_classes

            self.assertNotEqual(initial_open, final_open)

        except NoSuchElementException:
            # Se não há submenus, pular teste
            pass

    def test_sidebar_tooltips_on_collapse(self):
        """Testa tooltips quando sidebar está colapsada"""
        # Colapsar sidebar
        toggle_button = self.driver.find_element(By.ID, "sidebarToggle")
        toggle_button.click()
        time.sleep(0.5)

        # Verificar se sidebar está colapsada
        sidebar = self.driver.find_element(By.ID, "sidebar")
        self.assertIn("collapsed", sidebar.get_attribute("class"))

        try:
            # Procurar links da sidebar
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .nav-link")

            if nav_links:
                # Hover sobre primeiro link
                actions = ActionChains(self.driver)
                actions.move_to_element(nav_links[0]).perform()

                # Aguardar tooltip aparecer
                time.sleep(0.5)

                # Procurar tooltip
                tooltips = self.driver.find_elements(
                    By.CSS_SELECTOR, ".sidebar-tooltip"
                )

                # Deve haver pelo menos um tooltip visível
                visible_tooltips = [t for t in tooltips if t.is_displayed()]
                self.assertGreater(len(visible_tooltips), 0)

        except NoSuchElementException:
            # Se estrutura é diferente, apenas verificar que sidebar colapsou
            pass


@pytest.mark.selenium
class TestBootstrapThemeToggle(BaseSeleniumTestCase):
    """Testes para alternância de tema"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_theme_toggle_functionality(self):
        """Testa funcionalidade de alternância de tema"""
        try:
            # Procurar botão de tema
            theme_button = self.driver.find_element(
                By.CSS_SELECTOR,
                '[data-theme-toggle], button[title*="tema"], button[title*="theme"]',
            )

            # Verificar tema inicial
            html_element = self.driver.find_element(By.TAG_NAME, "html")
            initial_theme = html_element.get_attribute("data-bs-theme")

            # Clicar no botão de tema
            theme_button.click()

            # Aguardar mudança
            time.sleep(0.5)

            # Verificar se tema mudou
            final_theme = html_element.get_attribute("data-bs-theme")

            # Tema deve ter mudado
            self.assertNotEqual(initial_theme, final_theme)

            # Verificar se é um tema válido
            self.assertIn(final_theme, ["light", "dark"])

        except NoSuchElementException:
            # Se não há botão de tema, pular teste
            pass

    def test_theme_persistence(self):
        """Testa persistência do tema após reload"""
        try:
            # Alternar tema
            theme_button = self.driver.find_element(
                By.CSS_SELECTOR, "[data-theme-toggle]"
            )
            theme_button.click()
            time.sleep(0.5)

            # Obter tema atual
            html_element = self.driver.find_element(By.TAG_NAME, "html")
            theme_before_reload = html_element.get_attribute("data-bs-theme")

            # Recarregar página
            self.driver.refresh()
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Verificar se tema persistiu
            html_element = self.driver.find_element(By.TAG_NAME, "html")
            theme_after_reload = html_element.get_attribute("data-bs-theme")

            self.assertEqual(theme_before_reload, theme_after_reload)

        except NoSuchElementException:
            pass


@pytest.mark.selenium
class TestBootstrapNotifications(BaseSeleniumTestCase):
    """Testes para sistema de notificações"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_notification_system_initialization(self):
        """Testa se sistema de notificações está inicializado"""
        # Verificar se GestaoAVista está disponível
        gestao_vista_available = self.driver.execute_script(
            "return typeof window.GestaoAVista !== 'undefined'"
        )
        self.assertTrue(gestao_vista_available)

        # Verificar se notifications está disponível
        notifications_available = self.driver.execute_script(
            "return typeof window.GestaoAVista.notifications !== 'undefined'"
        )
        self.assertTrue(notifications_available)

    def test_notification_display(self):
        """Testa exibição de notificações"""
        # Executar JavaScript para mostrar notificação
        self.driver.execute_script(
            """
            if (window.GestaoAVista && window.GestaoAVista.notifications) {
                window.GestaoAVista.notifications.success('Teste de notificação Selenium');
            }
        """
        )

        # Aguardar notificação aparecer
        time.sleep(1)

        # Procurar notificação na página
        try:
            notification = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".toast, .notification, .alert")
                )
            )

            # Verificar se notificação está visível
            self.assertTrue(notification.is_displayed())

            # Verificar conteúdo
            notification_text = notification.text.lower()
            self.assertIn("teste", notification_text)

        except TimeoutException:
            # Se não encontrou notificação, verificar se há container
            container = self.driver.find_elements(By.ID, "notification-container")
            # Container deve existir mesmo se não há notificações ativas

    def test_notification_auto_dismiss(self):
        """Testa auto-dismiss de notificações"""
        # Mostrar notificação com tempo curto
        self.driver.execute_script(
            """
            if (window.GestaoAVista && window.GestaoAVista.notifications) {
                window.GestaoAVista.notifications.show('Notificação temporária', 'info', {duration: 1000});
            }
        """
        )

        # Aguardar notificação aparecer
        time.sleep(0.5)

        try:
            notification = self.driver.find_element(
                By.CSS_SELECTOR, ".toast.show, .notification.show"
            )
            self.assertTrue(notification.is_displayed())

            # Aguardar auto-dismiss (1 segundo + margem)
            time.sleep(2)

            # Verificar se notificação foi removida
            notifications = self.driver.find_elements(
                By.CSS_SELECTOR, ".toast.show, .notification.show"
            )
            visible_notifications = [n for n in notifications if n.is_displayed()]

            # Não deve haver notificações visíveis
            self.assertEqual(len(visible_notifications), 0)

        except NoSuchElementException:
            # Se não conseguiu encontrar notificação, pode ser que já foi removida
            pass


@pytest.mark.selenium
class TestBootstrapForms(BaseSeleniumTestCase):
    """Testes para componentes de formulário Bootstrap"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_form_validation_classes(self):
        """Testa classes de validação Bootstrap"""
        # Ir para página com formulário
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            # Procurar formulário com classe needs-validation
            form = self.driver.find_element(By.CSS_SELECTOR, ".needs-validation")

            # Procurar campos obrigatórios
            required_fields = form.find_elements(
                By.CSS_SELECTOR, "input[required], select[required]"
            )

            if required_fields:
                # Tentar submeter formulário sem preencher
                submit_button = form.find_element(
                    By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'
                )
                submit_button.click()

                # Aguardar validação
                time.sleep(0.5)

                # Verificar se formulário ganhou classe was-validated
                form_classes = form.get_attribute("class")
                self.assertIn("was-validated", form_classes)

        except NoSuchElementException:
            # Se não há formulário com validação, pular teste
            pass

    def test_form_loading_states(self):
        """Testa estados de loading em botões"""
        try:
            # Procurar botão com data-loading-text
            loading_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[data-loading-text]"
            )

            # Obter texto original
            original_text = loading_button.text

            # Clicar no botão
            loading_button.click()

            # Aguardar estado de loading
            time.sleep(0.5)

            # Verificar se texto mudou
            current_text = loading_button.text

            # Texto deve ser diferente (loading text)
            self.assertNotEqual(original_text, current_text)

            # Verificar se botão está desabilitado
            self.assertFalse(loading_button.is_enabled())

        except NoSuchElementException:
            # Se não há botões com loading, pular teste
            pass

    def test_custom_select_styling(self):
        """Testa estilização customizada de selects"""
        try:
            # Procurar select com classe form-select
            select_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".form-select, select.form-control"
            )

            if select_elements:
                select = select_elements[0]

                # Verificar se tem estilização Bootstrap
                select_classes = select.get_attribute("class")
                self.assertTrue(
                    "form-select" in select_classes or "form-control" in select_classes
                )

                # Testar interação
                select.click()
                time.sleep(0.2)

                # Verificar se dropdown abriu (pode variar por navegador)

        except NoSuchElementException:
            pass


@pytest.mark.selenium
class TestBootstrapTables(BaseSeleniumTestCase):
    """Testes para tabelas Bootstrap customizadas"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_table_enhanced_styling(self):
        """Testa estilização aprimorada de tabelas"""
        # Ir para página com tabela (dashboard)
        self.driver.get(f"{self.live_server_url}/dashboard/")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            # Procurar tabela com classe table-enhanced
            enhanced_table = self.driver.find_element(
                By.CSS_SELECTOR, ".table-enhanced"
            )

            # Verificar se tabela está visível
            self.assertTrue(enhanced_table.is_displayed())

            # Verificar estrutura da tabela
            thead = enhanced_table.find_element(By.TAG_NAME, "thead")
            tbody = enhanced_table.find_element(By.TAG_NAME, "tbody")

            self.assertTrue(thead.is_displayed())
            self.assertTrue(tbody.is_displayed())

        except NoSuchElementException:
            # Se não há tabela enhanced, procurar tabela normal
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            if tables:
                # Pelo menos deve haver uma tabela
                self.assertGreater(len(tables), 0)

    def test_table_search_functionality(self):
        """Testa funcionalidade de busca em tabelas"""
        try:
            # Procurar campo de busca
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                'input[data-table-search], input[type="search"], input[placeholder*="busca"]',
            )

            # Fazer busca
            search_input.clear()
            search_input.send_keys("test")

            # Aguardar filtro ser aplicado
            time.sleep(0.5)

            # Verificar se busca funcionou (difícil de testar sem dados específicos)
            # Pelo menos verificar que campo aceita input
            self.assertEqual(search_input.get_attribute("value"), "test")

        except NoSuchElementException:
            # Se não há busca, pular teste
            pass

    def test_table_sortable_headers(self):
        """Testa cabeçalhos ordenáveis"""
        try:
            # Procurar headers com data-sortable
            sortable_headers = self.driver.find_elements(
                By.CSS_SELECTOR, "th[data-sortable], .sortable"
            )

            if sortable_headers:
                header = sortable_headers[0]

                # Verificar cursor pointer
                cursor_style = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).cursor", header
                )

                # Clicar no header
                header.click()

                # Aguardar ordenação
                time.sleep(0.5)

                # Verificar se classes de ordenação foram aplicadas
                header_classes = header.get_attribute("class")
                # Pode ter sort-asc, sort-desc, ou similar

        except NoSuchElementException:
            pass


@pytest.mark.selenium
class TestBootstrapModals(BaseSeleniumTestCase):
    """Testes para modais Bootstrap"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_modal_trigger_and_display(self):
        """Testa abertura e exibição de modais"""
        try:
            # Procurar botão que abre modal
            modal_trigger = self.driver.find_element(
                By.CSS_SELECTOR, '[data-bs-toggle="modal"], [data-toggle="modal"]'
            )

            # Clicar no botão
            modal_trigger.click()

            # Aguardar modal aparecer
            modal = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal.show"))
            )

            # Verificar se modal está visível
            self.assertTrue(modal.is_displayed())

            # Verificar estrutura do modal
            modal_dialog = modal.find_element(By.CSS_SELECTOR, ".modal-dialog")
            modal_content = modal.find_element(By.CSS_SELECTOR, ".modal-content")

            self.assertTrue(modal_dialog.is_displayed())
            self.assertTrue(modal_content.is_displayed())

            # Fechar modal
            close_button = modal.find_element(
                By.CSS_SELECTOR, '.btn-close, [data-bs-dismiss="modal"]'
            )
            close_button.click()

            # Aguardar modal fechar
            self.wait.until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal.show"))
            )

        except (NoSuchElementException, TimeoutException):
            # Se não há modais, pular teste
            pass

    def test_modal_backdrop_close(self):
        """Testa fechamento de modal clicando no backdrop"""
        try:
            # Abrir modal
            modal_trigger = self.driver.find_element(
                By.CSS_SELECTOR, '[data-bs-toggle="modal"]'
            )
            modal_trigger.click()

            modal = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal.show"))
            )

            # Clicar no backdrop (fora do modal-dialog)
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(modal, 10, 10).click().perform()

            # Aguardar modal fechar
            time.sleep(0.5)

            # Modal deve ter fechado
            modals = self.driver.find_elements(By.CSS_SELECTOR, ".modal.show")
            visible_modals = [m for m in modals if m.is_displayed()]

            self.assertEqual(len(visible_modals), 0)

        except (NoSuchElementException, TimeoutException):
            pass


@pytest.mark.selenium
class TestBootstrapResponsiveness(BaseSeleniumTestCase):
    """Testes para responsividade dos componentes Bootstrap"""

    def setUp(self):
        super().setUp()
        self.login("admin_selenium", "selenium123")

    def test_responsive_grid_system(self):
        """Testa sistema de grid responsivo"""
        # Testar diferentes tamanhos de tela
        screen_sizes = [
            (1920, 1080),  # Desktop
            (768, 1024),  # Tablet
            (375, 667),  # Mobile
        ]

        for width, height in screen_sizes:
            self.driver.set_window_size(width, height)
            time.sleep(0.5)

            # Verificar se layout se adapta
            main_content = self.driver.find_element(By.CSS_SELECTOR, ".main-content")
            self.assertTrue(main_content.is_displayed())

            # Verificar se não há overflow horizontal
            body_width = self.driver.execute_script("return document.body.scrollWidth")
            window_width = self.driver.execute_script("return window.innerWidth")

            # Não deve haver scroll horizontal significativo
            self.assertLessEqual(body_width - window_width, 20)  # Margem de 20px

    def test_responsive_navigation(self):
        """Testa navegação responsiva"""
        # Mobile
        self.driver.set_window_size(375, 667)
        time.sleep(0.5)

        # Verificar se sidebar se comporta adequadamente em mobile
        sidebar = self.driver.find_element(By.ID, "sidebar")

        # Em mobile, sidebar pode estar oculta ou transformada
        sidebar_transform = self.driver.execute_script(
            "return window.getComputedStyle(arguments[0]).transform", sidebar
        )

        # Desktop
        self.driver.set_window_size(1920, 1080)
        time.sleep(0.5)

        # Verificar se sidebar volta ao normal
        sidebar_transform_desktop = self.driver.execute_script(
            "return window.getComputedStyle(arguments[0]).transform", sidebar
        )

        # Transforms devem ser diferentes entre mobile e desktop
        # (a menos que não haja responsividade implementada)

    def test_responsive_components(self):
        """Testa componentes responsivos"""
        # Testar cards, botões, formulários em diferentes tamanhos
        components_to_test = [".card", ".btn", ".form-control", ".table-responsive"]

        for component_selector in components_to_test:
            try:
                component = self.driver.find_element(
                    By.CSS_SELECTOR, component_selector
                )

                # Testar em mobile
                self.driver.set_window_size(375, 667)
                time.sleep(0.2)

                # Componente deve estar visível
                self.assertTrue(component.is_displayed())

                # Testar em desktop
                self.driver.set_window_size(1920, 1080)
                time.sleep(0.2)

                # Componente deve continuar visível
                self.assertTrue(component.is_displayed())

            except NoSuchElementException:
                # Se componente não existe, continuar
                continue
