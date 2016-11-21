FROM python:2.7
RUN pip install --upgrade pip
RUN apt-get update
RUN apt-get install -y r-base-core
RUN mkdir -p /app/user
WORKDIR /app/user
ADD requirements.txt /app/user/requirements.txt
ADD requirements-dev.txt /app/user/requirements-dev.txt
RUN mkdir /src
RUN pip install --src /src -r requirements-dev.txt
ADD . /app/user
RUN mkdir -p /app/logs/
RUN pip install django-model-utils==1.3.1
EXPOSE 8000
