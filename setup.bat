python -m pip install -r requirements.txt
echo yes| python manage.py collectstatic
python manage.py runserver