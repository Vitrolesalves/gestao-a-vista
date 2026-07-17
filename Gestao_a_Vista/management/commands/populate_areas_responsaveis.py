from django.core.management.base import BaseCommand

from Gestao_a_Vista.models import AreaResponsavel


class Command(BaseCommand):
    help = "Popula a tabela de áreas responsáveis com dados iniciais"

    def handle(self, *args, **options):
        areas = [
            {"nome": "TI - Tecnologia da Informação", "ordem": 1},
            {"nome": "RH - Recursos Humanos", "ordem": 2},
            {"nome": "Financeiro", "ordem": 3},
            {"nome": "Operações", "ordem": 4},
            {"nome": "Comercial", "ordem": 5},
            {"nome": "Jurídico", "ordem": 6},
            {"nome": "Manutenção", "ordem": 7},
            {"nome": "Segurança", "ordem": 8},
            {"nome": "Administração", "ordem": 9},
            {"nome": "Logística", "ordem": 10},
            {"nome": "Facilities", "ordem": 11},
            {"nome": "Qualidade", "ordem": 12},
            {"nome": "Marketing", "ordem": 13},
            {"nome": "Compras", "ordem": 14},
            {"nome": "Contabilidade", "ordem": 15},
        ]

        for area_data in areas:
            area, created = AreaResponsavel.objects.get_or_create(
                nome=area_data["nome"], defaults={"ordem": area_data["ordem"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Área criada: {area.nome}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Área já existe: {area.nome}"))

        total_areas = AreaResponsavel.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Total de áreas no banco: {total_areas}")
        )
