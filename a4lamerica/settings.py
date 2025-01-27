"""
Django settings for a4lamerica project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 根据环境变量设置所有环境相关配置
if DEBUG:
    # 开发环境设置
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        '192.168.1.*',  # 允许所有192.168.1网段
    ]
    # 开发环境媒体文件配置
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    SECURE_PROXY_SSL_HEADER = None
    USE_X_FORWARDED_HOST = False
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://192.168.1.70:8000',
        'http://192.168.1.71:8000',
        'http://192.168.1.75:8000',
        'http://192.168.1.*:8000',
    ]
    # 根据请求动态设置SITE_URL
    SITE_URL = 'http://192.168.1.70:8000'  # 使用开发机器的实际IP
    PROTOCOL = 'http'
    
    # 开发环境日志配置
    LOG_DIR = BASE_DIR / 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 开发环境限制配置
    IP_RATE_LIMIT_MAX = 200      
    IP_RATE_LIMIT_TIMEOUT = 3000
    DEVICE_RATE_LIMIT_MAX = 300  
    DEVICE_RATE_LIMIT_TIMEOUT = 864000

else:
    # 生产环境设置
    ALLOWED_HOSTS = [
        'a4lamerica.com',
        'www.a4lamerica.com',
        '192.168.1.69',     # 服务器内网IP，即使配置了hosts也需要
    ]
    
    # 从环境变量获取额外的allowed hosts（用于外网IP）
    if os.getenv('EXTRA_ALLOWED_HOSTS'):
        ALLOWED_HOSTS.extend(os.getenv('EXTRA_ALLOWED_HOSTS').split(','))
    
    # Session settings（仅生产环境）
    SESSION_COOKIE_AGE = 86400  # 24小时，以秒为单位
    SESSION_SAVE_EVERY_REQUEST = True  # 每次请求都更新session
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # 浏览器关闭时session不过期
    SESSION_COOKIE_NAME = 'a4lamerica_sessionid'  # 自定义session cookie名称
    
    # 媒体文件配置
    MEDIA_URL = '/media/'
    MEDIA_ROOT = '/var/www/a4lamerica/media'  # Apache用户需要有这个目录的写权限
    
    SECURE_SSL_REDIRECT = False  # 由 Apache 处理
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    CSRF_TRUSTED_ORIGINS = [
        'https://a4lamerica.com',
        'https://www.a4lamerica.com',
        'http://a4lamerica.com',
        'http://www.a4lamerica.com'
    ]
    SITE_URL = 'https://a4lamerica.com'
    PROTOCOL = 'https'
    
    # 生产环境日志配置
    LOG_DIR = Path('/var/log/apache2')
    
    # 生产环境限制配置
    IP_RATE_LIMIT_MAX = 5
    IP_RATE_LIMIT_TIMEOUT = 300
    DEVICE_RATE_LIMIT_MAX = 10
    DEVICE_RATE_LIMIT_TIMEOUT = 86400

    # 文件上传权限设置
    FILE_UPLOAD_PERMISSIONS = 0o644
    FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
    
    # 建议在生产环境使用 CDN 或专门的文件存储服务
    # AWS S3 配置示例（如果使用 S3）
    # AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    # AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    # AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    # AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    # MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# 基于环境配置的日志设置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG' if DEBUG else 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'debug.log' if DEBUG else '/var/log/apache2/a4lamerica_error.log',
            'formatter': 'verbose',
        },
        'cron': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'cron.log' if DEBUG else '/var/log/apache2/cron.log',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django': {  # Django框架的日志
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'accounts': {  # accounts应用的普通日志
            'handlers': ['file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,  # 防止日志重复
        },
        'accounts.tasks': {  # accounts应用的cron任务日志
            'handlers': ['cron'],
            'level': 'INFO',
            'propagate': False,  # 防止日志重复
        }
    },
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'django_crontab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'a4lamerica.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

WSGI_APPLICATION = 'a4lamerica.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Google reCAPTCHA 配置
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')  # 从Google获取的站点密钥
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')  # 从Google获取的密钥
RECAPTCHA_SCORE_THRESHOLD = os.getenv('RECAPTCHA_SCORE_THRESHOLD')  # 设置分数阈值，低于此分数视为机器人

# 设置日期时间格式为美国短格式
DATE_FORMAT = 'm/d/Y'           # 例如: 01/15/2024
TIME_FORMAT = 'g:i A'           # 例如: 3:45 PM
DATETIME_FORMAT = 'm/d/Y g:i A' # 例如: 01/15/2024 3:45 PM

# 根据环境设置CRONJOBS
if DEBUG:
    CRONJOBS = [
        ('0 1 * * *', 'accounts.tasks.cleanup_expired_registrations',  # 每天凌晨1点执行
         '>> ' + str(LOG_DIR / 'cron.log') + ' 2>&1')
    ]
else:
    CRONJOBS = [
        ('0 1 * * *', 'accounts.tasks.cleanup_expired_registrations', 
         '>> /var/log/apache2/cron.log 2>&1')  # 生产环境日志路径
    ]

# CRONTAB配置
CRONTAB_LOCK_JOBS = True
CRONTAB_COMMAND_PREFIX = 'DJANGO_SETTINGS_MODULE=a4lamerica.settings'