import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

email = 'admin@biswastech.com'
password = 'admin123'

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password, name='Admin')
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")
