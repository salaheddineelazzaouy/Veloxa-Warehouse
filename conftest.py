import pytest
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant
from apps.warehouse.models import Product

User = get_user_model()


@pytest.fixture
def tenant(db):
    t, _ = Tenant.objects.get_or_create(slug="test", defaults={"name": "Test Tenant"})
    return t


@pytest.fixture
def admin_user(db, tenant):
    return User.objects.create_superuser("admin", "admin@test.com", "password", tenant=tenant)


@pytest.fixture
def warehouse_user(db, tenant):
    user = User.objects.create_user("wmgr", "wmgr@test.com", "password", tenant=tenant)
    user.role = "warehouse_manager"
    user.save()
    return user


@pytest.fixture
def viewer_user(db, tenant):
    return User.objects.create_user("viewer", "viewer@test.com", "password", tenant=tenant)


@pytest.fixture
def product(db, tenant):
    return Product.objects.create(sku="TEST-001", name="Test Product", cost_price=100, tenant=tenant)
