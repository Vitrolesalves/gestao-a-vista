from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def check_page_permission(page_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("gestao_a_vista:login")

            if request.user.role == "administrador":
                return view_func(request, *args, **kwargs)

            if request.user.has_page_permission(page_name):
                return view_func(request, *args, **kwargs)

            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("gestao_a_vista:home")

        return _wrapped_view

    return decorator
