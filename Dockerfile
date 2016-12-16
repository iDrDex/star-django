FROM python:2.7
RUN pip install --upgrade pip
RUN apt-get update
RUN apt-get install -y r-base-core
RUN mkdir -p /app/user
RUN mkdir -p /app/logs/
RUN bash -c "echo 'install.packages(\"meta\",repos=\"http://cran.rstudio.com/\")' | R --no-save"
RUN pip install fabric
WORKDIR /app/user
ADD requirements.txt /app/user/requirements.txt
ADD requirements-dev.txt /app/user/requirements-dev.txt
RUN mkdir /src
RUN pip install --src /src -r requirements-dev.txt
ADD . /app/user
EXPOSE 8000
