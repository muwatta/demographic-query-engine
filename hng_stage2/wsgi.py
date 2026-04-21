import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hng_stage2.settings')

if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    from django.core.management import call_command
    try:
        call_command('migrate', '--noinput')
        # Also seed the database if empty
        from profiles.models import Profile
        if Profile.objects.count() == 0:
            call_command('seed_profiles')
    except Exception as e:
        print(f"ERROR: {e}")

application = get_wsgi_application()
app = application