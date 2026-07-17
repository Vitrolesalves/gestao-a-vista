from django.apps import AppConfig

class GestaoAVistaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Gestao_a_Vista'

    def ready(self):
        # Importa os signals assim que o app iniciar
        import Gestao_a_Vista.signals

        # Remove constraints físicas de chaves estrangeiras cruzadas (multi-banco)
        # após as migrações serem concluídas, evitando consultas na inicialização do app.
        from django.db.models.signals import post_migrate
        post_migrate.connect(self.remove_cross_db_constraints, sender=self)

        # Registra o alias de banco de cada Regional já existente (em vez de
        # pré-criar estaticamente um banco por UF brasileira, usada ou não).
        self.register_regional_db_aliases()

    def register_regional_db_aliases(self):
        try:
            from .db_manager import ensure_db_alias_registered
            from .models import Regional
            for db_slug in Regional.objects.values_list('db_slug', flat=True):
                if not db_slug:
                    continue
                db_name = "db_teste" if db_slug == "go" else f"{db_slug}_gestao"
                ensure_db_alias_registered(f"db_{db_slug}", db_name)
        except Exception:
            # Tabela Regional ainda não existe (primeiro migrate) ou banco
            # indisponível neste momento do startup - sem problema, os
            # aliases também são registrados sob demanda quando usados.
            pass

    def remove_cross_db_constraints(self, **kwargs):
        try:
            from django.conf import settings
            from django.db import connections
            for db_alias in settings.DATABASES:
                if db_alias == 'dw_vpn':
                    continue
                try:
                    with connections[db_alias].cursor() as cursor:
                        cursor.execute(
                            'ALTER TABLE "Gestao_a_Vista_psicossocialprojeto" '
                            'DROP CONSTRAINT IF EXISTS "Gestao_a_Vista_psico_created_by_id_017130c4_fk_Gestao_a_";'
                        )
                except Exception:
                    pass
        except Exception:
            pass