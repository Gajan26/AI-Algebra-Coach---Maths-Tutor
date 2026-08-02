"""FastAPI API for handwritten-algebra transcription and coaching sessions."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from agents import MathStep, generate_coach_reply, run_coach_loop

# Load only the local backend secret file. It is intentionally git-ignored.
load_dotenv(Path(__file__).with_name(".env"), override=True)

# Validate required environment variables
if not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. "
        "Create a backend/.env file with your Anthropic API key. "
        "See backend/.env.example for the required variables."
    )

app = FastAPI(title="AI Algebra Coach API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

VISION_PROMPT = """You transcribe handwritten Algebra homework. Return only JSON in this exact shape:
{"steps": [{"line": 1, "latex": "3x + 5 = 20"}]}
Preserve the student's work exactly; do not solve, correct, explain, or infer missing steps.
Use clean LaTeX for each algebraic expression."""


class VisionResult(BaseModel):
    steps: list[MathStep] = Field(default_factory=list)


class SessionMessage(BaseModel):
    type: str
    steps: list[MathStep] = Field(default_factory=list)
    message: str = Field(default="", max_length=1_000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=20)


def transcribe_image(image: bytes, mime_type: str) -> VisionResult:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured.")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    encoded = base64.b64encode(image).decode("ascii")
    response = client.messages.create(
        model=os.getenv("VISION_MODEL", "claude-3-5-sonnet-20241022"),
        max_tokens=1024,
        system=VISION_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe these handwritten algebra steps."},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": encoded,
                        },
                    },
                ],
            },
        ],
    )
    content = response.content[0].text if response.content else None
    if not content:
        raise HTTPException(status_code=502, detail="Vision model returned no transcription.")
    try:
        return VisionResult.model_validate_json(content)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="Vision model returned invalid structured data.") from exc


@app.post("/api/vision/process", response_model=VisionResult)
async def process_vision(image: UploadFile = File(...)) -> VisionResult:
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
    payload = await image.read()
    if not payload or len(payload) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be between 1 byte and 10 MB.")
    return transcribe_image(payload, image.content_type)


@app.websocket("/ws/session/{session_id}")
async def session_socket(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = SessionMessage.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValidationError):
                await websocket.send_json({"type": "error", "payload": {"message": "Invalid session message."}})
                continue
            if message.type != "evaluate":
                if message.type == "student_response" and message.message.strip():
                    await websocket.send_json(generate_coach_reply(message.steps, message.message.strip(), message.history).model_dump())
                    continue
                await websocket.send_json({"type": "error", "payload": {"message": "Unsupported or empty session message."}})
                continue
            for event in run_coach_loop(message.steps):
                if event.type != "coach_message":
                    await websocket.send_json(event.model_dump())
            await websocket.send_json(generate_coach_reply(message.steps).model_dump())
    except WebSocketDisconnect:
        return
