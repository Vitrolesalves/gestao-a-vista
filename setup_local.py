"""Prepara um ambiente local de avaliação do Gestão à Vista.

Uso:
    python setup_local.py

Roda os checks do Django, aplica as migrations no SQLite local (db.sqlite3)
e cria/atualiza um usuário administrador para navegar pelo sistema.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.core.management import call_command

    django.setup()

    print("Rodando os checks do Django...")
    call_command("check")

    print("Aplicando migrations no banco local...")
    call_command("migrate", interactive=False)

    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(username="admin")
    user.email = "admin@local.test"
    user.name = "Admin"
    user.role = "administrador"
    user.is_global_admin = True
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password("admin12345")
    user.save()

    action = "criado" if created else "atualizado"
    print(f"Admin local {action}: admin / admin12345")
    print("Suba o servidor com:")
    print("  python manage.py runserver")
    return 0


if __name__ == "__main__":
    sys.exit(main())
