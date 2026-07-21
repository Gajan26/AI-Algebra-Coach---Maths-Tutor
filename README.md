# AI Algebra Coach

AI Algebra Coach is a local web application that transcribes handwritten Algebra work and provides concise, Socratic next-step prompts. It is designed for school and introductory college Algebra, including equations, inequalities, systems, quadratics, factoring, polynomials, functions, exponents, logarithms, and rational expressions.

## What it does

- Upload a JPEG, PNG, or WebP image of handwritten Algebra work.
- Transcribe the work into numbered LaTeX steps with OpenAI vision.
- Show the original transcribed work on a math canvas.
- Stream targeted coach feedback through a WebSocket.
- Accept a student's explanation or next step and retain it as private coaching context without automatically adding that entry to the visible canvas.

## Architecture

```text
Next.js browser UI
  ├─ POST image → FastAPI /api/vision/process → OpenAI GPT-4o vision
  └─ WebSocket → FastAPI /ws/session/{id} → Socratic coach loop

PostgreSQL schema: schema.sql
```

- `frontend/` — Next.js 15, Tailwind configuration, KaTeX math rendering, camera capture, and WebSocket UI.
- `backend/` — FastAPI vision endpoint, WebSocket handler, and coach orchestration.
- `schema.sql` — PostgreSQL users, coaching sessions, and interaction logs.

## Run locally

Requirements: Python 3.10+, Node.js 20+, and an OpenAI API project with billing enabled.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (this file is ignored by Git):

```env
OPENAI_API_KEY=your_project_secret_key
CORS_ORIGINS=http://localhost:3000
```

Start the API:

```bash
uvicorn main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\n' > .env.local
npm run dev
```

Open http://localhost:3000.

## Key security

- Use a project secret key, never a Codex or workspace admin key.
- Keep `OPENAI_API_KEY` in `backend/.env` only. Never use a `NEXT_PUBLIC_` key name.
- `backend/.env` is excluded by `.gitignore`; do not commit it or paste a key into issues, chat, or screenshots.
- Use a separate project/key for development and production, set spend alerts, and rotate a key if it is exposed.
- Before public deployment, add user authentication, rate limiting, and server-side logging controls to the FastAPI endpoints.

## Codex and GPT-5.6

This project was built and iterated in collaboration with **OpenAI Codex**, using **GPT-5.6** as the coding assistant. Codex was used to scaffold the Next.js/FastAPI structure, create the SQL schema, implement the camera/upload and WebSocket flows, refine the Socratic coaching behaviour, and run local syntax and production-build checks.

GPT-5.6 was used in the development workflow; it is not the runtime tutoring model. The application currently uses `gpt-4o` for image transcription and model-backed coaching, configured through `VISION_MODEL` and `COACH_MODEL` if you need to override the defaults.

## Current scope

The database schema is included, but persistence and authentication are not yet wired into the FastAPI routes. The app is suitable for local development; add authentication, durable session storage, rate limits, and a production secret manager before deploying it for students.
