# Dev Notes

## Local DB

We are running the local DB from a docker container.

Start postgres container:

```
docker-compose up -d db
```

Stop the database:

```bash
docker-compose stop db
```

Remove the database container (data persists):

```bash
docker-compose rm -f db
```

## Create Virtual Environment

This is the process for creating a virtual environment. It includes command to freeze dependencies.

1. Create and activate virtual environment:

    ```bash
    python -m venv venv

    # Windows:
    venv\Scripts\activate
    # Unix/MacOS:
    source venv/bin/activate
    ```

2. Install Requirements

    - Option 1: Install from base requirements, re-loading the dependencies:
        1. Install base requirements:

            ```bash
            pip install -r requirements-base.txt
            ```

        2. Save full production dependencies with all sub-dependencies:

            ```bash
            pip freeze > requirements-full.txt
            ```

    - Option 2: Install complete requirements with existing dependencies

        ```bash
        pip install -r requirements-full.txt
        ```


## Start Server

### Development

Run the debugger, using the run profile.

### Production

(See the procedure. Note some things will be different from dev.)

## Deploy Project

(See the notes on multiserver for now)

## Migrations

NOTE: There was some special code added to env.py to prevent alembic from trying to delete postgis tables. Alembic autogen will not ignore
tables not in the project "metadata". I think this means if I delete a table, alembic autogen migrations will not delete it.

In any case, I should check the migration every time I create one.

1. Activate VENV

2. Set flask app variable (shown here for development)

    ```
    $env:FLASK_APP="app:create_app('development')"
    ```

3. FIRST TIME FOR PROJECT ON MACHINE ONLY!!!

    (SEE NOTE ABOVE ABOUT SPECIAL CODE NEEDED IN ENV.PY)

    Initial setup

    ```
    flask db init
    ```

4. Create the migration

    ```
    flask db migrate -m "some name for the migration"
    ```

5. REVIEW THE MIGRATION! MAKE SURE IT IS WHAT WE EXPECT!

6. Apply the migration

    ```
    flask db upgrade
    ```