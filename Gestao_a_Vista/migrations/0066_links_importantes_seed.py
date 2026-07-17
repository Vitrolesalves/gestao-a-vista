from django.db import migrations

LINKS_BASE = [
    ("Sistema 360", "https://sistema360.example.com/dashboard", ""),
    ("OpsVista", "https://portal.opsvista.example.com/", ""),
    ("Portal Corporativo", "https://portal.example.com/Login.aspx", ""),
    ("Prisma", "https://prisma.example.com/Prisma4/Process/StockIssue", ""),
    ("Home Grupo Exemplo", "https://www.example.com/", ""),
    ("Canal de Ética", "https://etica.example.com/", ""),
]


def criar_links_base(apps, schema_editor):
    LinkImportante = apps.get_model("Gestao_a_Vista", "LinkImportante")
    for ordem, (titulo, url, descricao) in enumerate(LINKS_BASE, start=1):
        LinkImportante.objects.get_or_create(
            titulo=titulo,
            defaults={"url": url, "descricao": descricao, "ordem": ordem, "ativo": True},
        )


def remover_links_base(apps, schema_editor):
    LinkImportante = apps.get_model("Gestao_a_Vista", "LinkImportante")
    titulos = [titulo for titulo, _, _ in LINKS_BASE]
    LinkImportante.objects.filter(titulo__in=titulos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0065_linkimportante'),
    ]

    operations = [
        migrations.RunPython(criar_links_base, remover_links_base),
    ]
