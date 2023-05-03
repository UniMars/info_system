pipreqs . --encoding=utf-8 --force
python manage.py makemigrations
python manage.py migrate
net stop celery_worker
net stop celery_beat
net start celery_worker
net start celery_beat
celery -A info_system worker --loglevel=debug --logfile="./logs/celery/worker.log" -P gevent
celery -A info_system beat --loglevel=debug --logfile="./logs/celery/beat.log"