from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PrestadorServico
from .models import OcorrenciaPlanoAcao
from .models import (
    CRKPI,
    CMOEfetivoConformidade,
    CMOEfetivoCobertura,
    CMOEfetivoTroca,
    CMOEfetivoLancamento,
    CMOEfetivoLog,
    ControleChip,
    CustomUser,
    Dashboard,
    DesativacaoCR,
    ErrosDashboard,
    Estrutura,
    EventoCalendario2026,
    GerenteKPI,
    GestaoSala,
    ImplantacoesOpsVista,
    LinkImportante,
    MonitoramentoLog,
    PlannerAttachment,
    PlannerComment,
    PlannerPipelineStage,
    PlannerProject,
    PlannerProjectResponsavel,
    PortariaBase,
    RelatorioItem,
    ReservaSala,
    Script,
    Service,
    ShiftComplianceItem,
    ShiftEvidence,
    ShiftRecord,
    TipoServico,
    Regional,
    Unidade,
    UserActivity,
    UserPermissionGroup,
    UserProfile,
)


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "name", "role", "regional", "is_global_admin", "setor", "is_online", "is_regulatory", "is_general", "is_staff")
    list_filter = ("role", "regional", "is_global_admin", "setor", "is_online", "is_regulatory", "is_general", "is_staff")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações Pessoais", {"fields": ("name", "email")}),
        (
            "Controle de Notificações",
            {
                "fields": (
                    "is_regulatory",
                    "is_general",
                    "crs",
                    "setor",
                )
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "role",
                    "is_global_admin",
                    "regional",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "name", "password1", "password2", "role", "is_regulatory", "is_general", "crs", "setor"),
            },
        ),
    )
    search_fields = ("username", "name", "email", "crs")
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Dashboard)
admin.site.register(Script)
admin.site.register(MonitoramentoLog)
admin.site.register(DesativacaoCR)


@admin.register(TipoServico)
class TipoServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "created_at")
    list_filter = ("ativo", "created_at")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(PlannerProjectResponsavel)
class PlannerProjectResponsavelAdmin(admin.ModelAdmin):
    list_display = ("projeto", "responsavel", "created_at")
    list_filter = ("created_at",)
    search_fields = ("projeto__nome", "responsavel__name")
    ordering = ("created_at",)


@admin.register(PlannerPipelineStage)
class PlannerPipelineStageAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "ordem", "ativo", "status_legado")
    list_editable = ("cor", "ordem", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "status_legado")
    ordering = ("ordem", "nome")


@admin.register(PlannerProject)
class PlannerProjectAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "get_responsaveis_display",
        "data_inicial",
        "data_conclusao",
        "prioridade",
        "status",
        "tipo_servico",
    )
    list_filter = ("status", "prioridade", "tipo_servico")
    search_fields = ("nome", "responsaveis__name", "tipo_servico__nome")
    date_hierarchy = "data_inicial"
    inlines = [
        type(
            "PlannerProjectResponsavelInline",
            (admin.TabularInline,),
            {
                "model": PlannerProjectResponsavel,
                "extra": 1,
            },
        )
    ]


@admin.register(PlannerComment)
class PlannerCommentAdmin(admin.ModelAdmin):
    list_display = ("projeto", "autor", "created_at")
    list_filter = ("projeto", "autor")
    search_fields = ("projeto__nome", "autor__name", "conteudo")


@admin.register(PlannerAttachment)
class PlannerAttachmentAdmin(admin.ModelAdmin):
    list_display = ("nome", "projeto", "uploaded_by", "created_at")
    list_filter = ("projeto", "uploaded_by")
    search_fields = ("nome", "projeto__nome", "uploaded_by__name")


@admin.register(CRKPI)
class CRKPIAdmin(admin.ModelAdmin):
    list_display = (
        "cr",
        "cliente",
        "gerente",
        "tipo_servico",
        "performance_total",
        "nps",
        "visita_operacional_concluida",
    )
    list_filter = ("tipo_servico", "gerente", "visita_operacional_concluida")
    search_fields = ("cr", "cliente", "gerente")
    list_editable = ("performance_total", "nps", "visita_operacional_concluida")
    ordering = ("cliente", "cr")

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("cr", "cliente", "gerente", "tipo_servico")},
        ),
        (
            "Performance",
            {
                "fields": (
                    "performance_diurno",
                    "performance_noturno",
                    "performance_total",
                )
            },
        ),
        (
            "Visita Operacional",
            {"fields": ("visita_operacional_concluida", "data_ultima_visita")},
        ),
        ("Avaliação", {"fields": ("nps", "observacoes")}),
    )


