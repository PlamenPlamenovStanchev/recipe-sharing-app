# Recipe Sharing frontend

React foundation built with Vite, Tailwind CSS, and React Router.

## Local development

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The default `.env` routes `/api` through Vite's local proxy to
`http://localhost:5000`, avoiding browser CORS issues during development. Set
`VITE_API_BASE_URL` to a deployed API origin when that origin allows the
frontend's browser requests.

## Checks

```powershell
npm run lint
npm run build
```
