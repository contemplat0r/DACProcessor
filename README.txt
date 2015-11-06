
Celery commandline:

$ celery -A dac.dacbrowser.controllers.celery worker --loglevel=info --beat


To have launchd start rabbitmq at login:
    mkdir -p ~/Library/LaunchAgents
    ln -sfv /usr/local/opt/rabbitmq/*.plist ~/Library/LaunchAgents
Then to load rabbitmq now:
    launchctl load ~/Library/LaunchAgents/homebrew.mxcl.rabbitmq.plist
Or, if you don't want/need launchctl, you can just run:
    rabbitmq-server


Create (and initially fill by apple devices/provisional profiles) database before start application:

$ pythom manage.py create_database

Application start:

$ python manage.py runserver
