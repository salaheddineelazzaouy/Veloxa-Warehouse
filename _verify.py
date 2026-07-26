import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
import sys
sys.path.insert(0, r'C:\Users\Salah\Documents\pos inevntory\veloxa_warehouse')
with open(r'C:\Users\Salah\Documents\pos inevntory\veloxa_warehouse\.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from lib.pagination import AllowAllPagination

User = get_user_model()
factory = RequestFactory()
pag = AllowAllPagination()

# Test with superadmin
admin = User.objects.get(username='admin')
request = factory.get('/api/warehouse/products/?all=1')
request.user = admin
from apps.warehouse.models import Product
qs = Product.objects.all()
result = pag.paginate_queryset(qs, request)
print(f'Superadmin ?all=1: returned {len(result)} items (expected 38, full list)')

# Test with regular user
regular = User.objects.get(username='manager')
request2 = factory.get('/api/warehouse/products/?all=1')
request2.user = regular
pag2 = AllowAllPagination()
result2 = pag2.paginate_queryset(qs, request2)
print(f'Regular user ?all=1: returned {len(result2)} items (expected 20, paginated)')

# Verify no ?all=1 with regular user
request3 = factory.get('/api/warehouse/products/')
request3.user = regular
pag3 = AllowAllPagination()
result3 = pag3.paginate_queryset(qs, request3)
print(f'Regular user no all: returned {len(result3)} items (expected 20, paginated)')
