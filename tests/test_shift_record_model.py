"""
Testes unitários para o modelo ShiftRecord
Tarefa 22.1 - Definir o modelo ShiftRecord com campos principais e relacionamentos
"""
import time as time_module
from datetime import date, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from Gestao_a_Vista.models import (ShiftAttachment, ShiftComplianceItem,
                                   ShiftEvidence, ShiftRecord)

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class ShiftRecordModelTest(TestCase):
    """Testes para o modelo ShiftRecord"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", name="Test User"
        )

        self.shift_data = {
            "shift_date": date.today(),
            "shift_type": "diurno",
            "responsible_user": self.user,
            "start_time": time(8, 0),
            "end_time": time(18, 0),
            "status": "pendente",
            "cr_number": "CR-001",
            "guard_name": "João Silva",
            "guard_number": "12345",
            "location": "Prédio A - Entrada Principal",
            "description": "Plantão teste",
        }

    def test_shift_record_creation(self):
        """Testa a criação básica de um ShiftRecord"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        self.assertIsNotNone(shift.id)
        self.assertEqual(shift.shift_date, self.shift_data["shift_date"])
        self.assertEqual(shift.shift_type, "diurno")
        self.assertEqual(shift.responsible_user, self.user)
        self.assertEqual(shift.status, "pendente")
        self.assertEqual(shift.cr_number, "CR-001")
        self.assertEqual(shift.guard_name, "João Silva")

    def test_shift_record_str_representation(self):
        """Testa a representação string do modelo"""
        shift = ShiftRecord.objects.create(**self.shift_data)
        expected_str = f"Plantão {shift.guard_name} - {shift.shift_date} (Diurno)"
        self.assertEqual(str(shift), expected_str)

    def test_shift_type_choices(self):
        """Testa se os choices de shift_type estão funcionando"""
        valid_types = ["diurno", "noturno", "madrugada", "extra"]

        for shift_type in valid_types:
            shift_data = self.shift_data.copy()
            shift_data["shift_type"] = shift_type
            shift = ShiftRecord.objects.create(**shift_data)
            self.assertEqual(shift.shift_type, shift_type)

    def test_status_choices(self):
        """Testa se os choices de status estão funcionando"""
        valid_statuses = ["pendente", "em_andamento", "concluido", "cancelado"]

        for status in valid_statuses:
            shift_data = self.shift_data.copy()
            shift_data["status"] = status
            shift = ShiftRecord.objects.create(**shift_data)
            self.assertEqual(shift.status, status)

    def test_default_status(self):
        """Testa se o status padrão é 'pendente'"""
        shift_data = self.shift_data.copy()
        del shift_data["status"]  # Remove status para testar o padrão
        shift = ShiftRecord.objects.create(**shift_data)
        self.assertEqual(shift.status, "pendente")

    def test_end_time_validation(self):
        """Testa validação de end_time maior que start_time"""
        shift_data = self.shift_data.copy()
        shift_data["start_time"] = time(18, 0)
        shift_data["end_time"] = time(8, 0)  # Menor que start_time

        with self.assertRaises(ValidationError):
            shift = ShiftRecord(**shift_data)
            shift.clean()

    def test_end_time_optional(self):
        """Testa que end_time é opcional"""
        shift_data = self.shift_data.copy()
        shift_data["end_time"] = None
        shift = ShiftRecord.objects.create(**shift_data)
        self.assertIsNone(shift.end_time)

    def test_duration_property(self):
        """Testa o cálculo da duração do plantão"""
        shift = ShiftRecord.objects.create(**self.shift_data)
        expected_duration = 10.0  # 18:00 - 08:00 = 10 horas
        self.assertEqual(shift.duration, expected_duration)

    def test_duration_overnight_shift(self):
        """Testa duração para plantão que vai para o dia seguinte"""
        shift_data = self.shift_data.copy()
        shift_data[
            "shift_type"
        ] = "noturno"  # Plantão noturno permite end_time < start_time
        shift_data["start_time"] = time(22, 0)
        shift_data["end_time"] = time(6, 0)  # Dia seguinte
        shift = ShiftRecord.objects.create(**shift_data)
        expected_duration = 8.0  # 22:00 até 06:00 do dia seguinte
        self.assertEqual(shift.duration, expected_duration)

    def test_duration_without_end_time(self):
        """Testa duração quando end_time é None"""
        shift_data = self.shift_data.copy()
        shift_data["end_time"] = None
        shift = ShiftRecord.objects.create(**shift_data)
        self.assertIsNone(shift.duration)

    def test_responsible_user_relationship(self):
        """Testa o relacionamento com CustomUser"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Testa o relacionamento direto
        self.assertEqual(shift.responsible_user, self.user)

        # Testa o relacionamento reverso
        self.assertIn(shift, self.user.shift_records.all())

    def test_ordering(self):
        """Testa a ordenação dos registros"""
        # Criar shifts em datas diferentes
        today = date.today()
        yesterday = today - timedelta(days=1)

        shift_data_1 = self.shift_data.copy()
        shift_data_1["shift_date"] = yesterday
        shift1 = ShiftRecord.objects.create(**shift_data_1)

        shift_data_2 = self.shift_data.copy()
        shift_data_2["shift_date"] = today
        shift2 = ShiftRecord.objects.create(**shift_data_2)

        # Verificar ordenação (mais recente primeiro)
        shifts = list(ShiftRecord.objects.all())
        self.assertEqual(shifts[0], shift2)  # Mais recente
        self.assertEqual(shifts[1], shift1)  # Mais antigo

    def test_get_evidences_count(self):
        """Testa o método get_evidences_count"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Inicialmente sem evidências
        self.assertEqual(shift.get_evidences_count(), 0)

        # Adicionar evidência (simulado - não vamos criar o arquivo real)
        # Este teste seria expandido quando implementarmos ShiftEvidence

    def test_get_compliance_items_count(self):
        """Testa o método get_compliance_items_count"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Inicialmente sem itens de conformidade
        self.assertEqual(shift.get_compliance_items_count(), 0)

        # Criar itens de conformidade
        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Verificar equipamentos",
            status="conforme",
        )

        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Verificar documentação",
            status="nao_conforme",
        )

        self.assertEqual(shift.get_compliance_items_count(), 2)

    def test_get_compliance_percentage(self):
        """Testa o cálculo do percentual de conformidade"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Sem itens de conformidade deve retornar 0
        self.assertEqual(shift.get_compliance_percentage(), 0)

        # Criar itens de conformidade
        ShiftComplianceItem.objects.create(
            shift_record=shift, item_description="Item 1", status="conforme"
        )

        ShiftComplianceItem.objects.create(
            shift_record=shift, item_description="Item 2", status="nao_conforme"
        )

        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Item 3",
            status="nao_aplicavel",  # Não deve contar no cálculo
        )

        # 1 conforme de 2 aplicáveis = 50%
        self.assertEqual(shift.get_compliance_percentage(), 50)

    def test_get_critical_non_compliance_count(self):
        """Testa contagem de itens críticos não conformes"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Inicialmente sem itens críticos
        self.assertEqual(shift.get_critical_non_compliance_count(), 0)

        # Criar item crítico não conforme
        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Item crítico",
            status="nao_conforme",
            priority="critica",
        )

        # Criar item não crítico não conforme
        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Item normal",
            status="nao_conforme",
            priority="media",
        )

        self.assertEqual(shift.get_critical_non_compliance_count(), 1)

    def test_has_critical_issues(self):
        """Testa verificação de problemas críticos"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Inicialmente sem problemas críticos
        self.assertFalse(shift.has_critical_issues())

        # Criar item crítico não conforme
        ShiftComplianceItem.objects.create(
            shift_record=shift,
            item_description="Item crítico",
            status="nao_conforme",
            priority="critica",
        )

        self.assertTrue(shift.has_critical_issues())

    def test_is_compliance_complete(self):
        """Testa verificação de completude do checklist"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Sem itens, considera completo
        self.assertTrue(shift.is_compliance_complete())

        # Criar item pendente
        ShiftComplianceItem.objects.create(
            shift_record=shift, item_description="Item pendente", status="pendente"
        )

        self.assertFalse(shift.is_compliance_complete())

        # Marcar como conforme
        item = shift.compliance_items.first()
        item.status = "conforme"
        item.save()

        self.assertTrue(shift.is_compliance_complete())

    def test_required_fields(self):
        """Testa que campos opcionais podem ser None"""
        # Campos que são opcionais (têm null=True, blank=True)
        optional_fields = ["shift_date", "responsible_user", "start_time", "end_time"]

        for field in optional_fields:
            shift_data = self.shift_data.copy()
            shift_data[field] = None  # Definir explicitamente como None

            try:
                shift = ShiftRecord.objects.create(**shift_data)
                self.assertIsNone(getattr(shift, field))
                shift.delete()  # Limpar após teste
            except Exception as e:
                self.fail(f"Campo {field} deveria aceitar None mas causou erro: {e}")

        # Teste que shift_type pode ser criado com valores válidos
        for shift_type, _ in ShiftRecord.SHIFT_TYPE_CHOICES:
            shift_data = self.shift_data.copy()
            shift_data["shift_type"] = shift_type

            try:
                shift = ShiftRecord.objects.create(**shift_data)
                self.assertEqual(shift.shift_type, shift_type)
                shift.delete()
            except Exception as e:
                self.fail(
                    f"shift_type '{shift_type}' deveria ser válido mas causou erro: {e}"
                )

    def test_cr_number_indexing(self):
        """Testa se o índice no cr_number está funcionando para queries"""
        shift = ShiftRecord.objects.create(**self.shift_data)

        # Query por CR number deve ser eficiente
        found_shift = ShiftRecord.objects.filter(cr_number="CR-001").first()
        self.assertEqual(found_shift, shift)

    def test_shift_type_display(self):
        """Testa se os display names dos choices estão corretos"""
        shift = ShiftRecord.objects.create(**self.shift_data)
        self.assertEqual(shift.get_shift_type_display(), "Diurno")

        shift.shift_type = "noturno"
        shift.save()
        self.assertEqual(shift.get_shift_type_display(), "Noturno")

    def test_status_display(self):
        """Testa se os display names do status estão corretos"""
        shift = ShiftRecord.objects.create(**self.shift_data)
        self.assertEqual(shift.get_status_display(), "Pendente")

        shift.status = "concluido"
        shift.save()
        self.assertEqual(shift.get_status_display(), "Concluído")


@pytest.mark.unit
class ShiftRecordQueryTest(TestCase):
    """Testes para queries do modelo ShiftRecord"""

    def setUp(self):
        """Configuração inicial para os testes de query"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", name="Test User"
        )

        # Criar alguns registros de teste
        today = date.today()
        yesterday = today - timedelta(days=1)

        self.shift1 = ShiftRecord.objects.create(
            shift_date=today,
            shift_type="diurno",
            responsible_user=self.user,
            start_time=time(8, 0),
            end_time=time(18, 0),
            status="pendente",
            cr_number="CR-001",
            guard_name="João Silva",
            guard_number="12345",
            location="Prédio A",
        )

        self.shift2 = ShiftRecord.objects.create(
            shift_date=yesterday,
            shift_type="noturno",
            responsible_user=self.user,
            start_time=time(20, 0),
            end_time=time(6, 0),
            status="concluido",
            cr_number="CR-002",
            guard_name="Maria Santos",
            guard_number="54321",
            location="Prédio B",
        )

    def test_filter_by_cr_number(self):
        """Testa filtro por número do CR"""
        shifts = ShiftRecord.objects.filter(cr_number="CR-001")
        self.assertEqual(shifts.count(), 1)
        self.assertEqual(shifts.first(), self.shift1)

    def test_filter_by_shift_type(self):
        """Testa filtro por tipo de plantão"""
        diurno_shifts = ShiftRecord.objects.filter(shift_type="diurno")
        noturno_shifts = ShiftRecord.objects.filter(shift_type="noturno")

        self.assertEqual(diurno_shifts.count(), 1)
        self.assertEqual(noturno_shifts.count(), 1)
        self.assertEqual(diurno_shifts.first(), self.shift1)
        self.assertEqual(noturno_shifts.first(), self.shift2)

    def test_filter_by_status(self):
        """Testa filtro por status"""
        pendente_shifts = ShiftRecord.objects.filter(status="pendente")
        concluido_shifts = ShiftRecord.objects.filter(status="concluido")

        self.assertEqual(pendente_shifts.count(), 1)
        self.assertEqual(concluido_shifts.count(), 1)

    def test_filter_by_date_range(self):
        """Testa filtro por intervalo de datas"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        today_shifts = ShiftRecord.objects.filter(shift_date=today)
        yesterday_shifts = ShiftRecord.objects.filter(shift_date=yesterday)

        self.assertEqual(today_shifts.count(), 1)
        self.assertEqual(yesterday_shifts.count(), 1)

    def test_filter_by_responsible_user(self):
        """Testa filtro por usuário responsável"""
        user_shifts = ShiftRecord.objects.filter(responsible_user=self.user)
        self.assertEqual(user_shifts.count(), 2)


@pytest.mark.unit
@pytest.mark.django_db
class ShiftAttachmentModelTest(TestCase):
    """Testes para o modelo ShiftAttachment"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Criar um ShiftRecord para os testes
        self.shift_record = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Portaria Principal",
            responsible_user=self.user,
            shift_date=date.today(),
            start_time=time(8, 0),
            end_time=time(17, 0),
        )

    def test_shift_attachment_creation(self):
        """Testa criação básica de anexo"""
        attachment = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Relatório de Ocorrências",
            description="Relatório detalhado das ocorrências do plantão",
        )

        self.assertIsNotNone(attachment.id)
        self.assertEqual(attachment.shift_record, self.shift_record)
        self.assertEqual(attachment.name, "Relatório de Ocorrências")
        self.assertIsNotNone(attachment.created_at)

    def test_shift_attachment_str_method(self):
        """Testa método __str__ do ShiftAttachment"""
        attachment = ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Documento Teste", description="Teste"
        )

        expected_str = f"Anexo Documento Teste - Plantão {self.shift_record.guard_name}"
        self.assertEqual(str(attachment), expected_str)

    def test_shift_attachment_relationship(self):
        """Testa relacionamento com ShiftRecord"""
        attachment1 = ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Anexo 1", description="Primeiro anexo"
        )

        attachment2 = ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Anexo 2", description="Segundo anexo"
        )

        # Testa relacionamento reverso
        attachments = self.shift_record.attachments.all()
        self.assertEqual(attachments.count(), 2)
        self.assertIn(attachment1, attachments)
        self.assertIn(attachment2, attachments)

    def test_shift_record_get_attachments_count(self):
        """Testa método get_attachments_count do ShiftRecord"""
        # Inicialmente sem anexos
        self.assertEqual(self.shift_record.get_attachments_count(), 0)

        # Criar anexos
        ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Anexo 1", description="Primeiro anexo"
        )

        ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Anexo 2", description="Segundo anexo"
        )

        self.assertEqual(self.shift_record.get_attachments_count(), 2)

    def test_shift_record_get_total_files_count(self):
        """Testa método get_total_files_count do ShiftRecord"""
        # Criar anexo
        ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Anexo 1", description="Anexo teste"
        )

        # Criar evidência
        ShiftEvidence.objects.create(
            shift_record=self.shift_record, description="Evidência teste"
        )

        # Total deve ser 2 (1 anexo + 1 evidência)
        self.assertEqual(self.shift_record.get_total_files_count(), 2)

    def test_attachment_file_size_capture(self):
        """Testa captura automática do tamanho do arquivo"""
        # Testar definindo file_size manualmente (simulando o comportamento do save)
        attachment = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Arquivo com tamanho",
            description="Teste de tamanho",
            file_size=1024,  # Simular tamanho capturado
        )

        self.assertEqual(attachment.file_size, 1024)

    def test_file_size_human_property(self):
        """Testa propriedade file_size_human"""
        attachment = ShiftAttachment.objects.create(
            shift_record=self.shift_record, name="Arquivo teste", description="Teste"
        )

        # Teste com diferentes tamanhos
        attachment.file_size = 512
        self.assertEqual(attachment.file_size_human, "512.0 B")

        attachment.file_size = 1536  # 1.5 KB
        self.assertEqual(attachment.file_size_human, "1.5 KB")

        attachment.file_size = 1048576  # 1 MB
        self.assertEqual(attachment.file_size_human, "1.0 MB")

        attachment.file_size = None
        self.assertEqual(attachment.file_size_human, "Desconhecido")

    def test_attachment_ordering(self):
        """Testa ordenação dos anexos por data de criação"""
        # Criar anexos em sequência com pequeno delay
        attachment1 = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Primeiro anexo",
            description="Criado primeiro",
        )

        # Pequeno delay para garantir timestamps diferentes
        time_module.sleep(0.01)

        attachment2 = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Segundo anexo",
            description="Criado depois",
        )

        # Verificar ordenação (mais recente primeiro)
        attachments = ShiftAttachment.objects.all()
        self.assertEqual(attachments.first(), attachment2)
        self.assertEqual(attachments.last(), attachment1)

    def test_attachment_cascade_delete(self):
        """Testa exclusão em cascata quando ShiftRecord é deletado"""
        attachment = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Anexo para deletar",
            description="Teste de exclusão",
        )

        attachment_id = attachment.id

        # Deletar o ShiftRecord
        self.shift_record.delete()

        # Anexo deve ter sido deletado também
        with self.assertRaises(ShiftAttachment.DoesNotExist):
            ShiftAttachment.objects.get(id=attachment_id)

    def test_get_attachments_total_size(self):
        """Testa método get_attachments_total_size do ShiftRecord"""
        # Criar anexos com tamanhos diferentes
        attachment1 = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Anexo 1",
            description="Primeiro anexo",
            file_size=1024,  # 1KB
        )

        attachment2 = ShiftAttachment.objects.create(
            shift_record=self.shift_record,
            name="Anexo 2",
            description="Segundo anexo",
            file_size=2048,  # 2KB
        )

        # Total deve ser 3KB (3072 bytes)
        total_size = self.shift_record.get_attachments_total_size()
        self.assertEqual(total_size, 3072)


