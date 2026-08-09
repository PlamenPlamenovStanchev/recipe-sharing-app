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
