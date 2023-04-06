pip list --format=freeze > requirements.txt
python manage.py makemigrations
python manage.py migrate