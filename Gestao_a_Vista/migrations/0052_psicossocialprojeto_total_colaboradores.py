from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0051_planner_pipeline_stages'),
    ]

    operations = [
        migrations.AddField(
            model_name='psicossocialprojeto',
            name='total_colaboradores',
            field=models.PositiveIntegerField(default=0, verbose_name='Total de Colaboradores do Contrato'),
        ),
    ]
