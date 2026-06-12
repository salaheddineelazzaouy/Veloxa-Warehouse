import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser("admin", "admin@test.com", "password")


@pytest.fixture
def warehouse_user(db):
    user = User.objects.create_user("wmgr", "wmgr@test.com", "password")
    user.role = "warehouse_manager"
    user.save()
    return user


@pytest.fixture
def viewer_user(db):
    return User.objects.create_user("viewer", "viewer@test.com", "password")


@pytest.fixture
def product(db):
    from apps.warehouse.models import Product
    return Product.objects.create(sku="TEST-001", name="Test Product", cost_price=100)
