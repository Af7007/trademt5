"""
Configuração Django específica para o sistema MLP
Usada para persistência independente na pasta atual
"""

import os
from pathlib import Path

# Configuração básica do Django
SECRET_KEY = 'django-mlp-secret-key'
DEBUG = True
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Nosso app MLP
    'services.quant_app',
]

# Database - SQLite na pasta atual
BASE_DIR = Path(__file__).resolve().parent
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configurações básicas
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'
STATIC_URL = '/static/'

# Middlewares essenciais
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs básicas
ROOT_URLCONF = []

# Templates básicos
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
