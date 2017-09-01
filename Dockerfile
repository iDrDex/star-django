FROM python:2.7-slim
# Install R and its meta package
RUN apt-get update && apt-get install -y --no-install-recommends \
     r-base-core r-base-dev \
     libpq-dev \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*
RUN bash -c "echo 'install.packages(\"meta\",repos=\"http://cran.rstudio.com/\")' | R --no-save"
# Install Python deps
RUN mkdir -p /app/user /app/logs
WORKDIR /app/user
RUN pip install --upgrade pip
RUN pip install fabric
ADD requirements.txt /app/user/requirements.txt
ADD requirements-dev.txt /app/user/requirements-dev.txt
RUN pip install --src /src -r requirements-dev.txt
# Add code
ADD . /app/user
EXPOSE 8000
