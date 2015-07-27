#!/bin/bash

source /home/ubuntu/venv/bin/activate

# NOTE: this won't stop subprocesses
# exec honcho run celery -A stargeo worker -l info --no-color

exec env $(cat .env | grep -v ^#) celery -A stargeo worker -l info --no-color
