echo 生成依赖
pipreqs . --encoding=utf-8 --force

echo model更新
python manage.py makemigrations
python manage.py migrate

echo celery启动
celery -A info_system worker -E --loglevel=debug  --logfile="./logs/celery/worker.log" -P gevent
celery -A info_system beat --loglevel=debug --logfile="./logs/celery/beat.log"
celery -A info_system flower
