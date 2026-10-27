from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel


class Module(TimeStampedModel):
    """
    Top-level grouping of back-office functionality (e.g., Catalog, Orders, Administration).
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, help_text="Unique slug like 'catalog', 'orders'")
    icon = models.CharField(max_length=50, default="bi-folder", help_text="Bootstrap icon class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Submodule(TimeStampedModel):
    """
    Second-level navigation unit under a Module (e.g., Products under Catalog).
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='submodules')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=80, unique=True, help_text="Unique key like 'catalog.products'")
    url_name = models.CharField(max_length=100, blank=True, help_text="Django URL route name")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['module__order', 'order', 'name']

    def __str__(self):
        return f"{self.module.name} ➔ {self.name}"


class Permission(TimeStampedModel):
    """
    Specific capability on a submodule (view, create, edit, delete, export).
    """
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ]

    submodule = models.ForeignKey(Submodule, on_delete=models.CASCADE, related_name='permissions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    code = models.CharField(max_length=120, unique=True, help_text="e.g. 'catalog.products.view'")
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ['submodule__module__order', 'submodule__order', 'action']
        unique_together = ('submodule', 'action')

    def __str__(self):
        return f"{self.submodule.name} ({self.get_action_display()})"


class Role(TimeStampedModel):
    """
    Role assigned to staff users (e.g. 'Catalog Manager', 'Order Dispatcher').
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False, help_text="System-protected role that cannot be deleted")
    permissions = models.ManyToManyField(Permission, through='RolePermission', related_name='roles', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RolePermission(TimeStampedModel):
    """
    Explicit junction linking a Role to its granted Permissions.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.code}"


class UserRole(TimeStampedModel):
    """
    Junction linking a Django User (staff) to one or more Roles.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} ➔ {self.role.name}"
