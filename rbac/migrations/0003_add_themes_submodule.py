from django.db import migrations


def add_themes_submodule(apps, schema_editor):
    Module = apps.get_model('rbac', 'Module')
    Submodule = apps.get_model('rbac', 'Submodule')
    Permission = apps.get_model('rbac', 'Permission')
    Role = apps.get_model('rbac', 'Role')
    RolePermission = apps.get_model('rbac', 'RolePermission')

    # Ensure Settings module exists
    settings_mod, _ = Module.objects.get_or_create(
        code='settings',
        defaults={
            'name': 'Settings',
            'icon': 'bi-gear-fill',
            'order': 5
        }
    )

    # Ensure Theme Management submodule exists
    submodule, created = Submodule.objects.get_or_create(
        code='settings.themes',
        defaults={
            'module': settings_mod,
            'name': 'Theme Management',
            'url_name': 'admin_theme_manager',
            'order': 3
        }
    )
    if not created and submodule.url_name != 'admin_theme_manager':
        submodule.url_name = 'admin_theme_manager'
        submodule.save(update_fields=['url_name'])

    # Ensure permissions exist: view, edit
    actions = [
        ('view', 'View Theme Management'),
        ('edit', 'Edit / Activate Themes'),
    ]
    created_perms = []
    for action, name in actions:
        perm_code = f"settings.themes.{action}"
        perm, _ = Permission.objects.get_or_create(
            code=perm_code,
            defaults={
                'submodule': submodule,
                'action': action,
                'name': name,
            }
        )
        created_perms.append(perm)

    # Automatically grant to Super Admin role
    superadmin_role = Role.objects.filter(name='Super Admin').first()
    if superadmin_role:
        for perm in created_perms:
            RolePermission.objects.get_or_create(role=superadmin_role, permission=perm)

    # Automatically grant to any role that already possessed settings.site_settings permissions
    for action in ['view', 'edit']:
        site_settings_perm = Permission.objects.filter(code=f'settings.site_settings.{action}').first()
        target_perm = Permission.objects.filter(code=f'settings.themes.{action}').first()
        if site_settings_perm and target_perm:
            roles = Role.objects.filter(rolepermission__permission=site_settings_perm).distinct()
            for role in roles:
                RolePermission.objects.get_or_create(role=role, permission=target_perm)


def remove_themes_submodule(apps, schema_editor):
    Submodule = apps.get_model('rbac', 'Submodule')
    Submodule.objects.filter(code='settings.themes').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0002_add_system_errors_submodule'),
    ]

    operations = [
        migrations.RunPython(add_themes_submodule, remove_themes_submodule),
    ]
