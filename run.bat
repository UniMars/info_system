.\.venv\Scripts\activate
python -m pip install -r requirements.txt
echo yes| python manage.py collectstatic
python manage.py runserver 8002