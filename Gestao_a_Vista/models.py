import uuid
from datetime import date, time

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db import models


def get_default_hora_inicio():
    return time(8, 0)  # 08:00


def get_default_hora_fim():
    return time(18, 0)  # 18:00


def get_default_data():
    return date.today()


def get_default_sala():
    # Com UUID, retornamos a primeira sala disponível ou None
    sala = GestaoSala.objects.first()
    return sala.id_sala if sala else None


class Regional(models.Model):
    """
    Modelo para representar as regionais do sistema (Cidade - UF)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, verbose_name="Nome da Regional", unique=True)
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)")
    db_slug = models.SlugField(max_length=50, unique=True, verbose_name="Identificador do Banco de Dados")
    cidade = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cidade")
    diretor_regional = models.CharField(max_length=255, blank=True, null=True, verbose_name="Diretor Regional")
    diretor_executivo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Diretor Executivo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Gestao_a_Vista_regional"
        verbose_name = "Regional"
        verbose_name_plural = "Regionais"

    def __str__(self):
        if self.cidade:
            return f"{self.nome} ({self.cidade} - {self.estado})"
        return f"{self.nome} ({self.estado})"


class CustomUser(AbstractUser):
    """
    Modelo de usuário customizado
    """

    ROLE_CHOICES = [
        ("administrador", "Administrador"),
        ("gerente", "Gerente"),
        ('coordenador', 'Coordenador'),
        ('supervisor', 'Supervisor'),
        ("publico", "Público"),
        ("cliente", "Cliente"),
    ]

    PAGE_PERMISSIONS = [
        ("dashboard", "Dashboards"),
        ("monitoramento", "Monitoramento"),
        ("qr_generator", "Gerador QR Code"),
        ("etiquetas_generator", "Gerador de Etiquetas"),
        ("desativacao_cr", "Desativação de CR"),
        ("controle_chips", "Controle de Chips"),
        ("implantacoes_opsvista", "Implantações OpsVista"),
        ("implantacoes_fluxo", "Fluxo de Implantações"),
        ("desmobilizacoes_fluxo", "Fluxo de Desmobilização"),
        ("portaria_base", "Portaria Base"),
        ("gestao_salas", "Gestão de Salas"),
        ("reserva_salas", "Reserva de Salas"),
        ("calendario_reservas", "Calendário de Reservas"),
        ("livro_ata", "Livro ATA"),
        ("planner", "Planner"),
        ("explorer", "Explorer"),
        ("torre_controle", "Torre de Controle"),
        ("relatorios", "Relatórios"),
        ("gestao_qualidade", "Gestão da Qualidade"),
        ("calendario_2026", "Calendário 2026"),
        ("psicossocial", "Psicossocial"),
        ("financeiro", "Financeiro"),
        ("cmo_efetivo", "CMO (Conformidade de Efetivo)"),
        ("cmo_efetivo_torre", "CMO Efetivo — Ações da Torre"),
        ("cmo_efetivo_cmo", "CMO Efetivo — Ações da CMO"),
        ("links_importantes", "Links Importantes"),
    ]

    SETOR_CHOICES = [
        ('TI', 'TI'),
        ('PEC', 'PEC/ FINANCEIRO'),
        ('QUALIDADE', 'Qualidade'),
        ('PROJETOS', 'Projetos'),
        ('SESMT', 'SESMT'),
        ('SUPRIMENTOS', 'Suprimentos'),
        ('BI', 'BI'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="publico")
    is_online = models.BooleanField(default=False)
    is_regulatory = models.BooleanField(default=False, verbose_name="É do Regulatório?")
    crs = models.TextField(blank=True, verbose_name="CRs (separados por vírgula)", help_text="Ex: CR 01, CR 02. Deixe em branco se for Geral.")
    is_general = models.BooleanField(default=False, verbose_name="Recebe de todos os CRs? (Geral)")
    setor = models.CharField(_("Setor"), max_length=20, choices=SETOR_CHOICES, blank=True, null=True, db_index=True)
    regional = models.ForeignKey(Regional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Regional")
    is_global_admin = models.BooleanField(default=False, verbose_name="É Administrador Global supremo?")
    notificar_livro_ata = models.BooleanField(default=False, verbose_name="Recebe notificação de Livro Ata pendente (WhatsApp)")
    whatsapp_notificacao = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp para notificação", help_text="Ex: 5562999999999 (com DDI e DDD)")
    tutorial_visto = models.BooleanField(default=False, verbose_name="Já viu o tutorial de primeiro acesso?")
    page_permissions = models.JSONField(
        default=dict
    )  # Armazena as permissões de página como um dicionário

    # Adicionando related_names para resolver os conflitos
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    class Meta:
        db_table = "Gestao_a_Vista_customuser"

    def __str__(self):
        return self.name or self.username

    def has_page_permission(self, page_name):
        if self.role == "administrador":
            return True
        if page_name in self.page_permissions:
            return self.page_permissions[page_name]
        default_perms = self.get_default_permissions()
        return default_perms.get(page_name, False)

    def get_default_permissions(self):
        if self.role == "administrador":
            return {page[0]: True for page in self.PAGE_PERMISSIONS}
        elif self.role == "gerente":
            return {
                "dashboard": True,
                "monitoramento": True,
                "qr_generator": True,
                "etiquetas_generator": True,
                "desativacao_cr": False,
                "controle_chips": True,
                "implantacoes_opsvista": True,
                "implantacoes_fluxo": True,
                "desmobilizacoes_fluxo": True,
                "portaria_base": True,
                "gestao_salas": True,
                "reserva_salas": True,
                "calendario_reservas": True,
                "livro_ata": True,
                "planner": True,
                "explorer": True,
                "torre_controle": True,
                "relatorios": True,
                "psicossocial": False,
                "financeiro": True,
                "links_importantes": True,
            }
        elif self.role == "publico":
            return {
                "dashboard": True,
                "monitoramento": False,
                "qr_generator": False,
                "etiquetas_generator": False,
                "desativacao_cr": False,
                "controle_chips": False,
                "implantacoes_opsvista": False,
                "implantacoes_fluxo": False,
                "desmobilizacoes_fluxo": False,
                "portaria_base": True,
                "gestao_salas": False,
                "reserva_salas": True,
                "calendario_reservas": True,
                "livro_ata": True,
                "planner": False,
                "explorer": False,
                "torre_controle": False,
                "relatorios": False,
                "psicossocial": False,
                "financeiro": False,
                "links_importantes": True,
            }
        else:  # cliente
            return {page[0]: False for page in self.PAGE_PERMISSIONS}


class UserProfile(models.Model):
    """
    Perfil adicional do usuário
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    phone = models.CharField(_("telefone"), max_length=20, blank=True)
    address = models.TextField(_("endereço"), blank=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("perfil de usuário")
        verbose_name_plural = _("perfis de usuário")

    def __str__(self):
        return f"Perfil de {self.user.username}"


class UserActivity(models.Model):
    """
    Registro de atividades do usuário
    """

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="activities"
    )
    action = models.CharField(_("ação"), max_length=255, default="login")
    details = models.TextField(_("detalhes"), blank=True)
    timestamp = models.DateTimeField(_("data/hora"), default=timezone.now)

    class Meta:
        verbose_name = _("atividade do usuário")
        verbose_name_plural = _("atividades do usuário")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class UserPermissionGroup(models.Model):
    """
    Grupos de permissões customizados
    """

    name = models.CharField(_("nome"), max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, verbose_name=_("permissões"))
    description = models.TextField(_("descrição"), blank=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("grupo de permissões")
        verbose_name_plural = _("grupos de permissões")

    def __str__(self):
        return self.name


class Dashboard(models.Model):
    """Modelo para dashboards do Power BI"""

    STATUS_CHOICES = [
        ("Sucesso", "Sucesso"),
        ("Erro", "Erro"),
        ("Pendente", "Pendente"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        _("nome"), max_length=100, db_index=True
    )  # OTIMIZADO: índice para buscas
    descricao = models.TextField(_("descrição"), blank=True)
    cliente = models.CharField(
        _("cliente"), max_length=100, db_index=True
    )  # OTIMIZADO: índice para filtros
    servico = models.CharField(
        _("serviço"), max_length=100, db_index=True
    )  # OTIMIZADO: índice para filtros
    url = models.URLField(_("URL"), blank=True)
    powerbi_url = models.URLField(_("URL do Power BI"), blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="Sucesso",
        db_index=True,  # OTIMIZADO: índice para filtros de status
    )
    ultima_atualizacao = models.DateTimeField(
        _("última atualização"), auto_now=True, db_index=True
    )  # OTIMIZADO
    created_at = models.DateTimeField(
        _("criado em"), auto_now_add=True, db_index=True
    )  # OTIMIZADO: índice para ordenação
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("dashboard")
        verbose_name_plural = _("dashboards")
        ordering = ["-created_at"]
        # OTIMIZADO: Índices compostos para queries comuns
        indexes = [
            models.Index(fields=["cliente", "status"], name="dash_cliente_status_idx"),
            models.Index(fields=["servico", "status"], name="dash_servico_status_idx"),
            models.Index(
                fields=["-created_at", "status"], name="dash_created_status_idx"
            ),
        ]

    def __str__(self):
        return f"{self.nome} - {self.cliente}"

    def get_crs(self):
        """Retorna queryset de CRs relacionados"""
        return self.dashboard_crs.all()

    def get_cr_list(self):
        """Retorna lista de CRs relacionados"""
        return [dcr.cr for dcr in self.dashboard_crs.all() if dcr.cr]

    def get_cr_display(self):
        """Retorna string com CRs separados por vírgula"""
        crs = self.get_cr_list()
        return ", ".join(crs) if crs else "Nenhum CR"

    def get_cr_display_html(self):
        """Retorna string com CRs separados por quebra de linha HTML"""
        crs = self.get_cr_list()
        return "<br>".join(crs) if crs else "Nenhum CR"


class DashboardCR(models.Model):
    """Tabela intermediária para relacionar Dashboard com CRs da Estrutura"""

    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="dashboard_crs"
    )
    estrutura_id = models.CharField(
        max_length=36,
        verbose_name=_("ID da Estrutura"),
        help_text=_("ID da estrutura na tabela estrutura"),
    )
    cr = models.CharField(
        max_length=100, verbose_name=_("CR"), help_text=_("Código CR da estrutura")
    )

    class Meta:
        verbose_name = _("Dashboard CR")
        verbose_name_plural = _("Dashboard CRs")
        unique_together = ("dashboard", "estrutura_id")

    def __str__(self):
        return f"{self.dashboard.nome} - {self.cr}"

    @property
    def estrutura(self):
        """Retorna a estrutura relacionada"""
        try:
            return Estrutura.objects.get(id=self.estrutura_id)
        except Estrutura.DoesNotExist:
            return None


class Script(models.Model):
    """
    Modelo para scripts monitorados
    """

    STATUS_CHOICES = [
        ("Pendente", "Pendente"),
        ("Sucesso", "Sucesso"),
        ("Erro", "Erro"),
    ]

    nome = models.CharField(_("nome"), max_length=100)
    descricao = models.TextField(_("descrição"), blank=True)
    caminho = models.CharField(_("caminho"), max_length=255)
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="Pendente"
    )
    ultima_atualizacao = models.DateTimeField(_("última atualização"), auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, verbose_name=_("criado por"), on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("script")
        verbose_name_plural = _("scripts")
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class MonitoramentoLog(models.Model):
    """
    Log de eventos de monitoramento
    """

    tipo = models.CharField(
        _("tipo"), max_length=20, default="dashboard"
    )  # 'dashboard' ou 'script'
    item_id = models.IntegerField(_("ID do item"), default=0)
    status_anterior = models.CharField(
        _("status anterior"), max_length=20, default="Pendente"
    )
    status_novo = models.CharField(_("novo status"), max_length=20, default="Pendente")
    observacao = models.TextField(_("observação"), blank=True)
    usuario = models.ForeignKey(
        CustomUser, verbose_name=_("usuário"), on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("log de monitoramento")
        verbose_name_plural = _("logs de monitoramento")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tipo} {self.item_id} - {self.status_novo}"


class Service(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="service_logos/", null=True, blank=True)

    def __str__(self):
        return self.name


class LogoServico(models.Model):
    """
    Modelo para armazenar logos de serviços em base64
    """

    nome = models.CharField(_("nome do serviço"), max_length=100)
    img_base64 = models.TextField(_("logo em base64"))

    class Meta:
        db_table = "logo_servico"
        verbose_name = _("logo de serviço")
        verbose_name_plural = _("logos de serviços")
        ordering = ["nome"]
        managed = True  # Tabela já existe, não gerenciar via Django

    def __str__(self):
        return self.nome


class Estrutura(models.Model):
    id = models.CharField(max_length=36, primary_key=True)  # UUID como string
    descricao = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    status = models.IntegerField(
        null=True, blank=True, db_index=True
    )  # OTIMIZADO: índice para filtros
    qrcode = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    criado = models.DateTimeField(auto_now_add=True, null=True)
    hierarquiadescricao = models.CharField(max_length=255, null=True, blank=True)
    grupo = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    pec = models.CharField(max_length=100, null=True, blank=True)
    cr = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO: CRÍTICO!
    nivel_4 = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    nivel_5 = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    nivel_6 = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )  # OTIMIZADO
    nivel_7 = models.CharField(max_length=100, null=True, blank=True)
    nivel_8 = models.CharField(max_length=100, null=True, blank=True)
    nivel_9 = models.CharField(max_length=100, null=True, blank=True)
    nivel_10 = models.CharField(max_length=100, null=True, blank=True)
    nivel_11 = models.CharField(max_length=100, null=True, blank=True)
    diretor = models.CharField(max_length=100, null=True, blank=True)
    gr = models.CharField(max_length=100, null=True, blank=True)
    gc = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "estrutura"
        managed = True

    def __str__(self):
        return f"{self.descricao} - CR: {self.cr}"


class DesativacaoCR(models.Model):
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("solicitado", "Solicitado"),
        ("desativado", "Desativado"),
    ]

    contrato = models.CharField(max_length=100)
    solicitante = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ativo")
    datasolicitacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Gestao_a_Vista_desativacaocr"

    def __str__(self):
        return f"{self.contrato} - {self.solicitante}"


