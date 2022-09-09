from os import environ

SECRET_KEY = "not_empty"
SITE_ID = 1

if "POSTGRES_HOST" in environ:
    # Run against Docker:
    #
    # docker run --rm -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=qss -p 5432:5432 postgres:12
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": environ["POSTGRES_DATABASE"],
            "USER": environ["POSTGRES_USER"],
            "PASSWORD": environ["POSTGRES_PASSWORD"],
            "HOST": environ["POSTGRES_HOST"],
            "PORT": "5432",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

MIDDLEWARE_CLASSES = tuple()

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

INSTALLED_APPS = ("tests",)
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

# Avoid a warning on Django >= 3.2.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
}
