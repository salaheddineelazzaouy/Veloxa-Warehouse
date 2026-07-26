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
from lib.pagination import AllowAllPagination

User = get_user_model()
factory = RequestFactory()
from apps.warehouse.models import Product
qs = Product.objects.all()

# Test with superadmin
admin = User.objects.get(username='admin')
request = factory.get('/api/warehouse/products/?all=1')
request.user = admin
pag = AllowAllPagination()
result = pag.paginate_queryset(qs, request)
print(f'Superadmin ?all=1: returned {len(result)} items (expected all)')

# Test with regular user
regular = User.objects.get(username='manager')
request2 = factory.get('/api/warehouse/products/?all=1')
request2.user = regular
pag2 = AllowAllPagination()
result2 = pag2.paginate_queryset(qs, request2)
print(f'Regular user ?all=1: returned {len(result2)} items (expected 20, paginated)')
