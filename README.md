# Teacher Budget Buddy Premium (Telegram Mini App + FastAPI)

Premium-style Telegram Mini App for tracking income/expenses with categories + analytics.

- Frontend: React + Vite + TypeScript + Tailwind + Framer Motion + React Query
- Backend: FastAPI + SQLModel (SQLite) + Telegram WebApp `initData` verification

## Quick start (local)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Put your BotFather token into TELEGRAM_BOT_TOKEN

uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd web
npm install
cp .env.example .env
npm run dev
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000

## How auth works
Frontend sends Telegram `initData` in header `X-TG-Init-Data`.
Backend verifies signature using your bot token.
