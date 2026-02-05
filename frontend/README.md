# Reddit Trace Frontend

Stack: Vite + React + TypeScript + Ant Design.

## Development

1) Start the backend (FastAPI)

```powershell
cd backend
uvicorn app.main:app --reload
```

Backend docs: `http://localhost:8000/docs`

2) Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### API Proxy

Dev server proxies ` /api → http://localhost:8000 ` via `frontend/vite.config.ts`.

If your backend runs on a different host/port, edit that proxy.

