from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0026_reincidenciaocorrencia_data_aprovacao_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitacaoCadastro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=255, verbose_name='Nome Completo')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='E-mail')),
                ('telefone', models.CharField(max_length=20, verbose_name='Telefone')),
                ('senha', models.CharField(max_length=128, verbose_name='Senha')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('aprovado', 'Aprovado'), ('rejeitado', 'Rejeitado')], default='pendente', max_length=20, verbose_name='Status')),
                ('data_solicitacao', models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')),
            ],
            options={
                'verbose_name': 'Solicitação de Cadastro',
                'verbose_name_plural': 'Solicitações de Cadastro',
                'db_table': 'solicitacao_cadastro',
            },
        ),
    ]