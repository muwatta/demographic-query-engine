import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hng_stage2.settings')
application = get_wsgi_application()
app = application

if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    try:
        call_command('migrate', '--noinput')
    except Exception as e:
        print(f"Migration error: {e}")