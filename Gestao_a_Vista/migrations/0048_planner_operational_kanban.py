# Generated for operational Kanban + 5W2H improvements

from django.db import migrations, models


def migrar_status_crm_para_operacional(apps, schema_editor):
    PlannerProject = apps.get_model("Gestao_a_Vista", "PlannerProject")
    mapa = {
        "Lead": "Entrada / Backlog",
        "Qualificação": "Triagem",
        "Proposta": "Planejamento 5W2H",
        "Negociação": "Em Execução",
        "Fechado": "Concluído",
        "Perdido": "Cancelado / Suspenso",
        "Ativo": "Entrada / Backlog",
        "Em andamento": "Em Execução",
        "Pausado": "Aguardando Terceiros / Cliente",
    }
    for antigo, novo in mapa.items():
        PlannerProject.objects.filter(status=antigo).update(status=novo)


def reverter_status_operacional_para_crm(apps, schema_editor):
    PlannerProject = apps.get_model("Gestao_a_Vista", "PlannerProject")
    mapa = {
        "Entrada / Backlog": "Lead",
        "Triagem": "Qualificação",
        "Planejamento 5W2H": "Proposta",
        "Em Execução": "Negociação",
        "Aguardando Terceiros / Cliente": "Negociação",
        "Validação / Testes": "Proposta",
        "Concluído": "Fechado",
        "Cancelado / Suspenso": "Perdido",
    }
    for antigo, novo in mapa.items():
        PlannerProject.objects.filter(status=antigo).update(status=novo)


class Migration(migrations.Migration):

    dependencies = [
        ("Gestao_a_Vista", "0047_planner_crm_5w2h"),
    ]

    operations = [
        migrations.AddField(
            model_name="plannerproject",
            name="tipo_demanda",
            field=models.CharField(choices=[("implantacao", "Implantação"), ("acompanhamento", "Acompanhamento"), ("ocorrencia", "Ocorrência"), ("desenvolvimento", "Desenvolvimento de Sistemas"), ("melhoria", "Melhoria"), ("suporte", "Suporte"), ("treinamento", "Treinamento")], db_index=True, default="implantacao", max_length=30, verbose_name="tipo da demanda"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="impacto",
            field=models.CharField(choices=[("Baixo", "Baixo"), ("Médio", "Médio"), ("Alto", "Alto"), ("Crítico", "Crítico")], db_index=True, default="Médio", max_length=20, verbose_name="impacto"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="solicitante",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="solicitante"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="responsavel_tecnico",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="responsável técnico"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="validador",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="validador"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="sla",
            field=models.CharField(blank=True, max_length=80, null=True, verbose_name="SLA"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="percentual_progresso",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="progresso (%)"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="modulo_sistema",
            field=models.CharField(blank=True, max_length=160, null=True, verbose_name="módulo/sistema"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="ambiente",
            field=models.CharField(blank=True, choices=[("", "Não se aplica"), ("producao", "Produção"), ("homologacao", "Homologação"), ("desenvolvimento", "Desenvolvimento")], default="", max_length=30, verbose_name="ambiente"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="etapa_implantacao",
            field=models.CharField(blank=True, max_length=160, null=True, verbose_name="etapa da implantação"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="go_live_previsto",
            field=models.DateField(blank=True, null=True, verbose_name="go-live previsto"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="treinamento_realizado",
            field=models.BooleanField(default=False, verbose_name="treinamento realizado?"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="severidade",
            field=models.CharField(blank=True, choices=[("Baixo", "Baixo"), ("Médio", "Médio"), ("Alto", "Alto"), ("Crítico", "Crítico")], max_length=20, null=True, verbose_name="severidade"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="causa_raiz",
            field=models.TextField(blank=True, null=True, verbose_name="causa raiz"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="acao_corretiva",
            field=models.TextField(blank=True, null=True, verbose_name="ação corretiva"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="acao_preventiva",
            field=models.TextField(blank=True, null=True, verbose_name="ação preventiva"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="link_referencia",
            field=models.URLField(blank=True, null=True, verbose_name="link / PR / commit / documentação"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="criterio_aceite",
            field=models.TextField(blank=True, null=True, verbose_name="critério de aceite"),
        ),
        migrations.AlterField(
            model_name="plannerproject",
            name="status",
            field=models.CharField(choices=[("Entrada / Backlog", "Entrada / Backlog"), ("Triagem", "Triagem"), ("Planejamento 5W2H", "Planejamento 5W2H"), ("Em Execução", "Em Execução"), ("Aguardando Terceiros / Cliente", "Aguardando Terceiros / Cliente"), ("Validação / Testes", "Validação / Testes"), ("Concluído", "Concluído"), ("Cancelado / Suspenso", "Cancelado / Suspenso")], db_index=True, default="Entrada / Backlog", max_length=40, verbose_name="status"),
        ),
        migrations.AlterField(
            model_name="plannerproject",
            name="prioridade",
            field=models.CharField(choices=[("Crítica", "Crítica"), ("Alto", "Alto"), ("Médio", "Médio"), ("Baixo", "Baixo")], db_index=True, default="Médio", max_length=20, verbose_name="prioridade"),
        ),
        migrations.RunPython(migrar_status_crm_para_operacional, reverter_status_operacional_para_crm),
        migrations.AddIndex(
            model_name="plannerproject",
            index=models.Index(fields=["tipo_demanda", "status"], name="planner_demanda_status_idx"),
        ),
    ]
