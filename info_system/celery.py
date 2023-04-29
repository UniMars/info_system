from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery
from django.conf import settings

# 设置 Django 的 settings.py 作为 Celery 的默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'info_system.settings')

# 创建一个 Celery 实例
app = Celery('info_system')

# 使用 Django 的设置模块配置 Celery
app.config_from_object('django.conf:settings')

# 让 Celery 自动发现你的任务模块
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'test_task': {
        'task': 'datas.tasks.test_celery_task',
        'schedule': timedelta(seconds=3),
        'args': (),
    },
}
