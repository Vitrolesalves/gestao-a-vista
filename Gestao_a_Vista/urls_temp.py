from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from . import views
from .decorators import check_page_permission
from .models import (GestaoSala, PlannerAttachment, PlannerComment,
                     PlannerProject, ShiftComplianceItem, ShiftEvidence,
                     ShiftRecord)
from .views import (CalendarioReservasView, GestaoSalasView, LivroAtaView,
                    PlannerView, ReservaSalasView, SalaCriarView,
                    SalaDeletarView, SalaEditarView, controle_acessos,
                    controle_chips, dashboard, desativacao_cr,
                    etiquetas_generator, monitoramento, portaria_base,
                    qr_generator, reserva_salas)

app_name = "gestao_a_vista"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("home/", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "dashboard/",
        check_page_permission("dashboard")(views.dashboard),
        name="dashboard",
    ),
    path(
        "monitoramento/",
        check_page_permission("monitoramento")(views.monitoramento),
        name="monitoramento",
    ),
    path(
        "monitoramento/atualizar/<str:tipo>/<int:item_id>/",
        check_page_permission("monitoramento")(views.atualizar_item),
        name="atualizar_item",
    ),
    path(
        "qr-generator/",
        check_page_permission("qr_generator")(views.qr_generator),
        name="qr_generator",
    ),
    path(
        "etiquetas/",
        check_page_permission("etiquetas_generator")(views.etiquetas_generator),
        name="etiquetas_generator",
    ),
    path("api/locations/", views.get_locations, name="get_locations"),
    path("api/service-logo/", views.get_service_logo, name="get_service_logo"),
    path("api/download-pdf/", views.download_qr_pdf, name="download_qr_pdf"),
    path("api/generate-qr/", views.generate_qr_code, name="generate_qr"),
    path("qr-generator/download/<str:qr_data>/", views.download_qr, name="download_qr"),
    path(
        "desativacao-cr/",
        check_page_permission("desativacao_cr")(views.desativacao_cr),
        name="desativacao_cr",
    ),
    path(
        "controle-chips/",
        check_page_permission("controle_chips")(views.controle_chips),
        name="controle_chips",
    ),
    path(
        "controle-acessos/",
        check_page_permission("controle_acessos")(views.controle_acessos),
        name="controle_acessos",
    ),
    path(
        "portaria-base/",
        check_page_permission("portaria_base")(views.portaria_base),
        name="portaria_base",
    ),
    path(
        "gestao-salas/",
        check_page_permission("gestao_salas")(GestaoSalasView.as_view()),
        name="gestao_salas",
    ),
    path(
        "gestao-salas/criar/",
        check_page_permission("gestao_salas")(SalaCriarView.as_view()),
        name="sala_criar",
    ),
    path(
        "gestao-salas/<int:pk>/editar/",
        check_page_permission("gestao_salas")(SalaEditarView.as_view()),
        name="sala_editar",
    ),
    path(
        "gestao-salas/<int:pk>/deletar/",
        check_page_permission("gestao_salas")(SalaDeletarView.as_view()),
        name="sala_deletar",
    ),
    path(
        "reserva-salas/",
        check_page_permission("reserva_salas")(ReservaSalasView.as_view()),
        name="reserva_salas",
    ),
    path(
        "calendario-reservas/",
        check_page_permission("calendario_reservas")(CalendarioReservasView.as_view()),
        name="calendario_reservas",
    ),
    path(
        "api/reservas/<int:reserva_id>/",
        check_page_permission("calendario_reservas")(CalendarioReservasView.as_view()),
        name="reserva_delete",
    ),
    path(
        "livro-ata/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        name="livro_ata",
    ),
    path(
        "api/livro-ata/shifts/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_shifts"},
        name="livro_ata_shifts",
    ),
    path(
        "api/livro-ata/shifts/<uuid:shift_id>/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_shift_details"},
        name="livro_ata_shift_details",
    ),
    path(
        "planner/",
        check_page_permission("planner")(PlannerView.as_view()),
        name="planner",
    ),
]
