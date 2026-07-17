from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path  # <-- Adicione o re_path aqui
from django.conf import settings       # <-- Adicione esta linha se não existir
from django.views.static import serve
from .views import AcaoPlanoEmailView
from .views import notificar_gerente_auditoria_ajax, resolver_auditoria_ajax

from . import views
from .decorators import check_page_permission
from .models import (GestaoSala, PlannerAttachment, PlannerComment,
                     PlannerProject, ShiftComplianceItem, ShiftEvidence,
                     ShiftRecord)
from .qr_code_service import generate_qr_code_improved

from django.urls import path
from .views import PainelReincidenciasView, AprovarReincidenciaView

from .views import GerarDadosTesteView # Importe a nova view lá em cima

# Importações das views
from .views import (CalendarioReservasView,
                    LivroOcorrenciasView, LivroOcorrenciasDetalheView,
                    GestaoSalasView, LivroAtaView, SelecionarUnidadeView,
                    PlannerView, ReservaSalasView, SalaCriarView,
                    SalaDeletarView, SalaEditarView,
                    controle_acessos, controle_chips, dashboard,
                    desativacao_cr, etiquetas_generator, monitoramento,
                    portaria_base, qr_generator,
                    UnidadeListView, UnidadeCriarView, UnidadeEditarView, UnidadeDeletarView)

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
        "financeiro/",
        check_page_permission("financeiro")(views.financeiro),
        name="financeiro",
    ),
    path(
        "financeiro/api/data/",
        check_page_permission("financeiro")(views.financeiro_api_data),
        name="financeiro_api_data",
    ),
    path(
        "financeiro/api/chat/",
        check_page_permission("financeiro")(views.financeiro_api_chat),
        name="financeiro_api_chat",
    ),
    path(
        "financeiro/api/email/",
        check_page_permission("financeiro")(views.financeiro_api_email),
        name="financeiro_api_email",
    ),
    path(
        "financeiro/api/upload/",
        check_page_permission("financeiro")(views.financeiro_api_upload),
        name="financeiro_api_upload",
    ),
    path(
        "financeiro/api/run-pipeline/",
        check_page_permission("financeiro")(views.financeiro_api_run_pipeline),
        name="financeiro_api_run_pipeline",
    ),
    path(
        "financeiro/api/clear/",
        check_page_permission("financeiro")(views.financeiro_api_clear),
        name="financeiro_api_clear",
    ),
    path(
        "financeiro/api/test-ollama/",
        views.test_ollama_connection,
        name="financeiro_api_test_ollama",
    ),
    path(
        "monitoramento/",
        check_page_permission("monitoramento")(views.monitoramento),
        name="monitoramento",
    ),
    path(
        "monitoramento/atualizar/<str:tipo>/<str:item_id>/",
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
    path("api/download-livro-ata-pdf/", views.download_livro_ata_pdf, name="download_livro_ata_pdf"),
    path("api/generate-qr/", views.generate_qr_code, name="generate_qr"),
    path("api/generate-qr-v2/", generate_qr_code_improved, name="generate_qr_v2"),
    path("api/livro-ata-status/", views.livro_ata_status, name="livro_ata_status"),
    path("api/generate-livro-ata-qr/", views.generate_livro_ata_qr, name="generate_livro_ata_qr"),
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
        "implantacoes-opsvista/",
        check_page_permission("implantacoes_opsvista")(views.implantacoes_opsvista),
        name="implantacoes_opsvista",
    ),
    path(
        "implantacoes-fluxo/",
        check_page_permission("implantacoes_fluxo")(views.implantacoes_fluxo),
        name="implantacoes_fluxo",
    ),
    path(
        "desmobilizacoes-fluxo/",
        check_page_permission("desmobilizacoes_fluxo")(views.desmobilizacoes_fluxo),
        name="desmobilizacoes_fluxo",
    ),
    path(
        "api/desmobilizacoes-fluxo/criar/",
        views.desmobilizacoes_fluxo_criar,
        name="desmobilizacoes_fluxo_criar",
    ),
    path(
        "api/desmobilizacoes-fluxo/card-details/",
        views.desmobilizacoes_fluxo_card_details,
        name="desmobilizacoes_fluxo_card_details",
    ),
    path(
        "api/desmobilizacoes-fluxo/status/",
        views.desmobilizacoes_fluxo_status,
        name="desmobilizacoes_fluxo_status",
    ),
    path(
        "api/desmobilizacoes-fluxo/salvar/",
        views.desmobilizacoes_fluxo_salvar,
        name="desmobilizacoes_fluxo_salvar",
    ),
    path(
        "api/desmobilizacoes-fluxo/excluir/",
        views.desmobilizacoes_fluxo_excluir,
        name="desmobilizacoes_fluxo_excluir",
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
    
    # === ROTAS DE GESTÃO DE SALAS ===
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
        "gestao-salas/<uuid:pk>/editar/",
        check_page_permission("gestao_salas")(SalaEditarView.as_view()),
        name="sala_editar",
    ),
    path(
        "gestao-salas/<uuid:pk>/deletar/",
        check_page_permission("gestao_salas")(SalaDeletarView.as_view()),
        name="sala_deletar",
    ),
    
    path(
        "api/prestadores/criar/", 
        views.criar_prestador_ajax, 
        name="criar_prestador_ajax"
    ),
    # Rotas AJAX para Prestadores de Serviço
    path("api/prestadores/listar/", views.listar_prestadores_ajax, name="listar_prestadores_ajax"),
    path("api/prestadores/criar/", views.criar_prestador_ajax, name="criar_prestador_ajax"), # A que criamos na etapa anterior
    path("api/prestadores/<int:pk>/editar/", views.editar_prestador_ajax, name="editar_prestador_ajax"),
    path("api/prestadores/<int:pk>/deletar/", views.deletar_prestador_ajax, name="deletar_prestador_ajax"),
    
    # === ROTAS DE GESTÃO DE UNIDADES ===
    path(
        "gestao-salas/unidades/",
        check_page_permission("gestao_salas")(UnidadeListView.as_view()),
        name="unidade_listar",
    ),
    path(
        "gestao-salas/unidades/criar/",
        check_page_permission("gestao_salas")(UnidadeCriarView.as_view()),
        name="unidade_criar",
    ),
    path(
        "gestao-salas/unidades/<int:pk>/editar/", 
        check_page_permission("gestao_salas")(UnidadeEditarView.as_view()),
        name="unidade_editar",
    ),
    path(
        "gestao-salas/unidades/<int:pk>/deletar/", 
        check_page_permission("gestao_salas")(UnidadeDeletarView.as_view()),
        name="unidade_deletar",
    ),

    # === ROTAS DE RESERVA E CALENDÁRIO ===
    path(
        "selecionar-unidade/",
        SelecionarUnidadeView.as_view(),
        name="selecionar_unidade",
    ),
    path(
        "reserva-salas/<slug:unidade_slug>/",
        ReservaSalasView.as_view(),
        name="reserva_salas",
    ),
    path(
        "api/salas/",
        views.api_salas,
        name="api_salas_geral",
    ),
    path(
        "api/salas/<slug:unidade_slug>/",
        views.api_salas_por_unidade,
        name="api_salas_por_unidade",
    ),
    path(
        "api/horarios/<slug:unidade_slug>/",
        ReservaSalasView.as_view(),
        name="api_horarios",
    ),
    path(
        "calendario-reservas/",
        CalendarioReservasView.as_view(),
        name="calendario_reservas",
    ),
    path(
        "api/reservas/",
        CalendarioReservasView.as_view(),
        name="api_reservas",
    ),
    path(
        "api/reservas/historico/",
        views.api_historico_reservas,
        name="api_historico_reservas",
    ),
    path(
        "api/reservas/<uuid:reserva_id>/",
        CalendarioReservasView.as_view(),
        name="reserva_delete",
    ),
    path(
        "gestao-salas/qr-code/<uuid:sala_id>/",
        views.baixar_qr_code_sala,
        name="baixar_qr_code_sala",
    ),
    
    # === ROTAS DO LIVRO ATA ===
    path(
        "livro-ata/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        name="livro_ata",
    ),
    path(
        "livroata/qrcode=<str:qrcode_id>/",  # Mudei de uuid para str para evitar quebra de regex
        LivroAtaView.as_view(),
        name="livro_ata_qrcode",
    ),
    path(
        "livroata/qrcode=<str:qrcode_id>",  # Rota sem barra no final para garantir
        LivroAtaView.as_view(),
        name="livro_ata_qrcode_no_slash",
    ),
    path(
        "api/livro-ata/shifts/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_shifts"},
        name="livro_ata_shifts",
    ),
    path(
        "api/livro-ata/qrcode-shifts/",
        LivroAtaView.as_view(),
        {"action": "get_shifts"},
        name="livro_ata_qrcode_shifts",
    ),
    path(
        "api/livro-ata/shifts/<uuid:shift_id>/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_shift_details"},
        name="livro_ata_shift_details",
    ),
    path(
        "api/livro-ata/qrcode-shifts/<uuid:shift_id>/",
        LivroAtaView.as_view(),
        {"action": "get_shift_details"},
        name="livro_ata_qrcode_shift_details",
    ),
    path(
        "api/livro-ata/relatorio/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_relatorio"},
        name="livro_ata_relatorio",
    ),
    path(
        "api/livro-ata/qrcode-relatorio/",
        LivroAtaView.as_view(),
        {"action": "get_relatorio"},
        name="livro_ata_qrcode_relatorio",
    ),
    path(
        "api/livro-ata/notificacao-teste/",
        views.enviar_notificacao_teste_whatsapp,
        name="livro_ata_notificacao_teste",
    ),
    path(
        "api/livro-ata/whatsapp-status/",
        views.livro_ata_whatsapp_status,
        name="livro_ata_whatsapp_status",
    ),
    path(
        "api/livro-ata/gerentes/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_gerentes"},
        name="livro_ata_gerentes",
    ),
    path(
        "api/livro-ata/relatorio-mensal/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_relatorio_mensal"},
        name="livro_ata_relatorio_mensal",
    ),
    path(
        "api/livro-ata/relatorio-consolidado/",
        check_page_permission("livro_ata")(LivroAtaView.as_view()),
        {"action": "get_relatorio_consolidado"},
        name="livro_ata_relatorio_consolidado",
    ),

    # === OUTROS MÓDULOS ===
    path(
        "planner/",
        check_page_permission("planner")(PlannerView.as_view()),
        name="planner",
    ),
    path(
        "planer/",
        check_page_permission("planner")(PlannerView.as_view()),
        name="planer",
    ),
    path(
        "explorer/",
        check_page_permission("explorer")(views.ExplorerView.as_view()),
        name="explorer",
    ),
    path(
        "relatorios/",
        check_page_permission("relatorios")(views.relatorios),
        name="relatorios",
    ),

    # === ROTAS DA NOVA TORRE DE CONTROLE (LIVRO DE OCORRÊNCIAS) ===
    path(
        "torre-controle/",
        LivroOcorrenciasView.as_view(),
        name="torre_controle",
    ),
    path(
        "torre-controle/detalhe/<str:pk>/", 
        check_page_permission("torre_controle")(LivroOcorrenciasDetalheView.as_view()),
        name="livro_ocorrencia_detalhe",
    ),
    # === AUDITOR DE RONDA (subpágina da Torre de Controle, com abas) ===
    path(
        "torre-controle/auditoria/",
        check_page_permission("torre_controle")(views.AuditorRondaView.as_view()),
        name="auditoria_torre",
    ),
    path(
        "torre-controle/auditoria/hash/",
        check_page_permission("torre_controle")(views.AuditoriaOcorrenciasView.as_view()),
        name="auditoria_hash_torre",
    ),
    path(
        "api/auditoria-torre/marcar/",
        login_required(views.marcar_auditoria_ajax),
        name="marcar_auditoria_torre",
    ),
    path(
        "api/auditoria-torre/carregar-mais/",
        login_required(views.carregar_mais_auditoria),
        name="carregar_mais_auditoria",
    ),


    # Health check endpoint para diagnóstico
    path("health/", views.health_check, name="health_check"),
    # Login otimizado para testes
    path("fast-login/", views.fast_login_view, name="fast_login"),
    
    # API endpoints para histórico de mudanças do projeto
    path(
        "api/project/<uuid:project_id>/change-history/",
        views.get_project_change_history,
        name="get_project_change_history",
    ),
    path(
        "api/project/<uuid:project_id>/change-history-summary/",
        views.get_project_history_summary,
        name="get_project_history_summary",
    ),
    
    # === GESTÃO DA QUALIDADE ===
    path(
        "gestao-qualidade/",
        check_page_permission("gestao_qualidade")(views.GestaoQualidadeView.as_view()),
        name="gestao_qualidade",
    ),
    path(
        "api/gestao-qualidade/treinamento/criar/",
        check_page_permission("gestao_qualidade")(views.criar_treinamento),
        name="criar_treinamento",
    ),
    path(
        "api/gestao-qualidade/visita-tecnica/criar/",
        check_page_permission("gestao_qualidade")(views.criar_visita_tecnica),
        name="criar_visita_tecnica",
    ),
    path(
        "api/gestao-qualidade/nao-conformidade/criar/",
        check_page_permission("gestao_qualidade")(views.criar_nao_conformidade),
        name="criar_nao_conformidade",
    ),
    path(
        "api/gestao-qualidade/plano-acao/criar/",
        check_page_permission("gestao_qualidade")(views.criar_plano_acao),
        name="criar_plano_acao",
    ),
    path(
        "api/gestao-qualidade/visita-tecnica/<uuid:visita_id>/evidencias/",
        check_page_permission("gestao_qualidade")(views.listar_evidencias_visita),
        name="listar_evidencias_visita",
    ),
    path(
        "api/gestao-qualidade/evidencia/<uuid:evidencia_id>/visualizar/",
        check_page_permission("gestao_qualidade")(views.visualizar_evidencia),
        name="visualizar_evidencia",
    ),
    
    # TREINAMENTO CRUD
    path(
        "api/gestao-qualidade/treinamento/<uuid:treinamento_id>/",
        check_page_permission("gestao_qualidade")(views.obter_treinamento),
        name="obter_treinamento",
    ),
    path(
        "api/gestao-qualidade/treinamento/<uuid:treinamento_id>/atualizar/",
        check_page_permission("gestao_qualidade")(views.atualizar_treinamento),
        name="atualizar_treinamento",
    ),
    path(
        "api/gestao-qualidade/treinamento/<uuid:treinamento_id>/deletar/",
        check_page_permission("gestao_qualidade")(views.deletar_treinamento),
        name="deletar_treinamento",
    ),
    
    # VISITA TÉCNICA CRUD
    path(
        "api/gestao-qualidade/visita-tecnica/<uuid:visita_id>/",
        check_page_permission("gestao_qualidade")(views.obter_visita_tecnica),
        name="obter_visita_tecnica",
    ),
    path(
        "api/gestao-qualidade/visita-tecnica/<uuid:visita_id>/atualizar/",
        check_page_permission("gestao_qualidade")(views.atualizar_visita_tecnica),
        name="atualizar_visita_tecnica",
    ),
    path(
        "api/gestao-qualidade/visita-tecnica/<uuid:visita_id>/deletar/",
        check_page_permission("gestao_qualidade")(views.deletar_visita_tecnica),
        name="deletar_visita_tecnica",
    ),
    
    # NÃO CONFORMIDADE CRUD
    path(
        "api/gestao-qualidade/nao-conformidade/criar-manual/",
        check_page_permission("gestao_qualidade")(views.criar_nao_conformidade_manual),
        name="criar_nao_conformidade_manual",
    ),
    path(
        "api/gestao-qualidade/nao-conformidade/<uuid:nc_id>/",
        check_page_permission("gestao_qualidade")(views.obter_nao_conformidade),
        name="obter_nao_conformidade",
    ),
    path(
        "api/gestao-qualidade/nao-conformidade/<uuid:nc_id>/atualizar/",
        check_page_permission("gestao_qualidade")(views.atualizar_nao_conformidade),
        name="atualizar_nao_conformidade",
    ),
    path(
        "api/gestao-qualidade/nao-conformidade/<uuid:nc_id>/deletar/",
        check_page_permission("gestao_qualidade")(views.deletar_nao_conformidade),
        name="deletar_nao_conformidade",
    ),
    
    # PLANO DE AÇÃO CRUD
    path(
        "api/gestao-qualidade/plano-acao/<uuid:plano_id>/",
        check_page_permission("gestao_qualidade")(views.obter_plano_acao),
        name="obter_plano_acao",
    ),
    path(
        "api/gestao-qualidade/plano-acao/<uuid:plano_id>/atualizar/",
        check_page_permission("gestao_qualidade")(views.atualizar_plano_acao),
        name="atualizar_plano_acao",
    ),
    path(
        "api/gestao-qualidade/plano-acao/<uuid:plano_id>/deletar/",
        check_page_permission("gestao_qualidade")(views.deletar_plano_acao),
        name="deletar_plano_acao",
    ),
    path(
        "api/gestao-qualidade/plano-acao/<uuid:plano_id>/evidencias/adicionar/",
        check_page_permission("gestao_qualidade")(views.adicionar_evidencias_plano_acao),
        name="adicionar_evidencias_plano_acao",
    ),
    
    # PWA
    path("manifest.json", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    
    # CALENDÁRIO 2026
    path(
        "calendario-2026/",
        check_page_permission("calendario_2026")(views.calendario_2026),
        name="calendario_2026",
    ),
    path(
        "calendario-2026/api/eventos/",
        check_page_permission("calendario_2026")(views.listar_eventos_calendario),
        name="listar_eventos_calendario",
    ),
    path(
        "calendario-2026/api/eventos/criar/",
        check_page_permission("calendario_2026")(views.criar_evento_calendario),
        name="criar_evento_calendario",
    ),
    path(
        "calendario-2026/api/eventos/<uuid:evento_id>/",
        check_page_permission("calendario_2026")(views.obter_evento_calendario),
        name="obter_evento_calendario",
    ),
    path(
        "calendario-2026/api/eventos/<uuid:evento_id>/atualizar/",
        check_page_permission("calendario_2026")(views.atualizar_evento_calendario),
        name="atualizar_evento_calendario",
    ),
    path(
        "calendario-2026/api/eventos/<uuid:evento_id>/excluir/",
        check_page_permission("calendario_2026")(views.excluir_evento_calendario),
        name="excluir_evento_calendario",
    ),

    # PLANOS DE AÇÃO DA TORRE DE CONTROLE
    path('api/ocorrencias/plano/criar/', views.criar_plano_ocorrencia, name='criar_plano_ocorrencia'),
    path('api/ocorrencias/plano/<uuid:pk>/aprovar/', views.aprovar_plano_ocorrencia, name='aprovar_plano_ocorrencia'),
    path('api/ocorrencias/plano/<uuid:pk>/compra/', views.cadastrar_compra_ocorrencia, name='cadastrar_compra_ocorrencia'),
    path('api/ocorrencias/plano/<uuid:pk>/status_compra/', views.atualizar_status_compra, name='atualizar_status_compra'),
    path('api/ocorrencias/plano/retirada/', views.registrar_retirada_ocorrencia, name='registrar_retirada_ocorrencia'),
    path('api/ocorrencias/plano/<uuid:pk>/excluir/', views.excluir_plano_ocorrencia, name='excluir_plano_ocorrencia'),
    path('api/ocorrencias/historico_item/', views.historico_item_ocorrencia_api, name='historico_item_ocorrencia'),
    
    # NOVA ROTA: Dashboard de Retrospectiva
    path('api/ocorrencias/retrospectiva/', views.retrospectiva_ocorrencias_api, name='retrospectiva_ocorrencias_api'),
    path('ocorrencias/retrospectiva/exportar/pdf/', views.exportar_retrospectiva_pdf, name='exportar_retrospectiva_pdf'),
    path('ocorrencias/retrospectiva/exportar/excel/', views.exportar_retrospectiva_excel, name='exportar_retrospectiva_excel'),
    
    path('ocorrencias/reincidencias/painel/', PainelReincidenciasView.as_view(), name='painel_reincidencias'),
    path('ocorrencias/reincidencias/aprovar/<int:pk>/', AprovarReincidenciaView.as_view(), name='aprovar_reincidencia'),

    path('ocorrencias/reincidencias/gerar-teste/', GerarDadosTesteView.as_view(), name='gerar_dados_teste'),

    
    path('api/auditoria/<str:pk>/notificar/', notificar_gerente_auditoria_ajax, name='notificar_gerente_auditoria'),
    path('api/auditoria/<str:pk>/resolver/', resolver_auditoria_ajax, name='resolver_auditoria'),
    path('api/auditoria/<str:pk>/voltar-nc/', views.voltar_nc_auditoria_ajax, name='voltar_nc_auditoria'),
    path('api/ocorrencias/enviar-auditoria/', views.enviar_para_auditoria, name='enviar_para_auditoria'),

    path("api/auditoria-torre/tratar-coincidencia/", login_required(views.tratar_coincidencia_ajax), name="tratar_coincidencia_ajax"),

    path('cadastro/', views.solicitar_cadastro, name='solicitar_cadastro'),
    path('solicitacoes-cadastro/', views.listar_solicitacoes, name='solicitacoes_cadastro'),

# Adicione na lista de urlpatterns:
    path('ocorrencias/plano/acao-email/<uuid:pk>/<str:acao>/', AcaoPlanoEmailView.as_view(), name='acao_plano_email'),
    
    # === ROTAS PSICOSSOCIAL NR-01 ===
    path('psicossocial/', views.psicossocial_list, name='psicossocial'),
    path('psicossocial/criar/', views.psicossocial_create, name='psicossocial_create'),
    path('psicossocial/<uuid:project_id>/deletar/', views.psicossocial_delete, name='psicossocial_delete'),
    path('psicossocial/sra/', views.psicossocial_sra, name='psicossocial_sra'),
    path('psicossocial/sra/<int:pk>/deletar/', views.psicossocial_sra_delete, name='psicossocial_sra_delete'),
    path('psicossocial/api/autocomplete/', views.psicossocial_autocomplete, name='psicossocial_autocomplete'),
    path('psicossocial/api/sra-list/', views.psicossocial_sra_list_api, name='psicossocial_sra_list_api'),
    path('gerenciar-regionais/', views.gerenciar_regionais, name='gerenciar_regionais'),
    path('alterar-regional-ativa/', views.alterar_regional_ativa, name='alterar_regional_ativa'),
    # === MÓDULO CMO EFETIVO (Conformidade de Efetivo) ===
    path('cmo-efetivo/', views.CMOEfetivoView.as_view(), name='cmo_efetivo'),
    path('api/cmo-efetivo/autocomplete/', views.cmo_efetivo_autocomplete, name='cmo_efetivo_autocomplete'),
    path('api/cmo-efetivo/conformidade/salvar/', views.cmo_efetivo_salvar_conformidade, name='cmo_efetivo_salvar_conformidade'),
    path('api/cmo-efetivo/registro-movimentacao/salvar/', views.cmo_efetivo_salvar_registro_movimentacao, name='cmo_efetivo_salvar_registro_movimentacao'),
    path('api/cmo-efetivo/cobertura/salvar/', views.cmo_efetivo_salvar_cobertura, name='cmo_efetivo_salvar_cobertura'),
    path('api/cmo-efetivo/troca/solicitar/', views.cmo_efetivo_solicitar_troca, name='cmo_efetivo_solicitar_troca'),
    path('api/cmo-efetivo/troca/decidir/', views.cmo_efetivo_decidir_troca, name='cmo_efetivo_decidir_troca'),
    path('api/cmo-efetivo/lancamento/marcar/', views.cmo_efetivo_marcar_lancado, name='cmo_efetivo_marcar_lancado'),
    path('api/cmo-efetivo/cancelar/', views.cmo_efetivo_cancelar, name='cmo_efetivo_cancelar'),
    # === MÓDULO LINKS IMPORTANTES ===
    path('links-importantes/', views.LinksImportantesView.as_view(), name='links_importantes'),
    path('api/links-importantes/salvar/', views.links_importantes_salvar, name='links_importantes_salvar'),
    path('api/links-importantes/excluir/', views.links_importantes_excluir, name='links_importantes_excluir'),
    # === MÓDULO CONTROLE DE ORDENS E BACKLOG (DEMO) ===
    path(
        'controle-ordens/',
        check_page_permission('controle_ordens')(views.controle_ordens),
        name='controle_ordens',
    ),
    # === AJUDA / TUTORIAL DE PRIMEIRO ACESSO ===
    path('ajuda/', views.AjudaView.as_view(), name='ajuda'),
    path('api/tutorial/marcar-visto/', views.tutorial_marcar_visto, name='tutorial_marcar_visto'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

