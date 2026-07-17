from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ImplantacoesOpsVista, Estrutura


class ImplantacoesOpsVistaForm(forms.ModelForm):
    """
    Formulário para ImplantacoesOpsVista
    """

    # Campo para implantações como texto (será convertido para lista)
    implantacoes_text = forms.CharField(
        label=_("Implantações"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Digite as implantações separadas por vírgula",
            }
        ),
        help_text=_("Digite as implantações separadas por vírgula"),
        required=True,
    )

    # Campo CR como ChoiceField
    cr_id = forms.ChoiceField(
        label="CR",
        choices=[],  # Será populado no __init__
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = ImplantacoesOpsVista
        fields = ["cr_id", "sistema", "servico", "status", "observacoes"]
        widgets = {
            "sistema": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome do sistema OpsVista",
                    "required": True,
                }
            ),
            "servico": forms.Select(attrs={"class": "form-select", "required": True}),
            "status": forms.Select(attrs={"class": "form-select", "required": True}),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observações adicionais (opcional)",
                }
            ),
        }
        labels = {
            "cr_id": _("CR"),
            "sistema": _("Sistema"),
            "servico": _("Serviço"),
            "status": _("Status"),
            "observacoes": _("Observações"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurar choices para CR (com tratamento de erro para testes)
        try:
            estruturas = Estrutura.objects.all()
            cr_choices = [("", "Selecione um CR")] + [(e.id, e.cr) for e in estruturas]
            self.fields["cr_id"].choices = cr_choices
        except Exception:
            # Em caso de erro (como em testes), usar choices vazias
            self.fields["cr_id"].choices = [("", "Selecione um CR")]

        # Se estamos editando, preencher o campo implantacoes_text
        if self.instance and self.instance.pk and self.instance.implantacoes:
            if isinstance(self.instance.implantacoes, list):
                self.fields["implantacoes_text"].initial = ", ".join(
                    self.instance.implantacoes
                )
            else:
                self.fields["implantacoes_text"].initial = str(
                    self.instance.implantacoes
                )

    def clean_implantacoes_text(self):
        """
        Validar e converter o texto de implantações para lista
        """
        implantacoes_text = self.cleaned_data.get("implantacoes_text", "")

        if not implantacoes_text.strip():
            raise forms.ValidationError(_("O campo implantações é obrigatório."))

        # Converter texto em lista, removendo espaços extras
        implantacoes_list = [
            item.strip() for item in implantacoes_text.split(",") if item.strip()
        ]

        if not implantacoes_list:
            raise forms.ValidationError(
                _("Pelo menos uma implantação deve ser informada.")
            )

        return implantacoes_list

    def clean_sistema(self):
        """
        Validar campo sistema
        """
        sistema = self.cleaned_data.get("sistema", "")

        if not sistema.strip():
            raise forms.ValidationError(_("O campo sistema é obrigatório."))

        if len(sistema.strip()) < 3:
            raise forms.ValidationError(
                _("O nome do sistema deve ter pelo menos 3 caracteres.")
            )

        return sistema.strip()

    def save(self, commit=True):
        """
        Salvar o formulário, convertendo implantacoes_text para o campo implantacoes
        """
        instance = super().save(commit=False)

        # Converter implantacoes_text para lista e salvar no campo implantacoes
        implantacoes_list = self.cleaned_data.get("implantacoes_text", [])
        instance.implantacoes = implantacoes_list

        if commit:
            instance.save()

        return instance


class ImplantacoesOpsVistaFilterForm(forms.Form):
    """
    Formulário para filtros da listagem de ImplantacoesOpsVista
    """

    cr = forms.ChoiceField(
        choices=[],  # Será populado no __init__
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    sistema = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Buscar por sistema..."}
        ),
    )

    servico = forms.ChoiceField(
        choices=[("", "Todos os serviços")] + ImplantacoesOpsVista.SERVICO_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    status = forms.ChoiceField(
        choices=[("", "Todos os status")] + ImplantacoesOpsVista.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices para CR no filtro (com tratamento de erro para testes)
        try:
            estruturas = Estrutura.objects.all()
            cr_choices = [("", "Todos os CRs")] + [(e.id, e.cr) for e in estruturas]
            self.fields["cr"].choices = cr_choices
        except Exception:
            # Em caso de erro (como em testes), usar choices vazias
            self.fields["cr"].choices = [("", "Todos os CRs")]
