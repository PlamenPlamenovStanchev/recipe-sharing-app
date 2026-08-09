# Recipe Sharing App

A full-stack application for sharing, discovering, and managing recipes.

## Planned technologies

- Backend: Python, Flask, Flask-RESTful, SQLAlchemy, PostgreSQL, Alembic/Flask-Migrate, and Marshmallow
- Frontend: React and Tailwind CSS

## Local setup

Create and activate the backend virtual environment, then install dependencies:

```powershell
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt -r backend\requirements-dev.txt
```

Copy `backend/.env.example` to `backend/.env` and set distinct PostgreSQL
databases for `DATABASE_URL` and `TEST_DATABASE_URL`.

## Database migrations

Run these commands from `backend/` after activating the virtual environment:

```powershell
flask --app run:app db init -d migrations
flask --app run:app db migrate -d migrations -m "describe schema change"
flask --app run:app db upgrade -d migrations
flask --app run:app db current -d migrations
flask --app run:app db history -d migrations
```

For development-only seed data, after applying migrations:

```powershell
flask --app run:app seed-db
```

## Tests and coverage

Run model tests from `backend/`:

```powershell
$env:RUN_DATABASE_TESTS = "1"
pytest
pytest --cov=app --cov-report=term-missing
pytest --cov=app --cov-report=html
```

The HTML coverage report is written to `backend/htmlcov/index.html`.

## Postman collection

Import both files from the [`postman`](postman) directory into Postman:

- `Recipe-Sharing-API.postman_collection.json`
- `Recipe-Sharing-Local.postman_environment.json`

Select the **Recipe Sharing - Local** environment and start the backend at
`http://localhost:5000`. Run **Authentication / Register** once if the demo
account does not exist, then run **Authentication / Login**. A successful login
automatically saves `access_token`, and **Recipes / Create Recipe** saves the
created `recipe_id`. Comment and admin-user creation requests similarly save
`comment_id` and `user_id`.

For moderator or administrator requests, log in with an appropriate locally
created account and replace the environment token by running **Login** with
that account's demonstration credentials. Select an image file manually in the
multipart request before running **Images / Upload Recipe Image**. Donation
requests must target another user's approved recipe. The included passwords and
email addresses are demonstration placeholders only; do not store real secrets
in the collection or environment export.
