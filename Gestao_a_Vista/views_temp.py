from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (CRKPI, AreaResponsavel, ControleChip, CustomUser,
                     Dashboard, DesativacaoCR, ErrosDashboard, Estrutura,
                     GerenteKPI, GestaoSala, LogoServico, MonitoramentoLog,
                     PlannerAttachment, PlannerComment, PlannerProject,
                     PortariaBase, RelatorioItem, ReservaSala, Script, Service,
                     ShiftComplianceItem, ShiftEvidence, ShiftRecord,
                     TipoServico, Unidade)


class GestaoSalasView(LoginRequiredMixin, ListView):
    model = GestaoSala
    template_name = "gestao_salas.html"
    context_object_name = "salas"

    def get_queryset(self):
        unidade_id = self.request.GET.get("unidade", 1)
        return GestaoSala.objects.filter(unidade_id=unidade_id).order_by("nome")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["unidades"] = Unidade.objects.filter(ativa=True)
        contexto["unidade_selecionada"] = int(self.request.GET.get("unidade", 1))
        return contexto


class SalaCriarView(LoginRequiredMixin, CreateView):
    model = GestaoSala
    fields = [
        "nome",
        "capacidade",
        "hora_inicio",
        "hora_fim",
        "contrato",
        "quantidade_m",
        "unidade",
    ]
    template_name = "sala_form.html"

    def get_success_url(self):
        return (
            reverse_lazy("gestao_a_vista:gestao_salas")
            + f"?unidade={self.object.unidade.id}"
        )

    def get_initial(self):
        initial = super().get_initial()
        unidade_id = self.request.GET.get("unidade", 1)
        initial["unidade"] = unidade_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unidades"] = Unidade.objects.filter(ativa=True)
        return context


