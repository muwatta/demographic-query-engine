from pathlib import Path
import dj_database_url
import os

import os
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-trn_)g)xi$dcqx)9m&@0ahjkr-*i8cdr(s8v#@!l8t^7@@1-3g'
DEBUG = False
USE_HTTPS = not DEBUG 

ALLOWED_HOSTS = ['.vercel.app', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'profiles',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'users.middleware.APIVersionMiddleware',  
    'users.middleware.RequestLogMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
#   JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # Strong random string
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_LIFETIME_SECONDS = 15 * 60   # 15 minutes
REFRESH_TOKEN_LIFETIME_SECONDS = 7 * 24 * 3600  # 7 days
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = ['https://your-web-portal.vercel.app']

ROOT_URLCONF = 'hng_stage2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hng_stage2.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    # Fallback to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [...]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'