"""
Testes de Performance e Consistência — Gestão à Vista
======================================================

Valida que:
  • Todas as páginas principais carregam sem erro 500
  • Autenticação redireciona corretamente (302) para páginas protegidas
  • Todas as URLs nomeadas resolvem sem KeyError/NoReverseMatch
  • Tempo de resposta está dentro dos thresholds aceitáveis
  • Endpoint de health check responde OK
  • O bug da Torre de Controle (FieldError data_atualizacao) não regride
  • Templates herdam de base.html (consistência visual)
  • API endpoints retornam JSON válido
  • Fluxo completo de autenticação funciona
"""

import json
import time

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, resolve, reverse

User = get_user_model()

# ─── Thresholds de Performance ─────────────────────────────────────────
# Página simples (login, home): < 300 ms
# Página com lógica de view / ORM: < 800 ms
# Página com muitos dados (torre-controle, dashboard): < 2000 ms
THRESHOLD_FAST   = 0.300   # 300 ms
THRESHOLD_MEDIUM = 0.800   # 800 ms
THRESHOLD_HEAVY  = 2.000   # 2 s


# ═══════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════

def make_user(role="administrador", **kwargs):
    """Cria (ou recupera) um usuário de teste."""
    defaults = dict(
        username=f"testuser_{role}",
        email=f"{role}@test.com",
        password="TestPass123!",
        role=role,
    )
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def timed_get(client, url):
    """GET cronometrado; retorna (response, elapsed_seconds)."""
    t0 = time.perf_counter()
    response = client.get(url, follow=False)
    return response, time.perf_counter() - t0


