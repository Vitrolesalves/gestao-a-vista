"""
Testes unitários para formulários e validações do sistema Gestão à Vista
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import CharField, ChoiceField, EmailField, Form, ModelForm
from django.test import TestCase

from Gestao_a_Vista.models import Dashboard, Service, Unidade, UserProfile

User = get_user_model()


class DashboardForm(ModelForm):
    """Form para Dashboard (criado para testes)"""

    class Meta:
        model = Dashboard
        fields = [
            "nome",
            "descricao",
            "cliente",
            "servico",
            "url",
            "powerbi_url",
            "status",
        ]

    def clean_nome(self):
        """Validação customizada para nome"""
        nome = self.cleaned_data.get("nome")
        if not nome or len(nome.strip()) < 3:
            raise ValidationError("Nome deve ter pelo menos 3 caracteres")
        return nome.strip()

    def clean_url(self):
        """Validação customizada para URL"""
        url = self.cleaned_data.get("url")
        if url and not url.startswith(("http://", "https://")):
            raise ValidationError("URL deve começar com http:// ou https://")
        return url


class UserProfileForm(ModelForm):
    """Form para UserProfile (criado para testes)"""

    class Meta:
        model = UserProfile
        fields = ["phone", "address"]

    def clean_phone(self):
        """Validação customizada para telefone"""
        phone = self.cleaned_data.get("phone")
        if phone:
            # Remover caracteres não numéricos
            phone_digits = "".join(filter(str.isdigit, phone))
            if len(phone_digits) < 10:
                raise ValidationError("Telefone deve ter pelo menos 10 dígitos")
        return phone


class LoginForm(Form):
    """Form de login (criado para testes)"""

    username = CharField(max_length=150, required=True)
    password = CharField(max_length=128, required=True)

    def clean_username(self):
        """Validação do username"""
        username = self.cleaned_data.get("username")
        if not username:
            raise ValidationError("Username é obrigatório")
        return username.strip()


@pytest.mark.forms
class TestDashboardForm(TestCase):
    """Testes para o formulário de Dashboard"""

    def test_dashboard_form_valid_data(self):
        """Testa formulário com dados válidos"""
        form_data = {
            "nome": "Dashboard Teste",
            "descricao": "Descrição do dashboard",
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
            "url": "https://example.com",
            "powerbi_url": "https://app.powerbi.com/test",
            "status": "Sucesso",
        }

        form = DashboardForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_dashboard_form_required_fields(self):
        """Testa campos obrigatórios do formulário"""
        form_data = {}
        form = DashboardForm(data=form_data)

        self.assertFalse(form.is_valid())
        # Nome, cliente e serviço são obrigatórios no modelo
        self.assertIn("nome", form.errors)
        self.assertIn("cliente", form.errors)
        self.assertIn("servico", form.errors)

    def test_dashboard_form_nome_validation(self):
        """Testa validação customizada do nome"""
        # Nome muito curto
        form_data = {
            "nome": "AB",  # Menos de 3 caracteres
            "cliente": "Cliente",
            "servico": "Servico",
        }

        form = DashboardForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertIn("pelo menos 3 caracteres", str(form.errors["nome"]))

    def test_dashboard_form_nome_strip(self):
        """Testa que nome é limpo de espaços"""
        form_data = {
            "nome": "  Dashboard Teste  ",
            "cliente": "Cliente",
            "servico": "Servico",
        }

        form = DashboardForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["nome"], "Dashboard Teste")

    def test_dashboard_form_url_validation(self):
        """Testa validação da URL"""
        # URL inválida
        form_data = {
            "nome": "Dashboard Teste",
            "cliente": "Cliente",
            "servico": "Servico",
            "url": "invalid-url",
        }

        form = DashboardForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)

    def test_dashboard_form_valid_urls(self):
        """Testa URLs válidas"""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://app.powerbi.com/test",
        ]

        for url in valid_urls:
            form_data = {
                "nome": "Dashboard Teste",
                "cliente": "Cliente",
                "servico": "Servico",
                "url": url,
            }

            form = DashboardForm(data=form_data)
            self.assertTrue(form.is_valid(), f"URL {url} deveria ser válida")

    def test_dashboard_form_save(self):
        """Testa salvamento do formulário"""
        form_data = {
            "nome": "Dashboard Teste",
            "descricao": "Descrição",
            "cliente": "Cliente Teste",
            "servico": "Seguranca",
            "status": "Sucesso",
        }

        form = DashboardForm(data=form_data)
        self.assertTrue(form.is_valid())

        dashboard = form.save()
        self.assertEqual(dashboard.nome, "Dashboard Teste")
        self.assertEqual(dashboard.cliente, "Cliente Teste")


@pytest.mark.forms
class TestUserProfileForm(TestCase):
    """Testes para o formulário de UserProfile"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_user_profile_form_valid_data(self):
        """Testa formulário com dados válidos"""
        form_data = {"phone": "11999999999", "address": "Rua Teste, 123"}

        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_profile_form_empty_data(self):
        """Testa formulário com dados vazios (campos opcionais)"""
        form_data = {}
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_profile_form_phone_validation(self):
        """Testa validação do telefone"""
        # Telefone muito curto
        form_data = {"phone": "123", "address": "Endereço"}

        form = UserProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_user_profile_form_phone_formats(self):
        """Testa diferentes formatos de telefone"""
        valid_phones = [
            "11999999999",
            "(11) 99999-9999",
            "+55 11 99999-9999",
            "11 99999-9999",
        ]

        for phone in valid_phones:
            form_data = {"phone": phone, "address": "Endereço"}

            form = UserProfileForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Telefone {phone} deveria ser válido")

    def test_user_profile_form_save_with_user(self):
        """Testa salvamento do perfil com usuário"""
        form_data = {"phone": "11999999999", "address": "Rua Teste, 123"}

        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

        profile = form.save(commit=False)
        profile.user = self.user
        profile.save()

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone, "11999999999")


