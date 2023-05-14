echo 运行环境重启
httpd -k restart
net stop celery_worker
net stop celery_beat
net start celery_worker
net start celery_beat