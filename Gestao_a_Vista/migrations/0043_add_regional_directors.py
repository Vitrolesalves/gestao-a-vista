from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0042_set_default_regional'),
    ]

    operations = [
        migrations.AddField(
            model_name='regional',
            name='diretor_regional',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Diretor Regional'),
        ),
        migrations.AddField(
            model_name='regional',
            name='diretor_executivo',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Diretor Executivo'),
        ),
    ]
