"""
Testes para os modelos auxiliares do Livro ATA
"""
from datetime import date, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from Gestao_a_Vista.models import (ComplianceTemplate, EvidenceType,
                                   ShiftAttachment, ShiftCategory,
                                   ShiftComplianceItem, ShiftEvidence,
                                   ShiftLocation, ShiftRecord, ShiftTemplate)

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class ShiftTemplateModelTest(TestCase):
    """Testes para o modelo ShiftTemplate"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_shift_template_creation(self):
        """Testa criação básica de template de plantão"""
        template = ShiftTemplate.objects.create(
            nome="Template Diurno Padrão",
            shift_type="diurno",
            descricao="Template para plantões diurnos",
            observacoes_padrao="Verificar equipamentos no início do turno",
            duracao_estimada=timedelta(hours=8),
        )

        self.assertIsNotNone(template.id)
        self.assertEqual(template.nome, "Template Diurno Padrão")
        self.assertEqual(template.shift_type, "diurno")
        self.assertTrue(template.ativo)
        self.assertIsNotNone(template.created_at)

    def test_shift_template_str_method(self):
        """Testa método __str__ do ShiftTemplate"""
        template = ShiftTemplate.objects.create(
            nome="Template Noturno", shift_type="noturno"
        )

        expected_str = "Template Noturno (Noturno)"
        self.assertEqual(str(template), expected_str)

    def test_shift_template_unique_name(self):
        """Testa unicidade do nome do template"""
        ShiftTemplate.objects.create(nome="Template Único", shift_type="diurno")

        # Tentar criar outro com mesmo nome deve falhar
        with self.assertRaises(Exception):  # IntegrityError
            ShiftTemplate.objects.create(nome="Template Único", shift_type="noturno")

    def test_shift_template_ordering(self):
        """Testa ordenação dos templates"""
        template_b = ShiftTemplate.objects.create(
            nome="Template B", shift_type="diurno"
        )

        template_a = ShiftTemplate.objects.create(
            nome="Template A", shift_type="noturno"
        )

        templates = list(ShiftTemplate.objects.all())
        self.assertEqual(templates[0], template_a)
        self.assertEqual(templates[1], template_b)


@pytest.mark.unit
@pytest.mark.django_db
class ShiftLocationModelTest(TestCase):
    """Testes para o modelo ShiftLocation"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_shift_location_creation(self):
        """Testa criação básica de local de plantão"""
        location = ShiftLocation.objects.create(
            nome="Portaria Principal",
            codigo="PORT-01",
            endereco="Rua Principal, 123",
            responsavel=self.user,
            observacoes="Local de alta movimentação",
        )

        self.assertIsNotNone(location.id)
        self.assertEqual(location.nome, "Portaria Principal")
        self.assertEqual(location.codigo, "PORT-01")
        self.assertEqual(location.responsavel, self.user)
        self.assertTrue(location.ativo)

    def test_shift_location_str_method(self):
        """Testa método __str__ do ShiftLocation"""
        location = ShiftLocation.objects.create(nome="Recepção", codigo="REC-01")

        expected_str = "Recepção (REC-01)"
        self.assertEqual(str(location), expected_str)

    def test_shift_location_unique_constraints(self):
        """Testa restrições de unicidade"""
        ShiftLocation.objects.create(nome="Local Único", codigo="UNI-01")

        # Nome único
        with self.assertRaises(Exception):
            ShiftLocation.objects.create(nome="Local Único", codigo="UNI-02")

        # Código único
        with self.assertRaises(Exception):
            ShiftLocation.objects.create(nome="Outro Local", codigo="UNI-01")

    def test_get_active_shifts_count(self):
        """Testa contagem de plantões ativos no local"""
        location = ShiftLocation.objects.create(nome="Local Teste", codigo="TEST-01")

        # Inicialmente sem plantões
        self.assertEqual(location.get_active_shifts_count(), 0)

        # Criar plantão ativo
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
            location_ref=location,
            status="em_andamento",
        )

        self.assertEqual(location.get_active_shifts_count(), 1)

        # Finalizar plantão
        shift.status = "concluido"
        shift.save()

        self.assertEqual(location.get_active_shifts_count(), 0)


@pytest.mark.unit
@pytest.mark.django_db
class ShiftCategoryModelTest(TestCase):
    """Testes para o modelo ShiftCategory"""

    def test_shift_category_creation(self):
        """Testa criação básica de categoria de plantão"""
        category = ShiftCategory.objects.create(
            nome="Segurança",
            descricao="Plantões relacionados à segurança",
            cor="danger",
            icone="fas fa-shield-alt",
        )

        self.assertIsNotNone(category.id)
        self.assertEqual(category.nome, "Segurança")
        self.assertEqual(category.cor, "danger")
        self.assertEqual(category.icone, "fas fa-shield-alt")
        self.assertTrue(category.ativo)

    def test_shift_category_str_method(self):
        """Testa método __str__ do ShiftCategory"""
        category = ShiftCategory.objects.create(nome="Limpeza")

        self.assertEqual(str(category), "Limpeza")

    def test_shift_category_color_choices(self):
        """Testa opções de cor disponíveis"""
        expected_colors = [
            "primary",
            "secondary",
            "success",
            "danger",
            "warning",
            "info",
            "light",
            "dark",
        ]
        actual_colors = [choice[0] for choice in ShiftCategory.COLOR_CHOICES]

        for color in expected_colors:
            self.assertIn(color, actual_colors)

    def test_get_shifts_count(self):
        """Testa contagem de plantões na categoria"""
        category = ShiftCategory.objects.create(nome="Manutenção")

        # Inicialmente sem plantões
        self.assertEqual(category.get_shifts_count(), 0)

        # Criar plantão na categoria
        ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
            category=category,
        )

        self.assertEqual(category.get_shifts_count(), 1)


