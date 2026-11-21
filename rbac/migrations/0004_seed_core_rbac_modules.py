from django.db import migrations


def seed_core_rbac_modules(apps, schema_editor):
    Module = apps.get_model('rbac', 'Module')
    Submodule = apps.get_model('rbac', 'Submodule')
    Permission = apps.get_model('rbac', 'Permission')
    Role = apps.get_model('rbac', 'Role')
    RolePermission = apps.get_model('rbac', 'RolePermission')

    structure = [
        {
            'name': 'Catalog',
            'code': 'catalog',
            'icon': 'bi-boxes',
            'order': 1,
            'submodules': [
                {
                    'name': 'Products',
                    'code': 'catalog.products',
                    'url_name': 'admin_product_list',
                    'order': 1,
                    'actions': ['view', 'create', 'edit', 'delete']
                },
                {
                    'name': 'Categories',
                    'code': 'catalog.categories',
                    'url_name': 'admin_category_list',
                    'order': 2,
                    'actions': ['view', 'create', 'edit', 'delete']
                },
                {
                    'name': 'Brands',
                    'code': 'catalog.brands',
                    'url_name': 'admin_brand_list',
                    'order': 3,
                    'actions': ['view', 'create', 'edit', 'delete']
                },
                {
                    'name': 'Customer Reviews',
                    'code': 'catalog.reviews',
                    'url_name': 'admin_review_list',
                    'order': 4,
                    'actions': ['view', 'delete']
                },
            ]
        },
        {
            'name': 'Orders',
            'code': 'orders',
            'icon': 'bi-cart-check',
            'order': 2,
            'submodules': [
                {
                    'name': 'All Orders',
                    'code': 'orders.orders',
                    'url_name': 'admin_order_list',
                    'order': 1,
                    'actions': ['view', 'edit', 'delete', 'create']
                },
            ]
        },
        {
            'name': 'Customers',
            'code': 'customers',
            'icon': 'bi-people',
            'order': 3,
            'submodules': [
                {
                    'name': 'Customer Accounts',
                    'code': 'customers.customers',
                    'url_name': 'admin_customer_list',
                    'order': 1,
                    'actions': ['view', 'edit']
                },
            ]
        },
        {
            'name': 'User & Role Management',
            'code': 'rbac',
            'icon': 'bi-shield-lock-fill',
            'order': 4,
            'submodules': [
                {
                    'name': 'User Management',
                    'code': 'rbac.staff',
                    'url_name': 'admin_staff_list',
                    'order': 1,
                    'actions': ['view', 'create', 'edit', 'delete']
                },
                {
                    'name': 'Role & Permission Management',
                    'code': 'rbac.roles',
                    'url_name': 'admin_role_list',
                    'order': 2,
                    'actions': ['view', 'create', 'edit', 'delete']
                },
            ]
        },
        {
            'name': 'Settings',
            'code': 'settings',
            'icon': 'bi-gear-fill',
            'order': 5,
            'submodules': [
                {
                    'name': 'Store & Brand Settings',
                    'code': 'settings.site_settings',
                    'url_name': 'admin_site_settings',
                    'order': 1,
                    'actions': ['view', 'edit']
                },
                {
                    'name': 'System Error Logs',
                    'code': 'settings.system_errors',
                    'url_name': 'admin_system_errors',
                    'order': 2,
                    'actions': ['view', 'edit', 'delete']
                },
                {
                    'name': 'Theme Management',
                    'code': 'settings.themes',
                    'url_name': 'admin_theme_manager',
                    'order': 3,
                    'actions': ['view', 'edit']
                },
            ]
        },
    ]

    superadmin_role, _ = Role.objects.get_or_create(
        name='Super Admin',
        defaults={'description': 'Full unrestricted back-office privileges', 'is_system_role': True}
    )

    for mod_data in structure:
        module, _ = Module.objects.get_or_create(
            code=mod_data['code'],
            defaults={
                'name': mod_data['name'],
                'icon': mod_data['icon'],
                'order': mod_data['order']
            }
        )
        for sub_data in mod_data['submodules']:
            submodule, _ = Submodule.objects.get_or_create(
                code=sub_data['code'],
                defaults={
                    'module': module,
                    'name': sub_data['name'],
                    'url_name': sub_data['url_name'],
                    'order': sub_data['order']
                }
            )
            # Update url_name if changed
            if submodule.url_name != sub_data['url_name']:
                submodule.url_name = sub_data['url_name']
                submodule.save(update_fields=['url_name'])

            for action in sub_data['actions']:
                perm_code = f"{sub_data['code']}.{action}"
                perm, _ = Permission.objects.get_or_create(
                    code=perm_code,
                    defaults={
                        'submodule': submodule,
                        'action': action,
                        'name': f"{action.title()} {sub_data['name']}"
                    }
                )
                if superadmin_role:
                    RolePermission.objects.get_or_create(role=superadmin_role, permission=perm)


def revert_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0003_add_themes_submodule'),
    ]

    operations = [
        migrations.RunPython(seed_core_rbac_modules, revert_seed),
    ]
