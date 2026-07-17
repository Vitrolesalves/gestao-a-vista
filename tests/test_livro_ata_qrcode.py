"""
Testes para funcionalidade de QR Code do Livro Ata
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from Gestao_a_Vista.models import LivroAtaQRCode

User = get_user_model()


@pytest.mark.unit
class LivroAtaQRCodeTest(TestCase):
    """Testes para o modelo LivroAtaQRCode"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_livro_ata_qrcode_creation(self):
        """Testa criação de QR Code do Livro Ata"""
        qr_code = LivroAtaQRCode.objects.create(
            cr_id='test-cr-001',
            cr_descricao='Centro de Teste',
        )
        
        self.assertIsNotNone(qr_code.id)
        self.assertEqual(qr_code.cr_id, 'test-cr-001')
        self.assertEqual(qr_code.cr_descricao, 'Centro de Teste')
        self.assertIn(str(qr_code.id), qr_code.qr_code_url)

    def test_qr_code_url_generation(self):
        """Testa geração automática da URL do QR Code"""
        qr_code = LivroAtaQRCode.objects.create(
            cr_id='test-cr-002',
            cr_descricao='Centro de Teste 2',
        )
        
        expected_url = f"https://gestao.example.com/livroata/qrcode={qr_code.id}"
        self.assertEqual(qr_code.qr_code_url, expected_url)

    def test_qr_code_data_property(self):
        """Testa propriedade qr_code_data"""
        qr_code = LivroAtaQRCode.objects.create(
            cr_id='test-cr-003',
            cr_descricao='Centro de Teste 3',
        )
        
        self.assertEqual(qr_code.qr_code_data, qr_code.qr_code_url)

    def test_str_method(self):
        """Testa método __str__ do modelo"""
        qr_code = LivroAtaQRCode.objects.create(
            cr_id='test-cr-004',
            cr_descricao='Centro de Teste 4',
        )
        
        expected_str = f"Livro Ata - test-cr-004 (Centro de Teste 4)"
        self.assertEqual(str(qr_code), expected_str)

    def test_unique_cr_id_constraint(self):
        """Testa constraint de CR único"""
        LivroAtaQRCode.objects.create(
            cr_id='test-cr-unique',
            cr_descricao='Centro Único',
        )
        
        # Tentar criar outro com mesmo CR deve falhar
        with self.assertRaises(Exception):
            LivroAtaQRCode.objects.create(
                cr_id='test-cr-unique',
                cr_descricao='Centro Duplicado',
            )


