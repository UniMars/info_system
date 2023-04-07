"""
信息系统项目的Django设置。

使用Django 4.1通过 'django-admin startproject' 生成。

关于这个文件的更多信息，请见
https://docs.djangoproject.com/en/4.1/topics/settings/

有关所有设置及其值的完整列表，请见
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# 像这样在项目内部构建路径：BASE_DIR / '子目录'
BASE_DIR = Path(__file__).resolve().parent.parent

# 静态文件 (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# 安全警告：在生产环境中要保护好使用的密钥！
load_dotenv(dotenv_path=BASE_DIR / '.env')
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(64)

# 安全警告：不要在生产环境中开启调试模式！
DEBUG = False

ALLOWED_HOSTS = ['*']
# "127.0.0.1", "10.4.32.140"

# 应用程序定义

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "report.apps.ReportConfig",
    "datas.apps.DataDemoConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "info_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = "info_system.wsgi.application"

# 数据库
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        # "ENGINE": "django.db.backends.sqlite3",
        # "NAME": BASE_DIR / "DATA/db.sqlite3",
        "ENGINE": "django.db.backends.mysql",
        "NAME": 'info_sys',
        "USER": os.environ.get('MYSQL_USER'),
        "PASSWORD": os.environ.get('MYSQL_PASSWORD'),
        "HOST": '10.4.32.140',
        "PORT": '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
}

# 密码验证
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

# 国际化
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "zh-Hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = False

# 默认的主键字段类型
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 日志配置
if not os.path.exists(BASE_DIR / 'logs'):
    os.mkdir(BASE_DIR / 'logs')

DEFAULT_CHARSET = 'utf-8'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_verbose',
            'level': 'INFO',
        },
        'infofile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/info.log',
            "maxBytes": 1024 * 1024 * 512,
            "backupCount": 5,
            "encoding": "utf-8",
            'formatter': 'simple',
        },
        'errorfile': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/error.log',
            "maxBytes": 1024 * 1024 * 512,
            "backupCount": 5,
            "encoding": "utf-8",
            'formatter': 'verbose',
        },
        'debugfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/debug.log',
            "maxBytes": 1024 * 1024 * 512,
            "backupCount": 5,
            "encoding": "utf-8",
            'formatter': 'verbose',
        },
        'db_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/db_debug.log',
            "maxBytes": 1024 * 1024 * 512,
            "backupCount": 5,
            "encoding": "utf-8",
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'infofile', 'errorfile', 'debugfile'],
            'level': 'DEBUG',
        },
        'django.utils.autoreload': {
            'handlers': ['console', 'infofile', 'errorfile', 'debugfile'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['db_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'formatters': {
        'verbose': {
            'format':
                '%(levelname)s %(asctime)s MODULE:%(module)s PROCESS:%(process)d THREAD:%(thread)d MESSAGE:%(message)s'
        },
        'console_verbose': {
            'format':
                '%(levelname)s %(asctime)s MODULE:%(module)s PROCESS:%(process)d THREAD:%(thread)d CONSOLE_MESSAGE:%(message)s',
        },

        'simple': {
            'format': '%(levelname)s - %(asctime)s - %(message)s'
        },
    },
}
