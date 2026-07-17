from django.db import migrations, models
from django.utils.text import slugify


def backfill_db_slug(apps, schema_editor):
    """
    A primeira Regional criada em cada estado recebe o slug puro do estado
    (preserva exatamente o alias/banco fisico ja usado hoje - go, sp, es).
    Qualquer Regional adicional no mesmo estado (ex: VPA em SP) recebe um
    slug novo derivado do nome, para ganhar um banco proprio e isolado.
    """
    Regional = apps.get_model('Gestao_a_Vista', 'Regional')
    seen_estados = set()
    for reg in Regional.objects.order_by('created_at', 'id'):
        estado_lower = (reg.estado or '').strip().lower()
        if estado_lower and estado_lower not in seen_estados:
            slug = estado_lower
            seen_estados.add(estado_lower)
        else:
            base = slugify(f"{estado_lower}-{reg.nome}")[:45] or f"regional-{str(reg.id)[:8]}"
            slug = base
            i = 1
            while Regional.objects.filter(db_slug=slug).exclude(pk=reg.pk).exists():
                i += 1
                slug = f"{base}-{i}"[:50]
        reg.db_slug = slug
        reg.save(update_fields=['db_slug'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0054_auditoria_ocorrencia_hash_pk_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='regional',
            name='db_slug',
            field=models.SlugField(max_length=50, null=True, unique=True, verbose_name='Identificador do Banco de Dados'),
        ),
        migrations.RunPython(backfill_db_slug, noop_reverse),
        migrations.AlterField(
            model_name='regional',
            name='db_slug',
            field=models.SlugField(max_length=50, unique=True, verbose_name='Identificador do Banco de Dados'),
        ),
    ]
