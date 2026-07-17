"""
Configurações específicas para ambiente de testes
"""

import os
import tempfile

from .settings import *

# Configurações de teste
DEBUG = False
TESTING = True

# Banco de dados em memória para testes mais rápidos
# "readonly" também é mapeado para SQLite para evitar tentativas de conexão
# ao banco externo (localhost) durante os testes.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {"timeout": 20},
    },
    "readonly": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {"timeout": 20},
    },
}

# Migrações habilitadas para testes (necessário para criar tabelas)
# MIGRATION_MODULES podem ser desabilitadas em testes específicos se necessário

# Cache em memória para testes
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Configurações de sessão para testes
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Arquivos estáticos para testes
STATIC_ROOT = tempfile.mkdtemp()
MEDIA_ROOT = tempfile.mkdtemp()

# Desabilitar logging durante testes
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# Configurações de segurança para testes
SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Desabilitar configurações de segurança para testes
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configurações de email para testes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Password hashers mais rápidos para testes
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
