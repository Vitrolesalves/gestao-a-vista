import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from Gestao_a_Vista.models import ImplantacoesOpsVista, Estrutura
from Gestao_a_Vista.forms import (
    ImplantacoesOpsVistaForm,
    ImplantacoesOpsVistaFilterForm,
)
import json


User = get_user_model()


class ImplantacoesOpsVistaModelTest(TestCase):
    """Testes para o modelo ImplantacoesOpsVista"""

    def setUp(self):
        """Configuração inicial para os testes"""
        # Mock da estrutura já que é managed=False
        self.estrutura = MagicMock()
        self.estrutura.id = "test-uuid-123"
        self.estrutura.descricao = "CR Teste"
        self.estrutura.cr = "CR001"

    @patch('Gestao_a_Vista.models.Estrutura.objects.get')
    def test_implantacao_creation(self, mock_estrutura_get):
        """Teste de criação de uma implantação OpsVista"""
        mock_estrutura_get.return_value = self.estrutura
        
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1", "Sensor GPS"],
            servico="seguranca",
            status="ativo",
            observacoes="Teste de observação",
        )

        self.assertEqual(implantacao.cr_id, self.estrutura.id)
        self.assertEqual(implantacao.sistema, "Sistema Teste")
        self.assertEqual(implantacao.implantacoes, ["Câmera 1", "Sensor GPS"])
        self.assertEqual(implantacao.servico, "seguranca")
        self.assertEqual(implantacao.status, "ativo")
        self.assertEqual(implantacao.observacoes, "Teste de observação")
        self.assertIsNotNone(implantacao.created_at)
        self.assertIsNotNone(implantacao.updated_at)

    def test_implantacao_str_method(self):
        """Teste do método __str__ do modelo"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1"],
            servico="seguranca",
            status="ativo",
        )

        expected_str = f"{self.estrutura.id} - Sistema Teste"
        self.assertEqual(str(implantacao), expected_str)

    def test_get_implantacoes_display_with_list(self):
        """Teste do método get_implantacoes_display com lista"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1", "Sensor GPS", "Tracker"],
            servico="seguranca",
            status="ativo",
        )

        expected_display = "Câmera 1, Sensor GPS, Tracker"
        self.assertEqual(implantacao.get_implantacoes_display(), expected_display)

    def test_get_implantacoes_display_with_empty_list(self):
        """Teste do método get_implantacoes_display com lista vazia"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=[],
            servico="seguranca",
            status="ativo",
        )

        self.assertEqual(implantacao.get_implantacoes_display(), "")

    def test_status_choices(self):
        """Teste das opções de status"""
        expected_choices = [
            ("ativo", "Ativo"),
            ("desmobilizado", "Desmobilizado"),
        ]
        self.assertEqual(ImplantacoesOpsVista.STATUS_CHOICES, expected_choices)

    def test_servico_choices(self):
        """Teste das opções de serviço"""
        expected_choices = [
            ("seguranca", "Segurança"),
            ("facilities", "Facilities"),
            ("portaria", "Portaria"),
            ("manutencao", "Manutenção"),
            ("jardinagem", "Jardinagem"),
            ("brigadista", "Brigadista"),
        ]
        self.assertEqual(ImplantacoesOpsVista.SERVICO_CHOICES, expected_choices)

    def test_default_status(self):
        """Teste do status padrão"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1"],
            servico="seguranca",
        )

        self.assertEqual(implantacao.status, "ativo")

    def test_cascade_delete(self):
        """Teste de exclusão em cascata quando CR é deletado"""
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1"],
            servico="seguranca",
            status="ativo",
        )

        implantacao_id = implantacao.id
        self.estrutura.delete()

        with self.assertRaises(ImplantacoesOpsVista.DoesNotExist):
            ImplantacoesOpsVista.objects.get(id=implantacao_id)


