echo 安装虚拟环境
virtualenv .venv
.venv/Scripts/activate
pip install -r requirements.txt

echo 生成依赖
pipreqs . --encoding=utf-8 --force

echo model更新
python manage.py makemigrations
python manage.py migrate

echo 运行环境重启
httpd -k restart
net stop celery_worker
net stop celery_beat
net start celery_worker
net start celery_beat

echo celery启动
celery -A info_system worker -E --loglevel=debug  --logfile="./logs/celery/worker.log" -P gevent
celery -A info_system beat --loglevel=debug --logfile="./logs/celery/beat.log"
celery -A info_system flower