class SalaEditarView(LoginRequiredMixin, UpdateView):
    model = GestaoSala
    fields = [
        "nome",
        "capacidade",
        "hora_inicio",
        "hora_fim",
        "contrato",
        "quantidade_m",
        "unidade",
    ]
    template_name = "sala_editar.html"

    def get_success_url(self):
        return (
            reverse_lazy("gestao_a_vista:gestao_salas")
            + f"?unidade={self.object.unidade.id}"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unidades"] = Unidade.objects.filter(ativa=True)
        return context


class SalaDeletarView(LoginRequiredMixin, DeleteView):
    model = GestaoSala
    template_name = "sala_confirm_delete.html"

    def get_success_url(self):
        unidade_id = self.object.unidade.id
        return reverse_lazy("gestao_a_vista:gestao_salas") + f"?unidade={unidade_id}"


def reserva_salas(request):
    """
    View para a página de reserva de salas.
    Gerencia tanto a exibição do formulário quanto o processamento da reserva.
    """
    # Obtém todas as unidades e salas disponíveis
    unidades = Unidade.objects.all()
    salas = GestaoSala.objects.all()

    if request.method == "POST":
        # Processa o formulário de reserva
        try:
            unidade = Unidade.objects.get(id=request.POST.get("unidade"))
            sala = GestaoSala.objects.get(id=request.POST.get("sala"))
            data = request.POST.get("data")
            hora_inicio = request.POST.get("hora_inicio")
            hora_fim = request.POST.get("hora_fim")
            titulo = request.POST.get("titulo")
            descricao = request.POST.get("descricao")
            participantes = request.POST.get("participantes")

            # Cria a nova reserva
            reserva = ReservaSala.objects.create(
                unidade=unidade,
                sala=sala,
                data=data,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                titulo=titulo,
                descricao=descricao,
                participantes=participantes,
            )

            messages.success(request, "Reserva realizada com sucesso!")
            return redirect("gestao_a_vista:reserva_salas")

        except Exception as e:
            messages.error(
                request, "Erro ao realizar a reserva. Por favor, tente novamente."
            )
            return redirect("gestao_a_vista:reserva_salas")

    context = {
        "unidades": unidades,
        "salas": salas,
    }

    return render(request, "reserva_salas.html", context)


class LivroAtaView(TemplateView):
    template_name = "livro_ata.html"

    def get(self, request, *args, **kwargs):
        action = kwargs.get("action")

        if action == "get_shifts":
            return self.get_shifts(request)
        elif action == "get_shift_details":
            shift_id = kwargs.get("shift_id")
            return self.get_shift_details(request, shift_id)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_shifts(self, request):
        cr_number = request.GET.get("cr_number")
        if not cr_number:
            return JsonResponse({"error": "Número do CR é obrigatório"}, status=400)

        shifts = ShiftRecord.objects.filter(cr_number=cr_number.upper()).order_by(
            "-date", "-time"
        )
        data = []

        for shift in shifts:
            shift_data = {
                "id": str(shift.id),
                "cr_number": shift.cr_number,
                "guard_name": shift.guard_name,
                "guard_number": shift.guard_number,
                "date": shift.date.isoformat(),
                "time": shift.time.isoformat(),
                "shift_type": shift.shift_type,
                "location": shift.location,
                "description": shift.description,
            }
            data.append(shift_data)

        return JsonResponse({"shifts": data})

    def get_shift_details(self, request, shift_id):
        try:
            shift = ShiftRecord.objects.get(id=shift_id)
        except ShiftRecord.DoesNotExist:
            return JsonResponse({"error": "Plantão não encontrado"}, status=404)

        evidences = shift.evidences.all()
        compliance_items = shift.compliance_items.all()

        evidence_data = [
            {
                "id": str(evidence.id),
                "image_url": evidence.image.url if evidence.image else None,
                "description": evidence.description,
            }
            for evidence in evidences
        ]

        compliance_data = [
            {
                "id": str(item.id),
                "item_description": item.item_description,
                "status": item.status,
                "observations": item.observations,
            }
            for item in compliance_items
        ]

        data = {
            "shift": {
                "id": str(shift.id),
                "cr_number": shift.cr_number,
                "guard_name": shift.guard_name,
                "guard_number": shift.guard_number,
                "date": shift.date.isoformat(),
                "time": shift.time.isoformat(),
                "shift_type": shift.shift_type,
                "location": shift.location,
                "description": shift.description,
            },
            "evidences": evidence_data,
            "compliance_items": compliance_data,
        }

        return JsonResponse(data)


class PlannerView(LoginRequiredMixin, TemplateView):
    """
    View para a página do Planner
    """

    template_name = "planner.html"

    def get(self, request, *args, **kwargs):
        """
        Manipula as requisições GET
        """
        action = request.GET.get("action")

        if action == "get_project":
            try:
                project_id = request.GET.get("project_id")
                projeto = PlannerProject.objects.get(id=project_id)
                return JsonResponse(
                    {
                        "status": "success",
                        "project": {
                            "nome": projeto.nome,
                            "responsavel_id": str(projeto.responsavel.id),
                            "data_inicial": projeto.data_inicial.strftime("%Y-%m-%d"),
                            "data_conclusao": projeto.data_conclusao.strftime(
                                "%Y-%m-%d"
                            ),
                            "prioridade": projeto.prioridade,
                            "observacao": projeto.observacao,
                            "status": projeto.status,
                            "tipo": projeto.tipo,
                            "tipo_servico_id": str(projeto.tipo_servico.id),
                        },
                    }
                )
            except PlannerProject.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Projeto não encontrado"}
                )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        elif action == "check_service_type":
            try:
                nome = request.GET.get("nome", "").strip()
                if nome:
                    exists = TipoServico.objects.filter(nome__iexact=nome).exists()
                    return JsonResponse({"exists": exists})
                return JsonResponse({"exists": False})
            except Exception as e:
                return JsonResponse({"exists": False, "error": str(e)})

        elif action == "filter_projects":
            try:
                nome = request.GET.get("nome", "")
                responsavel = request.GET.get("responsavel", "")
                tipo = request.GET.get("tipo", "")
                status = request.GET.get("status", "")
                prioridade = request.GET.get("prioridade", "")
                data_inicial = request.GET.get("data_inicial", "")
                data_final = request.GET.get("data_final", "")

                projetos = PlannerProject.objects.all()

                if nome:
                    projetos = projetos.filter(nome__icontains=nome)
                if responsavel:
                    projetos = projetos.filter(responsavel__name__icontains=responsavel)
                if tipo and tipo != "all":
                    projetos = projetos.filter(tipo_servico__nome=tipo)
                if status and status != "all":
                    projetos = projetos.filter(status=status)
                if prioridade and prioridade != "all":
                    projetos = projetos.filter(prioridade=prioridade)
                if data_inicial:
                    projetos = projetos.filter(data_inicial__gte=data_inicial)
                if data_final:
                    projetos = projetos.filter(data_conclusao__lte=data_final)

                projetos_data = []
                for projeto in projetos:
                    projetos_data.append(
                        {
                            "id": str(projeto.id),
                            "nome": projeto.nome,
                            "responsavel": projeto.responsavel.name,
                            "tipo": projeto.tipo,
                            "prioridade": projeto.prioridade,
                            "status": projeto.status,
                            "data_inicial": projeto.data_inicial.strftime("%d/%m/%Y"),
                            "data_conclusao": projeto.data_conclusao.strftime(
                                "%d/%m/%Y"
                            ),
                            "observacao": projeto.observacao,
                        }
                    )

                return JsonResponse(
                    {
                        "status": "success",
                        "projects": projetos_data,
                        "total": len(projetos_data),
                    }
                )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Obtém todos os projetos
        projetos = PlannerProject.objects.all()

        # Agrupa os projetos por status
        projetos_por_status = {
            "Ativo": projetos.filter(status="Ativo"),
            "Em_andamento": projetos.filter(status="Em andamento"),
            "Pausado": projetos.filter(status="Pausado"),
            "Concluido": projetos.filter(status="Concluído"),
        }

        # Agrupa os projetos por tipo - apenas tipos que têm projetos
        projetos_por_tipo = {}

        # Obtém todos os tipos de serviço que têm pelo menos um projeto
        for projeto in projetos:
            if projeto.tipo_servico:
                tipo_nome = projeto.tipo_servico.nome
                if tipo_nome not in projetos_por_tipo:
                    projetos_por_tipo[tipo_nome] = []
                projetos_por_tipo[tipo_nome].append(projeto)

        # Converte listas em querysets para manter compatibilidade com o template
        for tipo_nome in projetos_por_tipo:
            projeto_ids = [p.id for p in projetos_por_tipo[tipo_nome]]
            projetos_por_tipo[tipo_nome] = PlannerProject.objects.filter(
                id__in=projeto_ids
            )

        # Todos os tipos de serviço para os formulários
        todos_tipos_servico = TipoServico.objects.filter(ativo=True)

        context.update(
            {
                "projetos": projetos,
                "projetos_por_status": projetos_por_status,
                "projetos_por_tipo": projetos_por_tipo,
                "tipos_servico": todos_tipos_servico,
                "status_choices": PlannerProject.STATUS_CHOICES,
                "priority_choices": PlannerProject.PRIORITY_CHOICES,
                "usuarios": CustomUser.objects.filter(is_active=True).order_by("name"),
            }
        )

        return context