class ControleChip(models.Model):
    """
    Modelo para controle de chips
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    OPERADORA_CHOICES = [
        ("claro", "Claro"),
        ("vivo", "Vivo"),
        ("tim", "Tim"),
    ]

    STATUS_CHOICES = [
        ("solicitar", "Solicitar"),
        ("pendente_ativacao", "Pendente Ativação"),
        ("pendente_entrega", "Pendente Entrega"),
        ("entregue", "Entregue"),
    ]

    data = models.DateField(_("data"))
    id_portal = models.CharField(_("ID Portal"), max_length=100, null=True, blank=True)
    solicitante = models.CharField(_("solicitante"), max_length=255)
    cr = models.CharField(_("CR"), max_length=100)
    operadora = models.CharField(
        _("operadora"), max_length=20, choices=OPERADORA_CHOICES
    )
    numero_telefone = models.CharField(
        _("número telefone"), max_length=20, null=True, blank=True
    )
    responsavel_retirada = models.CharField(_("responsável retirada"), max_length=255)
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="solicitar"
    )
    observacoes = models.TextField(_("observações"), blank=True, null=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        db_table = "Gestao_a_Vista_controlechip"
        verbose_name = _("controle de chip")
        verbose_name_plural = _("controle de chips")
        ordering = ["-data", "-created_at"]

    def __str__(self):
        return f"{self.id_portal} - {self.numero_telefone}"


class AreaResponsavel(models.Model):
    """
    Modelo para áreas responsáveis da portaria base
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(_("nome"), max_length=255)
    ativa = models.BooleanField(_("ativa"), default=True)
    ordem = models.IntegerField(_("ordem"), default=0)

    class Meta:
        db_table = "area_responsavel"
        verbose_name = _("área responsável")
        verbose_name_plural = _("áreas responsáveis")
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class PortariaBase(models.Model):
    """
    Modelo para registro de entrada na portaria base
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        _("nome"), max_length=255, db_index=True
    )  # OTIMIZADO: índice para buscas
    cpf = models.IntegerField(
        _("CPF"), db_index=True
    )  # OTIMIZADO: índice para buscas por CPF
    data_nascimento = models.DateField(_("data de nascimento"))
    motivo_entrada = models.CharField(_("motivo da entrada"), max_length=255)
    user_cadastro = models.ForeignKey(
        CustomUser,
        verbose_name=_("usuário cadastro"),
        on_delete=models.CASCADE,
        db_index=True,  # OTIMIZADO
    )
    area_responsavel = models.ForeignKey(
        AreaResponsavel,
        verbose_name=_("área responsável"),
        on_delete=models.PROTECT,
        related_name="entradas",
        db_index=True,  # OTIMIZADO
    )
    liberado_por = models.CharField(
        _("liberado por"), max_length=255, blank=True, null=True
    )
    data = models.DateTimeField(
        _("data"), auto_now_add=True, db_index=True
    )  # OTIMIZADO: índice para filtros de data

    class Meta:
        db_table = "portaria_base"
        verbose_name = _("entrada portaria base")
        verbose_name_plural = _("entradas portaria base")
        ordering = ["-data"]
        # OTIMIZADO: Índices compostos para queries comuns
        indexes = [
            models.Index(
                fields=["-data", "area_responsavel"], name="portaria_data_area_idx"
            ),
            models.Index(fields=["nome", "cpf"], name="portaria_nome_cpf_idx"),
        ]

    def __str__(self):
        return f"{self.nome} - {self.data.strftime('%d/%m/%Y %H:%M')}"


class Unidade(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    ativa = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    @property
    def total_salas(self):
        """Retorna o número total de salas ativas desta unidade"""
        return self.salas_contrato.count()

    class Meta:
        db_table = "unidade"
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"


class GestaoSala(models.Model):
    id_sala = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    capacidade = models.IntegerField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    quantidade_m = models.IntegerField(
        help_text="Quantidade de mesas. Se 0 ou 1, a reserva será da sala inteira."
    )
    # ADICIONE A LINHA ABAIXO:
    foto = models.ImageField(upload_to='salas_fotos/', null=True, blank=True)
    
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, default=1, related_name="salas_contrato")

    def __str__(self):
        return f"{self.nome} - {self.unidade.nome}"

    def clean(self):
        """
        Validação customizada para garantir nomes únicos por unidade
        """
        from django.core.exceptions import ValidationError
        
        # Verificar se já existe uma sala com o mesmo nome na mesma unidade
        existing_sala = GestaoSala.objects.filter(
            nome__iexact=self.nome.strip(),
            unidade=self.unidade
        ).exclude(id_sala=self.id_sala)
        
        if existing_sala.exists():
            raise ValidationError({
                'nome': f'Já existe uma sala com o nome "{self.nome}" nesta unidade.'
            })

    class Meta:
        db_table = "gestao_sala"
        verbose_name = "Gestão de Sala"
        verbose_name_plural = "Gestão de Salas"
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'unidade'],
                name='unique_sala_nome_unidade'
            )
        ]

    @property
    def mesas(self):
        """Retorna uma lista de dicionários com as mesas da sala"""
        if self.quantidade_m <= 1:
            return []
        return [
            {"id": i + 1, "nome": f"Mesa {str(i+1).zfill(2)}"}
            for i in range(self.quantidade_m)
        ]


class ReservaSala(models.Model):
    id_reserva = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sala_id = models.UUIDField(db_column='sala_id')  # Referência UUID para GestaoSala
    data = models.DateField(null=True, blank=True)
    horario = models.CharField(max_length=255, null=True, blank=True)  # Campo que existe
    email = models.CharField(max_length=255, null=True, blank=True)
    telefone = models.CharField(max_length=255, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    mesa_id = models.IntegerField(null=True, blank=True, db_column='mesa_id')  # Campo que existe
    solicitante = models.CharField(max_length=255, null=True, blank=True)  # Campo que existe
    status = models.CharField(max_length=255, null=True, blank=True)  # Campo que existe
    created_at = models.DateTimeField(null=True, blank=True)  # Campo que existe
    updated_at = models.DateTimeField(null=True, blank=True)  # Campo que existe
    dia_inteiro = models.BooleanField(null=True, blank=True)  # Campo que existe
    servico_limpeza = models.BooleanField(default=False, null=True, blank=True)
    servico_entreposto = models.BooleanField(default=False, null=True, blank=True)
    servico_coffe = models.BooleanField(default=False, null=True, blank=True)
    
    # Propriedades para compatibilidade com o código existente
    @property
    def sala(self):
        """Simula ForeignKey para GestaoSala"""
        try:
            return GestaoSala.objects.get(id_sala=self.sala_id)
        except (GestaoSala.DoesNotExist, ValueError):
            return None
    
    @property
    def hora_inicio(self):
        """Converte horario para TimeField"""
        if self.horario:
            try:
                from datetime import datetime
                return datetime.strptime(self.horario, '%H:%M').time()
            except ValueError:
                return None
        return None
    
    @property
    def hora_fim(self):
        """Calcula hora_fim baseado em hora_inicio + 30 min"""
        if self.hora_inicio:
            from datetime import datetime, timedelta
            dt = datetime.combine(datetime.today(), self.hora_inicio)
            dt_fim = dt + timedelta(minutes=30)
            return dt_fim.time()
        return None
    
    @property
    def mesa_numero(self):
        """Alias para mesa_id"""
        return self.mesa_id
    
    @property
    def nome(self):
        """Alias para solicitante"""
        return self.solicitante or 'Reserva'
    
    @property
    def criado(self):
        """Alias para created_at"""
        return self.created_at
    
    @property
    def atualizado(self):
        """Alias para updated_at"""
        return self.updated_at

    class Meta:
        db_table = "reserva_sala"
        verbose_name = "Reserva de Sala"
        verbose_name_plural = "Reservas de Sala"
        ordering = ["-data", "horario"]
        indexes = [
            models.Index(fields=["sala_id", "data"], name="reservasala_sala_data_idx"),
            models.Index(fields=["data", "status"], name="reservasala_data_status_idx"),
        ]

    def __str__(self):
        sala_nome = self.sala.nome if self.sala else f"Sala {self.sala_id}"
        return f"{sala_nome} - {self.data} {self.horario or 'Sem horário'}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.db.models import Q
        
        # Validações básicas
        if not self.sala_id:
            raise ValidationError("Sala é obrigatória")
        
        if not self.data:
            raise ValidationError("Data é obrigatória")
            
        if not self.horario:
            raise ValidationError("Horário é obrigatório")
            
        # Verificar se a sala existe
        try:
            sala = GestaoSala.objects.get(id_sala=self.sala_id)
        except GestaoSala.DoesNotExist:
            raise ValidationError("Sala não encontrada")
        
        # Buscar reservas existentes na mesma sala, data e com status ativa
        conflitos = ReservaSala.objects.filter(
            sala_id=self.sala_id,
            data=self.data,
            status='ativa'
        )
        
        # Lógica de mesas:
        # - Se a sala está sendo reservada inteira (mesa_id nulo), verifica qualquer outra reserva no local
        # - Se for mesa específica, verifica sobreposição apenas nela ou com quem reservou a sala inteira
        if self.mesa_id:
            conflitos = conflitos.filter(Q(mesa_id=self.mesa_id) | Q(mesa_id__isnull=True))
            
        if self.pk:
            conflitos = conflitos.exclude(pk=self.pk)
            
        # Validar sobreposição de horários
        for reserva in conflitos:
            # Ignora caso não tenha conseguido converter horários (fail-safe)
            if not self.hora_inicio or not self.hora_fim or not reserva.hora_inicio or not reserva.hora_fim:
                continue
                
            # Verifica a sobreposição lógica de tempo
            if (self.hora_inicio < reserva.hora_fim and self.hora_fim > reserva.hora_inicio):
                raise ValidationError("Já existe uma reserva para este horário neste local.")
    
    def clean_original(self):
        from django.core.exceptions import ValidationError

        # Validar se a hora_fim é maior que hora_inicio
        if self.hora_fim <= self.hora_inicio:
            raise ValidationError("A hora final deve ser maior que a hora inicial")

        # Validar se o horário está dentro do horário de funcionamento da sala
        if (
            self.hora_inicio < self.sala.hora_inicio
            or self.hora_fim > self.sala.hora_fim
        ):
            raise ValidationError(
                "O horário deve estar dentro do horário de funcionamento da sala"
            )

        # Validar se já existe reserva para o mesmo horário
        reservas = ReservaSala.objects.filter(sala=self.sala, data=self.data)
        if self.mesa_numero:
            reservas = reservas.filter(mesa_numero=self.mesa_numero)
        else:
            reservas = reservas.filter(mesa_numero__isnull=True)

        if self.pk:
            reservas = reservas.exclude(pk=self.pk)

        for reserva in reservas:
            if (
                self.hora_inicio < reserva.hora_fim
                and self.hora_fim > reserva.hora_inicio
            ):
                raise ValidationError("Já existe uma reserva para este horário")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ShiftRecord(models.Model):
    """
    Modelo para registros de plantão no Livro ATA
    Conforme especificação do PRD - Seção 2.1
    """

    SHIFT_TYPE_CHOICES = [
        ("diurno", _("Diurno")),
        ("noturno", _("Noturno")),
        ("madrugada", _("Madrugada")),
        ("extra", _("Extra")),
    ]

    STATUS_CHOICES = [
        ("pendente", _("Pendente")),
        ("em_andamento", _("Em Andamento")),
        ("concluido", _("Concluído")),
        ("cancelado", _("Cancelado")),
    ]

    # Campos obrigatórios do PRD
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift_date = models.DateField(
        _("data do plantão"), db_index=True, null=True, blank=True
    )  # Renomeado de 'date'
    shift_type = models.CharField(
        _("tipo de plantão"), max_length=20, choices=SHIFT_TYPE_CHOICES, db_index=True
    )
    responsible_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_("usuário responsável"),
        related_name="shift_records",
        db_index=True,
        null=True,
        blank=True,
    )
    start_time = models.TimeField(
        _("horário de início"), null=True, blank=True
    )  # Renomeado de 'time'
    end_time = models.TimeField(_("horário de fim"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        db_index=True,
    )

    # Relacionamentos com modelos auxiliares
    template = models.ForeignKey(
        "ShiftTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("template"),
        related_name="shift_records",
        help_text=_("Template usado para criar este plantão"),
    )
    location_ref = models.ForeignKey(
        "ShiftLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("local de referência"),
        related_name="shift_records",
        help_text=_("Local cadastrado para este plantão"),
    )
    category = models.ForeignKey(
        "ShiftCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("categoria"),
        related_name="shift_records",
        help_text=_("Categoria do plantão"),
    )

    # Campos específicos do contexto (mantidos do modelo original)
    cr_number = models.CharField(_("número do CR"), max_length=20, db_index=True)
    guard_name = models.CharField(_("nome do vigilante"), max_length=255)
    guard_number = models.CharField(_("número do vigilante"), max_length=50)
    location = models.CharField(
        _("localização"), max_length=255
    )  # Mantido para compatibilidade
    description = models.TextField(_("descrição da ocorrência"), blank=True)

    # Campos de auditoria
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("registro de plantão")
        verbose_name_plural = _("registros de plantão")
        ordering = ["-shift_date", "-start_time"]
        # Índices compostos para queries comuns
        indexes = [
            models.Index(fields=["cr_number", "shift_date"], name="shift_cr_date_idx"),
            models.Index(fields=["shift_type", "status"], name="shift_type_status_idx"),
            models.Index(
                fields=["responsible_user", "shift_date"], name="shift_user_date_idx"
            ),
        ]

    def __str__(self):
        return f"Plantão {self.guard_name} - {self.shift_date} ({self.get_shift_type_display()})"

    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError

        # Validar se end_time é maior que start_time (considerando plantões noturnos)
        if self.end_time and self.start_time:
            # Para plantões noturnos, end_time pode ser menor que start_time
            # (ex: 22:00 às 06:00 do dia seguinte)
            # Só validamos se for o mesmo dia e end_time <= start_time
            if self.end_time <= self.start_time and self.shift_type not in [
                "noturno",
                "madrugada",
            ]:
                raise ValidationError(
                    {
                        "end_time": _(
                            "O horário de fim deve ser maior que o horário de início."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """Override do save para executar validações"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Calcula a duração do plantão em horas"""
        if self.end_time and self.start_time:
            from datetime import datetime, timedelta

            start = datetime.combine(self.shift_date, self.start_time)
            end = datetime.combine(self.shift_date, self.end_time)

            # Se end_time for menor que start_time, assumir que é no dia seguinte
            if self.end_time < self.start_time:
                end += timedelta(days=1)

            duration = end - start
            return duration.total_seconds() / 3600  # Retorna em horas
        return None

    def get_evidences_count(self):
        """Retorna o número de evidências anexadas"""
        return self.evidences.count()

    def get_attachments_count(self):
        """Retorna o número de anexos (documentos)"""
        return self.attachments.count()

    def get_total_files_count(self):
        """Retorna o número total de arquivos (evidências + anexos)"""
        return self.get_evidences_count() + self.get_attachments_count()

    def get_compliance_items_count(self):
        """Retorna o número de itens de conformidade"""
        return self.compliance_items.count()

    def get_compliance_percentage(self):
        """Calcula o percentual de conformidade"""
        items = self.compliance_items.exclude(status="nao_aplicavel")
        if not items:
            return 0

        conforme_count = items.filter(status="conforme").count()
        return int((conforme_count / items.count()) * 100)

    def get_critical_non_compliance_count(self):
        """Retorna o número de itens críticos não conformes"""
        return self.compliance_items.filter(
            priority="critica", status="nao_conforme"
        ).count()

    def get_pending_compliance_count(self):
        """Retorna o número de itens pendentes de verificação"""
        return self.compliance_items.filter(status="pendente").count()

    def get_compliance_by_area(self):
        """Retorna estatísticas de conformidade por área"""
        from django.db.models import Count, Q

        return (
            self.compliance_items.values("area")
            .annotate(
                total=Count("id"),
                conforme=Count("id", filter=Q(status="conforme")),
                nao_conforme=Count("id", filter=Q(status="nao_conforme")),
                pendente=Count("id", filter=Q(status="pendente")),
            )
            .order_by("area")
        )

    def has_critical_issues(self):
        """Verifica se há itens críticos não conformes"""
        return self.get_critical_non_compliance_count() > 0

    def is_compliance_complete(self):
        """Verifica se todos os itens foram verificados"""
        return self.get_pending_compliance_count() == 0

    def get_attachments_total_size(self):
        """Retorna o tamanho total dos anexos em bytes"""
        total_size = 0
        for attachment in self.attachments.all():
            if attachment.file_size:
                total_size += attachment.file_size
        return total_size


