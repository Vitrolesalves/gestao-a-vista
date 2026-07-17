import uuid
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0027_solicitacaocadastro'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardImplantacao',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do Fluxo')),
                ('status', models.CharField(choices=[('em_andamento', 'Em andamento'), ('pausada', 'Pausada'), ('concluida', 'Concluída')], default='em_andamento', max_length=20, db_index=True, verbose_name='Status')),
                ('etapa_atual', models.IntegerField(default=1, db_index=True, verbose_name='Etapa Atual')),
                ('tipo_implantacao', models.CharField(blank=True, null=True, max_length=50, verbose_name='Tipo de Implantação')),
                ('mapeamento_locais', models.TextField(blank=True, null=True, verbose_name='Mapeamento de Locais')),
                ('anexo_mapeamento', models.FileField(blank=True, null=True, upload_to='implantacoes/mapeamento/', verbose_name='Anexo do Mapeamento')),
                ('anexo_checklist', models.FileField(blank=True, null=True, upload_to='implantacoes/checklist/', verbose_name='Anexo do Checklist')),
                ('rotinas_criadas', models.BooleanField(default=False, verbose_name='Rotinas Criadas')),
                ('anexo_rotinas', models.FileField(blank=True, null=True, upload_to='implantacoes/rotinas/', verbose_name='Anexo das Rotinas')),
                ('anexo_qrcodes', models.FileField(blank=True, null=True, upload_to='implantacoes/qrcodes/', verbose_name='Anexo dos QR Codes')),
                ('anexo_treinamento', models.FileField(blank=True, null=True, upload_to='implantacoes/treinamento/', verbose_name='Anexo do Treinamento')),
                ('anexo_entrega', models.FileField(blank=True, null=True, upload_to='implantacoes/entrega/', verbose_name='Anexo da Entrega')),
                ('link_bi', models.URLField(blank=True, null=True, verbose_name='Link do BI')),
                ('anexo_bi', models.FileField(blank=True, null=True, upload_to='implantacoes/bi/', verbose_name='Anexo do BI')),
                ('bi_inicio_data', models.DateTimeField(blank=True, null=True, verbose_name='Início da etapa do BI')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Fluxo de Implantação',
                'verbose_name_plural': 'Fluxos de Implantação',
                'db_table': 'Gestao_a_Vista_cardimplantacao',
                'ordering': ['-created_at'],
            },
        ),
    ]
