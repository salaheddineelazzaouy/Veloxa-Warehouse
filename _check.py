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
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()
u = User.objects.get(username='admin')
refresh = RefreshToken.for_user(u)
token = str(refresh.access_token)
print(f'TOKEN={token}')
