"""
Cria/migra o banco de dados fisico de uma Regional ja cadastrada, usando o
db_slug dela. Util para provisionar (ou reprovisionar) o banco de uma
Regional que foi criada antes de ganhar um db_slug proprio (ex: uma segunda
Regional no mesmo estado, que so recebeu o slug via migration de backfill).

Uso:
  python manage.py provision_regional_db "VPA (São José dos Campos)"
  python manage.py provision_regional_db 005211a6-ff49-4038-9dc6-5339d515eea3
"""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from Gestao_a_Vista.db_manager import check_and_create_regional_db
from Gestao_a_Vista.models import Regional


class Command(BaseCommand):
    help = "Cria/migra o banco de dados fisico de uma Regional a partir do seu db_slug"

    def add_arguments(self, parser):
        parser.add_argument(
            'regional',
            help="Nome (Regional.nome) ou id (UUID) da Regional a provisionar",
        )

    def handle(self, *args, **options):
        identificador = options['regional']

        regional = None
        try:
            regional = Regional.objects.filter(id=identificador).first()
        except (ValueError, ValidationError):
            regional = None
        if not regional:
            regional = Regional.objects.filter(nome=identificador).first()

        if not regional:
            raise CommandError(f"Regional nao encontrada: '{identificador}'")

        if not regional.db_slug:
            raise CommandError(
                f"Regional '{regional.nome}' nao tem db_slug definido. "
                "Rode a migration 0055 antes."
            )

        self.stdout.write(f"Provisionando banco da regional '{regional.nome}' (db_slug='{regional.db_slug}')...")
        check_and_create_regional_db(regional.db_slug)
        self.stdout.write(self.style.SUCCESS(
            f"Banco da regional '{regional.nome}' provisionado e migrado com sucesso."
        ))