@pytest.mark.forms
class TestLoginForm(TestCase):
    """Testes para o formulário de login"""

    def test_login_form_valid_data(self):
        """Testa formulário de login com dados válidos"""
        form_data = {"username": "testuser", "password": "testpass123"}

        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_form_required_fields(self):
        """Testa campos obrigatórios do login"""
        form_data = {}
        form = LoginForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn("password", form.errors)

    def test_login_form_username_strip(self):
        """Testa que username é limpo de espaços"""
        form_data = {"username": "  testuser  ", "password": "testpass123"}

        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], "testuser")

    def test_login_form_empty_username(self):
        """Testa validação de username vazio"""
        form_data = {"username": "", "password": "testpass123"}

        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


@pytest.mark.forms
class TestFormValidations(TestCase):
    """Testes para validações gerais de formulários"""

    def test_email_validation(self):
        """Testa validação de email"""
        from django.forms import EmailField

        field = EmailField()

        # Email válido
        self.assertEqual(field.clean("test@example.com"), "test@example.com")

        # Email inválido
        with self.assertRaises(ValidationError):
            field.clean("invalid-email")

    def test_choice_field_validation(self):
        """Testa validação de campo de escolha"""
        choices = [
            ("admin", "Administrador"),
            ("user", "Usuário"),
            ("guest", "Convidado"),
        ]

        field = ChoiceField(choices=choices)

        # Escolha válida
        self.assertEqual(field.clean("admin"), "admin")

        # Escolha inválida
        with self.assertRaises(ValidationError):
            field.clean("invalid")

    def test_max_length_validation(self):
        """Testa validação de tamanho máximo"""
        field = CharField(max_length=10)

        # Texto dentro do limite
        self.assertEqual(field.clean("test"), "test")

        # Texto muito longo
        with self.assertRaises(ValidationError):
            field.clean("texto muito longo para o campo")

    def test_required_field_validation(self):
        """Testa validação de campo obrigatório"""
        field = CharField(required=True)

        # Campo preenchido
        self.assertEqual(field.clean("valor"), "valor")

        # Campo vazio
        with self.assertRaises(ValidationError):
            field.clean("")

        with self.assertRaises(ValidationError):
            field.clean(None)


@pytest.mark.forms
class TestCustomValidators(TestCase):
    """Testes para validadores customizados"""

    def test_phone_number_validator(self):
        """Testa validador de número de telefone"""

        def validate_phone(value):
            if value:
                digits = "".join(filter(str.isdigit, value))
                if len(digits) < 10:
                    raise ValidationError("Telefone deve ter pelo menos 10 dígitos")
                if len(digits) > 15:
                    raise ValidationError("Telefone deve ter no máximo 15 dígitos")

        # Telefone válido
        validate_phone("11999999999")  # Não deve levantar exceção

        # Telefone muito curto
        with self.assertRaises(ValidationError):
            validate_phone("123")

        # Telefone muito longo
        with self.assertRaises(ValidationError):
            validate_phone("1234567890123456")

    def test_url_validator(self):
        """Testa validador de URL"""

        def validate_url(value):
            if value and not value.startswith(("http://", "https://")):
                raise ValidationError("URL deve começar com http:// ou https://")

        # URLs válidas
        validate_url("http://example.com")
        validate_url("https://example.com")

        # URL inválida
        with self.assertRaises(ValidationError):
            validate_url("ftp://example.com")

        with self.assertRaises(ValidationError):
            validate_url("example.com")

    def test_name_validator(self):
        """Testa validador de nome"""

        def validate_name(value):
            if not value or len(value.strip()) < 2:
                raise ValidationError("Nome deve ter pelo menos 2 caracteres")
            if any(char.isdigit() for char in value):
                raise ValidationError("Nome não pode conter números")

        # Nome válido
        validate_name("João Silva")

        # Nome muito curto
        with self.assertRaises(ValidationError):
            validate_name("A")

        # Nome com números
        with self.assertRaises(ValidationError):
            validate_name("João123")
