# Recipe Sharing App

[![CI](https://github.com/PlamenPlamenovStanchev/recipe-sharing-app/actions/workflows/ci.yml/badge.svg)](https://github.com/PlamenPlamenovStanchev/recipe-sharing-app/actions/workflows/ci.yml)

A full-stack course project for publishing, moderating, and discovering
community recipes. It combines a Flask REST API with a responsive React client,
role-based access control, private image storage, community interactions,
administration tools, API documentation, automated tests, and production
operations workflows.

## Features by role

### Anonymous visitor

- Browse the public catalog of approved recipes.
- View recipe details, ingredients, steps, authors, dates, images, and like
  counts.
- Read non-deleted comments.
- Register and log in.

### USER

- Create recipes as drafts with ordered ingredients and steps.
- Edit, upload images for, submit, or delete owned `DRAFT` and `REJECTED`
  recipes.
- Comment on approved recipes and edit or soft-delete owned comments.
- Like and unlike approved recipes, with one like per user and recipe.
- Create EUR donation attempts for another user's approved recipe.

### MODERATOR

- Access the oldest-first pending recipe queue.
- Review and edit recipes, replace recipe images, approve submissions, or reject
  them with a reason.
- Edit or soft-delete any comment.
- Use the normal authenticated recipe, comment, like, and donation operations.

### ADMIN

- Includes all moderator capabilities.
- List and inspect users.
- Create and update accounts, roles, and active status.
- Deactivate and reactivate accounts without deleting their content.
- Benefits from self-protection and last-active-admin safety rules.

Frontend role checks improve navigation only. The backend remains authoritative
for every permission decision.

## Technology stack

### Backend

- Python 3.13
- Flask and Flask-RESTful
- SQLAlchemy and Flask-SQLAlchemy
- Marshmallow validation and serialization
- PostgreSQL / Neon and Psycopg
- Alembic / Flask-Migrate
- Flask-JWT-Extended
- Argon2 password hashing
- Gunicorn and restricted Flask-CORS production support
- Pytest, factory-boy, and pytest-cov

### Frontend

- React
- Vite
- Tailwind CSS
- React Router
- Oxlint

### External services

- Private AWS S3 recipe image storage with temporary presigned URLs
- AWS SES welcome email delivery after registration
- Provider-neutral donation orchestration
- A configurable Wise provider shell; real Wise HTTP transfers are **not
  implemented**
- Private Cloudflare R2 storage for scheduled production backups

## Architecture

The backend follows a layered Flask-RESTful design:

- **Resources** translate HTTP requests and responses and remain intentionally
  thin.
- **Services** contain business rules, permissions, state transitions, and
  external-service orchestration.
- **Repositories** own database queries and persistence operations.
- **Schemas** validate input and serialize safe API output with Marshmallow.
- **Models** define SQLAlchemy entities, relationships, indexes, constraints,
  and enums.
- **Validators** provide reusable password, username, text, and recipe rules.

The React application separates routing, authentication context, API clients,
pages, layouts, and reusable UI components. Public requests use the public API
client; authenticated requests inherit the centrally managed Bearer token.

## Database overview

The main entities are:

- `User` with role, active status, Argon2 password hash, and authored content.
- `Recipe` with status, author, reviewer, moderation timestamps, rejection
  reason, and an S3 `image_key`.
- Reusable `Ingredient` records joined through ordered `RecipeIngredient`
  records.
- Ordered `RecipeStep` records.
- `Comment` records with an `is_deleted` soft-deletion flag.
- `RecipeLike` with a unique `(user_id, recipe_id)` database constraint.
- `Donation` with exact decimal amount, donor, recipient, status, external
  transfer identifier, and unique idempotency key.

Foreign keys and delete behavior preserve account and donation history while
allowing recipe-owned child rows to follow recipe lifecycle rules.

## Authentication and authorization

Registration validates email, username, names, and a password containing at
least eight characters, uppercase, lowercase, and a digit. Passwords are stored
only as Argon2 hashes.

Login returns a JWT access token. Protected requests use:

```text
Authorization: Bearer <access_token>
```

The JWT subject contains the user ID. Protected endpoints reload the user from
the database, reject inactive accounts, and evaluate the current database role;
they do not trust a stale role claim from the client. Password hashes, secrets,
and provider credentials are never serialized.

## Recipe moderation

```text
DRAFT ──submit──> PENDING ──approve──> APPROVED
                         └──reject───> REJECTED ──edit/resubmit──> PENDING
```

Only approved recipes appear in the public catalog. Owners can view their own
non-public recipes; moderators and administrators can view the moderation
queue. Invalid state transitions return conflicts instead of silently changing
state.

## Images

Recipe images accept JPEG, PNG, and WebP files up to 5 MB. The backend verifies
file signatures, generates safe object keys, and stores only `image_key` in
PostgreSQL—never image bytes or temporary URLs. S3 remains private, while API
responses generate configurable, short-lived presigned GET URLs. Failed uploads
do not update the recipe, and uploaded objects are cleaned up when later
database persistence fails where practical.

## Comments and likes

Comments are available only on approved recipes. Content is trimmed and limited
to 2–1000 characters. Authors can edit or soft-delete their own comments;
moderators and administrators can manage any comment. Deleted comments are
excluded from normal listings.

Approved recipes support public like counts. Authenticated users can like once,
unlike, and receive a conflict for duplicate likes. The database unique
constraint and repository error handling protect against concurrent duplicates.

## Donations and payment status

Authenticated users may donate to another user's approved recipe. Amounts are
accepted as positive decimal strings with at most two decimal places; the
current currency is EUR. Donation records are created with unique idempotency
keys before provider orchestration.

The repository contains a `PaymentProvider` abstraction, a deterministic fake
provider for tests, and a `WisePaymentProvider` shell. The Wise shell makes no
external API calls and raises a not-configured error because verified Wise API
endpoints and transfer behavior have not been implemented. Consequently, this
project must not be presented as processing real Wise payments. Provider
failures are handled safely and persisted donation state is marked failed where
possible.

## Admin user management

The ADMIN API and dashboard support user listing, detail retrieval, account
creation, safe field and role updates, deactivation, and reactivation. Sensitive
fields are excluded from responses. Administrators cannot deactivate or demote
themselves through protected operations, and the service prevents removal of
the last active administrator.

## Local setup

Prerequisites: Python 3.13, Node.js 22, npm, and PostgreSQL. Copy environment
templates locally and replace placeholders; never commit `.env` files.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
flask --app run:app db upgrade -d migrations
flask --app run:app run
```

The API starts at `http://localhost:5000`. The Vite development proxy forwards
`/api` requests to this address.

### Frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Environment variables

The committed examples contain safe placeholders. Production values belong in
the hosting provider's secret store.

Backend runtime variables:

```text
FLASK_ENV
HOST
PORT
SECRET_KEY
JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRES_MINUTES
DATABASE_URL
FRONTEND_ORIGIN
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_S3_BUCKET_NAME
AWS_S3_PRESIGNED_URL_EXPIRATION
AWS_SES_REGION
AWS_SES_SENDER_EMAIL
PAYMENT_PROVIDER
WISE_API_TOKEN
WISE_PROFILE_ID
```

Test and optional development seed variables:

```text
TEST_DATABASE_URL
RUN_DATABASE_TESTS
SEED_ADMIN_EMAIL
SEED_ADMIN_USERNAME
SEED_ADMIN_PASSWORD
SEED_MODERATOR_EMAIL
SEED_MODERATOR_USERNAME
SEED_MODERATOR_PASSWORD
SEED_USER_EMAIL
SEED_USER_USERNAME
SEED_USER_PASSWORD
```

Frontend variables—these are public build-time configuration, never secrets:

```text
VITE_API_BASE_URL
VITE_DEV_API_PROXY_TARGET
```

## Database migrations

Run migration commands from `backend/` with the virtual environment active:

```powershell
flask --app run:app db upgrade -d migrations
flask --app run:app db current -d migrations
flask --app run:app db history -d migrations
```

After an intentional model change, generate and review a new migration:

```powershell
flask --app run:app db migrate -d migrations -m "describe the change"
```

Production releases must run `db upgrade` before starting the new application
version.

## Development seed data

After applying migrations in the development environment:

```powershell
flask --app run:app seed-db
```

The command is idempotent, refuses to run outside development, and creates
representative users and recipes. Override its demonstration credentials with
the `SEED_*` variables when needed.

## Quality checks

### Backend tests and coverage

```powershell
cd backend
pytest
pytest --cov=app --cov-report=term-missing --cov-fail-under=60
```

By default, tests use a disposable isolated SQLite database and mock AWS and
payment integrations. To opt into an explicit isolated PostgreSQL test database,
set `RUN_DATABASE_TESTS` and `TEST_DATABASE_URL`; never reuse `DATABASE_URL`.

### Frontend lint and build

```powershell
cd frontend
npm run lint
npm run build
```

The production frontend output is written to `frontend/dist`.

## API documentation

With the backend running:

- Swagger UI: [http://localhost:5000/docs](http://localhost:5000/docs)
- OpenAPI JSON: [http://localhost:5000/openapi.json](http://localhost:5000/openapi.json)

Swagger's **Authorize** dialog accepts the JWT returned by `/auth/login` and
adds the Bearer prefix automatically.

## Postman

Import both files from [`postman/`](postman):

- `Recipe-Sharing-API.postman_collection.json`
- `Recipe-Sharing-Local.postman_environment.json`

The collection covers all current API operations. Login saves `access_token`;
recipe, comment, and admin-user creation requests save their corresponding ID
variables for subsequent requests. Included account values are demonstration
placeholders, not personal credentials.

## CI/CD and operations

`.github/workflows/ci.yml` runs independent backend and frontend jobs on pushes,
pull requests, and manual dispatch. It executes the backend test suite with a
60% coverage gate, then runs frontend dependency installation, lint, and the
production build. It contains no production database or cloud credentials.

No workflow deploys the application automatically. The project is prepared for
Gunicorn-based Python hosting and a Netlify frontend. See
[DEPLOYMENT.md](DEPLOYMENT.md) for production variables, restricted CORS,
migration and start commands, Netlify SPA routing, and smoke tests.

The independent `.github/workflows/backup.yml` runs daily around 03:00 UTC and
supports manual dispatch. It uses PostgreSQL 18 client binaries explicitly,
backs up the production PostgreSQL database and private S3 recipe images to a
separate private Cloudflare R2 bucket, verifies archives, and retains 7 daily,
5 weekly, and 12 monthly backup sets. Credentials exist only as GitHub Actions
secrets in the `production-backups` environment. Setup, restoration, and
workflow-disable instructions are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Security decisions

- Argon2 password hashing and write-only password input fields.
- Short-lived JWT access tokens with database-backed active-user and role
  checks.
- Backend-enforced ownership, RBAC, and moderation transitions.
- Exact production CORS origin; wildcard production CORS is rejected.
- Private S3 objects and expiring presigned image URLs.
- File signature, type, empty-file, and 5 MB upload validation.
- Decimal donation amounts instead of floating-point money.
- Database constraints for uniqueness and positive amounts.
- Soft-deleted comments and non-destructive account deactivation.
- Non-fatal SES failures after a committed registration.
- No frontend, repository, CI, Postman, or documentation secrets.
- Isolated tests with mocked external services and no production Neon access.
- Private, separate backup storage with least-privilege credentials and
  retention pruning scoped to a dedicated prefix.

## Project structure

```text
recipe-sharing-app/
├── .github/workflows/       # CI and production backup workflows
├── backend/
│   ├── app/
│   │   ├── authorization/   # JWT identity and role helpers
│   │   ├── models/          # SQLAlchemy entities and enums
│   │   ├── repositories/    # Database access
│   │   ├── resources/       # Flask-RESTful HTTP endpoints
│   │   ├── schemas/         # Marshmallow input/output schemas
│   │   ├── services/        # Business and integration logic
│   │   └── validators/      # Reusable validation rules
│   ├── migrations/          # Alembic migration history
│   └── tests/               # Unit, integration, fixtures, and factories
├── frontend/
│   ├── public/              # Netlify SPA redirect
│   └── src/                 # React pages, components, auth, routing, API client
├── postman/                 # Collection and local environment template
├── DEPLOYMENT.md            # Production and backup runbook
└── README.md
```

## Screenshots

Screenshots can be added under `docs/screenshots/` for the final course defense:

- Public recipe catalog and recipe details
- Recipe editor and image upload
- Comments, likes, and donation dialog
- Moderator pending queue
- Admin user management dashboard
- Swagger UI and successful CI run

## Author

**Plamen Plamenov Stanchev**

Recipe Sharing App — full-stack course project.
