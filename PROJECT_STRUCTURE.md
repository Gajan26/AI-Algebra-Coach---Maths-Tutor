# AI Algebra Coach

The project is organized as a Next.js App Router client and a FastAPI service.

```text
.
├── frontend/
│   ├── app/                 # Next.js routes, KaTeX canvas, and split-screen page
│   ├── components/          # Canvas, camera, and coach-feed components
│   ├── lib/                 # API/WebSocket clients and shared types
│   └── public/              # Static assets
├── backend/
│   ├── main.py              # FastAPI vision endpoint and session WebSocket
│   ├── agents.py            # Assessment, pedagogy, and UI-control flow
│   └── requirements.txt     # Python runtime dependencies
├── schema.sql               # PostgreSQL tables, validation, and indexes
└── AI Algebra Coach.md      # Product and implementation brief
```

## Run locally

1. Create a PostgreSQL database and run `psql "$DATABASE_URL" -f schema.sql`.
2. In `backend`, create a virtual environment and install `pip install -r requirements.txt`; then run `uvicorn main:app --reload --port 8000`.
3. In `frontend`, copy the front-end settings in `.env.example` to `.env.local`, run `npm install`, then `npm run dev`.

The API requires `OPENAI_API_KEY` before it can transcribe homework. The WebSocket coach loop is deterministic for the initial sign-change misconception and can be extended with LangGraph/model assessment later.
