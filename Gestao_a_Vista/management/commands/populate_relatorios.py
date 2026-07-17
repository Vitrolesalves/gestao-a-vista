from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Gestao_a_Vista.models import RelatorioItem


class Command(BaseCommand):
    help = "Popula dados de teste para Relatórios"

    def handle(self, *args, **options):
        self.stdout.write("Criando dados de teste para Relatórios...")

        # Limpar dados existentes
        RelatorioItem.objects.all().delete()

        # Criar relatórios de teste
        relatorios_data = [
            {
                "numero": "EPI-2024-001",
                "nome": "Inspeção EPI Equipe Alpha",
                "cr": "CR-001",
                "responsavel": "João Silva",
                "data": date(2024, 1, 15),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-001",
                "nome": "APR Viagem Salvador-BA",
                "cr": "CR-002",
                "responsavel": "Maria Santos",
                "data": date(2024, 1, 20),
                "tipo": "APR",
            },
            {
                "numero": "EPI-2024-002",
                "nome": "Inspeção EPI Setor Manutenção",
                "cr": "CR-003",
                "responsavel": "Carlos Oliveira",
                "data": date(2024, 1, 22),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-002",
                "nome": "APR Viagem São Paulo-SP",
                "cr": "CR-001",
                "responsavel": "Ana Costa",
                "data": date(2024, 1, 25),
                "tipo": "APR",
            },
            {
                "numero": "EPI-2024-003",
                "nome": "Inspeção EPI Equipe Beta",
                "cr": "CR-004",
                "responsavel": "Pedro Almeida",
                "data": date(2024, 1, 28),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-003",
                "nome": "APR Viagem Brasília-DF",
                "cr": "CR-002",
                "responsavel": "João Silva",
                "data": date(2024, 2, 1),
                "tipo": "APR",
            },
            {
                "numero": "EPI-2024-004",
                "nome": "Inspeção EPI Equipe Gamma",
                "cr": "CR-005",
                "responsavel": "Maria Santos",
                "data": date(2024, 2, 5),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-004",
                "nome": "APR Viagem Rio de Janeiro-RJ",
                "cr": "CR-003",
                "responsavel": "Carlos Oliveira",
                "data": date(2024, 2, 8),
                "tipo": "APR",
            },
            {
                "numero": "EPI-2024-005",
                "nome": "Inspeção EPI Setor Administrativo",
                "cr": "CR-001",
                "responsavel": "Ana Costa",
                "data": date(2024, 2, 12),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-005",
                "nome": "APR Viagem Belo Horizonte-MG",
                "cr": "CR-004",
                "responsavel": "Pedro Almeida",
                "data": date(2024, 2, 15),
                "tipo": "APR",
            },
            {
                "numero": "EPI-2024-006",
                "nome": "Inspeção EPI Equipe Delta",
                "cr": "CR-002",
                "responsavel": "João Silva",
                "data": date(2024, 2, 18),
                "tipo": "EPI",
            },
            {
                "numero": "APR-2024-006",
                "nome": "APR Viagem Recife-PE",
                "cr": "CR-005",
                "responsavel": "Maria Santos",
                "data": date(2024, 2, 22),
                "tipo": "APR",
            },
        ]

        for relatorio_data in relatorios_data:
            RelatorioItem.objects.create(**relatorio_data)
            self.stdout.write(f"Relatório criado: {relatorio_data['numero']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados de teste criados com sucesso! "
                f"{RelatorioItem.objects.count()} relatórios criados."
            )
        )