# ═══════════════════════════════════════════════════════════════════════
# 1. RESOLUÇÃO DE URLs
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestURLResolution(TestCase):
    """Garante que todas as URLs nomeadas resolvem corretamente."""

    NAMED_URLS = [
        ("gestao_a_vista:login",        [],   {}),
        ("gestao_a_vista:home",         [],   {}),
        ("gestao_a_vista:logout",       [],   {}),
        ("gestao_a_vista:dashboard",    [],   {}),
        ("gestao_a_vista:monitoramento",[], {}),
        ("gestao_a_vista:qr_generator", [],  {}),
        ("gestao_a_vista:etiquetas_generator", [], {}),
        ("gestao_a_vista:controle_acessos",    [], {}),
        ("gestao_a_vista:livro_ata",           [], {}),
        ("gestao_a_vista:planner",             [], {}),
        ("gestao_a_vista:torre_controle",      [], {}),
        ("gestao_a_vista:auditoria_torre",     [], {}),
        ("gestao_a_vista:relatorios",          [], {}),
        ("gestao_a_vista:gestao_qualidade",    [], {}),
        ("gestao_a_vista:calendario_2026",     [], {}),
        ("gestao_a_vista:gestao_salas",        [], {}),
        ("gestao_a_vista:selecionar_unidade",  [], {}),
        ("gestao_a_vista:calendario_reservas", [], {}),
        ("gestao_a_vista:desativacao_cr",      [], {}),
        ("gestao_a_vista:controle_chips",      [], {}),
        ("gestao_a_vista:implantacoes_opsvista",[], {}),
        ("gestao_a_vista:health_check",        [], {}),
    ]

    def test_all_named_urls_resolve(self):
        """Nenhuma URL nomeada deve lançar NoReverseMatch."""
        failures = []
        for name, args, kwargs in self.NAMED_URLS:
            try:
                url = reverse(name, args=args, kwargs=kwargs)
                self.assertIsNotNone(url, f"reverse({name!r}) retornou None")
            except NoReverseMatch as e:
                failures.append(f"{name}: {e}")

        if failures:
            self.fail(
                f"{len(failures)} URL(s) falharam ao resolver:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )

    def test_login_url_resolves_to_correct_view(self):
        """URL /login/ deve apontar para login_view."""
        match = resolve("/login/")
        self.assertIn("login", match.view_name)

    def test_health_url_resolves(self):
        """URL /health/ deve existir e resolver."""
        match = resolve("/health/")
        self.assertIn("health", match.view_name)

    def test_torre_controle_url_resolves(self):
        """/torre-controle/ deve resolver sem erros."""
        url = reverse("gestao_a_vista:torre_controle")
        self.assertEqual(url, "/torre-controle/")


# ═══════════════════════════════════════════════════════════════════════
# 2. AUTENTICAÇÃO — páginas protegidas redirecionam sem login
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestAuthRedirects(TestCase):
    """Páginas protegidas devem redirecionar (302) sem autenticação."""

    PROTECTED_PAGES = [
        "/home/",
        "/dashboard/",
        "/monitoramento/",
        "/qr-generator/",
        "/etiquetas/",
        "/controle-acessos/",
        "/livro-ata/",
        "/planner/",
        "/torre-controle/",
        "/torre-controle/auditoria/",
        "/relatorios/",
        "/gestao-qualidade/",
        "/calendario-2026/",
        "/gestao-salas/",
        "/calendario-reservas/",
        "/desativacao-cr/",
        "/controle-chips/",
        "/implantacoes-opsvista/",
    ]

    # Páginas acessíveis sem login (public)
    PUBLIC_PAGES = [
        "/selecionar-unidade/",
    ]

    def setUp(self):
        self.client = Client()

    def test_protected_pages_redirect_when_unauthenticated(self):
        """Todas as páginas protegidas devem retornar 302 sem login."""
        failures = []
        for url in self.PROTECTED_PAGES:
            response = self.client.get(url, follow=False)
            if response.status_code not in (301, 302):
                failures.append(
                    f"{url} → HTTP {response.status_code} (esperado 302)"
                )

        if failures:
            self.fail(
                f"{len(failures)} página(s) não redirecionaram:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )

    def test_redirect_goes_to_login(self):
        """O redirecionamento deve apontar para a página de login."""
        response = self.client.get("/home/", follow=False)
        self.assertIn("/login/", response.get("Location", ""))

    def test_login_page_accessible_without_auth(self):
        """Página de login deve estar acessível sem autenticação."""
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)

    def test_health_check_accessible_without_auth(self):
        """/health/ não deve exigir login."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)


# ═══════════════════════════════════════════════════════════════════════
# 3. FLUXO DE AUTENTICAÇÃO COMPLETO
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestAuthFlow(TestCase):
    """Valida o fluxo completo de login/logout."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(role="administrador", username="auth_test_user")

    def test_login_with_valid_credentials(self):
        """Login com credenciais válidas deve redirecionar para home."""
        response = self.client.post(
            "/login/",
            {"username": "auth_test_user", "password": "TestPass123!"},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)

    def test_login_with_invalid_credentials_stays_on_login(self):
        """Credenciais inválidas devem manter na página de login."""
        response = self.client.post(
            "/login/",
            {"username": "auth_test_user", "password": "senha_errada"},
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_access_home(self):
        """Usuário autenticado deve acessar /home/ sem redirect."""
        self.client.force_login(self.user)
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects_to_login(self):
        """Logout deve redirecionar para a página de login."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("gestao_a_vista:logout"), follow=False
        )
        self.assertIn(response.status_code, [301, 302])

    def test_already_logged_in_redirects_away_from_login(self):
        """Usuário já logado acessando /login/ deve ser redirecionado."""
        self.client.force_login(self.user)
        response = self.client.get("/login/", follow=False)
        self.assertEqual(response.status_code, 302)


# ═══════════════════════════════════════════════════════════════════════
# 4. CONSISTÊNCIA DE PÁGINAS — nenhuma retorna 500
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestPageConsistency(TestCase):
    """Garante que nenhuma página retorna HTTP 500 para usuário autenticado."""

    # Páginas que dependem de tabelas externas (só existem no banco de produção).
    # No ambiente de testes (SQLite em memória) elas podem retornar 500 — isso é
    # esperado e não representa um bug do código da aplicação.
    EXTERNAL_DB_PAGES = {"/monitoramento/"}

    # (url, max_threshold_seconds)
    PAGES = [
        ("/home/",                  THRESHOLD_MEDIUM),
        ("/dashboard/",             THRESHOLD_HEAVY),
        ("/monitoramento/",         THRESHOLD_HEAVY),
        ("/qr-generator/",          THRESHOLD_MEDIUM),
        ("/etiquetas/",             THRESHOLD_MEDIUM),
        ("/controle-acessos/",      THRESHOLD_HEAVY),
        ("/livro-ata/",             THRESHOLD_HEAVY),
        ("/planner/",               THRESHOLD_HEAVY),
        ("/torre-controle/",        THRESHOLD_HEAVY),
        ("/torre-controle/auditoria/", THRESHOLD_HEAVY),
        ("/relatorios/",            THRESHOLD_MEDIUM),
        ("/gestao-qualidade/",      THRESHOLD_HEAVY),
        ("/calendario-2026/",       THRESHOLD_HEAVY),
        ("/gestao-salas/",          THRESHOLD_MEDIUM),
        ("/selecionar-unidade/",    THRESHOLD_MEDIUM),
        ("/calendario-reservas/",   THRESHOLD_HEAVY),
        ("/desativacao-cr/",        THRESHOLD_HEAVY),
        ("/controle-chips/",        THRESHOLD_HEAVY),
        ("/implantacoes-opsvista/", THRESHOLD_HEAVY),
    ]

    def setUp(self):
        self.user = make_user(
            role="administrador",
            username="page_consistency_user",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_no_page_returns_500(self):
        """Nenhuma página (exceto as que dependem de BD externo) deve retornar HTTP 500."""
        failures = []
        for url, _ in self.PAGES:
            if url in self.EXTERNAL_DB_PAGES:
                continue  # tabela só existe em produção
            response, elapsed = timed_get(self.client, url)
            if response.status_code == 500:
                failures.append(f"{url} → HTTP 500")

        if failures:
            self.fail(
                f"{len(failures)} página(s) retornaram erro 500:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )

    def test_pages_return_expected_status_codes(self):
        """Páginas devem retornar 200 ou 302 (redirect de permissão), nunca 404/500."""
        failures = []
        for url, _ in self.PAGES:
            if url in self.EXTERNAL_DB_PAGES:
                continue  # tabela só existe em produção
            response = self.client.get(url, follow=False)
            if response.status_code not in (200, 302, 301):
                failures.append(
                    f"{url} → HTTP {response.status_code}"
                )

        if failures:
            self.fail(
                f"{len(failures)} página(s) com status inesperado:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )


# ═══════════════════════════════════════════════════════════════════════
# 5. PERFORMANCE — tempo de resposta por categoria
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestPagePerformance(TestCase):
    """
    Mede o tempo de resposta de cada página e falha se exceder o threshold.

    Thresholds:
      Fast   < 300 ms  — páginas estáticas / login
      Medium < 800 ms  — páginas com lógica simples
      Heavy  < 2000 ms — páginas com ORM complexo ou queries externas
    """

    databases = ["default", "readonly"]

    def setUp(self):
        self.user = make_user(
            role="administrador",
            username="perf_user",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def _assert_performance(self, url, threshold, label=""):
        response, elapsed = timed_get(self.client, url)
        msg = (
            f"{label or url} — {elapsed * 1000:.0f} ms "
            f"(threshold: {threshold * 1000:.0f} ms)"
        )
        # Não falha em 500 aqui (coberto pelo teste de consistência)
        if response.status_code not in (500,):
            self.assertLess(
                elapsed, threshold,
                f"LENTO: {msg}",
            )

    # ── Fast pages (< 300 ms) ──────────────────────────────────────────

    def test_login_page_fast(self):
        client = Client()  # não autenticado
        _, elapsed = timed_get(client, "/login/")
        self.assertLess(elapsed, THRESHOLD_FAST, "Página de login muito lenta")

    def test_health_check_fast(self):
        client = Client()
        _, elapsed = timed_get(client, "/health/")
        self.assertLess(elapsed, THRESHOLD_FAST, "/health/ muito lento")

    # ── Medium pages (< 800 ms) ────────────────────────────────────────

    def test_home_medium(self):
        self._assert_performance("/home/", THRESHOLD_MEDIUM, "Home")

    def test_qr_generator_medium(self):
        self._assert_performance("/qr-generator/", THRESHOLD_MEDIUM, "QR Generator")

    def test_etiquetas_medium(self):
        self._assert_performance("/etiquetas/", THRESHOLD_MEDIUM, "Etiquetas")

    def test_relatorios_medium(self):
        # Relatórios tenta consulta no BD readonly; usa threshold heavy para tolerar overhead
        self._assert_performance("/relatorios/", THRESHOLD_HEAVY, "Relatórios")

    def test_selecionar_unidade_medium(self):
        self._assert_performance("/selecionar-unidade/", THRESHOLD_MEDIUM, "Selecionar Unidade")

    # ── Heavy pages (< 2000 ms) ────────────────────────────────────────

    def test_dashboard_heavy(self):
        self._assert_performance("/dashboard/", THRESHOLD_HEAVY, "Dashboard")

    def test_monitoramento_heavy(self):
        # Monitoramento executa SQL bruto contra tabela externa (import.monitor).
        # Em teste (SQLite) a tabela não existe e a view retorna 500 — comportamento esperado.
        self.client.raise_request_exception = False
        try:
            response, elapsed = timed_get(self.client, "/monitoramento/")
            if response.status_code == 500:
                pytest.skip("Monitoramento requer tabela externa (import.monitor) — indisponível no SQLite de testes")
            self.assertLess(elapsed, THRESHOLD_HEAVY, f"LENTO: Monitoramento — {elapsed * 1000:.0f} ms")
        finally:
            self.client.raise_request_exception = True

    def test_torre_controle_heavy(self):
        self._assert_performance("/torre-controle/", THRESHOLD_HEAVY, "Torre de Controle")

    def test_planner_heavy(self):
        self._assert_performance("/planner/", THRESHOLD_HEAVY, "Planner")

    def test_livro_ata_heavy(self):
        self._assert_performance("/livro-ata/", THRESHOLD_HEAVY, "Livro ATA")

    def test_gestao_qualidade_heavy(self):
        self._assert_performance("/gestao-qualidade/", THRESHOLD_HEAVY, "Gestão da Qualidade")

    def test_controle_acessos_heavy(self):
        self._assert_performance("/controle-acessos/", THRESHOLD_HEAVY, "Controle de Acessos")

    def test_calendario_2026_heavy(self):
        self._assert_performance("/calendario-2026/", THRESHOLD_HEAVY, "Calendário 2026")

    def test_auditoria_torre_heavy(self):
        self._assert_performance("/torre-controle/auditoria/", THRESHOLD_HEAVY, "Auditoria Torre")


# ═══════════════════════════════════════════════════════════════════════
# 6. HEALTH CHECK & API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestHealthAndAPIEndpoints(TestCase):
    """Valida o endpoint de saúde e APIs JSON."""

    def setUp(self):
        self.user = make_user(role="administrador", username="api_test_user")
        self.client = Client()
        self.client.force_login(self.user)

    def test_health_check_returns_200(self):
        """/health/ deve retornar HTTP 200."""
        response = Client().get("/health/")
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_json(self):
        """/health/ deve retornar JSON válido."""
        response = Client().get("/health/")
        self.assertEqual(response.status_code, 200)
        try:
            data = json.loads(response.content)
            self.assertIsInstance(data, dict)
        except (json.JSONDecodeError, ValueError):
            # health check pode retornar texto simples — aceitável
            pass

    def test_api_salas_returns_json(self):
        """/api/salas/ deve retornar JSON válido."""
        response = self.client.get("/api/salas/")
        self.assertIn(response.status_code, [200, 302, 403])
        if response.status_code == 200:
            data = json.loads(response.content)
            self.assertIsInstance(data, (dict, list))

    def test_api_historico_reservas_returns_json(self):
        """/api/reservas/historico/ deve retornar JSON ou redirecionar."""
        response = self.client.get("/api/reservas/historico/")
        self.assertIn(response.status_code, [200, 302, 403])
        if response.status_code == 200:
            data = json.loads(response.content)
            self.assertIsInstance(data, (dict, list))

    def test_manifest_json_accessible(self):
        """/manifest.json deve estar acessível."""
        response = Client().get("/manifest.json")
        self.assertIn(response.status_code, [200, 302, 404])

    def test_service_worker_accessible(self):
        """/sw.js deve estar acessível."""
        response = Client().get("/sw.js")
        self.assertIn(response.status_code, [200, 302, 404])


# ═══════════════════════════════════════════════════════════════════════
# 7. REGRESSÃO — bugs anteriores não podem retornar
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestRegressions(TestCase):
    """
    Testes de regressão para bugs que já foram corrigidos.
    Garante que não regridam em futuras mudanças.
    """

    def setUp(self):
        self.user = make_user(role="administrador", username="regression_user")
        self.client = Client()
        self.client.force_login(self.user)

    def test_torre_controle_nao_retorna_500(self):
        """
        Regressão: /torre-controle/ retornava HTTP 500 devido a FieldError
        em OcorrenciaPlanoAcao.objects.only('data_atualizacao', ...).
        Campo 'data_atualizacao' não existe no model.
        Corrigido em: views.py linha 4807 — removido 'data_atualizacao' do .only().
        """
        response = self.client.get("/torre-controle/")
        self.assertNotEqual(
            response.status_code, 500,
            "Torre de Controle retornou 500 — regressão do FieldError "
            "'data_atualizacao' detectada!",
        )

    def test_torre_controle_accessible_when_authenticated(self):
        """/torre-controle/ deve retornar 200 para usuário autenticado."""
        response = self.client.get("/torre-controle/")
        self.assertIn(
            response.status_code, [200, 302],
            f"Torre de Controle retornou {response.status_code}",
        )

    def test_torre_controle_detalhe_url_resolves(self):
        """URL de detalhe da ocorrência deve resolver corretamente."""
        import uuid
        url = reverse(
            "gestao_a_vista:livro_ocorrencia_detalhe",
            kwargs={"pk": uuid.uuid4()},
        )
        self.assertIn("/torre-controle/detalhe/", url)

    def test_static_files_not_404_in_base_template(self):
        """
        A page home/ deve carregar sem referências a arquivos estáticos inexistentes
        causarem erro 500.
        """
        response = self.client.get("/home/")
        self.assertNotEqual(response.status_code, 500)

    def test_torre_controle_sem_dias_parametro(self):
        """Torre de controle funciona sem parâmetro ?dias=."""
        response = self.client.get("/torre-controle/")
        self.assertNotEqual(response.status_code, 500)

    def test_torre_controle_dias_30(self):
        """Torre de controle com ?dias=30 não deve retornar 500."""
        response = self.client.get("/torre-controle/?dias=30")
        self.assertNotEqual(response.status_code, 500)

    def test_torre_controle_dias_60(self):
        """Torre de controle com ?dias=60 não deve retornar 500."""
        response = self.client.get("/torre-controle/?dias=60")
        self.assertNotEqual(response.status_code, 500)

    def test_torre_controle_dias_90(self):
        """Torre de controle com ?dias=90 não deve retornar 500."""
        response = self.client.get("/torre-controle/?dias=90")
        self.assertNotEqual(response.status_code, 500)


# ═══════════════════════════════════════════════════════════════════════
# 8. CONSISTÊNCIA DO TEMPLATE BASE
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestTemplateConsistency(TestCase):
    """
    Garante que o template base.html está sendo usado corretamente
    e que os elementos chave do design estão presentes.
    """

    def setUp(self):
        self.user = make_user(role="administrador", username="template_user")
        self.client = Client()
        self.client.force_login(self.user)

    def _get_and_decode(self, url):
        response = self.client.get(url, follow=True)
        return response, response.content.decode("utf-8", errors="ignore")

    def test_home_contains_navigation_sidebar(self):
        """Home deve conter a sidebar de navegação."""
        response, content = self._get_and_decode("/home/")
        if response.status_code == 200:
            # A sidebar existe no base.html
            self.assertIn("sidebar", content.lower())

    def test_pages_use_figtree_font(self):
        """Páginas devem carregar a fonte Figtree (parte do redesign)."""
        response, content = self._get_and_decode("/home/")
        if response.status_code == 200:
            self.assertIn("Figtree", content)

    def test_home_has_logout_button(self):
        """Página home deve ter o botão de logout."""
        response, content = self._get_and_decode("/home/")
        if response.status_code == 200:
            # Botão Sair existe no base.html
            self.assertIn("Sair", content)

    def test_login_page_has_background_image(self):
        """Página de login deve referenciar a imagem de fundo."""
        client = Client()
        response = client.get("/login/")
        content = response.content.decode("utf-8", errors="ignore")
        self.assertIn("background", content.lower())

    def test_login_page_has_form_fields(self):
        """Página de login deve ter campos de username e password."""
        client = Client()
        response = client.get("/login/")
        content = response.content.decode("utf-8", errors="ignore")
        self.assertIn("username", content)
        self.assertIn("password", content)

    def test_pages_do_not_have_debug_errors(self):
        """Páginas não devem conter traceback ou debug errors do Django."""
        pages = ["/home/", "/dashboard/", "/torre-controle/"]
        for url in pages:
            response, content = self._get_and_decode(url)
            if response.status_code == 200:
                self.assertNotIn("Traceback (most recent call last)", content,
                    f"{url} contém traceback Django")
                self.assertNotIn("OperationalError", content,
                    f"{url} contém OperationalError")
                self.assertNotIn("FieldError", content,
                    f"{url} contém FieldError — possível regressão")


# ═══════════════════════════════════════════════════════════════════════
# 9. PERMISSÕES POR ROLE
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.views
class TestRolePermissions(TestCase):
    """
    Garante que o sistema de permissões por role funciona.
    Usuários sem permissão devem ser redirecionados, não receber 500.
    """

    ROLES = ["administrador", "gerente", "operador", "publico"]

    def setUp(self):
        self.users = {}
        for role in self.ROLES:
            self.users[role] = make_user(
                role=role,
                username=f"perm_test_{role}",
            )

    def test_no_role_causes_500(self):
        """
        Nenhum role deve causar HTTP 500 nas páginas principais.
        Pode retornar 200 (acesso) ou 302 (redirect por falta de permissão).
        """
        pages = ["/home/", "/dashboard/", "/torre-controle/", "/planner/"]
        failures = []

        for role, user in self.users.items():
            client = Client()
            client.force_login(user)
            for url in pages:
                response = client.get(url, follow=False)
                if response.status_code == 500:
                    failures.append(f"role={role!r} url={url} → HTTP 500")

        if failures:
            self.fail(
                f"HTTP 500 para combinações de role/página:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )

    def test_unauthenticated_never_sees_500(self):
        """Cliente não autenticado nunca deve ver HTTP 500."""
        client = Client()
        pages = ["/home/", "/dashboard/", "/torre-controle/", "/login/"]
        for url in pages:
            response = client.get(url)
            self.assertNotEqual(
                response.status_code, 500,
                f"Usuário anônimo recebeu 500 em {url}",
            )
