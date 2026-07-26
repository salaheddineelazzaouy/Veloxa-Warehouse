import os, django
from pathlib import Path
env_path = Path(__file__).parent / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
c = Client()

print("=== RBAC Test ===")

viewer = User.objects.filter(username='rbactest').first()
if viewer:
    c.login(username=viewer.username, password='pass1234')
    r1 = c.get('/products/')
    print('Viewer LIST /products/: ' + str(r1.status_code))
    r2 = c.get('/products/create/')
    print('Viewer CREATE /products/create/: ' + str(r2.status_code) + ' -> ' + str(r2.get('Location', '200 OK')))
    r3 = c.get('/backorders/create/')
    print('Viewer CREATE /backorders/create/: ' + str(r3.status_code) + ' -> ' + str(r3.get('Location', '200 OK')))
    r4 = c.get('/invoices/create/')
    print('Viewer CREATE /invoices/create/: ' + str(r4.status_code) + ' -> ' + str(r4.get('Location', '200 OK')))
    c.logout()

admin = User.objects.filter(role='super_admin').first()
if admin:
    c.login(username=admin.username, password='pass1234')
    r5 = c.get('/products/create/')
    print('Admin CREATE /products/create/: ' + str(r5.status_code))
    r6 = c.get('/landing/manage/')
    print('Admin LANDING /landing/manage/: ' + str(r6.status_code))
    c.logout()

wm = User.objects.filter(role='warehouse_manager').first()
if wm:
    c.login(username=wm.username, password='pass1234')
    r7 = c.get('/products/create/')
    print('WM CREATE /products/create/: ' + str(r7.status_code))
    r8 = c.get('/landing/manage/')
    print('WM LANDING /landing/manage/: ' + str(r8.status_code) + ' -> ' + str(r8.get('Location', '200 OK')))
    c.logout()

print("=== Done ===")
