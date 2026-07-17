import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0043_add_regional_directors'),
    ]

    operations = [
        migrations.CreateModel(
            name='CMOPonto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('colaborador_nome', models.CharField(max_length=255, verbose_name='Nome do Colaborador')),
                ('data_hora', models.DateTimeField(verbose_name='Data/Hora Batida')),
                ('foto', models.ImageField(upload_to='cmo_pontos/', verbose_name='Foto de Evidência')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cmo_ponto',
                'ordering': ['-data_hora'],
            },
        ),
        migrations.CreateModel(
            name='CMOTrocaServico',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('colaborador_nome', models.CharField(max_length=255, verbose_name='Colaborador Solicitante')),
                ('tipo', models.CharField(choices=[('troca', 'Troca de Turno'), ('cobertura', 'Cobertura de Turno')], max_length=20, verbose_name='Tipo')),
                ('colaborador_substituto', models.CharField(max_length=255, verbose_name='Colaborador Substituto')),
                ('dia', models.DateField(verbose_name='Dia do Serviço')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('aprovado', 'Aprovado'), ('rejeitado', 'Rejeitado')], default='pendente', max_length=20, verbose_name='Status')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cmo_troca_servico',
                'ordering': ['-criado_em'],
            },
        ),
    ]
