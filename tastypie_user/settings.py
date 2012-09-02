import os

ADMINS = (
    ('test@example.com', 'Mr. Test')
)

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.path.normpath(os.path.join(BASE_PATH, 'media'))

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'tastypie.db'
TEST_DATABASE_NAME = 'tastypie-test.db'

# for forwards compatibility
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%s' % DATABASE_ENGINE,
        'NAME': DATABASE_NAME,
        'TEST_NAME': TEST_DATABASE_NAME
    }
}


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'tastypie',
    'tastypie_user']

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# to make sure timezones are handled correctly in Django>=1.4
USE_TZ = True

ROOT_URLCONF = 'tests.basic_urls'

AUTHENTICATION_BACKENDS = (
    'tastypie_user.auth_backends.ApiKeyBackend',
    'tastypie_user.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',)
