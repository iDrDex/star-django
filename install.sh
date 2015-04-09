#!/bin/bash

sudo apt-get install -y nginx uwsgi-emperor redis-server rabbitmq-server supervisor

sudo cp stuff/celery.conf /etc/supervisor/conf.d/
sudo supervisorctl reload
