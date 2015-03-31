# STAR

*The Search Tag & Analyze Resource* for collaborative annotation and interpretation of disease from open digital samples from [GEO][].


## Making a working copy

Here are steps to make local deployment of this app in order to tinker it.

1. Get sources:

    ```bash
    git clone git@github.com:idrdex/star-django.git
    cd star-django
    ```

2. Install dependencies:

    We will use [virtualenv][] and [virtualenvwrapper][] to create isolated python environment,
    so start with:

    ```bash
    sudo pip install virtualenv virtualenvwrapper
    ```

    When create a virtualenv for our project and install dependencies:

    ```
    mkvirtualenv star
    pip install -r requirements-dev.txt
    ```

3. Update settings:

    All settings that should vary by deployment go to `.env` file, so:

    ```bash
    cp .env.example .env
    <edit> .env
    ```

    Adjust settings in `.env` file, you will probably need to only set `DATABASE_URL`
    and `LEGACY_DATABASE_URL` for your working copy.

    `LEGACY_DATABASE_URL` should refer to wep2py application database or its copy.
    `DATABASE_URL` should refer to new database, create it.


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


[geo]: http://www.ncbi.nlm.nih.gov/geo/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.org/en/latest/


## Deploying

1. Configure ssh connection by adding something like this to `~/.ssh/config`:

    ```ini
    Host stargeo
    HostName ec2-52-11-148-105.us-west-2.compute.amazonaws.com
    User ubuntu
    IdentityFile /path/to/stargeo.pem
    IdentitiesOnly yes
    ```

2. Ssh to server and create a deployment key:

    ```bash
    # On server
    ls ~/.ssh
    cat ~/.ssh/id_rsa.pub
    ```

    Copy a public key from `id_rsa.pub` to Github repository -> Settings -> Deploy keys.

    If you don't have a key on server then generate it with `ssh-keygen`.

3. Run locally:

    ```bash
    # to deploy latest commited
    fab deploy

    # to deploy whatever you have locally (not recommended)
    fab dirty_deploy
    ```
