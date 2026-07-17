# Generated for contextual Kanban stage information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Gestao_a_Vista", "0048_planner_operational_kanban"),
    ]

    operations = [
        migrations.AddField(
            model_name="plannerproject",
            name="triagem_diagnostico",
            field=models.TextField(blank=True, null=True, verbose_name="triagem - diagnóstico"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="triagem_priorizacao",
            field=models.TextField(blank=True, null=True, verbose_name="triagem - prioridade/impacto"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="planejamento_entregaveis",
            field=models.TextField(blank=True, null=True, verbose_name="planejamento - entregáveis"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="planejamento_riscos",
            field=models.TextField(blank=True, null=True, verbose_name="planejamento - riscos/dependências"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="execucao_andamento",
            field=models.TextField(blank=True, null=True, verbose_name="execução - andamento"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="validacao_resultado",
            field=models.TextField(blank=True, null=True, verbose_name="validação - resultado"),
        ),
    ]