@admin.register(GerenteKPI)
class GerenteKPIAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "clientes",
        "percentual_geral",
        "nps_media",
        "percentual_visitas",
    )
    search_fields = ("nome",)
    ordering = ("nome",)

    fieldsets = (
        ("Informações Básicas", {"fields": ("nome", "clientes", "percentual_geral")}),
        (
            "Serviços Média",
            {
                "fields": (
                    "servicos_media_ronda",
                    "servicos_media_facilities",
                    "servicos_media_manutencao",
                )
            },
        ),
        ("Visitas Operacionais", {"fields": ("visitas_concluidas", "visitas_total")}),
        ("NPS", {"fields": ("nps_media",)}),
    )

    def percentual_visitas(self, obj):
        return f"{obj.percentual_visitas:.1f}%"

    percentual_visitas.short_description = "Percentual Visitas"


@admin.register(RelatorioItem)
class RelatorioItemAdmin(admin.ModelAdmin):
    list_display = ("numero", "nome", "cr", "responsavel", "tipo", "data", "created_at")
    list_filter = ("tipo", "cr", "responsavel", "data")
    search_fields = ("numero", "nome", "cr", "responsavel")
    date_hierarchy = "data"
    ordering = ("-data", "-created_at")

    fieldsets = (
        ("Informações Básicas", {"fields": ("numero", "nome", "tipo")}),
        ("Detalhes", {"fields": ("cr", "responsavel", "data")}),
        ("Arquivo", {"fields": ("arquivo",), "classes": ("collapse",)}),
    )


@admin.register(ErrosDashboard)
class ErrosDashboardAdmin(admin.ModelAdmin):
    list_display = ("id", "dashboard", "data", "prox_att")
    list_filter = ("data", "dashboard")
    search_fields = ("dashboard",)
    date_hierarchy = "data"
    ordering = ("-data",)


@admin.register(ControleChip)
class ControleChipAdmin(admin.ModelAdmin):
    list_display = (
        "id_portal",
        "solicitante",
        "cr",
        "operadora",
        "numero_telefone",
        "status",
        "data",
    )
    list_filter = ("status", "operadora", "data")
    search_fields = ("id_portal", "solicitante", "cr", "numero_telefone")
    date_hierarchy = "data"
    ordering = ("-data", "-created_at")

    fieldsets = (
        ("Informações Básicas", {"fields": ("data", "id_portal", "solicitante", "cr")}),
        (
            "Detalhes do Chip",
            {
                "fields": (
                    "operadora",
                    "numero_telefone",
                    "responsavel_retirada",
                    "status",
                )
            },
        ),
        ("Observações", {"fields": ("observacoes",)}),
    )


@admin.register(ImplantacoesOpsVista)
class ImplantacoesOpsVistaAdmin(admin.ModelAdmin):
    list_display = (
        "get_cr_descricao",
        "sistema",
        "servico",
        "status",
        "created_at",
    )
    list_filter = ("status", "servico", "created_at")
    search_fields = ("cr__descricao", "sistema", "cr__cr")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_cr_descricao(self, obj):
        """Método para exibir a descrição do CR"""
        if obj.cr:
            return obj.cr.descricao
        return obj.cr_id
    get_cr_descricao.short_description = "CR"
    get_cr_descricao.admin_order_field = "cr_id"

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "cr_id",
                    "sistema",
                    "implantacoes",
                    "servico",
                    "status",
                )
            },
        ),
        ("Observações", {"fields": ("observacoes",)}),
    )


@admin.register(EventoCalendario2026)
class EventoCalendario2026Admin(admin.ModelAdmin):
    list_display = (
        'data_inicio',
        'data_fim',
        'titulo',
        'tipo',
        'cor',
        'created_at',
    )
    list_filter = ('tipo', 'data_inicio', 'created_at')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_inicio'
    ordering = ('data_inicio', 'titulo')

    fieldsets = (
        (
            'Informações do Evento',
            {
                'fields': (
                    'data_inicio',
                    'data_fim',
                    'titulo',
                    'tipo',
                    'descricao',
                    'cor',
                )
            },
        ),
    )



