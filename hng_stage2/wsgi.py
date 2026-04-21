import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hng_stage2.settings')

# Run migrations on first request (only if on Vercel)
if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    from django.core.management import call_command
    try:
        call_command('migrate', '--noinput')
    except Exception:
        pass

application = get_wsgi_application()
app = application