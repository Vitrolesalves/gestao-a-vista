import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from Gestao_a_Vista.models import ImplantacoesOpsVista, Estrutura
from Gestao_a_Vista.forms import ImplantacoesOpsVistaForm
import json


User = get_user_model()


class ImplantacoesOpsVistaSimpleTest(TestCase):
    """Testes simplificados para ImplantacoesOpsVista"""

    def setUp(self):
        """Configuração inicial para os testes"""
        # Usar estrutura existente ou criar mock simples
        self.estrutura, created = Estrutura.objects.get_or_create(
            id="test-estrutura-123",
            defaults={'descricao': "CR Teste"}
        )

    def test_model_creation_simple(self):
        """Teste básico de criação do modelo"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr=self.estrutura,
            sistema="Sistema Teste",
            implantacoes=["Implantacao 1", "Implantacao 2"],
            servico="seguranca",
            status="ativo"
        )
        
        self.assertEqual(implantacao.sistema, "Sistema Teste")
        self.assertEqual(implantacao.servico, "seguranca")
        self.assertEqual(implantacao.status, "ativo")
        self.assertEqual(len(implantacao.implantacoes), 2)

    def test_model_str_method(self):
        """Teste do método __str__ do modelo"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr=self.estrutura,
            sistema="Sistema Teste",
            implantacoes=["Implantacao 1"],
            servico="seguranca",
            status="ativo"
        )
        
        expected_str = f"{self.estrutura.descricao} - Sistema Teste"
        self.assertEqual(str(implantacao), expected_str)

    def test_form_basic_validation(self):
        """Teste básico de validação do formulário"""
        form_data = {
            'cr': self.estrutura.id,
            'sistema': 'Sistema Teste',
            'implantacoes_text': 'Implantacao 1, Implantacao 2',
            'servico': 'seguranca',
            'status': 'ativo'
        }
        
        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_choices_validation(self):
        """Teste das choices do modelo"""
        # Testar status choices
        valid_statuses = ["ativo", "desmobilizado"]
        for status in valid_statuses:
            implantacao = ImplantacoesOpsVista(
                cr=self.estrutura,
                sistema="Sistema Teste",
                implantacoes=["Teste"],
                servico="seguranca",
                status=status
            )
            implantacao.full_clean()  # Não deve gerar erro
        
        # Testar servico choices
        valid_servicos = ["seguranca", "facilities", "portaria", "manutencao", "jardinagem", "brigadista"]
        for servico in valid_servicos:
            implantacao = ImplantacoesOpsVista(
                cr=self.estrutura,
                sistema="Sistema Teste",
                implantacoes=["Teste"],
                servico=servico,
                status="ativo"
            )
            implantacao.full_clean()  # Não deve gerar erro


class ImplantacoesOpsVistaViewSimpleTest(TestCase):
    """Testes simplificados das views"""

    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='administrador'
        )
        
        # Usar estrutura existente ou criar mock simples
        self.estrutura, created = Estrutura.objects.get_or_create(
            id="test-estrutura-456",
            defaults={'descricao': "CR View Teste"}
        )

    def test_view_requires_login(self):
        """Teste se a view requer login"""
        url = reverse('gestao_a_vista:implantacoes_opsvista')
        response = self.client.get(url)
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)

    def test_view_with_login(self):
        """Teste da view com usuário logado"""
        self.client.force_login(self.user)
        url = reverse('gestao_a_vista:implantacoes_opsvista')
        
        response = self.client.get(url)
        
        # Deve retornar 200 ou 403 (dependendo das permissões)
        self.assertIn(response.status_code, [200, 403])
