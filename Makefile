mig:
	python manage.py makemigrations
	python manage.py migrate


fix:
	python manage.py loaddata categories products districts regions


admin:
	python manage.py createsuperuser