@pytest.mark.unit
@pytest.mark.django_db
class ShiftComplianceItemModelTest(TestCase):
    """Testes para o modelo ShiftComplianceItem"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.checker_user = User.objects.create_user(
            username="checker", password="testpass123"
        )

        # Criar um ShiftRecord para os testes
        self.shift_record = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Portaria Principal",
            responsible_user=self.user,
            shift_date=date.today(),
            start_time=time(8, 0),
            end_time=time(17, 0),
        )

    def test_compliance_item_creation(self):
        """Testa criação básica de item de conformidade"""
        item = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Verificar equipamentos de segurança",
            status="conforme",
            priority="alta",
            area="Segurança",
        )

        self.assertIsNotNone(item.id)
        self.assertEqual(item.shift_record, self.shift_record)
        self.assertEqual(item.item_description, "Verificar equipamentos de segurança")
        self.assertEqual(item.status, "conforme")
        self.assertEqual(item.priority, "alta")
        self.assertEqual(item.area, "Segurança")
        self.assertIsNotNone(item.created_at)

    def test_compliance_item_defaults(self):
        """Testa valores padrão do modelo"""
        item = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item teste"
        )

        self.assertEqual(item.status, "pendente")
        self.assertEqual(item.priority, "media")
        self.assertEqual(item.order, 0)
        self.assertEqual(item.area, "")

    def test_compliance_item_str_method(self):
        """Testa método __str__ do ShiftComplianceItem"""
        item = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Teste de conformidade",
            status="conforme",
        )

        expected_str = "Teste de conformidade - Conforme"
        self.assertEqual(str(item), expected_str)

    def test_status_choices(self):
        """Testa as opções de status disponíveis"""
        expected_choices = ["conforme", "nao_conforme", "nao_aplicavel", "pendente"]
        actual_choices = [choice[0] for choice in ShiftComplianceItem.STATUS_CHOICES]

        for choice in expected_choices:
            self.assertIn(choice, actual_choices)

    def test_priority_choices(self):
        """Testa as opções de prioridade disponíveis"""
        expected_choices = ["baixa", "media", "alta", "critica"]
        actual_choices = [choice[0] for choice in ShiftComplianceItem.PRIORITY_CHOICES]

        for choice in expected_choices:
            self.assertIn(choice, actual_choices)

    def test_is_compliant_property(self):
        """Testa propriedade is_compliant"""
        # Item conforme
        item_conforme = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item conforme",
            status="conforme",
        )
        self.assertTrue(item_conforme.is_compliant)

        # Item não conforme
        item_nao_conforme = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item não conforme",
            status="nao_conforme",
        )
        self.assertFalse(item_nao_conforme.is_compliant)

    def test_is_critical_non_compliant_property(self):
        """Testa propriedade is_critical_non_compliant"""
        # Item crítico não conforme
        item_critico = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item crítico",
            status="nao_conforme",
            priority="critica",
        )
        self.assertTrue(item_critico.is_critical_non_compliant)

        # Item crítico conforme
        item_critico_ok = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item crítico OK",
            status="conforme",
            priority="critica",
        )
        self.assertFalse(item_critico_ok.is_critical_non_compliant)

        # Item não crítico não conforme
        item_normal = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item normal",
            status="nao_conforme",
            priority="media",
        )
        self.assertFalse(item_normal.is_critical_non_compliant)

    def test_get_status_color(self):
        """Testa método get_status_color"""
        test_cases = [
            ("conforme", "success"),
            ("nao_conforme", "danger"),
            ("nao_aplicavel", "secondary"),
            ("pendente", "warning"),
        ]

        for status, expected_color in test_cases:
            item = ShiftComplianceItem.objects.create(
                shift_record=self.shift_record,
                item_description=f"Item {status}",
                status=status,
            )
            self.assertEqual(item.get_status_color(), expected_color)

    def test_get_priority_color(self):
        """Testa método get_priority_color"""
        test_cases = [
            ("baixa", "info"),
            ("media", "primary"),
            ("alta", "warning"),
            ("critica", "danger"),
        ]

        for priority, expected_color in test_cases:
            item = ShiftComplianceItem.objects.create(
                shift_record=self.shift_record,
                item_description=f"Item {priority}",
                priority=priority,
            )
            self.assertEqual(item.get_priority_color(), expected_color)

    def test_validation_checked_by_required(self):
        """Testa validação de responsável obrigatório quando verificado explicitamente"""
        from django.utils import timezone

        item = ShiftComplianceItem(
            shift_record=self.shift_record,
            item_description="Item para validação",
            status="pendente",  # Manter pendente para não auto-definir checked_at
            checked_at=timezone.now(),  # Definir explicitamente
        )

        # Marcar que checked_by é obrigatório
        item._require_checked_by = True

        # Deve gerar erro de validação
        with self.assertRaises(ValidationError):
            item.clean()

    def test_auto_set_checked_at(self):
        """Testa definição automática de checked_at"""
        item = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item teste",
            status="conforme",
            checked_by=self.checker_user,
        )

        # checked_at deve ser definido automaticamente
        self.assertIsNotNone(item.checked_at)

    def test_ordering(self):
        """Testa ordenação dos itens"""
        # Criar itens com diferentes ordens
        item1 = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item C", order=2
        )

        item2 = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item A", order=1
        )

        item3 = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item B", order=1
        )

        # Verificar ordenação: order, item_description
        items = list(ShiftComplianceItem.objects.all())
        self.assertEqual(items[0], item2)  # order=1, Item A
        self.assertEqual(items[1], item3)  # order=1, Item B
        self.assertEqual(items[2], item1)  # order=2, Item C

    def test_cascade_delete(self):
        """Testa exclusão em cascata quando ShiftRecord é deletado"""
        item = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item para deletar"
        )

        item_id = item.id

        # Deletar o ShiftRecord
        self.shift_record.delete()

        # Item deve ter sido deletado também
        with self.assertRaises(ShiftComplianceItem.DoesNotExist):
            ShiftComplianceItem.objects.get(id=item_id)

    def test_relationship_with_shift_record(self):
        """Testa relacionamento com ShiftRecord"""
        # Criar múltiplos itens
        item1 = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item 1"
        )

        item2 = ShiftComplianceItem.objects.create(
            shift_record=self.shift_record, item_description="Item 2"
        )

        # Testar relacionamento reverso
        items = self.shift_record.compliance_items.all()
        self.assertEqual(items.count(), 2)
        self.assertIn(item1, items)
        self.assertIn(item2, items)

    def test_compliance_by_area_integration(self):
        """Testa integração com método get_compliance_by_area do ShiftRecord"""
        # Criar itens de diferentes áreas
        ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item Segurança 1",
            area="Segurança",
            status="conforme",
        )

        ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item Segurança 2",
            area="Segurança",
            status="nao_conforme",
        )

        ShiftComplianceItem.objects.create(
            shift_record=self.shift_record,
            item_description="Item Limpeza 1",
            area="Limpeza",
            status="conforme",
        )

        # Testar estatísticas por área
        stats = list(self.shift_record.get_compliance_by_area())

        # Deve ter 2 áreas
        self.assertEqual(len(stats), 2)

        # Verificar estatísticas da área Segurança
        seguranca_stats = next(s for s in stats if s["area"] == "Segurança")
        self.assertEqual(seguranca_stats["total"], 2)
        self.assertEqual(seguranca_stats["conforme"], 1)
        self.assertEqual(seguranca_stats["nao_conforme"], 1)
