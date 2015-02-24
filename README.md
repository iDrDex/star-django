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
    pip install -r requirements.txt
    ```

3. Update settings:

    All settings that should vary by deployment go to `.env` file, so:

    ```bash
    cp .env.example .env
    <edit> .env
    ```

    Adjust settings in `.env` file, you will probably need to only set `DATABASE_URL`
    and `LEGACY_DATABASE_URL` for your working copy.
    `LEGACY_DATABASE_URL` should refer to wep2py application database or it's copy.

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
