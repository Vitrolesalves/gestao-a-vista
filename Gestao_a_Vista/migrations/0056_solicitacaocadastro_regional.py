import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0055_regional_db_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacaocadastro',
            name='regional',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='Gestao_a_Vista.regional',
                verbose_name='Regional Pretendida',
            ),
        ),
    ]
