from django.db import migrations

def set_default_regional_for_existing_users(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    Regional = apps.get_model('Gestao_a_Vista', 'Regional')
    CustomUser = apps.get_model('Gestao_a_Vista', 'CustomUser')
    
    # Create Goiânia - GO regional if it doesn't exist
    regional_go, created = Regional.objects.get_or_create(
        cidade="Goiânia",
        estado="GO",
        defaults={"nome": "Goiânia - GO"}
    )
    
    # Associate all users who don't have a regional with Goiânia
    users_to_update = CustomUser.objects.filter(regional__isnull=True)
    for user in users_to_update:
        if user.username == 'admin':
            user.is_global_admin = True
        user.regional = regional_go
        user.save()

def rollback_default_regional(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0041_regional_customuser_regional_customuser_is_global_admin'),
    ]

    operations = [
        migrations.RunPython(set_default_regional_for_existing_users, rollback_default_regional),
    ]
