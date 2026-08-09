# Production deployment

This guide prepares the application for deployment without tying it to a
specific Python hosting provider. Never commit real credentials or copy a
production database URL into test configuration.

## Backend

The backend requires Python 3.13, PostgreSQL, and the variables listed in
`backend/.env.example`. From the repository root, install dependencies with:

```sh
cd backend
python -m pip install -r requirements.txt
```

Set `FLASK_ENV=production`. The production configuration requires
`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, and `FRONTEND_ORIGIN` before the
application can start. `DATABASE_URL` accepts a normal Neon PostgreSQL URL; the
application converts `postgresql://` URLs to the Psycopg SQLAlchemy driver.
Keep `sslmode=require` in a hosted Neon connection string.

Apply all database migrations as a release/pre-start operation:

```sh
flask --app run:app db upgrade -d migrations
```

Start the API from `backend/` with Gunicorn:

```sh
gunicorn --bind "0.0.0.0:${PORT:-8000}" --workers 2 --threads 4 --timeout 120 run:app
```

The development entry point also honors `HOST` and `PORT`, but Flask's built-in
server must not be used as the production server.

## Backend environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `FLASK_ENV=production` | Yes | Selects strict production configuration. |
| `PORT` | Host-dependent | Port exposed by the hosting platform. |
| `DATABASE_URL` | Yes | Neon/PostgreSQL connection string. |
| `SECRET_KEY` | Yes | Strong Flask application secret. |
| `JWT_SECRET_KEY` | Yes | Separate strong JWT signing key. |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | No | Access-token lifetime; defaults to 60. |
| `FRONTEND_ORIGIN` | Yes | Exact frontend origin allowed by CORS. |
| `AWS_ACCESS_KEY_ID` | For images/email | AWS credential identifier. |
| `AWS_SECRET_ACCESS_KEY` | For images/email | AWS credential secret. |
| `AWS_REGION` | For images | S3 region. |
| `AWS_S3_BUCKET_NAME` | For images | Private S3 bucket. |
| `AWS_S3_PRESIGNED_URL_EXPIRATION` | No | Private image URL lifetime; defaults to 3600 seconds. |
| `AWS_SES_REGION` | For email | SES region. |
| `AWS_SES_SENDER_EMAIL` | For email | Verified SES sender. |
| `PAYMENT_PROVIDER` | Yes | Provider selection; currently `wise`. |
| `WISE_API_TOKEN` | Pending | Reserved for the unfinished real Wise integration. |
| `WISE_PROFILE_ID` | Pending | Reserved for the unfinished real Wise integration. |

S3 buckets must remain private. AWS credentials, payment credentials, Flask
secrets, and database URLs belong only in the backend host's secret store.

## CORS

Set `FRONTEND_ORIGIN` to the deployed frontend origin, with no path or trailing
slash, for example:

```text
FRONTEND_ORIGIN=https://example.netlify.app
```

Production startup rejects a missing origin and rejects `*`. If the Netlify
site receives a custom domain later, update this value and restart the backend.

## Frontend on Netlify

Create a Netlify site from the repository with these settings:

```text
Base directory: frontend
Build command: npm run build
Publish directory: frontend/dist (or dist when relative to the base directory)
```

Set the following public build variable in Netlify:

```text
VITE_API_BASE_URL=https://your-backend.example.com
```

Only variables prefixed with `VITE_` are exposed to browser code. Never create
frontend variables containing database, JWT, AWS, SES, or Wise secrets. The
`frontend/public/_redirects` file is copied into `dist` and routes all unknown
paths to `index.html`, allowing React Router pages to survive direct visits and
refreshes.

## Production smoke tests

After migrations and both deployments are complete, verify:

1. `GET https://your-backend.example.com/health` returns HTTP 200.
2. `/docs` loads and `/openapi.json` returns the API specification.
3. A request from the configured frontend origin receives the matching
   `Access-Control-Allow-Origin`; an unrelated origin does not.
4. The frontend loads, and refreshing `/recipes`, `/login`, `/moderator`, and
   `/admin` returns the SPA instead of a hosting 404.
5. Registration and login work, and protected requests send a Bearer JWT.
6. Database migrations are current and recipe creation persists to PostgreSQL.
7. Image upload returns a private presigned S3 URL without making the bucket
   public.
8. Registration remains successful if SES is temporarily unavailable.
9. Donation behavior is treated as provider-abstraction mode until the real
   Wise integration is completed and separately verified.

## Scheduled production backups

The independent `.github/workflows/backup.yml` workflow runs every day at
approximately 03:00 UTC and can also be started manually with
`workflow_dispatch`. It creates a compressed PostgreSQL custom-format dump,
verifies the dump with `pg_restore`, downloads and compresses the production
recipe image bucket, creates SHA-256 checksums, and uploads the results to a
separate private Cloudflare R2 bucket.

Backups are stored below `recipe-sharing-production/` with the following
retention policy:

- the newest 7 daily backups;
- the newest 5 Sunday weekly backups;
- the newest 12 first-of-month backups.

Configure a GitHub environment named `production-backups` and add these as
GitHub Actions secrets, either on that environment or at repository level:

| Secret | Purpose |
| --- | --- |
| `PRODUCTION_DATABASE_URL` | Production PostgreSQL/Neon URL used only by `pg_dump`. |
| `PRODUCTION_AWS_ACCESS_KEY_ID` | Read access to the production recipe image bucket. |
| `PRODUCTION_AWS_SECRET_ACCESS_KEY` | Secret for the production S3 reader. |
| `PRODUCTION_AWS_REGION` | Region containing the recipe image bucket. |
| `PRODUCTION_S3_RECIPE_BUCKET` | Production recipe image bucket name. |
| `CLOUDFLARE_R2_ACCOUNT_ID` | Account owning the private R2 backup bucket. |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` | R2 API token access key with backup-bucket access. |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | R2 API token secret. |
| `CLOUDFLARE_R2_BACKUP_BUCKET` | Separate private bucket receiving backups. |

Use least-privilege credentials: the production AWS identity needs read/list
access to recipe images, while the R2 identity needs list/read/write/delete only
inside the private backup bucket. The backup bucket must not be public and must
not be the live recipe image bucket. Never use `TEST_DATABASE_URL` or test
bucket credentials in this production workflow.

Test restoration periodically in an isolated database and private temporary
bucket. Download a selected dated prefix, verify it with `sha256sum -c
SHA256SUMS`, restore the database dump with `pg_restore`, and extract the image
archive before copying objects to an isolated recovery bucket.

After the course or project ends, open the repository's **Actions** page,
select **Production backups**, choose the workflow menu, and click **Disable
workflow**. This disables both scheduled and manual runs without deleting
existing R2 backups. Confirm the workflow shows as disabled, then separately
apply the desired final retention or deletion policy to the private R2 bucket.
