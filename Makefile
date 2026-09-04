.PHONY: install migrate run test check collectstatic superuser

install:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver 0.0.0.0:8000

test:
	python manage.py test

check:
	python manage.py check

collectstatic:
	python manage.py collectstatic --noinput

superuser:
	python manage.py createsuperuser
