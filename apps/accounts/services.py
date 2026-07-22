import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)
User = get_user_model()


def create_user(username: str, email: str, password: str, role: str = "viewer", **extra) -> User:
    if role not in dict(User.ROLE_CHOICES):
        raise ValueError(f"Invalid role: {role}")
    if "tenant" not in extra or extra.get("tenant") is None:
        from apps.tenants.models import Tenant
        tenant = Tenant.objects.first()
        extra["tenant"] = tenant
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        **extra,
    )
    group = Group.objects.filter(name=role).first()
    if group:
        user.groups.add(group)
    logger.info("Created user %s with role %s", user.username, role)
    return user


def assign_role(user: User, new_role: str) -> User:
    if new_role not in dict(User.ROLE_CHOICES):
        raise ValueError(f"Invalid role: {new_role}")
    user.role = new_role
    user.groups.clear()
    group = Group.objects.filter(name=new_role).first()
    if group:
        user.groups.add(group)
    user.save(update_fields=["role"])
    logger.info("Assigned role %s to user %s", new_role, user.username)
    return user


def deactivate_user(user: User) -> User:
    user.is_active = False
    user.save(update_fields=["is_active"])
    logger.info("Deactivated user %s", user.username)
    return user