@admin.register(PrestadorServico)
class PrestadorServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'area_servico', 'ativo')
    list_filter = ('area_servico', 'ativo')


@admin.register(OcorrenciaPlanoAcao)
class OcorrenciaPlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ('cr_colaborador', 'item_em_falta', 'status', 'criador_plano', 'is_regulatory', 'data_criacao')
    list_filter = ('status', 'tem_estoque', 'is_regulatory', 'data_criacao')
    search_fields = ('cr_colaborador', 'item_em_falta', 'colaborador_nc')
    readonly_fields = ('id', 'data_criacao')


from .models import CardImplantacao, CardDesmobilizacao

@admin.register(CardImplantacao)
class CardImplantacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'etapa_atual', 'tipo_implantacao', 'created_at')
    list_filter = ('status', 'etapa_atual', 'tipo_implantacao', 'created_at')
    search_fields = ('nome', 'tipo_implantacao')
    ordering = ('-created_at',)


@admin.register(CardDesmobilizacao)
class CardDesmobilizacaoAdmin(admin.ModelAdmin):
    list_display = ('cr', 'cr_descricao', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('cr', 'cr_descricao')
    ordering = ('-created_at',)


@admin.register(Regional)
class RegionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "estado", "cidade", "diretor_regional", "diretor_executivo", "created_at")
    list_filter = ("estado", "created_at")
    search_fields = ("nome", "cidade", "diretor_regional", "diretor_executivo")
    ordering = ("nome",)


# === MÓDULO CMO EFETIVO ===

@admin.register(CMOEfetivoConformidade)
class CMOEfetivoConformidadeAdmin(admin.ModelAdmin):
    list_display = ("colaborador_nome", "cliente_nome", "cr", "data_referencia", "status_efetivo", "status_lancamento", "cancelado")
    list_filter = ("status_efetivo", "status_lancamento", "cancelado", "tipo_servico_nome")
    search_fields = ("colaborador_nome", "cliente_nome", "cr", "colaborador_matricula")
    ordering = ("-data_referencia",)


@admin.register(CMOEfetivoCobertura)
class CMOEfetivoCoberturaAdmin(admin.ModelAdmin):
    list_display = ("nome_cobertura", "colaborador_substituido", "cliente_nome", "cr", "data_cobertura", "status")
    list_filter = ("status", "tipo_servico_nome")
    search_fields = ("nome_cobertura", "colaborador_substituido", "cliente_nome", "cr")
    ordering = ("-data_cobertura",)


@admin.register(CMOEfetivoTroca)
class CMOEfetivoTrocaAdmin(admin.ModelAdmin):
    list_display = ("colaborador_atual", "colaborador_substituto", "cliente_nome", "cr", "data_troca", "status_cmo", "cancelado")
    list_filter = ("status_cmo", "cancelado", "tipo_servico_nome")
    search_fields = ("colaborador_atual", "colaborador_substituto", "cliente_nome", "cr")
    ordering = ("-data_troca",)


@admin.register(CMOEfetivoLancamento)
class CMOEfetivoLancamentoAdmin(admin.ModelAdmin):
    list_display = ("ocorrencia_tipo", "cliente_nome", "colaborador_nome", "lancado", "data_lancamento", "responsavel_cmo")
    list_filter = ("ocorrencia_tipo", "lancado")
    search_fields = ("cliente_nome", "colaborador_nome", "ocorrencia_id")
    ordering = ("lancado", "-criado_em")


@admin.register(CMOEfetivoLog)
class CMOEfetivoLogAdmin(admin.ModelAdmin):
    list_display = ("entidade", "registro_id", "acao", "usuario", "data_hora")
    list_filter = ("entidade", "acao")
    search_fields = ("registro_id", "acao")
    ordering = ("-data_hora",)


# === MÓDULO LINKS IMPORTANTES ===

@admin.register(LinkImportante)
class LinkImportanteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "url", "ordem", "ativo", "criado_por", "created_at")
    list_filter = ("ativo",)
    search_fields = ("titulo", "url", "descricao")
    ordering = ("ordem", "titulo")