class ImplantacoesOpsVistaFormTest(TestCase):
    """Testes para o formulário ImplantacoesOpsVistaForm"""

    def setUp(self):
        """Configuração inicial para os testes"""
        # Mock da estrutura já que é managed=False
        self.estrutura = MagicMock()
        self.estrutura.id = "test-uuid-123"
        self.estrutura.descricao = "CR Teste"
        self.estrutura.cr = "CR001"

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_valid_data(self, mock_estrutura_all):
        """Teste com dados válidos"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr_id": self.estrutura.id,
            "sistema": "Sistema Teste",
            "implantacoes_text": "Câmera 1, Sensor GPS, Tracker",
            "servico": "seguranca",
            "status": "ativo",
            "observacoes": "Teste de observação",
        }

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertTrue(form.is_valid())

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_missing_required_fields(self, mock_estrutura_all):
        """Teste com campos obrigatórios faltando"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = []
        
        form_data = {"observacoes": "Apenas observação"}

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("cr_id", form.errors)
        self.assertIn("sistema", form.errors)
        self.assertIn("implantacoes_text", form.errors)
        self.assertIn("servico", form.errors)

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_clean_implantacoes_text_empty(self, mock_estrutura_all):
        """Teste de validação com implantações vazias"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr_id": self.estrutura.id,
            "sistema": "Sistema Teste",
            "implantacoes_text": "",
            "servico": "seguranca",
            "status": "ativo",
        }

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("implantacoes_text", form.errors)

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_clean_implantacoes_text_only_commas(self, mock_estrutura_all):
        """Teste de validação com apenas vírgulas"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr_id": self.estrutura.id,
            "sistema": "Sistema Teste",
            "implantacoes_text": ", , ,",
            "servico": "seguranca",
            "status": "ativo",
        }

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("implantacoes_text", form.errors)

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_clean_sistema_too_short(self, mock_estrutura_all):
        """Teste de validação com sistema muito curto"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr_id": self.estrutura.id,
            "sistema": "AB",
            "implantacoes_text": "Câmera 1",
            "servico": "seguranca",
            "status": "ativo",
        }

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("sistema", form.errors)

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_save_converts_implantacoes_text_to_list(self, mock_estrutura_all):
        """Teste se o formulário converte o texto em lista"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr_id": self.estrutura.id,
            "sistema": "Sistema Teste",
            "implantacoes_text": "Câmera 1, Sensor GPS, Tracker",
            "servico": "seguranca",
            "status": "ativo",
        }

        form = ImplantacoesOpsVistaForm(data=form_data)
        self.assertTrue(form.is_valid())

        instance = form.save()
        expected_list = ["Câmera 1", "Sensor GPS", "Tracker"]
        self.assertEqual(instance.implantacoes, expected_list)

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_form_edit_existing_instance(self, mock_estrutura_all):
        """Teste de edição de instância existente"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Original",
            implantacoes=["Câmera Original", "Sensor Original"],
            servico="seguranca",
            status="ativo",
        )

        form = ImplantacoesOpsVistaForm(instance=implantacao)

        # Verificar se o campo implantacoes_text foi preenchido corretamente
        expected_text = "Câmera Original, Sensor Original"
        self.assertEqual(form.fields["implantacoes_text"].initial, expected_text)


class ImplantacoesOpsVistaFilterFormTest(TestCase):
    """Testes para o formulário de filtros"""

    def setUp(self):
        """Configuração inicial para os testes"""
        # Mock da estrutura já que é managed=False
        self.estrutura = MagicMock()
        self.estrutura.id = "test-uuid-123"
        self.estrutura.descricao = "CR Teste"
        self.estrutura.cr = "CR001"

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_filter_form_valid(self, mock_estrutura_all):
        """Teste do formulário de filtros com dados válidos"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form_data = {
            "cr": self.estrutura.id,
            "sistema": "Sistema Teste",
            "servico": "seguranca",
            "status": "ativo",
        }

        form = ImplantacoesOpsVistaFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    @patch('Gestao_a_Vista.models.Estrutura.objects.all')
    def test_filter_form_empty_valid(self, mock_estrutura_all):
        """Teste do formulário de filtros vazio (todos os campos opcionais)"""
        # Mock da query de estruturas para o formulário
        mock_estrutura_all.return_value = [self.estrutura]
        
        form = ImplantacoesOpsVistaFilterForm(data={})
        self.assertTrue(form.is_valid())


