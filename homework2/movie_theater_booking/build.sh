#!/usr/bin/env bash
# Render build command: install, collect static files, set up the database.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_movies