class ShiftEvidence(models.Model):
    """
    Modelo para evidências de plantão (fotos, etc)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift_record = models.ForeignKey(
        ShiftRecord,
        on_delete=models.CASCADE,
        related_name="evidences",
        verbose_name=_("registro de plantão"),
    )
    evidence_type = models.ForeignKey(
        "EvidenceType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("tipo de evidência"),
        related_name="evidences",
        help_text=_("Tipo/categoria desta evidência"),
    )
    image = models.ImageField(_("imagem"), upload_to="shift_evidences/")
    description = models.TextField(_("descrição"), blank=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("evidência de plantão")
        verbose_name_plural = _("evidências de plantão")

    def __str__(self):
        return f"Evidência {self.id} - Plantão {self.shift_record.guard_name}"


class ShiftAttachment(models.Model):
    """
    Modelo para anexos de plantão (documentos, PDFs, etc)
    Complementa o ShiftEvidence para tipos de arquivo não-imagem
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift_record = models.ForeignKey(
        ShiftRecord,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("registro de plantão"),
    )
    evidence_type = models.ForeignKey(
        "EvidenceType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("tipo de evidência"),
        related_name="attachments",
        help_text=_("Tipo/categoria deste anexo"),
    )
    file = models.FileField(
        _("arquivo"),
        upload_to="shift_attachments/",
        help_text=_(
            "Documentos, PDFs, planilhas e outros arquivos relacionados ao plantão"
        ),
    )
    name = models.CharField(
        _("nome do arquivo"),
        max_length=255,
        help_text=_("Nome descritivo para o arquivo"),
    )
    description = models.TextField(_("descrição"), blank=True)
    file_size = models.PositiveIntegerField(
        _("tamanho do arquivo"), null=True, blank=True, help_text=_("Tamanho em bytes")
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("anexo de plantão")
        verbose_name_plural = _("anexos de plantão")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Anexo {self.name} - Plantão {self.shift_record.guard_name}"

    def save(self, *args, **kwargs):
        """Override do save para capturar o tamanho do arquivo"""
        if self.file and hasattr(self.file, "size"):
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_size_human(self):
        """Retorna o tamanho do arquivo em formato legível"""
        if not self.file_size:
            return "Desconhecido"

        for unit in ["B", "KB", "MB", "GB"]:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


class ShiftComplianceItem(models.Model):
    """
    Modelo para itens de conformidade do plantão
    Checklist de verificação por área conforme PRD
    """

    STATUS_CHOICES = [
        ("conforme", _("Conforme")),
        ("nao_conforme", _("Não Conforme")),
        ("nao_aplicavel", _("Não Aplicável")),
        ("pendente", _("Pendente")),
    ]

    PRIORITY_CHOICES = [
        ("baixa", _("Baixa")),
        ("media", _("Média")),
        ("alta", _("Alta")),
        ("critica", _("Crítica")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift_record = models.ForeignKey(
        ShiftRecord,
        on_delete=models.CASCADE,
        related_name="compliance_items",
        verbose_name=_("registro de plantão"),
        db_index=True,
    )
    item_description = models.CharField(
        _("descrição do item"),
        max_length=255,
        help_text=_("Descrição do item de conformidade a ser verificado"),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        db_index=True,
    )
    priority = models.CharField(
        _("prioridade"),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="media",
        help_text=_("Prioridade do item de conformidade"),
    )
    area = models.CharField(
        _("área"),
        max_length=100,
        blank=True,
        help_text=_("Área ou setor relacionado ao item"),
    )
    order = models.IntegerField(
        _("ordem"), default=0, help_text=_("Ordem de exibição do item no checklist")
    )
    observations = models.TextField(_("observações"), blank=True)
    checked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("verificado por"),
        related_name="compliance_checks",
        help_text=_("Usuário que verificou este item"),
    )
    checked_at = models.DateTimeField(
        _("verificado em"),
        null=True,
        blank=True,
        help_text=_("Data e hora da verificação"),
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("item de conformidade")
        verbose_name_plural = _("itens de conformidade")
        ordering = ["order", "item_description"]
        # Índices compostos para queries comuns
        indexes = [
            models.Index(
                fields=["shift_record", "status"], name="compliance_shift_status_idx"
            ),
            models.Index(
                fields=["priority", "status"], name="compliance_priority_status_idx"
            ),
            models.Index(fields=["area", "status"], name="compliance_area_status_idx"),
        ]

    def __str__(self):
        return f"{self.item_description} - {self.get_status_display()}"

    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError

        # Se status não é pendente e não tem checked_at, definir automaticamente
        if self.status != "pendente" and not self.checked_at:
            from django.utils import timezone

            self.checked_at = timezone.now()

        # Validação mais flexível: só exige checked_by se checked_at foi definido explicitamente
        # e não foi definido automaticamente acima
        if (
            self.checked_at
            and not self.checked_by
            and hasattr(self, "_require_checked_by")
        ):
            raise ValidationError(
                {"checked_by": _("É obrigatório informar quem verificou este item.")}
            )

    def save(self, *args, **kwargs):
        """Override do save para executar validações"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_compliant(self):
        """Retorna True se o item está conforme"""
        return self.status == "conforme"

    @property
    def is_critical_non_compliant(self):
        """Retorna True se é um item crítico não conforme"""
        return self.priority == "critica" and self.status == "nao_conforme"

    def get_status_color(self):
        """Retorna cor para exibição baseada no status"""
        colors = {
            "conforme": "success",
            "nao_conforme": "danger",
            "nao_aplicavel": "secondary",
            "pendente": "warning",
        }
        return colors.get(self.status, "secondary")

    def get_priority_color(self):
        """Retorna cor para exibição baseada na prioridade"""
        colors = {
            "baixa": "info",
            "media": "primary",
            "alta": "warning",
            "critica": "danger",
        }
        return colors.get(self.priority, "primary")
    
    KANBAN_STATUS_CHOICES = [
        ('nao_conforme', 'Não Conforme'),
        ('em_preparo', 'Em Preparo'),
        ('concluido', 'Concluído'),
    ]
    
    kanban_status = models.CharField(
        max_length=20, 
        choices=KANBAN_STATUS_CHOICES, 
        default='nao_conforme',
        db_index=True
    )
    kanban_updated_at = models.DateTimeField(null=True, blank=True)


class ShiftTemplate(models.Model):
    """
    Modelo para templates de plantão
    Permite criar modelos pré-configurados para diferentes tipos de plantão
    """

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    shift_type = models.CharField(
        _("tipo de plantão"),
        max_length=20,
        choices=ShiftRecord.SHIFT_TYPE_CHOICES,
        help_text=_("Tipo de plantão padrão para este template"),
    )
    descricao = models.TextField(_("descrição"), blank=True)
    observacoes_padrao = models.TextField(
        _("observações padrão"),
        blank=True,
        help_text=_(
            "Observações que aparecerão automaticamente nos plantões criados com este template"
        ),
    )
    duracao_estimada = models.DurationField(
        _("duração estimada"),
        null=True,
        blank=True,
        help_text=_("Duração estimada do plantão (horas:minutos)"),
    )
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Template de Plantão")
        verbose_name_plural = _("Templates de Plantão")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_shift_type_display()})"


class ShiftLocation(models.Model):
    """
    Modelo para locais de plantão
    Cadastro de locais onde os plantões podem ocorrer
    """

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    codigo = models.CharField(
        _("código"),
        max_length=20,
        unique=True,
        help_text=_("Código identificador do local (ex: PORT-01)"),
    )
    endereco = models.TextField(_("endereço"), blank=True)
    responsavel = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("responsável"),
        related_name="locations_managed",
        help_text=_("Responsável pelo local"),
    )
    observacoes = models.TextField(_("observações"), blank=True)
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Local de Plantão")
        verbose_name_plural = _("Locais de Plantão")
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["codigo"], name="shift_location_codigo_idx"),
            models.Index(fields=["ativo"], name="shift_location_ativo_idx"),
        ]

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    def get_active_shifts_count(self):
        """Retorna o número de plantões ativos neste local"""
        return self.shift_records.filter(
            status__in=["pendente", "em_andamento"]
        ).count()


class ShiftCategory(models.Model):
    """
    Modelo para categorias de plantão
    Permite categorizar plantões por finalidade, área ou departamento
    """

    COLOR_CHOICES = [
        ("primary", _("Azul")),
        ("secondary", _("Cinza")),
        ("success", _("Verde")),
        ("danger", _("Vermelho")),
        ("warning", _("Amarelo")),
        ("info", _("Azul Claro")),
        ("light", _("Claro")),
        ("dark", _("Escuro")),
    ]

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    descricao = models.TextField(_("descrição"), blank=True)
    cor = models.CharField(
        _("cor"),
        max_length=20,
        choices=COLOR_CHOICES,
        default="primary",
        help_text=_("Cor para identificação visual da categoria"),
    )
    icone = models.CharField(
        _("ícone"),
        max_length=50,
        blank=True,
        help_text=_("Classe CSS do ícone (ex: fas fa-shield-alt)"),
    )
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Categoria de Plantão")
        verbose_name_plural = _("Categorias de Plantão")
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_shifts_count(self):
        """Retorna o número de plantões nesta categoria"""
        return self.shift_records.count()


class EvidenceType(models.Model):
    """
    Modelo para tipos de evidência
    Classifica os tipos de evidências que podem ser coletadas
    """

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    descricao = models.TextField(_("descrição"), blank=True)
    obrigatorio = models.BooleanField(
        _("obrigatório"),
        default=False,
        help_text=_(
            "Se marcado, este tipo de evidência será obrigatório em todos os plantões"
        ),
    )
    aceita_multiplos = models.BooleanField(
        _("aceita múltiplos"),
        default=True,
        help_text=_(
            "Se marcado, permite múltiplas evidências deste tipo no mesmo plantão"
        ),
    )
    extensoes_permitidas = models.CharField(
        _("extensões permitidas"),
        max_length=200,
        blank=True,
        help_text=_(
            "Extensões de arquivo permitidas, separadas por vírgula (ex: jpg,png,pdf)"
        ),
    )
    tamanho_maximo_mb = models.PositiveIntegerField(
        _("tamanho máximo (MB)"),
        null=True,
        blank=True,
        help_text=_("Tamanho máximo do arquivo em MB"),
    )
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Tipo de Evidência")
        verbose_name_plural = _("Tipos de Evidência")
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_extensions_list(self):
        """Retorna lista das extensões permitidas"""
        if self.extensoes_permitidas:
            return [ext.strip().lower() for ext in self.extensoes_permitidas.split(",")]
        return []

    def is_extension_allowed(self, filename):
        """Verifica se a extensão do arquivo é permitida"""
        if not self.extensoes_permitidas:
            return True

        file_ext = filename.lower().split(".")[-1] if "." in filename else ""
        return file_ext in self.get_extensions_list()


class ComplianceTemplate(models.Model):
    """
    Modelo para templates de conformidade
    Define templates de checklist para diferentes áreas ou tipos de plantão
    """

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    area = models.CharField(
        _("área"),
        max_length=100,
        help_text=_("Área ou departamento relacionado (ex: Segurança, Limpeza)"),
    )
    descricao = models.TextField(_("descrição"), blank=True)
    shift_types = models.CharField(
        _("tipos de plantão"),
        max_length=100,
        blank=True,
        help_text=_(
            "Tipos de plantão onde este template se aplica (separados por vírgula)"
        ),
    )
    items_padrao = models.JSONField(
        _("itens padrão"),
        default=list,
        help_text=_("Lista de itens de conformidade padrão para este template"),
    )
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Template de Conformidade")
        verbose_name_plural = _("Templates de Conformidade")
        ordering = ["area", "nome"]
        indexes = [
            models.Index(fields=["area"], name="compliance_template_area_idx"),
            models.Index(fields=["ativo"], name="compliance_template_ativo_idx"),
        ]

    def __str__(self):
        return f"{self.nome} - {self.area}"

    def get_shift_types_list(self):
        """Retorna lista dos tipos de plantão aplicáveis"""
        if self.shift_types:
            return [t.strip() for t in self.shift_types.split(",")]
        return []

    def is_applicable_to_shift_type(self, shift_type):
        """Verifica se o template é aplicável ao tipo de plantão"""
        if not self.shift_types:
            return True  # Se não especificado, aplica a todos
        return shift_type in self.get_shift_types_list()

    def create_compliance_items_for_shift(self, shift_record):
        """Cria itens de conformidade para um plantão baseado no template"""
        items_created = []
        for item_data in self.items_padrao:
            if isinstance(item_data, dict):
                compliance_item = ShiftComplianceItem.objects.create(
                    shift_record=shift_record,
                    item_description=item_data.get("description", ""),
                    priority=item_data.get("priority", "media"),
                    area=self.area,
                    order=item_data.get("order", 0),
                )
                items_created.append(compliance_item)
        return items_created


def get_default_data_conclusao():
    return timezone.now() + timezone.timedelta(days=30)


class TipoServico(models.Model):
    """
    Modelo para gerenciar tipos de serviço do Planner
    """

    nome = models.CharField(_("nome"), max_length=100, unique=True)
    ativo = models.BooleanField(_("ativo"), default=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("Tipo de Serviço")
        verbose_name_plural = _("Tipos de Serviço")
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PlannerChecklistItem(models.Model):
    """
    Modelo para itens da lista de verificação do Planner
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projeto = models.ForeignKey(
        "PlannerProject", on_delete=models.CASCADE, related_name="checklist_items"
    )
    texto = models.CharField(_("texto"), max_length=255)
    concluido = models.BooleanField(_("concluído"), default=False)
    ordem = models.IntegerField(_("ordem"), default=0)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Item da Lista de Verificação")
        verbose_name_plural = _("Itens da Lista de Verificação")
        ordering = ["ordem", "created_at"]

    def __str__(self):
        return f"{self.texto} - {self.projeto.nome}"


class PlannerProjectResponsavel(models.Model):
    """
    Modelo para relacionar projetos e responsáveis
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projeto = models.ForeignKey(
        "PlannerProject", on_delete=models.CASCADE, related_name="projeto_responsaveis"
    )
    responsavel = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="responsavel_projetos"
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("Responsável do Projeto")
        verbose_name_plural = _("Responsáveis do Projeto")
        unique_together = ("projeto", "responsavel")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.responsavel.name} - {self.projeto.nome}"


class PlannerPipelineStage(models.Model):
    """Etapa configurável do pipeline CRM/Kanban de demandas."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(_("nome da etapa"), max_length=80, unique=True)
    cor = models.CharField(_("cor"), max_length=20, default="#2563eb")
    ordem = models.PositiveIntegerField(_("ordem"), default=0, db_index=True)
    ativo = models.BooleanField(_("ativo"), default=True, db_index=True)
    status_legado = models.CharField(_("status legado"), max_length=80, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    DEFAULT_STAGES = [
        ("Entrada / Backlog", "#2563eb", 10),
        ("Triagem", "#7c3aed", 20),
        ("Planejamento 5W2H", "#0891b2", 30),
        ("Em Execução", "#f59e0b", 40),
        ("Aguardando Terceiros / Cliente", "#ea580c", 50),
        ("Validação / Testes", "#4f46e5", 60),
        ("Concluído", "#16a34a", 70),
        ("Cancelado / Suspenso", "#64748b", 80),
    ]

    class Meta:
        verbose_name = _("Etapa do pipeline CRM")
        verbose_name_plural = _("Etapas do pipeline CRM")
        ordering = ["ordem", "nome"]
        indexes = [models.Index(fields=["ativo", "ordem"], name="planner_stage_active_order_idx")]

    def __str__(self):
        return self.nome

    @classmethod
    def ensure_default_pipeline(cls):
        stages = list(cls.objects.filter(ativo=True).order_by("ordem", "nome"))
        if stages:
            return stages
        for nome, cor, ordem in cls.DEFAULT_STAGES:
            cls.objects.get_or_create(
                nome=nome,
                defaults={"cor": cor, "ordem": ordem, "ativo": True, "status_legado": nome},
            )
        return list(cls.objects.filter(ativo=True).order_by("ordem", "nome"))

class PlannerProject(models.Model):
    """
    Modelo para projetos do Planner
    """

    STATUS_CHOICES = [
        ("Entrada / Backlog", "Entrada / Backlog"),
        ("Triagem", "Triagem"),
        ("Planejamento 5W2H", "Planejamento 5W2H"),
        ("Em Execução", "Em Execução"),
        ("Aguardando Terceiros / Cliente", "Aguardando Terceiros / Cliente"),
        ("Validação / Testes", "Validação / Testes"),
        ("Concluído", "Concluído"),
        ("Cancelado / Suspenso", "Cancelado / Suspenso"),
    ]

    PRIORITY_CHOICES = [
        ("Crítica", "Crítica"),
        ("Alto", "Alto"),
        ("Médio", "Médio"),
        ("Baixo", "Baixo"),
    ]

    TIPO_DEMANDA_CHOICES = [
        ("implantacao", "Implantação"),
        ("acompanhamento", "Acompanhamento"),
        ("ocorrencia", "Ocorrência"),
        ("desenvolvimento", "Desenvolvimento de Sistemas"),
        ("melhoria", "Melhoria"),
        ("suporte", "Suporte"),
        ("treinamento", "Treinamento"),
    ]

    IMPACTO_CHOICES = [
        ("Baixo", "Baixo"),
        ("Médio", "Médio"),
        ("Alto", "Alto"),
        ("Crítico", "Crítico"),
    ]

    AMBIENTE_CHOICES = [
        ("", "Não se aplica"),
        ("producao", "Produção"),
        ("homologacao", "Homologação"),
        ("desenvolvimento", "Desenvolvimento"),
    ]

    CRM_TIPO_CHOICES = [
        ("operacional", "Operacional"),
        ("analitico_360", "Analítico / Visão 360º"),
        ("colaborativo", "Colaborativo"),
    ]

    CANAL_RELACIONAMENTO_CHOICES = [
        ("", "Não informado"),
        ("reuniao", "Reunião"),
        ("email", "E-mail"),
        ("telefone", "Telefone"),
        ("whatsapp", "WhatsApp"),
        ("chamado", "Chamado / Service Desk"),
        ("presencial", "Presencial"),
        ("outro", "Outro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        _("nome"), max_length=255, db_index=True
    )  # OTIMIZADO: índice para buscas
    responsaveis = models.ManyToManyField(
        CustomUser,
        through="PlannerProjectResponsavel",
        related_name="projetos",
        verbose_name=_("responsáveis"),
    )
    data_inicial = models.DateField(_("data inicial"), default=timezone.now)
    data_conclusao = models.DateField(
        _("data de conclusão"), default=get_default_data_conclusao, db_index=True
    )  # OTIMIZADO
    prioridade = models.CharField(
        _("prioridade"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="Médio",
        db_index=True,
    )  # OTIMIZADO
    observacao = models.TextField(_("observação"), blank=True, null=True)

    # Classificação operacional da demanda
    tipo_demanda = models.CharField(
        _("tipo da demanda"),
        max_length=30,
        choices=TIPO_DEMANDA_CHOICES,
        default="implantacao",
        db_index=True,
    )
    impacto = models.CharField(_("impacto"), max_length=20, choices=IMPACTO_CHOICES, default="Médio", db_index=True)
    solicitante = models.CharField(_("solicitante"), max_length=255, blank=True, null=True)
    responsavel_tecnico = models.CharField(_("responsável técnico"), max_length=255, blank=True, null=True)
    validador = models.CharField(_("validador"), max_length=255, blank=True, null=True)
    sla = models.CharField(_("SLA"), max_length=80, blank=True, null=True)
    percentual_progresso = models.PositiveSmallIntegerField(_("progresso (%)"), default=0)

    # Campos específicos para implantação, ocorrências e desenvolvimento
    modulo_sistema = models.CharField(_("módulo/sistema"), max_length=160, blank=True, null=True)
    ambiente = models.CharField(_("ambiente"), max_length=30, choices=AMBIENTE_CHOICES, blank=True, default="")
    etapa_implantacao = models.CharField(_("etapa da implantação"), max_length=160, blank=True, null=True)
    go_live_previsto = models.DateField(_("go-live previsto"), null=True, blank=True)
    treinamento_realizado = models.BooleanField(_("treinamento realizado?"), default=False)
    severidade = models.CharField(_("severidade"), max_length=20, choices=IMPACTO_CHOICES, blank=True, null=True)
    causa_raiz = models.TextField(_("causa raiz"), blank=True, null=True)
    acao_corretiva = models.TextField(_("ação corretiva"), blank=True, null=True)
    acao_preventiva = models.TextField(_("ação preventiva"), blank=True, null=True)
    link_referencia = models.URLField(_("link / PR / commit / documentação"), blank=True, null=True)
    criterio_aceite = models.TextField(_("critério de aceite"), blank=True, null=True)

    # Informações contextuais por etapa do Kanban
    triagem_diagnostico = models.TextField(_("triagem - diagnóstico"), blank=True, null=True)
    triagem_priorizacao = models.TextField(_("triagem - prioridade/impacto"), blank=True, null=True)
    planejamento_entregaveis = models.TextField(_("planejamento - entregáveis"), blank=True, null=True)
    planejamento_riscos = models.TextField(_("planejamento - riscos/dependências"), blank=True, null=True)
    execucao_andamento = models.TextField(_("execução - andamento"), blank=True, null=True)
    validacao_resultado = models.TextField(_("validação - resultado"), blank=True, null=True)

    # Campos de CRM
    cliente = models.CharField(_("cliente"), max_length=255, blank=True, null=True, db_index=True)
    contato = models.CharField(_("contato"), max_length=255, blank=True, null=True)
    telefone = models.CharField(_("telefone"), max_length=50, blank=True, null=True)
    email = models.EmailField(_("email"), blank=True, null=True)
    origem_lead = models.CharField(_("origem do lead"), max_length=120, blank=True, null=True)
    valor_estimado = models.DecimalField(_("valor estimado"), max_digits=12, decimal_places=2, null=True, blank=True)
    probabilidade = models.PositiveSmallIntegerField(_("probabilidade (%)"), default=0)
    proxima_acao = models.CharField(_("próxima ação"), max_length=255, blank=True, null=True)

    # CRM profissional: visão 360º, operação e colaboração entre áreas
    crm_tipo = models.CharField(_("tipo de CRM"), max_length=30, choices=CRM_TIPO_CHOICES, default="operacional", db_index=True)
    visao_360 = models.TextField(_("visão 360º do cliente/demanda"), blank=True, null=True)
    saude_relacionamento = models.CharField(_("saúde do relacionamento"), max_length=40, blank=True, null=True)
    canal_relacionamento = models.CharField(_("canal de relacionamento"), max_length=30, choices=CANAL_RELACIONAMENTO_CHOICES, blank=True, default="")
    ultima_interacao = models.DateField(_("última interação"), null=True, blank=True)
    proxima_interacao = models.DateField(_("próxima interação"), null=True, blank=True)
    departamentos_envolvidos = models.CharField(_("departamentos envolvidos"), max_length=255, blank=True, null=True)
    stakeholders = models.TextField(_("stakeholders e papéis"), blank=True, null=True)
    resumo_colaborativo = models.TextField(_("resumo colaborativo"), blank=True, null=True)

    # Método 5W2H
    w2h_what = models.TextField(_("5W2H - What / O quê"), blank=True, null=True)
    w2h_why = models.TextField(_("5W2H - Why / Por quê"), blank=True, null=True)
    w2h_where = models.CharField(_("5W2H - Where / Onde"), max_length=255, blank=True, null=True)
    w2h_when = models.DateField(_("5W2H - When / Quando"), null=True, blank=True)
    w2h_who = models.CharField(_("5W2H - Who / Quem"), max_length=255, blank=True, null=True)
    w2h_how = models.TextField(_("5W2H - How / Como"), blank=True, null=True)
    w2h_how_much = models.DecimalField(_("5W2H - How much / Quanto custa"), max_digits=12, decimal_places=2, null=True, blank=True)

    etapa = models.ForeignKey(
        PlannerPipelineStage,
        on_delete=models.SET_NULL,
        related_name="projetos",
        verbose_name=_("etapa do pipeline"),
        null=True,
        blank=True,
        db_index=True,
    )
    status = models.CharField(
        _("status"),
        max_length=80,
        choices=STATUS_CHOICES,
        default="Entrada / Backlog",
        db_index=True,
    )  # Mantido para compatibilidade com relatórios/histórico
    tipo_servico = models.ForeignKey(
        TipoServico,
        on_delete=models.CASCADE,
        related_name="projetos",
        verbose_name=_("tipo de serviço"),
        null=True,
        blank=True,
        db_index=True,
    )  # OTIMIZADO
    created_at = models.DateTimeField(
        _("criado em"), auto_now_add=True, db_index=True
    )  # OTIMIZADO
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Projeto")
        verbose_name_plural = _("Projetos")
        ordering = ["-created_at"]
        # OTIMIZADO: Índices compostos para queries comuns
        indexes = [
            models.Index(
                fields=["status", "data_conclusao"], name="planner_status_conclusao_idx"
            ),
            models.Index(
                fields=["prioridade", "data_conclusao"],
                name="planner_prior_conclusao_idx",
            ),
            models.Index(
                fields=["tipo_servico", "status"], name="planner_tipo_status_idx"
            ),
            models.Index(
                fields=["tipo_demanda", "status"], name="planner_demanda_status_idx"
            ),
            models.Index(
                fields=["etapa", "data_conclusao"], name="planner_etapa_conclusao_idx"
            ),
        ]

    def __str__(self):
        return self.nome

    @property
    def tipo(self):
        """Propriedade para manter compatibilidade com código existente"""
        return self.tipo_servico.nome if self.tipo_servico else "Sem tipo"

    def get_responsaveis_display(self):
        """Retorna uma lista formatada dos responsáveis - OTIMIZADO"""
        # Usar cache para evitar múltiplas consultas
        if not hasattr(self, '_responsaveis_cache'):
            responsaveis = []
            # Usar select_related para evitar N+1 queries
            for resp in self.projeto_responsaveis.select_related('responsavel').all():
                responsaveis.append(resp.responsavel.name)
            self._responsaveis_cache = ", ".join(responsaveis) if responsaveis else "Sem responsáveis"
        return self._responsaveis_cache

    def get_checklist_progress(self):
        """Retorna o progresso da lista de verificação"""
        items = self.checklist_items.all()
        if not items:
            return 0
        completed = items.filter(concluido=True).count()
        return int((completed / items.count()) * 100)

class PlannerComment(models.Model):
    """
    Modelo para comentários em projetos
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projeto = models.ForeignKey(
        PlannerProject, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="comentarios_planner"
    )
    conteudo = models.TextField(_("conteúdo"))
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("comentário")
        verbose_name_plural = _("comentários")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comentário de {self.autor.name} em {self.projeto.nome}"


class PlannerAttachment(models.Model):
    """
    Modelo para anexos em projetos
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projeto = models.ForeignKey(
        PlannerProject, on_delete=models.CASCADE, related_name="anexos"
    )
    nome = models.CharField(_("nome"), max_length=255)
    arquivo = models.FileField(_("arquivo"), upload_to="planner_attachments/")
    uploaded_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="anexos_planner"
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("anexo")
        verbose_name_plural = _("anexos")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Anexo {self.nome} - {self.projeto.nome}"


# Histórico de Mudanças do Projeto
class PlannerProjectChangeHistory(models.Model):
    """
    Modelo para rastrear histórico de mudanças em projetos do Planner
    Registra todas as alterações feitas nos campos do projeto
    """
    CHANGE_TYPE_CHOICES = [
        ("criado", _("Criado")),
        ("atualizado", _("Atualizado")),
        ("status_alterado", _("Status Alterado")),
        ("prioridade_alterada", _("Prioridade Alterada")),
        ("responsavel_adicionado", _("Responsável Adicionado")),
        ("responsavel_removido", _("Responsável Removido")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Projeto que foi alterado
    projeto = models.ForeignKey(
        PlannerProject,
        on_delete=models.CASCADE,
        related_name="change_history",
        verbose_name=_("projeto"),
        db_index=True
    )

    # Usuário que fez a alteração
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("usuário"),
        related_name="project_changes_made"
    )

    # Tipo de alteração
    tipo_alteracao = models.CharField(
        _("tipo de alteração"),
        max_length=30,
        choices=CHANGE_TYPE_CHOICES,
        db_index=True
    )

    # Campo que foi alterado
    campo = models.CharField(
        _("campo alterado"),
        max_length=100,
        help_text=_("Nome do campo que foi alterado"),
        blank=True
    )

    # Valores antes e depois
    valor_anterior = models.TextField(
        _("valor anterior"),
        blank=True,
        null=True,
        help_text=_("Valor antes da alteração")
    )

    valor_novo = models.TextField(
        _("valor novo"),
        blank=True,
        null=True,
        help_text=_("Valor depois da alteração")
    )

    # Descrição adicional
    descricao = models.TextField(
        _("descrição"),
        blank=True,
        help_text=_("Descrição adicional sobre a alteração")
    )

    # Metadata
    created_at = models.DateTimeField(
        _("data/hora da alteração"),
        auto_now_add=True,
        db_index=True
    )

    ip_address = models.CharField(
        _("endereço IP"),
        max_length=45,
        blank=True,
        help_text=_("IP do usuário que fez a alteração")
    )

    class Meta:
        verbose_name = _("Histórico de Alteração do Projeto")
        verbose_name_plural = _("Históricos de Alteração dos Projetos")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["projeto", "-created_at"], name="proj_change_date_idx"),
            models.Index(fields=["usuario", "-created_at"], name="user_change_date_idx"),
            models.Index(fields=["tipo_alteracao"], name="change_type_idx"),
        ]

    def __str__(self):
        return f"{self.projeto.nome} - {self.get_tipo_alteracao_display()} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"


# Torre de Controle Models
class CRKPI(models.Model):
    TIPO_SERVICO_CHOICES = [
        ("vigilancia", _("Vigilância")),
        ("facilities", _("Facilities")),
        ("manutencao", _("Manutenção")),
        ("limpeza", _("Limpeza")),
    ]

    cr = models.CharField(_("CR"), max_length=20, unique=True)
    cliente = models.CharField(_("cliente"), max_length=200)
    gerente = models.CharField(_("gerente"), max_length=100)
    tipo_servico = models.CharField(
        _("tipo de serviço"), max_length=20, choices=TIPO_SERVICO_CHOICES
    )

    # Performance
    performance_diurno = models.IntegerField(
        _("performance diurno"),
        null=True,
        blank=True,
        help_text="Percentual de 0 a 100",
    )
    performance_noturno = models.IntegerField(
        _("performance noturno"),
        null=True,
        blank=True,
        help_text="Percentual de 0 a 100",
    )
    performance_total = models.IntegerField(
        _("performance total"), help_text="Percentual de 0 a 100"
    )

    # Visita Operacional
    visita_operacional_concluida = models.BooleanField(
        _("visita operacional concluída"), default=False
    )
    data_ultima_visita = models.DateField(
        _("data última visita"), null=True, blank=True
    )

    # NPS
    nps = models.DecimalField(
        _("NPS"), max_digits=3, decimal_places=1, help_text="Nota de 0.0 a 10.0"
    )

    # Observações
    observacoes = models.TextField(_("observações"), blank=True)

    # Auditoria
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("CR KPI")
        verbose_name_plural = _("CRs KPI")
        ordering = ["cliente", "cr"]

    def __str__(self):
        return f"{self.cr} - {self.cliente}"

    @property
    def get_tipo_servico_display_formatted(self):
        return dict(self.TIPO_SERVICO_CHOICES).get(self.tipo_servico, self.tipo_servico)


class GerenteKPI(models.Model):
    nome = models.CharField(_("nome"), max_length=100, unique=True)
    clientes = models.IntegerField(_("número de clientes"), default=0)
    percentual_geral = models.DecimalField(
        _("percentual geral"), max_digits=5, decimal_places=2
    )

    # Serviços Média
    servicos_media_ronda = models.DecimalField(
        _("média ronda"), max_digits=5, decimal_places=2, default=0
    )
    servicos_media_facilities = models.DecimalField(
        _("média facilities"), max_digits=5, decimal_places=2, default=0
    )
    servicos_media_manutencao = models.DecimalField(
        _("média manutenção"), max_digits=5, decimal_places=2, default=0
    )

    # Visitas Operacionais
    visitas_concluidas = models.IntegerField(_("visitas concluídas"), default=0)
    visitas_total = models.IntegerField(_("total de visitas"), default=0)

    # NPS Média
    nps_media = models.DecimalField(_("NPS média"), max_digits=3, decimal_places=2)

    # Auditoria
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Gerente KPI")
        verbose_name_plural = _("Gerentes KPI")
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def percentual_visitas(self):
        if self.visitas_total == 0:
            return 0
        return (self.visitas_concluidas / self.visitas_total) * 100


# Relatórios Models
class RelatorioItem(models.Model):
    TIPO_CHOICES = [
        ("EPI", _("Inspeção de EPI")),
        ("APR", _("APR - Viagem Segura")),
    ]

    numero = models.CharField(_("número"), max_length=50, unique=True)
    nome = models.CharField(_("nome"), max_length=200)
    cr = models.CharField(_("CR"), max_length=20)
    responsavel = models.CharField(_("responsável"), max_length=100)
    data = models.DateField(_("data"))
    tipo = models.CharField(_("tipo"), max_length=3, choices=TIPO_CHOICES)

    # Arquivo do relatório (opcional - para futura implementação)
    arquivo = models.FileField(
        _("arquivo"), upload_to="relatorios/", null=True, blank=True
    )

    # Auditoria
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Relatório")
        verbose_name_plural = _("Relatórios")
        ordering = ["-data", "-created_at"]

    def __str__(self):
        return f"{self.numero} - {self.nome}"

    @property
    def get_tipo_display_formatted(self):
        return dict(self.TIPO_CHOICES).get(self.tipo, self.tipo)


class ErrosDashboard(models.Model):
    """
    Modelo para registrar erros de dashboards
    """

    dashboard = models.CharField(_("dashboard"), max_length=255)
    data = models.DateTimeField(_("data"), default=timezone.now)
    prox_att = models.DateTimeField(_("próxima atualização"), null=True, blank=True)
    atualizacao = models.CharField(_("atualização"), max_length=50, default="erro")

    class Meta:
        db_table = "erros_dashboard"
        verbose_name = _("Erro de Dashboard")
        verbose_name_plural = _("Erros de Dashboard")
        ordering = ["-data"]  # Ordenar do mais recente para o mais antigo
        managed = True  # Tabela não gerenciada pelo Django (existe no PostgreSQL)

    def __str__(self):
        return f"{self.dashboard} - {self.data.strftime('%d/%m/%Y %H:%M')}"


class ImplantacoesOpsVista(models.Model):
    """
    Modelo para Implantações OpsVista
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('desmobilizado', 'Desmobilizado'),
    ]

    SERVICO_CHOICES = [
        ('seguranca', 'Segurança'),
        ('facilities', 'Facilities'),
        ('portaria', 'Portaria'),
        ('manutencao', 'Manutenção'),
        ('jardinagem', 'Jardinagem'),
        ('brigadista', 'Brigadista'),
    ]

    DASHBOARDS_CHOICES = [
        ('regional', 'Regional'),
        ('corporativo', 'Corporativo'),
        ('nao_possui', 'Não Possui'),
    ]

    # Campo CR como CharField que referencia estrutura.id
    cr_id = models.CharField(
        max_length=100,
        verbose_name=_('CR'),
        help_text=_('Centro de Responsabilidade'),
        db_column='cr_id',
    )

    sistema = models.CharField(
        _('sistema'), max_length=255, help_text=_('Nome do sistema OpsVista')
    )

    # Campo implantações como JSONField para múltiplos valores
    implantacoes = models.JSONField(
        _('implantações'), default=list, help_text=_('Lista de implantações realizadas')
    )

    # Campo dashboards
    dashboards = models.CharField(
        _('dashboards'),
        max_length=20,
        choices=DASHBOARDS_CHOICES,
        default='nao_possui',
        help_text=_('Tipo de dashboard disponível')
    )

    status = models.CharField(
        _('status'), max_length=20, choices=STATUS_CHOICES, default='ativo'
    )

    servico = models.CharField(_('serviço'), max_length=20, choices=SERVICO_CHOICES)

    observacoes = models.TextField(
        _('observações'),
        blank=True,
        null=True,
        help_text=_('Observações adicionais sobre a implantação'),
    )

    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_implantacoesopsvista'
        verbose_name = _('Implantação OpsVista')
        verbose_name_plural = _('Implantações OpsVista')
        ordering = ['-created_at']

    @property
    def cr(self):
        """Propriedade para acessar o objeto Estrutura"""
        if hasattr(self, '_cr_cache'):
            return self._cr_cache
        try:
            self._cr_cache = Estrutura.objects.get(id=self.cr_id)
            return self._cr_cache
        except Estrutura.DoesNotExist:
            return None
    
    def __str__(self):
        # Usar apenas cr_id para evitar problemas com managed=False
        return f'{self.cr_id} - {self.sistema}'

    def get_implantacoes_display(self):
        """Retorna as implantações como string formatada"""
        if isinstance(self.implantacoes, list):
            return ', '.join(self.implantacoes)
        return str(self.implantacoes)


class LivroAtaQRCode(models.Model):
    """
    Modelo para armazenar QR Codes do Livro de Ata
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CR referenciado (estrutura.id onde nivel_4 is null)
    cr_id = models.CharField(
        max_length=100,
        verbose_name=_("CR"),
        help_text=_("Centro de Responsabilidade"),
        unique=True,  # Cada CR pode ter apenas um QR code do Livro Ata
        db_index=True
    )
    
    # Descrição do CR (copiada da tabela estrutura)
    cr_descricao = models.CharField(
        _("descrição do CR"), 
        max_length=500, 
        blank=True, 
        null=True,
        help_text=_("Descrição do Centro de Responsabilidade")
    )
    
    # URL do QR Code gerado
    qr_code_url = models.URLField(
        _("URL do QR Code"),
        help_text=_("URL completa do QR Code: <SITE_URL>/livroata/qrcode=<id>")
    )
    
    # Dados adicionais
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)
    
    class Meta:
        db_table = "Gestao_a_Vista_livroataqrcode"
        verbose_name = _("QR Code Livro Ata")
        verbose_name_plural = _("QR Codes Livro Ata")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['cr_id']),
        ]
    
    def __str__(self):
        return f"Livro Ata - {self.cr_id} ({self.cr_descricao})"
    
    @property
    def qr_code_data(self):
        """Retorna os dados que devem estar no QR Code"""
        return self.qr_code_url
    
    def save(self, *args, **kwargs):
        # Gerar URL automaticamente se não existir
        if not self.qr_code_url:
            from django.conf import settings
            self.qr_code_url = f"{settings.SITE_URL}/livroata/qrcode={self.id}"
        super().save(*args, **kwargs)


# ================== GESTÃO DA QUALIDADE ==================

class Treinamento(models.Model):
    """
    Modelo para Gestão de Treinamentos
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.DateField(_('data'), help_text=_('Data do treinamento'))
    tema = models.CharField(_('tema'), max_length=255, help_text=_('Tema do treinamento'))
    local = models.CharField(_('local/contrato'), max_length=255, help_text=_('Local ou contrato'))
    responsavel = models.CharField(_('responsável'), max_length=255, help_text=_('Nome do responsável'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(_('observações'), blank=True, null=True)

    # Auditoria
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='treinamentos_criados', verbose_name=_('criado por'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_treinamento'
        verbose_name = _('Treinamento')
        verbose_name_plural = _('Treinamentos')
        ordering = ['-data']

    def __str__(self):
        return f'{self.tema} - {self.data}'


class VisitaTecnica(models.Model):
    """
    Modelo para Visitas Técnicas e Inspeções
    """
    TIPO_CHOICES = [
        ('inspecao', 'Inspeção'),
        ('auditoria', 'Auditoria'),
        ('visita_tecnica', 'Visita Técnica'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]

    RESULTADO_CONFORMIDADE_CHOICES = [
        ('conforme', 'Conforme'),
        ('nao_conforme', 'Não Conforme'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.DateField(_('data'), help_text=_('Data da visita/inspeção'))
    tipo = models.CharField(_('tipo'), max_length=20, choices=TIPO_CHOICES, default='visita_tecnica')
    local = models.CharField(_('local'), max_length=255, help_text=_('Local da visita'))
    responsavel = models.CharField(_('responsável'), max_length=255, help_text=_('Nome do responsável'))
    checklist = models.JSONField(_('checklist'), default=dict, blank=True, help_text=_('Checklist básico em formato JSON'))
    observacoes = models.TextField(_('observações'), blank=True, null=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pendente')
    resultado_conformidade = models.CharField(
        _('resultado de conformidade'),
        max_length=20,
        choices=RESULTADO_CONFORMIDADE_CHOICES,
        blank=True,
        null=True,
        help_text=_('Resultado da avaliação de conformidade')
    )

    # Auditoria
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='visitas_criadas', verbose_name=_('criado por'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_visitatecnica'
        verbose_name = _('Visita Técnica')
        verbose_name_plural = _('Visitas Técnicas')
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.local} - {self.data}'


class NaoConformidade(models.Model):
    """
    Modelo para Não Conformidades
    """
    CLASSIFICACAO_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_identificacao = models.DateField(_('data de identificação'), default=date.today)
    descricao = models.TextField(_('descrição'), help_text=_('Descrição objetiva da não conformidade'))
    referencia_normativa = models.CharField(_('referência normativa'), max_length=255, blank=True, null=True)
    classificacao = models.CharField(_('classificação'), max_length=20, choices=CLASSIFICACAO_CHOICES, default='media')
    responsavel = models.CharField(_('responsável'), max_length=255, help_text=_('Nome do responsável pela resolução'))
    prazo = models.DateField(_('prazo'), help_text=_('Prazo para resolução'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_resolucao = models.DateField(_('data de resolução'), blank=True, null=True)

    # Relações
    visita_tecnica = models.ForeignKey(VisitaTecnica, on_delete=models.SET_NULL, null=True, blank=True, related_name='nao_conformidades', verbose_name=_('visita técnica'))

    # Auditoria
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='nao_conformidades_criadas', verbose_name=_('criado por'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_naoconformidade'
        verbose_name = _('Não Conformidade')
        verbose_name_plural = _('Não Conformidades')
        ordering = ['-data_identificacao']

    def __str__(self):
        return f'NC - {self.descricao[:50]} - {self.get_status_display()}'

    @property
    def em_atraso(self):
        """Verifica se a não conformidade está em atraso"""
        if self.status != 'concluido' and self.prazo < date.today():
            return True
        return False


class PlanoAcao(models.Model):
    """
    Modelo para Plano de Ação
    """
    TIPO_ACAO_CHOICES = [
        ('corretiva', 'Ação Corretiva'),
        ('preventiva', 'Ação Preventiva'),
    ]

    is_regulatory = models.BooleanField(default=False, verbose_name="É Regulatório?")

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nao_conformidade = models.ForeignKey(NaoConformidade, on_delete=models.CASCADE, related_name='planos_acao', verbose_name=_('não conformidade'))
    tipo_acao = models.CharField(_('tipo de ação'), max_length=20, choices=TIPO_ACAO_CHOICES, default='corretiva')
    descricao = models.TextField(_('descrição da ação'), help_text=_('Descrição detalhada da ação a ser tomada'))
    responsavel = models.CharField(_('responsável'), max_length=255, help_text=_('Nome do responsável pela execução'))
    prazo = models.DateField(_('prazo'), help_text=_('Prazo para conclusão da ação'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_conclusao = models.DateField(_('data de conclusão'), blank=True, null=True)
    observacoes = models.TextField(_('observações'), blank=True, null=True)

    # Auditoria
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='planos_acao_criados', verbose_name=_('criado por'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_planoacao'
        verbose_name = _('Plano de Ação')
        verbose_name_plural = _('Planos de Ação')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_tipo_acao_display()} - {self.descricao[:50]}'


class EvidenciaQualidade(models.Model):
    """
    Modelo para Upload de Evidências
    """
    TIPO_CHOICES = [
        ('treinamento', 'Treinamento'),
        ('visita', 'Visita Técnica'),
        ('plano_acao', 'Plano de Ação'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(_('tipo'), max_length=20, choices=TIPO_CHOICES)
    descricao = models.CharField(_('descrição'), max_length=255, help_text=_('Descrição da evidência'))
    arquivo = models.FileField(_('arquivo'), upload_to='qualidade/evidencias/%Y/%m/')

    # Relações (nullable para flexibilidade)
    treinamento = models.ForeignKey(Treinamento, on_delete=models.CASCADE, null=True, blank=True, related_name='evidencias', verbose_name=_('treinamento'))
    visita_tecnica = models.ForeignKey(VisitaTecnica, on_delete=models.CASCADE, null=True, blank=True, related_name='evidencias', verbose_name=_('visita técnica'))
    plano_acao = models.ForeignKey(PlanoAcao, on_delete=models.CASCADE, null=True, blank=True, related_name='evidencias', verbose_name=_('plano de ação'))

    # Auditoria
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='evidencias_enviadas', verbose_name=_('enviado por'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        db_table = 'Gestao_a_Vista_evidenciaqualidade'
        verbose_name = _('Evidência de Qualidade')
        verbose_name_plural = _('Evidências de Qualidade')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.descricao} - {self.get_tipo_display()}'


class EventoCalendario2026(models.Model):
    '''
    Modelo para eventos do Calendário 2026 - Regional Centro Oeste
    '''
    TIPO_CHOICES = [
        ('feriado', 'Feriado'),
        ('live', 'Live'),
        ('apresentacao_resultado', 'Apresentação de Resultado'),
        ('alinhamento_estrategico', 'Alinhamento Estratégico'),
        ('apresentacao_presidencia', 'Apresentação Presidência'),
        ('apresentacao_trimestral', 'Apresentação Trimestral'),
        ('apresentacao_pp', 'Apresentação PP'),
        ('divulgacao_ata', 'Divulgação Ata'),
        ('workshop', 'Workshop'),
        ('aniversariante', 'Aniversariante'),
        ('confraternizacao', 'Confraternização'),
        ('outro', 'Outro'),
        ('ciclo_planejamento_cintya', 'Ciclo de planejamento - Cintya'),
        ('semana_kaisen_visitas', 'Semana Kaisen e Visitas a Clientes-Rafael, Allan e time'),
        ('circuito_infra_servicos', 'Circuito infra-serviços - Edi e time'),
        ('consultoria_lean', 'Consultoria Lean - Start do projeto'),
        ('trilha_treinamentos', 'Trilha de treinamentos'),
        ('aniversariante_mes', 'Aniversariante do mês'),
        ('confraternizacao_go', 'Confraternização - GO'),
        ('confraternizacao_df', 'Confraternização - DF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_inicio = models.DateField(_('data início'), help_text=_('Data de início do evento'))
    data_fim = models.DateField(_('data fim'), blank=True, null=True, help_text=_('Data de fim do evento (opcional para eventos de múltiplos dias)'))
    titulo = models.CharField(_('título'), max_length=255, help_text=_('Título do evento'))
    tipo = models.CharField(_('tipo'), max_length=50, choices=TIPO_CHOICES, default='outro')
    descricao = models.TextField(_('descrição'), blank=True, null=True, help_text=_('Descrição detalhada do evento'))
    cor = models.CharField(_('cor'), max_length=7, default='#3788d8', help_text=_('Código hexadecimal da cor (ex: #FF5733)'))
    legenda = models.CharField(_('legenda'), max_length=10, blank=True, null=True, help_text=_('Sigla personalizada para exibição no calendário (máx 10 caracteres)'))

    # Auditoria
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        db_table = 'Gestao_a_Vista_eventocalendario2026'
        verbose_name = _('Evento do Calendário 2026')
        verbose_name_plural = _('Eventos do Calendário 2026')
        ordering = ['data_inicio', 'titulo']

    def clean(self):
        '''
        Validação personalizada do modelo
        '''
        from django.core.exceptions import ValidationError

        if self.data_fim and self.data_inicio:
            if self.data_fim < self.data_inicio:
                raise ValidationError('Data fim não pode ser anterior à data início')

    def get_dias_evento(self):
        '''
        Retorna lista de datas que o evento ocupa
        '''
        from datetime import timedelta

        if not self.data_fim:
            return [self.data_inicio]

        dias = []
        data_atual = self.data_inicio
        while data_atual <= self.data_fim:
            dias.append(data_atual)
            data_atual += timedelta(days=1)
        return dias

    def __str__(self):
        if self.data_fim:
            return f'{self.titulo} - {self.data_inicio.strftime("%d/%m/%Y")} a {self.data_fim.strftime("%d/%m/%Y")}'
        return f'{self.titulo} - {self.data_inicio.strftime("%d/%m/%Y")}'
    

# Adicione isso ao final de Gestao_a_Vista/models.py

class LivroOcorrencia(models.Model):
    """
    Modelo para o Livro de Ocorrências da Torre de Controle.
    Armazena itens individuais que serão agrupados na visualização.
    """
    STATUS_CHOICES = [
        ('NC', 'Não Conforme'),
        ('AND', 'Em Andamento'),
        ('C', 'Conforme'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cr = models.CharField(_("CR"), max_length=100, db_index=True)
    numero = models.CharField(_("Número da Tarefa"), max_length=255, null=True, blank=True)
    solicitante = models.CharField(_("Solicitante"), max_length=255, db_index=True) # Ex: Jose
    item = models.CharField(_("Item"), max_length=255, db_index=True) # Ex: Lanterna
    quantidade = models.IntegerField(_("Quantidade"), default=1)
    
    # Gerente será buscado via relacionamento com CR ou CustomUser, 
    # mas podemos armazenar aqui se for um dado histórico fixo.
    # Vamos assumir busca dinâmica na view para manter integridade.
    
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='NC')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'Gestao_a_Vista_livroocorrencia'
        verbose_name = _('Ocorrência')
        verbose_name_plural = _('Livro de Ocorrências')
        indexes = [
            models.Index(fields=['cr', 'solicitante', 'item']), # Índice para o agrupamento rápido
        ]

    def __str__(self):
        return f"{self.item} - {self.solicitante} ({self.cr})"


# Adicione este novo modelo (Pode ser no final do arquivo)
class PrestadorServico(models.Model):
    AREA_CHOICES = [
        ('limpeza', 'Serviços de Limpeza'),
        ('entreposto', 'Serviços de Entreposto'),
        ('coffe', 'Serviços de Coffe'),
    ]
    nome = models.CharField('Nome', max_length=255)
    email = models.EmailField('Email')
    area_servico = models.CharField('Área de Serviço', max_length=50, choices=AREA_CHOICES)
    unidade = models.ForeignKey(
        'Unidade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Unidade / Local',
        related_name='prestadores'
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "prestador_servico"
        verbose_name = "Prestador de Serviço"

    def __str__(self):
        return f"{self.nome} - {self.get_area_servico_display()}"


class OcorrenciaPlanoAcao(models.Model):
    STATUS_CHOICES = [
        ('em_aprovacao', 'Em Aprovação'),
        ('compra_cadastrar', 'Compra - A Cadastrar'),
        ('compra_pedido', 'Compra - Pedido Realizado'),
        ('compra_entregue', 'Compra - Entregue (Aguardando Retirada)'),
        ('concluido', 'Concluído'),
        ('rejeitado', 'Rejeitado'),
        ('excluido', 'Excluído'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_regulatory = models.BooleanField(default=False, verbose_name="É Regulatório?")
    
    # Aba NC (Criação do Plano)
    item_em_falta = models.CharField(_("Item em Falta"), max_length=255)
    colaborador_nc = models.CharField(_("Colaborador (NC)"), max_length=255)
    cr_colaborador = models.CharField(_("CR do Colaborador"), max_length=100)
    criador_plano = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='planos_ocorrencia_criados')
    tem_estoque = models.BooleanField(_("Tem no Estoque?"), default=False)
    previsao_entrega = models.DateField(_("Previsão de Entrega"), null=True, blank=True)
    data_criacao = models.DateTimeField(_("Data de Criação"), auto_now_add=True)
    
    status = models.CharField(_("Status"), max_length=30, choices=STATUS_CHOICES, default='em_aprovacao')
    
    # Aba Em Aprovação
    aprovador = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_ocorrencia_aprovados')
    justificativa_aprovacao = models.TextField(_("Justificativa da Aprovação/Rejeição"), blank=True, null=True)

    # Aba Compra
    data_compra = models.DateField(_("Data da Compra"), null=True, blank=True)
    itens_compra = models.JSONField(_("Itens da Compra"), default=list, blank=True) # Ex: [{'nome': '...', 'quantidade': '...'}]
    nota_fiscal = models.FileField(_("Nota Fiscal"), upload_to='notas_fiscais_ocorrencia/', null=True, blank=True)
    comprador = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_ocorrencia_comprados')
    
    # Aba Retirada
    retirante = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_ocorrencia_retirados')
    recebedor = models.CharField(_("Nome do Recebedor"), max_length=255, blank=True, null=True)
    item_retirado = models.CharField(_("Item Retirado"), max_length=255, blank=True, null=True)
    data_retirada = models.DateTimeField(_("Data da Retirada"), null=True, blank=True)
    # NOVO CAMPO: Foto de retirada obrigatória
    foto_retirada = models.ImageField(_("Foto da Retirada"), upload_to='fotos_retirada_ocorrencia/', null=True, blank=True)
    
    guia_de_trafego = models.FileField(_("Guia de Tráfego"), upload_to='guias_trafego_ocorrencia/', null=True, blank=True)
    
    excluido_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_ocorrencia_excluidos')

    @property
    def esta_atrasado(self):
        from datetime import date
        if self.previsao_entrega and self.status not in ['compra_entregue', 'concluido', 'excluido', 'rejeitado']:
            return self.previsao_entrega < date.today()
        return False
    
    class Meta:
        db_table = 'ocorrencia_plano_acao'
        verbose_name = _("Plano de Ação da Ocorrência")
        verbose_name_plural = _("Planos de Ação das Ocorrências")
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=["status", "cr_colaborador"], name="ocorrencia_status_cr_idx"),
            models.Index(fields=["cr_colaborador", "item_em_falta"], name="ocorrencia_cr_item_idx"),
            models.Index(fields=["-data_criacao", "status"], name="ocorrencia_criacao_status_idx"),
        ]

    def __str__(self):
        return f"{self.item_em_falta} - {self.cr_colaborador}"
    

class HistoricoPlanoAcao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plano = models.ForeignKey(OcorrenciaPlanoAcao, on_delete=models.CASCADE, related_name='historicos')
    status_anterior = models.CharField(max_length=50, blank=True, null=True)
    status_novo = models.CharField(max_length=50)
    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'historico_plano_acao'
        ordering = ['data_alteracao']

    def __str__(self):
        return f"{self.plano.item_em_falta} - {self.status_novo}"
    


from django.db import models
from django.conf import settings # IMPORTANTE: Adicione esta linha
from django.utils import timezone

class ReincidenciaOcorrencia(models.Model):
    plano_original = models.ForeignKey(
        'OcorrenciaPlanoAcao', 
        on_delete=models.CASCADE, 
        related_name='reincidencias'
    )
    cr_colaborador = models.CharField(max_length=255)
    item_reincidente = models.CharField(max_length=255)
    coordenador = models.CharField(max_length=255, blank=True, null=True)
    gerente = models.CharField(max_length=255, blank=True, null=True)
    
    data_reincidencia = models.DateTimeField(auto_now_add=True)
    email_enviado = models.BooleanField(default=False)
    status_aprovacao = models.CharField(
        max_length=50, 
        choices=[('pendente', 'Pendente'), ('aprovado', 'Aprovado'), ('rejeitado', 'Rejeitado')],
        default='pendente'
    )
    
    # MUDE ESTA LINHA: Em vez de usar 'User', usamos settings.AUTH_USER_MODEL
    avaliado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    data_avaliacao = models.DateTimeField(null=True, blank=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    observacao = models.TextField(blank=True, null=True)
    justificativa_auditoria = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Reincidência: {self.cr_colaborador} - {self.item_reincidente}"


# Adicione em Gestao_a_Vista/models.py (se ainda não existir)
# Em Gestao_a_Vista/models.py

class AuditoriaOcorrenciaStatus(models.Model):
    ocorrencia_hash = models.CharField(max_length=255, primary_key=True)
    estrutura_id = models.CharField(max_length=50, null=True, blank=True) 
    
    auditado_em = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    auditado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="auditorias_realizadas")
    
    image_hash = models.CharField(max_length=255, null=True, blank=True)
    is_coincidencia = models.BooleanField(default=False)
    tratada = models.BooleanField(default=False)
    tratada_em = models.DateTimeField(null=True, blank=True)
    tratada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="coincidencias_tratadas")

    data_ocorrencia = models.DateTimeField(null=True, blank=True)
    colaborador = models.CharField(max_length=255, null=True, blank=True)
    item = models.CharField(max_length=255, null=True, blank=True)
    cr_nome = models.CharField(max_length=255, null=True, blank=True)

    tarefa_id = models.CharField(max_length=50, null=True, blank=True)
    numero = models.CharField(max_length=50, null=True, blank=True)
    inicio_real = models.DateTimeField(null=True, blank=True)

    evidencia_url = models.URLField(max_length=1000, null=True, blank=True)

    class Meta:
        db_table = "auditoria_ocorrencia_status"


class SolicitacaoCadastro(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]
    nome_completo = models.CharField(_("Nome Completo"), max_length=255)
    email = models.EmailField(_("E-mail"), unique=True)
    telefone = models.CharField(_("Telefone"), max_length=20)
    senha = models.CharField(_("Senha"), max_length=128) # Será salva com hash
    regional = models.ForeignKey(
        'Regional', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Regional Pretendida")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_solicitacao = models.DateTimeField(_("Data da Solicitação"), auto_now_add=True)

    class Meta:
        db_table = "solicitacao_cadastro"
        verbose_name = "Solicitação de Cadastro"
        verbose_name_plural = "Solicitações de Cadastro"

    def __str__(self):
        return f"{self.nome_completo} - {self.email}"


class CardImplantacao(models.Model):
    """
    Modelo para registrar os fluxos de implantações (Kanban/Planner)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(_("Nome do Fluxo"), max_length=255)
    
    STATUS_CHOICES = [
        ('em_andamento', 'Em andamento'),
        ('pausada', 'Pausada'),
        ('concluida', 'Concluída'),
    ]
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='em_andamento', db_index=True)
    
    etapa_atual = models.IntegerField(_("Etapa Atual"), default=1, db_index=True)
    created_by = models.ForeignKey(
        'CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='implantacoes_criadas',
        verbose_name=_("Criado por")
    )
    step2_concluido_em = models.DateTimeField(_("Etapa 2 concluída em"), blank=True, null=True)
    step3_concluido_em = models.DateTimeField(_("Etapa 3 concluída em"), blank=True, null=True)
    step4_concluido_em = models.DateTimeField(_("Etapa 4 concluída em"), blank=True, null=True)
    step5_concluido_em = models.DateTimeField(_("Etapa 5 concluída em"), blank=True, null=True)
    step6_concluido_em = models.DateTimeField(_("Etapa 6 concluída em"), blank=True, null=True)
    step7_concluido_em = models.DateTimeField(_("Etapa 7 concluída em"), blank=True, null=True)
    step8_concluido_em = models.DateTimeField(_("Etapa 8 concluída em"), blank=True, null=True)
    step9_concluido_em = models.DateTimeField(_("Etapa 9 concluída em"), blank=True, null=True)
    
    # Campo 2: Tipo de Implantação
    tipo_implantacao = models.CharField(_("Tipo de Implantação"), max_length=50, blank=True, null=True) # drop: seguranca, limpeza, engenharia
    
    # Campo 3: Mapeamento dos locais
    mapeamento_locais = models.TextField(_("Mapeamento de Locais"), blank=True, null=True)
    anexo_mapeamento = models.FileField(_("Anexo do Mapeamento"), upload_to='implantacoes/mapeamento/', blank=True, null=True)
    
    # Campo 4: Criação do Checklist
    anexo_checklist = models.FileField(_("Anexo do Checklist"), upload_to='implantacoes/checklist/', blank=True, null=True)
    
    # Campo 5: Criação das rotinas (RONDA, LIVRO)
    rotinas_criadas = models.BooleanField(_("Rotinas Criadas"), default=False)
    anexo_rotinas = models.FileField(_("Anexo das Rotinas"), upload_to='implantacoes/rotinas/', blank=True, null=True)
    
    # Campo 6: Criação dos QR codes
    anexo_qrcodes = models.FileField(_("Anexo dos QR Codes"), upload_to='implantacoes/qrcodes/', blank=True, null=True)
    
    # Campo 7: Treinamento
    anexo_treinamento = models.FileField(_("Anexo do Treinamento"), upload_to='implantacoes/treinamento/', blank=True, null=True)
    
    # Campo 8: Entrega do projeto
    anexo_entrega = models.FileField(_("Anexo da Entrega"), upload_to='implantacoes/entrega/', blank=True, null=True)
    
    # Campo 9: BI
    link_bi = models.URLField(_("Link do BI"), blank=True, null=True)
    anexo_bi = models.FileField(_("Anexo do BI"), upload_to='implantacoes/bi/', blank=True, null=True)
    bi_inicio_data = models.DateTimeField(_("Início da etapa do BI"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    
    class Meta:
        db_table = 'Gestao_a_Vista_cardimplantacao'
        verbose_name = _('Fluxo de Implantação')
        verbose_name_plural = _('Fluxos de Implantação')
        ordering = ['-created_at']
        
    def __str__(self):
        return self.nome


class ExplorerNode(models.Model):
    """
    Representa uma pasta ou um arquivo no explorador de projetos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nome"), max_length=255)
    is_folder = models.BooleanField(_("É pasta?"), default=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Pasta Pai")
    )
    content = models.TextField(_("Conteúdo"), blank=True, default="")
    file_type = models.CharField(
        _("Tipo de Arquivo"),
        max_length=20,
        choices=[('text', 'Texto Normal'), ('code', 'Código')],
        default='text'
    )
    language = models.CharField(
        _("Linguagem"),
        max_length=50,
        blank=True,
        default="plain",
        help_text="Linguagem de programação para syntax highlighting se for código (ex: html, javascript, python, css)"
    )
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    created_by_name = models.CharField(
        _("Criado por"),
        max_length=255,
        default="Sistema"
    )

    class Meta:
        db_table = 'Gestao_a_Vista_explorernode'
        verbose_name = _('Nó do Explorer')
        verbose_name_plural = _('Nós do Explorer')
        ordering = ['is_folder', 'name']

    def __str__(self):
        return f"{'Folder' if self.is_folder else 'File'}: {self.name}"


class ExplorerAuditLog(models.Model):
    """
    Registro de auditoria para o explorador de projetos (apenas administradores).
    """
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('OPEN', 'Abertura'),
        ('EDIT', 'Edição'),
        ('RENAME', 'Renomeação'),
        ('DELETE', 'Exclusão'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_name = models.CharField(
        _("Usuário"),
        max_length=255,
        default="Desconhecido"
    )
    action = models.CharField(_("Ação"), max_length=20, choices=ACTION_CHOICES)
    node_name = models.CharField(_("Nome do Item"), max_length=255)
    node_type = models.CharField(_("Tipo do Item"), max_length=10, choices=[('folder', 'Pasta'), ('file', 'Arquivo')])
    details = models.TextField(_("Detalhes"), blank=True)
    timestamp = models.DateTimeField(_("Data/Hora"), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'Gestao_a_Vista_explorerauditlog'
        verbose_name = _('Auditoria do Explorer')
        verbose_name_plural = _('Auditoria do Explorer')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user_name} - {self.action} - {self.node_name}"


class CardDesmobilizacao(models.Model):
    """
    Modelo para registrar os cards de desmobilização de CR (Kanban)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cr = models.CharField(_("CR"), max_length=100, db_index=True)
    cr_descricao = models.CharField(_("Descrição do CR"), max_length=500, blank=True, null=True)
    
    STATUS_CHOICES = [
        ('em_andamento', 'Em andamento'),
        ('pausada', 'Pausada'),
        ('concluida', 'Concluída'),
    ]
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='em_andamento', db_index=True)
    created_by = models.ForeignKey(
        'CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='desmobilizacoes_criadas',
        verbose_name=_("Criado por")
    )
    
    data_desmobilizacao = models.DateField(_("Data de Solicitação"), blank=True, null=True)
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    
    class Meta:
        db_table = 'Gestao_a_Vista_carddesmobilizacao'
        verbose_name = _('Desmobilização de CR')
        verbose_name_plural = _('Desmobilizações de CR')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.cr} - {self.cr_descricao or ''}"


class DesmobilizacaoPerguntaResposta(models.Model):
    """
    Modelo para registrar as respostas e o checklist das perguntas por área no fluxo de desmobilização.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(CardDesmobilizacao, related_name='respostas', on_delete=models.CASCADE)
    area = models.CharField(_("Área"), max_length=20, db_index=True) # 'TI', 'PEC', 'QUALIDADE', 'PROJETOS', 'SESMT', 'SUPRIMENTOS'
    pergunta_key = models.CharField(_("Chave da Pergunta"), max_length=50) # e.g. 'pergunta_1'
    texto_pergunta = models.TextField(_("Texto da Pergunta"))
    
    concluido = models.BooleanField(_("Concluído"), default=False)
    resposta_texto = models.TextField(_("Resposta/Observação"), blank=True, null=True)
    respondido_por_nome = models.CharField(_("Respondido por"), max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    
    class Meta:
        db_table = 'Gestao_a_Vista_desmobilizacaoperguntaresposta'
        verbose_name = _('Resposta de Desmobilização')
        verbose_name_plural = _('Respostas de Desmobilização')
        ordering = ['area', 'pergunta_key']
        
    def __str__(self):
        return f"{self.card.cr} - {self.area} - {self.pergunta_key}"


class DesmobilizacaoAnexo(models.Model):
    """
    Arquivos anexos dinâmicos para cada pergunta do fluxo de desmobilização.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pergunta_resposta = models.ForeignKey(DesmobilizacaoPerguntaResposta, related_name='anexos', on_delete=models.CASCADE)
    arquivo = models.FileField(_("Arquivo"), upload_to='desmobilizacoes/anexos/')
    nome_original = models.CharField(_("Nome Original"), max_length=255)
    uploaded_at = models.DateTimeField(_("Enviado em"), auto_now_add=True)
    
    class Meta:
        db_table = 'Gestao_a_Vista_desmobilizacaoanexo'
        verbose_name = _('Anexo de Desmobilização')
        verbose_name_plural = _('Anexos de Desmobilização')
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return self.nome_original


class PsicossocialProjeto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, verbose_name="Nome do Projeto/Contrato")
    empresa = models.CharField(max_length=255, verbose_name="Empresa")
    cnpj = models.CharField(max_length=25, blank=True, null=True, verbose_name="CNPJ")
    localidade = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cidade - UF")
    periodo_inicio = models.DateField(blank=True, null=True, verbose_name="Período Início")
    periodo_fim = models.DateField(blank=True, null=True, verbose_name="Período Fim")
    responsavel_tecnico = models.CharField(max_length=255, blank=True, null=True, verbose_name="Responsável Técnico SSMA")
    data_aplicacao = models.DateField(blank=True, null=True, verbose_name="Data de Aplicação")
    data_emissao = models.DateField(blank=True, null=True, verbose_name="Data de Emissão")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, db_constraint=False)
    
    # Novos campos para código de Empresa e Filial
    empresa_codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código da Empresa")
    filial_codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código da Filial")
    
    # Arquivos de Upload
    planilha_respostas = models.FileField(upload_to="psicossocial/uploads/")
    planilha_workforce = models.FileField(upload_to="psicossocial/uploads/", blank=True, null=True)
    
    # Arquivos Gerados
    planilha_resultado = models.FileField(upload_to="psicossocial/resultados/", blank=True, null=True)
    relatorio_word = models.FileField(upload_to="psicossocial/resultados/", blank=True, null=True)

    # Custom SRA Selection
    sra_tipo_selecao = models.CharField(max_length=50, default='todos')
    sra_cliente_filtro = models.CharField(max_length=255, blank=True, null=True)
    sra_unidade_filtro = models.CharField(max_length=255, blank=True, null=True)
    colaboradores_sra = models.ManyToManyField('ColaboradorSRA', blank=True)
    detalhamento_fatores_protetivos = models.TextField(blank=True, null=True, verbose_name="Detalhamento dos Fatores Protetivos")
    total_colaboradores = models.PositiveIntegerField(default=0, verbose_name="Total de Colaboradores do Contrato")

    class Meta:
        db_table = "Gestao_a_Vista_psicossocialprojeto"
        ordering = ["-created_at"]
        verbose_name = "Projeto Psicossocial"
        verbose_name_plural = "Projetos Psicossocial"

    def __str__(self):
        return f"{self.nome} - {self.empresa}"



