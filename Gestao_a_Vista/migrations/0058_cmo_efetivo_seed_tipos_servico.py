# Seed dos Tipos de Serviço usados pelo módulo CMO Efetivo (PRD "Central de
# Controle"). TipoServico é reaproveitado do Planner -- só garante que os 5
# valores do PRD existem, sem duplicar se já tiverem sido criados manualmente.
#
# ATENÇÃO: a tabela Gestao_a_Vista_tiposervico em produção não tem sequence/
# default configurado na coluna "id" (nem PRIMARY KEY -- ver comentário em
# CMOEfetivoConformidade.tipo_servico_nome no models.py) e já tem linhas com
# id NULL. Por isso os ids novos são calculados manualmente aqui (max(id)+1)
# em vez de depender do auto-increment do Django/Postgres, que não funciona
# nessa tabela hoje.

from django.db import migrations
from django.db.models import Max

TIPOS_SERVICO_CMO_EFETIVO = [
    "Limpeza",
    "Manutenção",
    "Alimentação",
    "Logística",
    "Segurança",
]


def seed_tipos_servico(apps, schema_editor):
    TipoServico = apps.get_model('Gestao_a_Vista', 'TipoServico')
    db_alias = schema_editor.connection.alias
    qs = TipoServico.objects.using(db_alias)

    existing_names = set(qs.exclude(nome__isnull=True).values_list('nome', flat=True))
    max_id = qs.exclude(id__isnull=True).aggregate(m=Max('id'))['m'] or 0

    novos = []
    for nome in TIPOS_SERVICO_CMO_EFETIVO:
        if nome in existing_names:
            continue
        max_id += 1
        novos.append(TipoServico(id=max_id, nome=nome, ativo=True))

    if novos:
        qs.bulk_create(novos)


def remove_tipos_servico(apps, schema_editor):
    # Não remove no reverse: outros módulos (Planner) podem já estar usando
    # esses tipos de serviço em registros existentes.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0057_cmo_efetivo_module'),
    ]

    operations = [
        migrations.RunPython(seed_tipos_servico, remove_tipos_servico),
    ]
