from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0039_colaboradorsra_situacao_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='psicossocialprojeto',
            name='detalhamento_fatores_protetivos',
            field=models.TextField(blank=True, null=True, verbose_name='Detalhamento dos Fatores Protetivos'),
        ),
    ]