class ColaboradorSRA(models.Model):
    cpf = models.CharField(max_length=20, db_index=True)
    nome = models.CharField(max_length=255)
    matricula = models.CharField(max_length=50, blank=True, null=True)
    negocio = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=10, blank=True, null=True)
    dt_demissao = models.DateField(blank=True, null=True)
    cr = models.CharField(max_length=100, blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True)
    situacao = models.CharField(max_length=100, blank=True, null=True, default='Ativo')
    
    # Novos campos SRA
    grupo_cliente = models.CharField(max_length=255, blank=True, null=True)
    empresa_codigo = models.CharField(max_length=50, blank=True, null=True)
    filial_codigo = models.CharField(max_length=50, blank=True, null=True)
    nome_unidade = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=50, blank=True, null=True)
    empresa_nome = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Gestao_a_Vista_colaboradorsra"
        verbose_name = "Colaborador SRA"
        verbose_name_plural = "Colaboradores SRA"

    def __str__(self):
        return f"{self.nome} ({self.cpf})"


class EmpresaSRA(models.Model):
    """Cadastro de empresas/filiais (Código Empresa + Código Filial) do SRA.

    Independente de ColaboradorSRA -- que é recriada do zero (delete +
    bulk_create) a cada sync de "Base Layout 1" -- justamente para que uma
    empresa importada via "Importar Empresas (CNPJ)" continue existindo
    mesmo que nenhum colaborador daquele Código Empresa/Filial esteja
    carregado na base no momento do upload.

    NOTA (staging): esta classe existia no Master mas tinha se perdido num
    merge nesta branch, deixando drift -- a migration 0062_empresasra criava
    a tabela e o makemigrations queria deletá-la. Restaurada idêntica ao
    Master em 15/07/2026.
    """

    empresa_codigo = models.CharField(max_length=50, db_index=True)
    filial_codigo = models.CharField(max_length=50, blank=True, default="")
    empresa_nome = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Gestao_a_Vista_empresasra"
        verbose_name = "Empresa SRA"
        verbose_name_plural = "Empresas SRA"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa_codigo", "filial_codigo"],
                name="unique_empresasra_empresa_filial",
            )
        ]

    def __str__(self):
        return f"{self.empresa_nome or self.empresa_codigo} ({self.empresa_codigo}/{self.filial_codigo})"


