# AI Algebra Coach

AI Algebra Coach is a web application that transcribes handwritten Algebra work and provides concise, Socratic next-step prompts. It is designed for school and introductory college Algebra, including equations, inequalities, systems, quadratics, factoring, polynomials, functions, exponents, logarithms, and rational expressions.

## What it does

- Upload a JPEG, PNG, or WebP image of handwritten Algebra work.
- Transcribe the work into numbered LaTeX steps using Claude's vision capabilities.
- Show the original transcribed work on a math canvas with KaTeX rendering.
- Stream targeted Socratic coach feedback through a WebSocket in real-time.
- Accept a student's explanation or next step as private coaching context.

## Architecture

```
Browser (Next.js)
  ├─ POST image → FastAPI /api/vision/process → Claude 3.5 Sonnet vision
  └─ WebSocket → FastAPI /ws/session/{id} → Socratic coach loop

Anthropic API (Claude 3.5 Sonnet)
  ├─ Vision: Image transcription to LaTeX
  └─ Text: Socratic coaching feedback
```

**Stack:**
- **Frontend:** Next.js 15 with Tailwind CSS, KaTeX math rendering, camera capture, WebSocket support
- **Backend:** FastAPI with async WebSocket support, Claude API integration
- **LLM:** Claude 3.5 Sonnet (vision + text generation)
- **Deployment:** Containerized (Docker), ready for cloud platforms

## Local Development

### Requirements
- Python 3.10+
- Node.js 20+
- Anthropic API account with available credits (get one at https://console.anthropic.com)

### Setup

**1. Clone and install backend dependencies:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure backend environment:**

Copy `backend/.env.example` to `backend/.env` and add your Anthropic API key:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials:
# ANTHROPIC_API_KEY=sk-ant-...
```

**3. Start the backend:**

```bash
uvicorn main:app --reload --port 8000
```

**4. In a new terminal, install and start frontend:**

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

**5. Open http://localhost:3000 in your browser**

## Costs & Usage

**Claude API Pricing (as of 2024):**
- Vision analysis: ~$0.003 per image (varies by size)
- Text generation: ~$0.003 per 1000 tokens

**Typical interaction cost:** $0.05–$0.15 per student homework submission (1 image + 2–3 coaching exchanges)

**Monitor spending:**
1. Set up billing alerts in [Anthropic Console](https://console.anthropic.com/account/billing/overview)
2. Check usage at https://console.anthropic.com/account/usage
3. Use separate API keys for development vs. production

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment guides including:
- Docker containerization
- Vercel (frontend) + Railway/Render (backend)
- AWS ECS/Lambda deployment
- Environment setup
- Database migrations
- Monitoring & logging
- Security best practices

## Project Structure

```
AI Algebra Coach/
├── backend/
│   ├── main.py                 # FastAPI server & vision endpoint
│   ├── agents.py               # Socratic coaching logic
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment template
│   ├── Dockerfile              # Backend container
│   └── schema.sql              # Database schema (optional)
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Main UI (two-panel split view)
│   │   └── layout.tsx          # App layout & metadata
│   ├── package.json            # Node dependencies
│   ├── .env.example            # Environment template
│   ├── tailwind.config.ts      # Tailwind configuration
│   ├── tsconfig.json           # TypeScript config
│   ├── Dockerfile              # Frontend container
│   └── next.config.ts          # Next.js config
├── docker-compose.yml          # Local dev stack
├── DEPLOYMENT.md               # Deployment guide
└── README.md                   # This file
```

## Key Security Notes

⚠️ **Before production deployment:**

1. **Keep your API key secure:**
   - Store `ANTHROPIC_API_KEY` in `backend/.env` only (git-ignored)
   - Use separate keys for dev/prod environments
   - Never commit `.env` files or paste keys in issues/chat

2. **Set up rate limiting** on FastAPI endpoints to prevent abuse:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

3. **Add authentication** before public deployment:
   - Implement user authentication (OAuth, session cookies, etc.)
   - Track usage per user
   - Prevent anonymous abuse

4. **Monitor spending:**
   - Set up billing alerts in Anthropic console
   - Log API usage in your application
   - Consider rate limits per user

5. **CORS configuration:**
   - Update `CORS_ORIGINS` in `.env` to your actual domain
   - In production: set to specific domain only, never `*`

## Environment Variables

### Backend (`backend/.env`)

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...           # Get from https://console.anthropic.com

# Configuration
CORS_ORIGINS=http://localhost:3000     # Comma-separated allowed origins
VISION_MODEL=claude-3-5-sonnet-20241022
COACH_MODEL=claude-3-5-sonnet-20241022
ENVIRONMENT=development                 # Set to 'production' in prod
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

**"ANTHROPIC_API_KEY is not configured"**
- Create `backend/.env` with your API key
- Restart the backend server

**Image processing fails**
- Check API key has billing enabled at https://console.anthropic.com
- Verify image is valid (JPEG, PNG, or WebP)
- Check Claude API status at https://status.anthropic.com

**WebSocket connection errors**
- Verify `CORS_ORIGINS` includes your frontend URL
- For production, use `wss://` (WebSocket Secure)

**Slow responses**
- Claude API can take 5–10 seconds for image analysis
- Add loading indicators in the UI
- Consider caching for identical images

## Development

### Running tests (if added)
```bash
cd backend
pytest
```

### Building for production
```bash
# Frontend
cd frontend
npm run build

# Backend
# Docker build handles dependencies (see Dockerfile)
```

## License

[Add your license here]

## Support

For issues or questions:
- Check the [Anthropic API docs](https://docs.anthropic.com)
- Review DEPLOYMENT.md for hosting guides
- File an issue in this repository

---

**Built with Claude 3.5 Sonnet** · Powered by Anthropic