class ImplantacoesOpsVistaViewTest(TestCase):
    """Testes para as views de ImplantacoesOpsVista"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", role="admin"
        )
        # Mock da estrutura já que é managed=False
        self.estrutura = MagicMock()
        self.estrutura.id = "test-uuid-123"
        self.estrutura.descricao = "CR Teste"
        self.estrutura.cr = "CR001"
        self.url = reverse("gestao_a_vista:implantacoes_opsvista")

    def test_view_requires_login(self):
        """Teste se a view requer login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect para login

    def test_view_get_list(self):
        """Teste de listagem das implantações"""
        self.client.login(username="testuser", password="testpass123")

        # Criar algumas implantações para teste
        ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema 1",
            implantacoes=["Câmera 1"],
            servico="seguranca",
            status="ativo",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sistema 1")
        self.assertContains(response, "Implantações OpsVista")

    def test_view_get_specific_record(self):
        """Teste de busca de registro específico"""
        self.client.login(username="testuser", password="testpass123")

        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Teste",
            implantacoes=["Câmera 1", "Sensor GPS"],
            servico="seguranca",
            status="ativo",
            observacoes="Teste",
        )

        response = self.client.get(f"{self.url}?id={implantacao.id}")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["sistema"], "Sistema Teste")
        self.assertEqual(data["implantacoes"], ["Câmera 1", "Sensor GPS"])

    def test_view_post_create_record(self):
        """Teste de criação de novo registro via POST"""
        self.client.login(username="testuser", password="testpass123")

        post_data = {
            "cr": self.estrutura.id,
            "sistema": "Novo Sistema",
            "implantacoes": ["Câmera Nova", "Sensor Novo"],
            "servico": "facilities",
            "status": "ativo",
            "observacoes": "Nova observação",
        }

        response = self.client.post(
            self.url, data=json.dumps(post_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verificar se foi criado no banco
        implantacao = ImplantacoesOpsVista.objects.get(sistema="Novo Sistema")
        self.assertEqual(implantacao.cr, self.estrutura)
        self.assertEqual(implantacao.implantacoes, ["Câmera Nova", "Sensor Novo"])

    def test_view_put_update_record(self):
        """Teste de atualização de registro via PUT"""
        self.client.login(username="testuser", password="testpass123")

        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Original",
            implantacoes=["Câmera Original"],
            servico="seguranca",
            status="ativo",
        )

        update_data = {
            "id": str(implantacao.id),
            "cr": self.estrutura.id,
            "sistema": "Sistema Atualizado",
            "implantacoes": ["Câmera Atualizada", "Sensor Novo"],
            "servico": "facilities",
            "status": "desmobilizado",
            "observacoes": "Observação atualizada",
        }

        response = self.client.put(
            self.url, data=json.dumps(update_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verificar se foi atualizado no banco
        implantacao.refresh_from_db()
        self.assertEqual(implantacao.sistema, "Sistema Atualizado")
        self.assertEqual(implantacao.status, "desmobilizado")

    def test_view_delete_record(self):
        """Teste de exclusão de registro via DELETE"""
        self.client.login(username="testuser", password="testpass123")

        implantacao = ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema para Deletar",
            implantacoes=["Câmera"],
            servico="seguranca",
            status="ativo",
        )

        delete_data = {"id": str(implantacao.id)}

        response = self.client.delete(
            self.url, data=json.dumps(delete_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verificar se foi deletado do banco
        with self.assertRaises(ImplantacoesOpsVista.DoesNotExist):
            ImplantacoesOpsVista.objects.get(id=implantacao.id)

    def test_view_filters(self):
        """Teste dos filtros da view"""
        self.client.login(username="testuser", password="testpass123")

        # Criar implantações com diferentes características
        ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Segurança",
            implantacoes=["Câmera 1"],
            servico="seguranca",
            status="ativo",
        )

        ImplantacoesOpsVista.objects.create(
            cr_id=self.estrutura.id,
            sistema="Sistema Facilities",
            implantacoes=["Sensor 1"],
            servico="facilities",
            status="desmobilizado",
        )

        # Testar filtro por serviço
        response = self.client.get(f"{self.url}?servico=seguranca")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sistema Segurança")
        self.assertNotContains(response, "Sistema Facilities")

        # Testar filtro por status
        response = self.client.get(f"{self.url}?status=ativo")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sistema Segurança")
        self.assertNotContains(response, "Sistema Facilities")


@pytest.mark.integration
class ImplantacoesOpsVistaIntegrationTest(TestCase):
    """Testes de integração para ImplantacoesOpsVista"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", role="admin"
        )
        self.estrutura = Estrutura.objects.create(
            id="test-estrutura-123",
            descricao="CR Teste Integração",
        )

    def test_complete_crud_workflow(self):
        """Teste do fluxo completo CRUD"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("gestao_a_vista:implantacoes_opsvista")

        # 1. Criar registro
        create_data = {
            "cr": self.estrutura.id,
            "sistema": "Sistema Workflow",
            "implantacoes": ["Câmera Workflow", "Sensor Workflow"],
            "servico": "seguranca",
            "status": "ativo",
            "observacoes": "Teste de workflow completo",
        }

        response = self.client.post(
            url, data=json.dumps(create_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # Obter ID do registro criado
        data = json.loads(response.content)
        record_id = data["data"]["id"]

        # 2. Ler registro
        response = self.client.get(f"{url}?id={record_id}")
        self.assertEqual(response.status_code, 200)

        # 3. Atualizar registro
        update_data = {
            "id": record_id,
            "cr": self.estrutura.id,
            "sistema": "Sistema Workflow Atualizado",
            "implantacoes": ["Câmera Atualizada"],
            "servico": "facilities",
            "status": "desmobilizado",
            "observacoes": "Atualizado no workflow",
        }

        response = self.client.put(
            url, data=json.dumps(update_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # 4. Verificar atualização
        implantacao = ImplantacoesOpsVista.objects.get(id=record_id)
        self.assertEqual(implantacao.sistema, "Sistema Workflow Atualizado")
        self.assertEqual(implantacao.servico, "facilities")

        # 5. Deletar registro
        delete_data = {"id": record_id}
        response = self.client.delete(
            url, data=json.dumps(delete_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # 6. Verificar exclusão
        with self.assertRaises(ImplantacoesOpsVista.DoesNotExist):
            ImplantacoesOpsVista.objects.get(id=record_id)