# === MÓDULO CMO EFETIVO (Conformidade de Efetivo) ===
#
# Implementa o PRD "Central de Controle" (substituição da PDM). Prefixo
# "CMOEfetivo*" mantido por clareza/histórico (havia um módulo antigo
# "CMOPonto"/"CMOTrocaServico", backend do app mobile de ponto/troca, hoje
# removido do projeto).
#
# Não particiona Cliente/Colaborador em models próprios: ColaboradorSRA já é
# a base de colaboradores/clientes/CRs, mas é recriada do zero a cada sync
# (delete + bulk_create), então não pode ser FK -- é usada só como fonte de
# autocomplete, e os dados relevantes são gravados como snapshot (CharField)
# aqui, no mesmo padrão já usado por LivroOcorrencia.
#
# Nenhum destes models está em DatabaseRouter.GLOBAL_MODELS -- ficam
# particionados por Regional automaticamente (mesmo padrão de
# LivroOcorrencia), via RegionalRoutingMiddleware.

# Lista fechada do PRD (módulo 7, tabela de campos): "Tipo de serviço | Ex.:
# Limpeza, Manutenção, Alimentação, Logística, Segurança". Deliberadamente
# NÃO reaproveita o model TipoServico (catálogo do Planner) -- misturava
# categorias do Planner (Dev, Teste, Implantação...) com as do CMO Efetivo
# no mesmo dropdown, além de TipoServico não ter PK no banco de produção
# (ver comentário mais abaixo em tipo_servico_nome).
CMO_EFETIVO_TIPO_SERVICO_CHOICES = [
    ("limpeza", "Limpeza"),
    ("manutencao", "Manutenção"),
    ("alimentacao", "Alimentação"),
    ("logistica", "Logística"),
    ("seguranca", "Segurança"),
]


