"""
Django settings for heracles project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_%6)i#c^)eqb#33h7hu9em)i7tu)j(zl634%f!5-ang%i-u5u-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

#SHOW_TOOLBAR_CALLBACK = lambda req: DEBUG and not req.is_ajax()
DEBUG_TOOLBAR_CONFIG = {
  'SHOW_TOOLBAR_CALLBACK': 'heracles.settings.show_toolbar_callback'
}
show_toolbar_callback = lambda req: True


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_activeurl',
    'django_xworkflows',
    'django_xworkflows.xworkflow_log',
    'bootstrap3',
    'bootstrap3_datetime',
    'debug_toolbar.apps.DebugToolbarConfig',

    'heracles',
    'sitewide',
    'krb5auth',
    'thoth',
)

AUTH_USER_MODEL = "krb5auth.KerberosUser"

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'krb5auth.middleware.LimitedRemoteUserMiddleware',
    'krb5auth.middleware.RequireLoginMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'krb5auth.auth_backend.Krb5RemoteUserBackend',
    #'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

ROOT_URLCONF = 'heracles.urls'

WSGI_APPLICATION = 'heracles.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smarthost.cc.ic.ac.uk'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_SUBJECT_PREFIX = '[Heracles] '


#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
