# LabApp PWA Migration
 
 # Labsense

AI-powered analysis of laboratory reports (PDF)

Upload your lab report → get structured markers → clinical interpretation → lifestyle insights
Production-oriented scaffold around the existing Telegram bot parser and interpreter.

## Structure

- `frontend/`: Next.js App Router PWA shell with Tailwind and shadcn/ui config.
- `backend/`: existing Python code plus `app/` FastAPI wrapper that imports the current parser/interpreter modules.
- `api/`: explicit API contract for frontend-backend integration.

## Backend entrypoint

```bash
cd /opt/labapp/backend
uvicorn app.main:app --reload
```

## Frontend entrypoint

```bash
cd /opt/labapp/frontend
npm install
npm run dev
```

## Current scope

- Keeps `backend/parser/` and `backend/interpreter/` intact.
- Adds upload, parse, interpret, auth, and payment-link routes.
- Uses temporary files for parsing and deletes them automatically.
- Stores scaffold analysis records locally for MVP history simulation.