class CMOEfetivoConformidade(models.Model):
    """Registro diário de conformidade do efetivo (o "PDM" real).

    A partir da reunião de 14/07/2026, este registro passa a ser alimentado
    pelo Livro de Ocorrências do OpsVista (pergunta de ronda "O efetivo
    está completo?") em vez de lançamento manual pela Torre -- ver
    CMO_EFETIVO_ITEM_CHECKLIST_VISTA mais abaixo. "Aguardando Confirmação"
    é o status padrão: formulário do Vista ainda em branco.
    """

    STATUS_EFETIVO_CHOICES = [
        ("aguardando_confirmacao", "Aguardando Confirmação"),
        ("conforme", "Conforme"),
        ("nao_conforme", "Não Conforme"),
    ]

    MOTIVO_NC_CHOICES = [
        ("falta_nao_justificada", "Falta não justificada"),
        ("falta_justificada", "Falta justificada"),
        ("atraso", "Atraso"),
        ("atestado_medico", "Atestado médico"),
        ("ferias", "Férias"),
        ("afastamento", "Afastamento"),
        ("abandono_posto", "Abandono de posto"),
        ("outro", "Outro"),
    ]

    STATUS_LANCAMENTO_CHOICES = [
        ("nao_aplica", "Não se aplica"),
        ("pendente", "Pendente de Lançamento"),
        ("lancado", "Lançado em Folha"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cliente_nome = models.CharField(max_length=255, verbose_name="Cliente", db_index=True)
    grupo_cliente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Grupo Cliente")
    cr = models.CharField(max_length=100, blank=True, null=True, verbose_name="CR", db_index=True)
    # Snapshot (nao FK): a tabela Gestao_a_Vista_tiposervico em producao nao
    # tem constraint de chave primaria (ha linhas com id NULL) -- o Postgres
    # recusa criar uma FK apontando pra ela. Mesmo padrao ja usado pra
    # cliente/colaborador (nomes gravados como texto, nao relacao).
    tipo_servico_nome = models.CharField(max_length=20, choices=CMO_EFETIVO_TIPO_SERVICO_CHOICES, blank=True, null=True, db_index=True, verbose_name="Tipo de Serviço")

    colaborador_nome = models.CharField(max_length=255, verbose_name="Colaborador")
    colaborador_matricula = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name="Matrícula")
    colaborador_telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")

    data_referencia = models.DateField(default=date.today, db_index=True, verbose_name="Data de Referência")
    status_efetivo = models.CharField(max_length=25, choices=STATUS_EFETIVO_CHOICES, default="aguardando_confirmacao", verbose_name="Status do Efetivo")
    motivo_nao_conformidade = models.CharField(max_length=30, choices=MOTIVO_NC_CHOICES, blank=True, null=True, verbose_name="Motivo da Não Conformidade")
    motivo_outro_detalhe = models.CharField(max_length=255, blank=True, null=True, verbose_name="Detalhe (quando motivo = Outro)")

    previsao_cobertura = models.DateTimeField(blank=True, null=True, verbose_name="Previsão de Cobertura")
    impacto_folha = models.BooleanField(default=False, verbose_name="Tem impacto em ponto/folha?")

    responsavel_contato = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="conformidades_efetivo_contato", verbose_name="Responsável pelo Contato",
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    status_lancamento = models.CharField(
        max_length=20, choices=STATUS_LANCAMENTO_CHOICES, default="nao_aplica",
        db_index=True, verbose_name="Status do Lançamento (CMO)",
    )

    cancelado = models.BooleanField(default=False, db_index=True)
    cancelado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="conformidades_efetivo_canceladas",
    )
    cancelado_em = models.DateTimeField(blank=True, null=True)
    motivo_cancelamento = models.TextField(blank=True, null=True)

    criado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="conformidades_efetivo_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cmo_efetivo_conformidade"
        verbose_name = "Conformidade de Efetivo"
        verbose_name_plural = "Conformidades de Efetivo"
        ordering = ["-data_referencia", "-atualizado_em"]
        indexes = [
            models.Index(fields=["cr", "data_referencia"], name="cmo_ef_conf_cr_data_idx"),
            models.Index(fields=["status_efetivo"], name="cmo_ef_conf_status_idx"),
            models.Index(fields=["status_lancamento"], name="cmo_ef_conf_lanc_idx"),
        ]

    def __str__(self):
        return f"{self.colaborador_nome} - {self.cliente_nome} - {self.data_referencia.strftime('%d/%m/%Y')}"


