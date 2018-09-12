# STAR

*The Search Tag & Analyze Resource* for collaborative annotation and interpretation of disease from open digital samples from [GEO][].


## Installing from source

1. Create an Ubuntu 16.04 instance.

2. Configure ssh connection by adding something like this to `~/.ssh/config`:

    ```ini
    Host stargeo
      HostName 123.45.67.89
      User ubuntu
      IdentityFile /path/to/stargeo.pem
      IdentitiesOnly yes
    ```

3. Clone code locally:

    ```bash
    git clone git@github.com:idrdex/star-django.git stargeo
    cd stargeo
    ```

    Switch to branch:

    ```bash
    git checkout limited
    ```

4. Install deployment dependencies (unless you've already installed dev ones):

    We will use [virtualenv][] and [virtualenvwrapper][] to create isolated python environment,
    so start with:

    ```bash
    sudo pip install virtualenv virtualenvwrapper
    ```

    When create a virtualenv for our project and install dependencies:

    ```
    mkvirtualenv star
    pip install -r requirements-deploy.txt
    ```

5. Install and configure:

    ```bash
    fab install
    fab config  # Fill in all the keys here
    fab restart
    ```

    Config command will open `~/app/.env` remote file in vim,
    alternatively you can ssh into instance and edit it directly.
    You will need to specify `BIOPORTAL_API_KEY` ([get here][bioportal-key]), `FROM_EMAIL` and `ADMIN`.

6. Create a superuser for yourself (need one to log into admin):

    ```bash
    fab manage:createsuperuser
    ```


## Making a working copy

Here are steps to make local deployment of this app in order to tinker it.

1. Get sources:

    ```bash
    git clone git@github.com:idrdex/star-django.git
    cd star-django
    ```

2. Install development dependencies (like above, different file):

    ```
    pip install -r requirements-dev.txt
    ```

3. Update settings:

    All settings that should vary by deployment go to `.env` file, so:

    ```bash
    cp .env.example .env
    <edit> .env
    ```

    Adjust settings in `.env` file, you will probably need to only set `DATABASE_URL`
    for your working copy.


4. Create or migrate database tables:

    ```bash
    ./manage.py migrate
    ./manage.py createsuperuser
    ```


5. Run it and have fun:

    ```bash
    ./manage.py runserver 5000
    ```

    Go to `http://localhost:5000/` to see the app
    or to `http://localhost:5000/admin/` to see admin panel.

    To debug background tasks you'll need to start celery:

    ```bash
    honcho start celery
    ```

    NOTE: it doesn't autorestart, you'll need to do that manually.

    To run both development web-server and celery in single terminal and autorestart both do:

    ```bash
    # .. install node.js and npm somehow
    npm install -g nodemon

    nodemon -x 'honcho start' -e py
    ```

[geo]: http://www.ncbi.nlm.nih.gov/geo/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.org/en/latest/
[bioportal-key]: https://bioportal.bioontology.org/help#Getting_an_API_key


## Deploying

1. Configure ssh connection (see in install).

2. Install deployment dependencies (see in install).

2. Run locally to deploy latest commit:

    ```bash
    fab deploy
    ```