@pytest.mark.unit
@pytest.mark.django_db
class EvidenceTypeModelTest(TestCase):
    """Testes para o modelo EvidenceType"""

    def test_evidence_type_creation(self):
        """Testa criação básica de tipo de evidência"""
        evidence_type = EvidenceType.objects.create(
            nome="Foto do Local",
            descricao="Fotografias do local do plantão",
            obrigatorio=True,
            aceita_multiplos=True,
            extensoes_permitidas="jpg,png,jpeg",
            tamanho_maximo_mb=5,
        )

        self.assertIsNotNone(evidence_type.id)
        self.assertEqual(evidence_type.nome, "Foto do Local")
        self.assertTrue(evidence_type.obrigatorio)
        self.assertTrue(evidence_type.aceita_multiplos)
        self.assertEqual(evidence_type.tamanho_maximo_mb, 5)

    def test_evidence_type_str_method(self):
        """Testa método __str__ do EvidenceType"""
        evidence_type = EvidenceType.objects.create(nome="Documento PDF")

        self.assertEqual(str(evidence_type), "Documento PDF")

    def test_get_extensions_list(self):
        """Testa método get_extensions_list"""
        evidence_type = EvidenceType.objects.create(
            nome="Imagens", extensoes_permitidas="jpg, png, gif, webp"
        )

        extensions = evidence_type.get_extensions_list()
        expected = ["jpg", "png", "gif", "webp"]
        self.assertEqual(extensions, expected)

        # Teste com campo vazio
        evidence_type_empty = EvidenceType.objects.create(nome="Qualquer Arquivo")
        self.assertEqual(evidence_type_empty.get_extensions_list(), [])

    def test_is_extension_allowed(self):
        """Testa método is_extension_allowed"""
        evidence_type = EvidenceType.objects.create(
            nome="Documentos", extensoes_permitidas="pdf,doc,docx"
        )

        # Extensões permitidas
        self.assertTrue(evidence_type.is_extension_allowed("documento.pdf"))
        self.assertTrue(evidence_type.is_extension_allowed("arquivo.DOC"))
        self.assertTrue(evidence_type.is_extension_allowed("texto.docx"))

        # Extensões não permitidas
        self.assertFalse(evidence_type.is_extension_allowed("imagem.jpg"))
        self.assertFalse(evidence_type.is_extension_allowed("planilha.xlsx"))

        # Sem extensão
        self.assertFalse(evidence_type.is_extension_allowed("arquivo_sem_extensao"))

        # Tipo sem restrições
        evidence_type_any = EvidenceType.objects.create(nome="Qualquer")
        self.assertTrue(evidence_type_any.is_extension_allowed("qualquer.arquivo"))


