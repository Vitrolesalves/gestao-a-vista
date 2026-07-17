from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.cache import cache


class UserOnlineStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # CORREÇÃO: Desabilitar temporariamente para debug do login
        # Este middleware pode estar causando lentidão no processo de login
        
        # TODO: Re-habilitar após resolver problema do TestSprite
        # try:
        #     if request.user.is_authenticated and hasattr(request.user, "is_online"):
        #         cache_key = f"user_online_{request.user.id}"
        #         last_update = cache.get(cache_key)
        #         
        #         if not last_update:
        #             User = get_user_model()
        #             if isinstance(request.user, User):
        #                 User.objects.filter(id=request.user.id).update(is_online=True)
        #                 cache.set(cache_key, now(), timeout=300)
        # except Exception as e:
        #     pass

        response = self.get_response(request)
        return response


class RegionalRoutingMiddleware:
    """
    Middleware para definir dinamicamente o banco de dados da thread atual
    baseado na regional do usuário logado ou na seleção do administrador supremo.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .thread_local import set_current_db, clear_current_db
        from .db_manager import ensure_db_alias_registered

        def activate(db_slug):
            db_slug = db_slug.strip().lower()
            db_name = "db_teste" if db_slug == "go" else f"{db_slug}_gestao"
            db_alias = f"db_{db_slug}"
            # Auto-registra o alias caso outro worker do uWSGI tenha criado
            # essa regional e este processo ainda não tenha ficado sabendo.
            ensure_db_alias_registered(db_alias, db_name)
            set_current_db(db_alias)

        if request.user.is_authenticated:
            # Se for o Administrador Supremo (is_global_admin=True)
            if getattr(request.user, 'is_global_admin', False):
                active_regional = request.session.get('active_regional')
                if active_regional:
                    activate(active_regional)
                else:
                    set_current_db("default")
            # Se for administrador/usuário de regional
            elif getattr(request.user, 'regional', None):
                db_slug = request.user.regional.db_slug or request.user.regional.estado
                if db_slug:
                    activate(db_slug)
                else:
                    set_current_db("default")
            else:
                set_current_db("default")
        else:
            set_current_db("default")

        try:
            response = self.get_response(request)
        finally:
            clear_current_db()

        return response
