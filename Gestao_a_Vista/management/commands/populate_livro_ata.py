from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Gestao_a_Vista.models import (ShiftComplianceItem, ShiftEvidence,
                                   ShiftRecord)


class Command(BaseCommand):
    help = "Popula dados de exemplo para o Livro ATA"

    def handle(self, *args, **options):
        self.stdout.write("Criando dados de exemplo para o Livro ATA...")

        # Criar alguns registros de plantão
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Plantão 1
        shift1 = ShiftRecord.objects.create(
            cr_number="CR-001",
            guard_name="João Silva",
            guard_number="12345",
            date=yesterday,
            time=time(8, 0),
            shift_type="Diurno",
            location="Prédio A - Entrada Principal",
            description="Plantão transcorreu normalmente. Realizadas todas as rondas conforme procedimento.",
        )

        # Plantão 2
        shift2 = ShiftRecord.objects.create(
            cr_number="CR-001",
            guard_name="Maria Santos",
            guard_number="54321",
            date=yesterday,
            time=time(20, 0),
            shift_type="Noturno",
            location="Prédio A - Entrada Principal",
            description="Ocorrência registrada: visitante tentou acessar o prédio fora do horário permitido. Orientado sobre os procedimentos.",
        )

        # Plantão 3
        shift3 = ShiftRecord.objects.create(
            cr_number="CR-002",
            guard_name="Carlos Oliveira",
            guard_number="67890",
            date=today,
            time=time(8, 0),
            shift_type="Diurno",
            location="Prédio B - Portaria",
            description="Plantão sem intercorrências. Todas as atividades realizadas conforme protocolo.",
        )

        # Criar itens de conformidade para o plantão 1
        compliance_items_1 = [
            (
                "Equipamentos de segurança funcionando",
                "conforme",
                "Todos os equipamentos testados e funcionando normalmente",
            ),
            (
                "Rondas realizadas nos horários corretos",
                "conforme",
                "Rondas realizadas conforme cronograma",
            ),
            ("Registro de visitantes atualizado", "conforme", ""),
            (
                "Área de emergência desobstruída",
                "nao_conforme",
                "Encontrada caixa bloqueando saída de emergência - removida",
            ),
            (
                "Câmeras de segurança operacionais",
                "conforme",
                "Sistema funcionando normalmente",
            ),
        ]

        for desc, status, obs in compliance_items_1:
            ShiftComplianceItem.objects.create(
                shift_record=shift1,
                item_description=desc,
                status=status,
                observations=obs,
            )

        # Criar itens de conformidade para o plantão 2
        compliance_items_2 = [
            ("Equipamentos de segurança funcionando", "conforme", ""),
            ("Rondas realizadas nos horários corretos", "conforme", ""),
            (
                "Registro de visitantes atualizado",
                "conforme",
                "Registrado tentativa de acesso fora do horário",
            ),
            ("Área de emergência desobstruída", "conforme", ""),
            (
                "Câmeras de segurança operacionais",
                "nao_conforme",
                "Câmera do 3º andar apresentou falha às 22h - reportado para manutenção",
            ),
            ("Iluminação externa funcionando", "conforme", ""),
        ]

        for desc, status, obs in compliance_items_2:
            ShiftComplianceItem.objects.create(
                shift_record=shift2,
                item_description=desc,
                status=status,
                observations=obs,
            )

        # Criar itens de conformidade para o plantão 3
        compliance_items_3 = [
            ("Equipamentos de segurança funcionando", "conforme", ""),
            ("Rondas realizadas nos horários corretos", "conforme", ""),
            ("Registro de visitantes atualizado", "conforme", ""),
            ("Área de emergência desobstruída", "conforme", ""),
            ("Câmeras de segurança operacionais", "conforme", ""),
            ("Iluminação externa funcionando", "conforme", ""),
            ("Portões e acessos seguros", "conforme", ""),
        ]

        for desc, status, obs in compliance_items_3:
            ShiftComplianceItem.objects.create(
                shift_record=shift3,
                item_description=desc,
                status=status,
                observations=obs,
            )

        self.stdout.write(self.style.SUCCESS(f"Criados com sucesso:"))
        self.stdout.write(f"- {ShiftRecord.objects.count()} registros de plantão")
        self.stdout.write(
            f"- {ShiftComplianceItem.objects.count()} itens de conformidade"
        )
        self.stdout.write(f"- {ShiftEvidence.objects.count()} evidências")

        self.stdout.write(self.style.SUCCESS("Dados de exemplo criados com sucesso!"))