class CMOEfetivoCobertura(models.Model):
    """Colaborador que cobre falta/ausência/necessidade operacional."""

    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("confirmada", "Confirmada"),
        ("nao_realizada", "Não Realizada"),
        ("cancelada", "Cancelada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conformidade_origem = models.ForeignKey(
        CMOEfetivoConformidade, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="coberturas", verbose_name="Não Conformidade de Origem",
    )

    nome_cobertura = models.CharField(max_length=255, verbose_name="Colaborador da Cobertura")
    matricula_cobertura = models.CharField(max_length=50, blank=True, null=True, verbose_name="Matrícula")

    cliente_nome = models.CharField(max_length=255, verbose_name="Cliente", db_index=True)
    grupo_cliente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Grupo Cliente")
    cr = models.CharField(max_length=100, blank=True, null=True, verbose_name="CR", db_index=True)
    # Snapshot (nao FK) -- ver comentario em CMOEfetivoConformidade.tipo_servico_nome
    tipo_servico_nome = models.CharField(max_length=20, choices=CMO_EFETIVO_TIPO_SERVICO_CHOICES, blank=True, null=True, db_index=True, verbose_name="Tipo de Serviço")

    colaborador_substituido = models.CharField(max_length=255, verbose_name="Colaborador Substituído")
    justificativa = models.TextField(verbose_name="Justificativa")
    data_cobertura = models.DateField(db_index=True, verbose_name="Data da Cobertura")
    horario_previsto = models.TimeField(blank=True, null=True, verbose_name="Horário Previsto")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente", db_index=True)
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    criado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="coberturas_efetivo_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cmo_efetivo_cobertura"
        verbose_name = "Cobertura de Efetivo"
        verbose_name_plural = "Coberturas de Efetivo"
        ordering = ["-data_cobertura", "-criado_em"]
        indexes = [
            models.Index(fields=["cr", "data_cobertura"], name="cmo_ef_cob_cr_data_idx"),
            models.Index(fields=["status"], name="cmo_ef_cob_status_idx"),
        ]

    def __str__(self):
        return f"{self.nome_cobertura} cobre {self.colaborador_substituido} - {self.data_cobertura.strftime('%d/%m/%Y')}"


