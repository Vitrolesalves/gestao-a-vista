from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from Gestao_a_Vista.models import CRKPI, GerenteKPI


class Command(BaseCommand):
    help = "Popula dados de teste para Torre de Controle"

    def handle(self, *args, **options):
        self.stdout.write("Criando dados de teste para Torre de Controle...")

        # Limpar dados existentes
        CRKPI.objects.all().delete()
        GerenteKPI.objects.all().delete()

        # Criar CRs KPI
        crs_data = [
            # JC Distribuição - Múltiplos CRs por serviço
            {
                "cr": "JC001-VIG",
                "cliente": "JC Distribuição LTDA",
                "gerente": "João Silva",
                "tipo_servico": "vigilancia",
                "performance_diurno": 69,
                "performance_noturno": 90,
                "performance_total": 79,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=5),
                "nps": Decimal("8.5"),
                "observacoes": "Melhoria necessária no período diurno",
            },
            {
                "cr": "JC002-FAC",
                "cliente": "JC Distribuição LTDA",
                "gerente": "João Silva",
                "tipo_servico": "facilities",
                "performance_total": 85,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=5),
                "nps": Decimal("8.3"),
            },
            {
                "cr": "JC003-MAN",
                "cliente": "JC Distribuição LTDA",
                "gerente": "João Silva",
                "tipo_servico": "manutencao",
                "performance_total": 78,
                "visita_operacional_concluida": False,
                "data_ultima_visita": date.today() - timedelta(days=10),
                "nps": Decimal("8.0"),
                "observacoes": "Atraso na manutenção preventiva",
            },
            # Central Supermercados - Múltiplos CRs
            {
                "cr": "SM001-VIG",
                "cliente": "Central Supermercados S.A.",
                "gerente": "Maria Santos",
                "tipo_servico": "vigilancia",
                "performance_diurno": 95,
                "performance_noturno": 88,
                "performance_total": 92,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=7),
                "nps": Decimal("9.2"),
            },
            {
                "cr": "SM002-FAC",
                "cliente": "Central Supermercados S.A.",
                "gerente": "Maria Santos",
                "tipo_servico": "facilities",
                "performance_total": 94,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=5),
                "nps": Decimal("9.0"),
            },
            {
                "cr": "SM003-LIM",
                "cliente": "Central Supermercados S.A.",
                "gerente": "Maria Santos",
                "tipo_servico": "limpeza",
                "performance_total": 96,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=3),
                "nps": Decimal("9.5"),
            },
            # ABC Indústrias
            {
                "cr": "IN001-VIG",
                "cliente": "ABC Indústrias LTDA",
                "gerente": "João Silva",
                "tipo_servico": "vigilancia",
                "performance_diurno": 78,
                "performance_noturno": 85,
                "performance_total": 82,
                "visita_operacional_concluida": False,
                "data_ultima_visita": date.today() - timedelta(days=30),
                "nps": Decimal("7.8"),
                "observacoes": "Visita operacional em atraso",
            },
            {
                "cr": "IN002-MAN",
                "cliente": "ABC Indústrias LTDA",
                "gerente": "João Silva",
                "tipo_servico": "manutencao",
                "performance_total": 92,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=12),
                "nps": Decimal("8.5"),
            },
            # Plaza Shopping Center
            {
                "cr": "SP001-VIG",
                "cliente": "Plaza Shopping Center",
                "gerente": "Carlos Oliveira",
                "tipo_servico": "vigilancia",
                "performance_diurno": 92,
                "performance_noturno": 94,
                "performance_total": 93,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=5),
                "nps": Decimal("8.9"),
            },
            {
                "cr": "SP002-FAC",
                "cliente": "Plaza Shopping Center",
                "gerente": "Carlos Oliveira",
                "tipo_servico": "facilities",
                "performance_total": 91,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=5),
                "nps": Decimal("9.1"),
            },
            {
                "cr": "SP003-LIM",
                "cliente": "Plaza Shopping Center",
                "gerente": "Carlos Oliveira",
                "tipo_servico": "limpeza",
                "performance_total": 89,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=6),
                "nps": Decimal("8.7"),
            },
            # Banco Seguro
            {
                "cr": "BS001-VIG",
                "cliente": "Banco Seguro S.A.",
                "gerente": "Maria Santos",
                "tipo_servico": "vigilancia",
                "performance_diurno": 88,
                "performance_noturno": 76,
                "performance_total": 83,
                "visita_operacional_concluida": False,
                "data_ultima_visita": date.today() - timedelta(days=12),
                "nps": Decimal("8.1"),
                "observacoes": "Performance noturna abaixo do esperado",
            },
            {
                "cr": "BS002-FAC",
                "cliente": "Banco Seguro S.A.",
                "gerente": "Maria Santos",
                "tipo_servico": "facilities",
                "performance_total": 87,
                "visita_operacional_concluida": True,
                "data_ultima_visita": date.today() - timedelta(days=9),
                "nps": Decimal("8.3"),
            },
        ]

        for cr_data in crs_data:
            CRKPI.objects.create(**cr_data)
            self.stdout.write(f"CR criado: {cr_data['cr']}")

        # Criar Gerentes KPI
        gerentes_data = [
            {
                "nome": "João Silva",
                "clientes": 2,
                "percentual_geral": Decimal("80.50"),
                "servicos_media_ronda": Decimal("80.50"),
                "servicos_media_facilities": Decimal("80.50"),
                "servicos_media_manutencao": Decimal("85.00"),
                "visitas_concluidas": 1,
                "visitas_total": 2,
                "nps_media": Decimal("8.15"),
            },
            {
                "nome": "Maria Santos",
                "clientes": 2,
                "percentual_geral": Decimal("87.50"),
                "servicos_media_ronda": Decimal("87.50"),
                "servicos_media_facilities": Decimal("90.50"),
                "servicos_media_manutencao": Decimal("87.00"),
                "visitas_concluidas": 1,
                "visitas_total": 2,
                "nps_media": Decimal("8.65"),
            },
            {
                "nome": "Carlos Oliveira",
                "clientes": 1,
                "percentual_geral": Decimal("91.00"),
                "servicos_media_ronda": Decimal("93.00"),
                "servicos_media_facilities": Decimal("91.00"),
                "servicos_media_manutencao": Decimal("88.00"),
                "visitas_concluidas": 1,
                "visitas_total": 1,
                "nps_media": Decimal("8.90"),
            },
        ]

        for gerente_data in gerentes_data:
            GerenteKPI.objects.create(**gerente_data)
            self.stdout.write(f"Gerente criado: {gerente_data['nome']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados de teste criados com sucesso! "
                f"{CRKPI.objects.count()} CRs e {GerenteKPI.objects.count()} gerentes."
            )
        )
