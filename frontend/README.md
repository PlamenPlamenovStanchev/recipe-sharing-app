# Recipe Sharing frontend

React foundation built with Vite, Tailwind CSS, and React Router.

## Local development

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` in `.env` to the Flask API origin. The default example
uses `http://localhost:5000`.

## Checks

```powershell
npm run lint
npm run build
```
