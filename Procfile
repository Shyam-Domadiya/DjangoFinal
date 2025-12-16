web: gunicorn --chdir demodev --bind 0.0.0.0:$PORT --workers 3 --worker-class sync --timeout 60 --access-logfile - --error-logfile - demodev.wsgi:application
release: python demodev/manage.py migrate