class CMOEfetivoTroca(models.Model):
    """Solicitação de troca de serviço, aprovada/reprovada pela CMO."""

    STATUS_CMO_CHOICES = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("reprovado", "Reprovado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    solicitante = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="trocas_efetivo_solicitadas", verbose_name="Solicitante",
    )

    cliente_nome = models.CharField(max_length=255, verbose_name="Cliente", db_index=True)
    grupo_cliente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Grupo Cliente")
    cr = models.CharField(max_length=100, blank=True, null=True, verbose_name="CR", db_index=True)
    # Snapshot (nao FK) -- ver comentario em CMOEfetivoConformidade.tipo_servico_nome
    tipo_servico_nome = models.CharField(max_length=20, choices=CMO_EFETIVO_TIPO_SERVICO_CHOICES, blank=True, null=True, db_index=True, verbose_name="Tipo de Serviço")

    colaborador_atual = models.CharField(max_length=255, verbose_name="Colaborador Atual")
    colaborador_substituto = models.CharField(max_length=255, verbose_name="Colaborador Substituto")
    justificativa = models.TextField(verbose_name="Justificativa")
    data_troca = models.DateField(db_index=True, verbose_name="Data da Troca")

    status_cmo = models.CharField(max_length=20, choices=STATUS_CMO_CHOICES, default="pendente", db_index=True, verbose_name="Status (CMO)")
    observacao_cmo = models.TextField(blank=True, null=True, verbose_name="Observação da CMO")

    conflito_detectado = models.BooleanField(default=False, verbose_name="Conflito detectado ao solicitar?")
    conflito_justificativa = models.TextField(blank=True, null=True, verbose_name="Justificativa do conflito")

    aprovado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="trocas_efetivo_decididas",
    )
    aprovado_em = models.DateTimeField(blank=True, null=True)

    cancelado = models.BooleanField(default=False, db_index=True)
    cancelado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="trocas_efetivo_canceladas",
    )
    cancelado_em = models.DateTimeField(blank=True, null=True)
    motivo_cancelamento = models.TextField(blank=True, null=True)

    criado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="trocas_efetivo_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cmo_efetivo_troca"
        verbose_name = "Troca de Serviço (Efetivo)"
        verbose_name_plural = "Trocas de Serviço (Efetivo)"
        ordering = ["-data_troca", "-criado_em"]
        indexes = [
            models.Index(fields=["cr", "status_cmo"], name="cmo_ef_troca_cr_status_idx"),
            models.Index(fields=["cliente_nome", "colaborador_atual", "data_troca"], name="cmo_ef_troca_conflito_idx"),
        ]

    def __str__(self):
        return f"{self.colaborador_atual} -> {self.colaborador_substituto} - {self.data_troca.strftime('%d/%m/%Y')}"


class CMOEfetivoLancamento(models.Model):
    """Fila de pendências que a CMO precisa lançar em folha de ponto."""

    OCORRENCIA_TIPO_CHOICES = [
        ("conformidade", "Conformidade de Efetivo"),
        ("cobertura", "Cobertura"),
        ("troca", "Troca de Serviço"),
        ("ajuste", "Ajuste Manual"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ocorrencia_tipo = models.CharField(max_length=20, choices=OCORRENCIA_TIPO_CHOICES, verbose_name="Tipo de Ocorrência")
    ocorrencia_id = models.CharField(max_length=36, blank=True, null=True, db_index=True, verbose_name="ID da Ocorrência de Origem")

    cliente_nome = models.CharField(max_length=255, verbose_name="Cliente")
    colaborador_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Colaborador")

    lancado = models.BooleanField(default=False, db_index=True, verbose_name="Lançado em Folha?")
    data_lancamento = models.DateTimeField(blank=True, null=True, verbose_name="Data do Lançamento")
    responsavel_cmo = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lancamentos_cmo_efetivo", verbose_name="Responsável (CMO)",
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cmo_efetivo_lancamento"
        verbose_name = "Lançamento CMO"
        verbose_name_plural = "Lançamentos CMO"
        ordering = ["lancado", "-criado_em"]
        indexes = [
            models.Index(fields=["lancado"], name="cmo_ef_lanc_lancado_idx"),
            models.Index(fields=["ocorrencia_tipo", "ocorrencia_id"], name="cmo_ef_lanc_origem_idx"),
        ]

    def get_ocorrencia_relacionada(self):
        """Retorna a instância de origem (Conformidade/Cobertura/Troca), se existir."""
        model_map = {
            "conformidade": CMOEfetivoConformidade,
            "cobertura": CMOEfetivoCobertura,
            "troca": CMOEfetivoTroca,
        }
        model_cls = model_map.get(self.ocorrencia_tipo)
        if not model_cls or not self.ocorrencia_id:
            return None
        return model_cls.objects.filter(pk=self.ocorrencia_id).first()

    def __str__(self):
        return f"{self.get_ocorrencia_tipo_display()} - {self.cliente_nome} - {'Lançado' if self.lancado else 'Pendente'}"


class CMOEfetivoLog(models.Model):
    """Log de auditoria polimórfico do módulo CMO Efetivo (RN09)."""

    ENTIDADE_CHOICES = [
        ("conformidade", "Conformidade de Efetivo"),
        ("cobertura", "Cobertura"),
        ("troca", "Troca de Serviço"),
        ("lancamento", "Lançamento CMO"),
        ("movimentacao", "Registro de Movimentação"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entidade = models.CharField(max_length=20, choices=ENTIDADE_CHOICES)
    registro_id = models.CharField(max_length=36, db_index=True)
    acao = models.CharField(max_length=100, verbose_name="Ação")
    valor_anterior = models.JSONField(default=dict, blank=True)
    valor_novo = models.JSONField(default=dict, blank=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "cmo_efetivo_log"
        verbose_name = "Log de Auditoria (CMO Efetivo)"
        verbose_name_plural = "Logs de Auditoria (CMO Efetivo)"
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["entidade", "registro_id"], name="cmo_ef_log_entidade_idx"),
        ]

    def __str__(self):
        return f"{self.get_entidade_display()} {self.registro_id} - {self.acao}"


# Requisitos da reunião de 14/07/2026 com o gerente do CMO: campos do
# formulário "Incluir Registro", que reproduz a Planilha Diária de
# Movimentações (Excel) mostrada na call.
CMO_EFETIVO_SITUACAO_CHOICES = [
    ("falta", "Falta"),
    ("folga", "Folga"),
    ("servico_extra", "Serviço Extra"),
    ("remanejamento", "Remanejamento"),
    ("ferias", "Férias"),
    ("atraso", "Atraso"),
    ("posto", "Posto"),
]

CMO_EFETIVO_SITUACAO_COBERTURA_CHOICES = [
    ("servico_normal", "Serviço Normal"),
    ("dobra_extra", "Fazendo Dobra/Extra"),
    ("extra_entrada", "Extra Entrada"),
    ("extra_saida", "Extra Saída"),
]


class CMOEfetivoRegistroMovimentacao(models.Model):
    """Registro de movimentação incluído pela Torre a partir de uma linha
    Não Conforme de Conformidade de Efetivo ("Incluir Registro"). Alimenta,
    com as mesmas colunas, as abas Lançamentos CMO e Previsão de Cobertura
    -- a folha de ponto é montada a partir daqui."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conformidade_origem = models.ForeignKey(
        CMOEfetivoConformidade, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="registros_movimentacao", verbose_name="Conformidade de Origem",
    )

    # Snapshot herdado da conformidade de origem -- mesmo padrão (CharField,
    # não FK) do resto do módulo, ver comentário no topo deste bloco.
    cliente_nome = models.CharField(max_length=255, verbose_name="Cliente", db_index=True)
    cr = models.CharField(max_length=100, blank=True, null=True, verbose_name="CR", db_index=True)
    tipo_servico_nome = models.CharField(max_length=20, choices=CMO_EFETIVO_TIPO_SERVICO_CHOICES, blank=True, null=True, verbose_name="Tipo de Serviço")
    data_referencia = models.DateField(default=date.today, db_index=True, verbose_name="Data de Referência")

    gerente = models.CharField(max_length=255, blank=True, verbose_name="Gerente")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    cargo = models.CharField(max_length=150, blank=True, verbose_name="Cargo")
    posto = models.CharField(max_length=150, blank=True, verbose_name="Posto")
    posto_cr = models.CharField(max_length=100, blank=True, verbose_name="Posto CR")
    horario = models.CharField(max_length=50, blank=True, verbose_name="Horário")
    intervalo = models.CharField(max_length=50, blank=True, verbose_name="Intervalo")
    cobertura = models.CharField(max_length=255, blank=True, verbose_name="Cobertura")
    cargo_cobertura = models.CharField(max_length=150, blank=True, verbose_name="Cargo (Cobertura)")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    situacao = models.CharField(max_length=20, choices=CMO_EFETIVO_SITUACAO_CHOICES, verbose_name="Situação")
    situacao_cobertura = models.CharField(max_length=20, choices=CMO_EFETIVO_SITUACAO_COBERTURA_CHOICES, blank=True, null=True, verbose_name="Situação da Cobertura")

    criado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="registros_movimentacao_cmo_efetivo",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cmo_efetivo_registro_movimentacao"
        verbose_name = "Registro de Movimentação (CMO)"
        verbose_name_plural = "Registros de Movimentação (CMO)"
        ordering = ["-data_referencia", "-criado_em"]
        indexes = [
            models.Index(fields=["cr", "data_referencia"], name="cmo_ef_mov_cr_data_idx"),
        ]

    def __str__(self):
        return f"{self.nome} - {self.cliente_nome} - {self.data_referencia.strftime('%d/%m/%Y')}"


# === MÓDULO LINKS IMPORTANTES ===

class LinkImportante(models.Model):
    """Atalhos de fácil acesso para sistemas/portais usados no dia a dia
    (Sistema360, OpsVista, Prisma, etc.), exibidos na aba "Links Importantes".
    Cadastro é global (compartilhado entre todas as regionais), por isso o
    model_name está no GLOBAL_MODELS do db_router."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(_("título"), max_length=100)
    url = models.URLField(_("URL"), max_length=500)
    descricao = models.CharField(_("descrição"), max_length=255, blank=True)
    ordem = models.PositiveIntegerField(_("ordem"), default=0)
    ativo = models.BooleanField(_("ativo"), default=True)
    criado_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="links_importantes_criados",
    )
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        db_table = "links_importantes"
        verbose_name = "Link Importante"
        verbose_name_plural = "Links Importantes"
        ordering = ["ordem", "titulo"]

    def __str__(self):
        return self.titulo