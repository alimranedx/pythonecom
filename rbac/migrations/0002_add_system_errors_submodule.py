from django.db import migrations


def add_system_errors_submodule(apps, schema_editor):
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

    # Ensure System Error Logs submodule exists
    submodule, _ = Submodule.objects.get_or_create(
        code='settings.system_errors',
        defaults={
            'module': settings_mod,
            'name': 'System Error Logs',
            'url_name': 'admin_system_errors',
            'order': 2
        }
    )

    # Ensure permissions exist: view, edit, delete
    actions = [
        ('view', 'View System Error Logs'),
        ('edit', 'Edit System Error Logs'),
        ('delete', 'Delete System Error Logs'),
    ]
    created_perms = []
    for action, name in actions:
        perm_code = f"settings.system_errors.{action}"
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

    # Automatically grant to any role that already possessed settings.site_settings.view
    site_settings_perm = Permission.objects.filter(code='settings.site_settings.view').first()
    if site_settings_perm:
        roles_with_site_settings = Role.objects.filter(rolepermission__permission=site_settings_perm).distinct()
        for role in roles_with_site_settings:
            for perm in created_perms:
                RolePermission.objects.get_or_create(role=role, permission=perm)


def remove_system_errors_submodule(apps, schema_editor):
    Submodule = apps.get_model('rbac', 'Submodule')
    Submodule.objects.filter(code='settings.system_errors').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_system_errors_submodule, remove_system_errors_submodule),
    ]
