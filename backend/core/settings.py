from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Security
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Apps
INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'app_accounts',
    'app_content',
    'app_feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {'default': env.db('DATABASE_URL')}

# Users and passwords
AUTH_USER_MODEL = 'app_accounts.User'
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
PASSWORD_RESET_TIMEOUT = 60 * 60

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Language and time
LANGUAGE_CODE = 'de'
LANGUAGES = [('de', 'Deutsch'), ('en', 'English')]
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# Content translation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'de'
MODELTRANSLATION_FALLBACK_LANGUAGES = ('de',)

# API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['core.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['djangorestframework_camel_case.render.CamelCaseJSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['djangorestframework_camel_case.parser.CamelCaseJSONParser'],
    'EXCEPTION_HANDLER': 'core.exceptions.api_exception_handler',
    'NON_FIELD_ERRORS_KEY': 'non_field',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/hour',
        'user': '1000/hour',
        'auth': '5/minute',
        'password_reset': '3/hour',
        'requests': '5/hour',
    },
}

# Sessions and CSRF
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = env.bool('SECURE_COOKIES', default=False)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Email
MAILERS = {
    'default': {
        'BACKEND': env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend'),
        'OPTIONS': {
            'host': env('EMAIL_HOST', default='localhost'),
            'port': env.int('EMAIL_PORT', default=587),
            'username': env('EMAIL_HOST_USER', default=''),
            'password': env('EMAIL_HOST_PASSWORD', default=''),
            'use_tls': env.bool('EMAIL_USE_TLS', default=True),
        },
    },
}
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@snipatlas.jensbaumann.com')
REPLY_TO_EMAIL = env('REPLY_TO_EMAIL')

# Frontend
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:4200')