@pytest.mark.unit
class LivroAtaViewQRCodeTest(TestCase):
    """Testes para a view LivroAtaView com QR Code"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Criar QR Code de teste
        self.qr_code = LivroAtaQRCode.objects.create(
            cr_id='test-cr-view',
            cr_descricao='Centro de Teste View',
        )

    def test_livro_ata_view_with_qrcode_context(self):
        """Testa view com parâmetro qrcode no contexto"""
        url = reverse('gestao_a_vista:livro_ata_qrcode', args=[self.qr_code.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('qrcode_id', response.context)
        self.assertEqual(response.context['qrcode_id'], str(self.qr_code.id))

    @patch('Gestao_a_Vista.decorators.check_page_permission')
    def test_livro_ata_view_with_qrcode_get_param(self, mock_permission):
        """Testa view com parâmetro qrcode via GET"""
        # Mock do decorator de permissão para permitir acesso
        mock_permission.return_value = lambda func: func
        
        url = reverse('gestao_a_vista:livro_ata')
        response = self.client.get(url, {'qrcode': str(self.qr_code.id)})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('qrcode_id', response.context)
        self.assertEqual(response.context['qrcode_id'], str(self.qr_code.id))

    @patch('Gestao_a_Vista.decorators.check_page_permission')
    @patch('django.db.connections')
    def test_get_shifts_by_qrcode(self, mock_connections, mock_permission):
        """Testa busca de plantões por QR Code"""
        # Mock do decorator de permissão para permitir acesso
        mock_permission.return_value = lambda func: func
        
        # Mock da conexão e cursor
        mock_cursor = MagicMock()
        mock_connections.__getitem__.return_value.cursor.return_value = mock_cursor
        
        # Mock dos resultados da query (incluindo novas colunas: expirada e colaborador)
        mock_cursor.fetchall.return_value = [
            (
                'task-id-1',
                'LIVRO DE OCORRÊNCIA - DIURNO',
                'T001',
                '2023-01-01 08:00:00',
                '2023-01-01 16:00:00',
                'CR-001',
                False,  # expirada
                'Portaria Principal',
                'João Silva',  # colaborador
                'RELATE INFORMAÇÕES DO PLANTÃO:',
                'Plantão realizado sem intercorrências'
            )
        ]
        
        url = reverse('gestao_a_vista:livro_ata_shifts')
        response = self.client.get(url, {'qrcode': str(self.qr_code.id)})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('shifts', data)
        self.assertGreater(len(data['shifts']), 0)

    @patch('Gestao_a_Vista.decorators.check_page_permission')
    def test_get_shifts_qrcode_not_found(self, mock_permission):
        """Testa busca com QR Code inexistente"""
        # Mock do decorator de permissão para permitir acesso
        mock_permission.return_value = lambda func: func
        
        import uuid
        fake_qrcode_id = str(uuid.uuid4())
        
        url = reverse('gestao_a_vista:livro_ata_shifts')
        response = self.client.get(url, {'qrcode': fake_qrcode_id})
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'QR Code não encontrado')

    @patch('Gestao_a_Vista.decorators.check_page_permission')
    @patch('django.db.connections')
    def test_get_shift_details_from_dw_vista(self, mock_connections, mock_permission):
        """Testa busca de detalhes de plantão do DW_Vista"""
        # Mock do decorator de permissão para permitir acesso
        mock_permission.return_value = lambda func: func
        
        # Mock da conexão e cursor
        mock_cursor = MagicMock()
        mock_connections.__getitem__.return_value.cursor.return_value = mock_cursor
        
        # Mock dos resultados da query (incluindo novas colunas: expirada e colaborador)
        mock_cursor.fetchall.return_value = [
            (
                'task-id-1',
                'LIVRO DE OCORRÊNCIA - DIURNO',
                'T001',
                '2023-01-01 08:00:00',
                '2023-01-01 16:00:00',
                'CR-001',
                False,  # expirada
                'Portaria Principal',
                'João Silva',  # colaborador
                'RELATE INFORMAÇÕES DO PLANTÃO:',
                'Plantão realizado sem intercorrências'
            ),
            (
                'task-id-1',
                'LIVRO DE OCORRÊNCIA - DIURNO',
                'T001',
                '2023-01-01 08:00:00',
                '2023-01-01 16:00:00',
                'CR-001',
                False,  # expirada
                'Portaria Principal',
                'João Silva',  # colaborador
                'Iluminação adequada - Conforme?',
                'CONFORME'
            )
        ]
        
        import uuid
        task_id = str(uuid.uuid4())
        
        url = reverse('gestao_a_vista:livro_ata_shift_details', args=[task_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('shift', data)
        self.assertIn('evidences', data)
        self.assertIn('compliance_items', data)

    def test_process_task_details_shift_type_extraction(self):
        """Testa extração do tipo de plantão do nome da tarefa"""
        from Gestao_a_Vista.views import LivroAtaView
        
        view = LivroAtaView()
        
        task_info = {
            'id': 'task-1',
            'nome': 'LIVRO DE OCORRÊNCIA - NOTURNO',
            'numero': 'T001',
            'inicio': None,
            'terminoreal': None,
            'estruturaqrcode': 'CR-001',
            'estrutura_descricao': 'Portaria'
        }
        
        executions = []
        
        shift_data, evidences, compliance_items, occurrences = view.process_task_details(task_info, executions)
        
        self.assertEqual(shift_data['shift_type'], 'NOTURNO')

    def test_process_task_details_evidences_extraction(self):
        """Testa extração de evidências das execuções"""
        from Gestao_a_Vista.views import LivroAtaView
        
        view = LivroAtaView()
        
        task_info = {
            'id': 'task-1',
            'nome': 'LIVRO DE OCORRÊNCIA - DIURNO',
            'numero': 'T001',
            'inicio': None,
            'terminoreal': None,
            'estruturaqrcode': 'CR-001',
            'estrutura_descricao': 'Portaria'
        }
        
        executions = [
            {
                'pergunta': 'Foto da área',
                'conteudo': 'https://api.opsvista.example.com/api/armazenamento/foto1.jpg'
            }
        ]
        
        shift_data, evidences, compliance_items, occurrences = view.process_task_details(task_info, executions)
        
        self.assertEqual(len(evidences), 1)
        self.assertEqual(evidences[0]['image_url'], 'https://api.opsvista.example.com/api/armazenamento/foto1.jpg')

    def test_process_task_details_compliance_extraction(self):
        """Testa extração de itens de conformidade"""
        from Gestao_a_Vista.views import LivroAtaView
        
        view = LivroAtaView()
        
        task_info = {
            'id': 'task-1',
            'nome': 'LIVRO DE OCORRÊNCIA - DIURNO',
            'numero': 'T001',
            'inicio': None,
            'terminoreal': None,
            'estruturaqrcode': 'CR-001',
            'estrutura_descricao': 'Portaria'
        }
        
        executions = [
            {
                'pergunta': 'Iluminação adequada - Conforme?',
                'conteudo': 'CONFORME'
            },
            {
                'pergunta': 'Limpeza da área - Conforme?',
                'conteudo': 'NÃO CONFORME'
            },
            {
                'pergunta': 'Equipamentos funcionando - Conforme?',
                'conteudo': 'NÃO APLICÁVEL'
            }
        ]
        
        shift_data, evidences, compliance_items, occurrences = view.process_task_details(task_info, executions)
        
        # Deve ter apenas 2 itens (NÃO APLICÁVEL não é contabilizado)
        self.assertEqual(len(compliance_items), 2)
        
        # Verificar status
        conforme_item = next(item for item in compliance_items if 'Iluminação' in item['item_description'])
        nao_conforme_item = next(item for item in compliance_items if 'Limpeza' in item['item_description'])
        
        self.assertEqual(conforme_item['status'], 'conforme')
        self.assertEqual(nao_conforme_item['status'], 'nao_conforme')
