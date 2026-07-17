import uuid
from django.db import migrations, models
import django.db.models.deletion
from django.contrib.auth.hashers import make_password

def create_supreme_admin(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    CustomUser = apps.get_model('Gestao_a_Vista', 'CustomUser')
    if not CustomUser.objects.filter(username='admin').exists():
        CustomUser.objects.create(
            username='admin',
            name='Administrador Global',
            email='admin@example.com',
            password=make_password('admin12345'),
            role='administrador',
            is_global_admin=True,
            is_active=True,
            is_staff=True,
            is_superuser=True
        )

def remove_supreme_admin(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    CustomUser = apps.get_model('Gestao_a_Vista', 'CustomUser')
    CustomUser.objects.filter(username='admin').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0040_psicossocialprojeto_detalhamento_fatores_protetivos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Regional',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=255, unique=True, verbose_name='Nome da Regional')),
                ('estado', models.CharField(max_length=2, verbose_name='Estado (UF)')),
                ('cidade', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cidade')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Regional',
                'verbose_name_plural': 'Regionais',
                'db_table': 'Gestao_a_Vista_regional',
            },
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_global_admin',
            field=models.BooleanField(default=False, verbose_name='É Administrador Global supremo?'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='regional',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Gestao_a_Vista.regional', verbose_name='Regional'),
        ),
        migrations.RunPython(create_supreme_admin, remove_supreme_admin),
    ]