@pytest.mark.unit
@pytest.mark.django_db
class ComplianceTemplateModelTest(TestCase):
    """Testes para o modelo ComplianceTemplate"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_compliance_template_creation(self):
        """Testa criação básica de template de conformidade"""
        template = ComplianceTemplate.objects.create(
            nome="Checklist Segurança",
            area="Segurança",
            descricao="Template para verificações de segurança",
            shift_types="diurno,noturno",
            items_padrao=[
                {
                    "description": "Verificar equipamentos de segurança",
                    "priority": "alta",
                    "order": 1,
                },
                {"description": "Conferir fechaduras", "priority": "media", "order": 2},
            ],
        )

        self.assertIsNotNone(template.id)
        self.assertEqual(template.nome, "Checklist Segurança")
        self.assertEqual(template.area, "Segurança")
        self.assertEqual(len(template.items_padrao), 2)
        self.assertTrue(template.ativo)

    def test_compliance_template_str_method(self):
        """Testa método __str__ do ComplianceTemplate"""
        template = ComplianceTemplate.objects.create(
            nome="Template Limpeza", area="Limpeza"
        )

        expected_str = "Template Limpeza - Limpeza"
        self.assertEqual(str(template), expected_str)

    def test_get_shift_types_list(self):
        """Testa método get_shift_types_list"""
        template = ComplianceTemplate.objects.create(
            nome="Template Multi", area="Geral", shift_types="diurno, noturno, extra"
        )

        shift_types = template.get_shift_types_list()
        expected = ["diurno", "noturno", "extra"]
        self.assertEqual(shift_types, expected)

        # Template sem tipos específicos
        template_any = ComplianceTemplate.objects.create(
            nome="Template Geral", area="Geral"
        )
        self.assertEqual(template_any.get_shift_types_list(), [])

    def test_is_applicable_to_shift_type(self):
        """Testa método is_applicable_to_shift_type"""
        template = ComplianceTemplate.objects.create(
            nome="Template Específico", area="Teste", shift_types="diurno,noturno"
        )

        # Tipos aplicáveis
        self.assertTrue(template.is_applicable_to_shift_type("diurno"))
        self.assertTrue(template.is_applicable_to_shift_type("noturno"))

        # Tipos não aplicáveis
        self.assertFalse(template.is_applicable_to_shift_type("madrugada"))
        self.assertFalse(template.is_applicable_to_shift_type("extra"))

        # Template sem restrições
        template_any = ComplianceTemplate.objects.create(
            nome="Template Geral", area="Geral"
        )
        self.assertTrue(template_any.is_applicable_to_shift_type("qualquer"))

    def test_create_compliance_items_for_shift(self):
        """Testa criação de itens de conformidade para plantão"""
        template = ComplianceTemplate.objects.create(
            nome="Template Teste",
            area="Teste",
            items_padrao=[
                {"description": "Item 1", "priority": "alta", "order": 1},
                {"description": "Item 2", "priority": "media", "order": 2},
            ],
        )

        # Criar plantão
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
        )

        # Criar itens baseados no template
        items_created = template.create_compliance_items_for_shift(shift)

        self.assertEqual(len(items_created), 2)
        self.assertEqual(items_created[0].item_description, "Item 1")
        self.assertEqual(items_created[0].priority, "alta")
        self.assertEqual(items_created[0].area, "Teste")
        self.assertEqual(items_created[1].item_description, "Item 2")
        self.assertEqual(items_created[1].priority, "media")

        # Verificar se foram criados no banco
        compliance_items = shift.compliance_items.all()
        self.assertEqual(compliance_items.count(), 2)


@pytest.mark.unit
@pytest.mark.django_db
class AuxiliaryModelsIntegrationTest(TestCase):
    """Testes de integração entre modelos auxiliares e principais"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Criar modelos auxiliares
        self.template = ShiftTemplate.objects.create(
            nome="Template Integração", shift_type="diurno"
        )

        self.location = ShiftLocation.objects.create(
            nome="Local Integração", codigo="INT-01"
        )

        self.category = ShiftCategory.objects.create(nome="Categoria Integração")

        self.evidence_type = EvidenceType.objects.create(
            nome="Tipo Evidência Integração"
        )

    def test_shift_record_with_auxiliary_models(self):
        """Testa ShiftRecord com modelos auxiliares"""
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
            template=self.template,
            location_ref=self.location,
            category=self.category,
        )

        self.assertEqual(shift.template, self.template)
        self.assertEqual(shift.location_ref, self.location)
        self.assertEqual(shift.category, self.category)

        # Testar relacionamentos reversos
        self.assertIn(shift, self.template.shift_records.all())
        self.assertIn(shift, self.location.shift_records.all())
        self.assertIn(shift, self.category.shift_records.all())

    def test_evidence_with_type(self):
        """Testa ShiftEvidence com EvidenceType"""
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
        )

        # Criar evidência com tipo
        evidence = ShiftEvidence.objects.create(
            shift_record=shift,
            evidence_type=self.evidence_type,
            description="Evidência de teste",
        )

        self.assertEqual(evidence.evidence_type, self.evidence_type)
        self.assertIn(evidence, self.evidence_type.evidences.all())

    def test_attachment_with_type(self):
        """Testa ShiftAttachment com EvidenceType"""
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
        )

        # Criar anexo com tipo
        attachment = ShiftAttachment.objects.create(
            shift_record=shift,
            evidence_type=self.evidence_type,
            name="Documento Teste",
            description="Anexo de teste",
        )

        self.assertEqual(attachment.evidence_type, self.evidence_type)
        self.assertIn(attachment, self.evidence_type.attachments.all())

    def test_cascade_and_set_null_behavior(self):
        """Testa comportamento de exclusão em cascata e SET_NULL"""
        shift = ShiftRecord.objects.create(
            shift_type="diurno",
            cr_number="CR001",
            guard_name="João Silva",
            guard_number="12345",
            location="Local Teste",
            template=self.template,
            location_ref=self.location,
            category=self.category,
        )

        shift_id = shift.id

        # Deletar modelos auxiliares (SET_NULL)
        self.template.delete()
        self.location.delete()
        self.category.delete()

        # ShiftRecord deve continuar existindo
        shift.refresh_from_db()
        self.assertIsNone(shift.template)
        self.assertIsNone(shift.location_ref)
        self.assertIsNone(shift.category)

        # Deletar ShiftRecord deve funcionar normalmente
        shift.delete()

        with self.assertRaises(ShiftRecord.DoesNotExist):
            ShiftRecord.objects.get(id=shift_id)
