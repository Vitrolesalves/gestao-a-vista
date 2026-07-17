# Generated for CRM Kanban + 5W2H conversion of Planner

from django.db import migrations, models


def migrar_status_planner_para_crm(apps, schema_editor):
    PlannerProject = apps.get_model("Gestao_a_Vista", "PlannerProject")
    mapa = {
        "Ativo": "Lead",
        "Em andamento": "Qualificação",
        "Pausado": "Negociação",
        "Concluído": "Fechado",
    }
    for antigo, novo in mapa.items():
        PlannerProject.objects.filter(status=antigo).update(status=novo)


def reverter_status_crm_para_planner(apps, schema_editor):
    PlannerProject = apps.get_model("Gestao_a_Vista", "PlannerProject")
    mapa = {
        "Lead": "Ativo",
        "Qualificação": "Em andamento",
        "Proposta": "Em andamento",
        "Negociação": "Pausado",
        "Fechado": "Concluído",
        "Perdido": "Pausado",
    }
    for antigo, novo in mapa.items():
        PlannerProject.objects.filter(status=antigo).update(status=novo)


class Migration(migrations.Migration):

    dependencies = [
        ("Gestao_a_Vista", "0046_customuser_notificar_livro_ata_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="plannerproject",
            name="cliente",
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name="cliente"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="contato",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="contato"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="telefone",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="telefone"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="email"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="origem_lead",
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name="origem do lead"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="valor_estimado",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="valor estimado"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="probabilidade",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="probabilidade (%)"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="proxima_acao",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="próxima ação"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_what",
            field=models.TextField(blank=True, null=True, verbose_name="5W2H - What / O quê"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_why",
            field=models.TextField(blank=True, null=True, verbose_name="5W2H - Why / Por quê"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_where",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="5W2H - Where / Onde"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_when",
            field=models.DateField(blank=True, null=True, verbose_name="5W2H - When / Quando"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_who",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="5W2H - Who / Quem"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_how",
            field=models.TextField(blank=True, null=True, verbose_name="5W2H - How / Como"),
        ),
        migrations.AddField(
            model_name="plannerproject",
            name="w2h_how_much",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="5W2H - How much / Quanto custa"),
        ),
        migrations.RunPython(migrar_status_planner_para_crm, reverter_status_crm_para_planner),
        migrations.AlterField(
            model_name="plannerproject",
            name="status",
            field=models.CharField(choices=[("Lead", "Lead"), ("Qualificação", "Qualificação"), ("Proposta", "Proposta"), ("Negociação", "Negociação"), ("Fechado", "Fechado"), ("Perdido", "Perdido")], db_index=True, default="Lead", max_length=20, verbose_name="status"),
        ),
    ]
