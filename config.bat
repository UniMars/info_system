pipreqs . --encoding=utf-8 --force
python manage.py makemigrations
python manage.py migrate

celery -A info_system worker --loglevel=debug --logfile="./logs/celery/worker.log" -P gevent
celery -A info_system beat --loglevel=debug --logfile="./logs/celery/beat.log"