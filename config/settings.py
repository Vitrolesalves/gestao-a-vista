"""
Django settings do projeto Gestão à Vista.

Toda configuração sensível (banco, e-mail, integrações) vem de variáveis de
ambiente — ver .env.example na raiz. Sem nada configurado, o projeto sobe com
SQLite local e e-mail no console, pronto para avaliação/desenvolvimento.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-chave-de-desenvolvimento-trocar-em-producao",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if o.strip()
]

# URL pública do site — usada para montar links absolutos (ex.: QR Codes do
# Livro Ata que precisam funcionar fora da rede local).
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = False

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "Gestao_a_Vista",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "Gestao_a_Vista.signals.RequestContextMiddleware",        # Contexto do request na thread
    "Gestao_a_Vista.middleware.RegionalRoutingMiddleware",     # Roteamento dinâmico de regional
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "Gestao_a_Vista.middleware.UserOnlineStatusMiddleware",  # Middleware com tratamento de erro
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "Gestao_a_Vista", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "Gestao_a_Vista.context_processors.user_permissions",
                "Gestao_a_Vista.context_processors.created_regionais_processor",
            ],
        },
    },
]

# WSGI application path
WSGI_APPLICATION = "config.wsgi.application"


# --- BANCO DE DADOS ---
# Com POSTGRES_HOST definido, usa PostgreSQL (arquitetura multi-banco por
# regional + réplica readonly para relatórios). Sem nada definido, cai em
# SQLite local — suficiente para rodar e navegar em todas as telas.
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "")

if POSTGRES_HOST:
    _pg_base = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "gestao_a_vista"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": POSTGRES_HOST,
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
    DATABASES = {
        "default": dict(_pg_base),
        # Réplica somente-leitura para consultas pesadas de relatório. Se não
        # houver réplica, aponte as variáveis READONLY_* para o mesmo banco.
        "readonly": {
            **_pg_base,
            "NAME": os.environ.get("READONLY_DB", _pg_base["NAME"]),
            "HOST": os.environ.get("READONLY_HOST", POSTGRES_HOST),
        },
    }
    # Router direciona consultas de relatório para o banco readonly e cada
    # Regional para seu próprio banco (registrado em runtime — ver
    # Gestao_a_Vista/db_manager.py e apps.py).
    DATABASE_ROUTERS = ["Gestao_a_Vista.db_router.DatabaseRouter"]
else:
    _sqlite = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
    DATABASES = {
        "default": dict(_sqlite),
        "readonly": dict(_sqlite),
    }
    # Sem múltiplos bancos no modo SQLite — router desativado.
    DATABASE_ROUTERS = []


# Password validation
if DEBUG:
    # Validadores mais simples em desenvolvimento
    AUTH_PASSWORD_VALIDATORS = []
else:
    # Produção: Validadores completos e hash seguro
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

# PASSWORD_HASHERS: Argon2 como principal (mais seguro), MD5 para compatibilidade
# com dados legados. Ao fazer login, o Django migra automaticamente senhas
# MD5 -> Argon2.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication settings
AUTH_USER_MODEL = "Gestao_a_Vista.CustomUser"
LOGIN_URL = "gestao_a_vista:login"
LOGIN_REDIRECT_URL = "gestao_a_vista:dashboard"
LOGOUT_REDIRECT_URL = "gestao_a_vista:login"
LOGOUT_URL = "gestao_a_vista:logout"

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hora em segundos
SESSION_SAVE_EVERY_REQUEST = False  # Salva sessão apenas quando modificada (evita write no DB a cada request)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Cache: arquivo para dados gerais + memória local para autenticação.
# Nota: Sessões NÃO usam cache puro para evitar logout inesperado.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, 'django_cache'),
        "TIMEOUT": 300,  # 5 minutos para dados gerais (não sessões)
        "OPTIONS": {
            "MAX_ENTRIES": 2000,
            "CULL_FREQUENCY": 3,
        },
    },
    # Cache específico para autenticação e status de usuário
    "auth": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "auth-cache",
        "TIMEOUT": 600,  # 10 minutos para dados de autenticação
        "OPTIONS": {
            "MAX_ENTRIES": 500,
            "CULL_FREQUENCY": 2,
        },
    }
}

# SESSIONS: cached_db lê do cache primeiro, persiste no DB — evita query de sessão em todo request
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# LOGGING: Configuração para filtrar erros HTTPS irrelevantes no desenvolvimento
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "ignore_https_errors": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: not any(
                [
                    "Bad request version" in record.getMessage(),
                    "Bad HTTP/0.9 request type" in record.getMessage(),
                    "Bad request syntax" in record.getMessage(),
                    "You're accessing the development server over HTTPS"
                    in record.getMessage(),
                ]
            ),
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "filters": ["ignore_https_errors"],
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# --- CONFIGURAÇÃO DE E-MAIL ---
# Sem EMAIL_HOST_USER definido, os e-mails são impressos no console (útil em
# desenvolvimento). Em produção, configure SMTP via variáveis de ambiente.
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
if EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.environ.get(
        "DEFAULT_FROM_EMAIL", f"Gestão à Vista <{EMAIL_HOST_USER}>"
    )
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = "Gestão à Vista <nao-responda@localhost>"

# --- CONFIGURAÇÃO UAZAPI (NOTIFICAÇÕES WHATSAPP) ---
# Integração opcional com a API de WhatsApp (uazapi). Sem os tokens, o módulo
# de notificações apenas registra que a integração não está configurada.
UAZAPI_BASE_URL = os.environ.get("UAZAPI_BASE_URL", "")
UAZAPI_INSTANCE_TOKEN = os.environ.get("UAZAPI_INSTANCE_TOKEN", "")
UAZAPI_ADMIN_TOKEN = os.environ.get("UAZAPI_ADMIN_TOKEN", "")
LIVRO_ATA_NOTIFICACAO_NUMERO_TESTE = os.environ.get(
    "LIVRO_ATA_NOTIFICACAO_NUMERO_TESTE", ""
)

# --- INTEGRACAO STREAMLIT FINANCEIRO ---
FINANCEIRO_URL = os.getenv("FINANCEIRO_URL", "http://localhost:8501")
