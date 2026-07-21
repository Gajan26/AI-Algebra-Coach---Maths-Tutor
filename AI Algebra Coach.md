\# Role & Objective  
You are an expert full-stack engineer and AI architect. Your task is to build a web application called “AI Algebra Coach” scoped specifically for Algebra. The core capability of this app is to let students upload an image of their handwritten algebra homework from their physical notebook or capture it live using their device's built-in camera, and then feed that image into a real-time, multi-agent feedback loop.  
\#\# 1\. Technical Stack & Architecture  
\- Frontend: Next.js (App Router) styled cleanly with Tailwind CSS.  
\- Rich-Text / Math Display: Tiptap with KaTeX rendering plugin.  
\- Backend: FastAPI (Python) handling WebSockets for real-time streaming feedback.  
\- Agent Orchestration: LangGraph or a deterministic state-machine structure.  
\- Vision Handling: OpenAI GPT-4o API  
\#\# 2\. Core Feature Specifications (Scope: Algebra Only)  
\#\#\# Feature 1: Two-Panel Split View UI  
\- Left Panel (The Canvas): Displays a clean, digital version of the student's mathematical steps. It features a "Capture Homework" section with two clear actions: "Upload Image" (file picker) and "Open Camera" (accesses device webcam/mobile camera feed via WebRTC \`getUserMedia\`).  
\- Right Panel (The Socratic Coach): A clean messaging feed that streams responses from the AI Algebra Coach agent.  
\#\#\# Feature 2: Camera Capture & Vision-to-LaTeX Pipeline  
\- When an image is captured or uploaded, the frontend sends the image to a FastAPI endpoint (\`/api/vision/process\`).  
\- The backend passes this image to a vision model with a strict system prompt instructing it to:  
  1\. Transcribe the handwritten algebra into a structured JSON array of mathematical steps formatted in clean LaTeX.  
  2\. Map these steps to lines (e.g., Line 1: \`3x \+ 5 \= 20\`, Line 2: \`3x \= 20 \+ 5\`).  
\- The frontend instantly renders these parsed lines onto the Left Panel Canvas.  
\#\#\# Feature 3: The AI Algebra Coach State-Machine Loop  
\- Once the lines are on the canvas, the system automatically triggers the Multi-Agent Evaluation Loop over WebSocket:  
  \- Agent 1 (Assessment): Evaluates the algebra line-by-line. In the example \`3x \+ 5 \= 20\` \-\> \`3x \= 20 \+ 5\`, it must catch the algebraic misconception (forgetting to invert the sign when moving constants across the equation).  
  \- Agent 2 (Pedagogical Feedback): Enforces a strict constraint, it is forbidden from providing the answer, giving the corrected step, or writing more than 2 lines of math. It must generate a short question (e.g., "Look at Line 2\. When you moved \+5 across the equals sign, what should happen to its sign?").  
  \- Agent 3 (UI Controller): Returns a structured JSON payload over WebSocket indicating which specific text snippet or line on the canvas should be highlighted in yellow/orange.  
\#\# 3\. Database Schema Requirement (PostgreSQL)  
Generate the database schema required to track this interaction, specifically including:  
\- \`users\` (id, role, email)  
\- \`coach\_sessions\` (id, student\_id, algebra\_topic, current\_hint\_level)  
\- \`interaction\_logs\` (id, session\_id, sender, chat\_message, canvas\_state\_snapshot as JSONB)  
\#\# 4\. Your Implementation Steps  
Please generate the complete source code systematically across the following files:  
1\. \`schema.sql\`: Full PostgreSQL setup with constraints and indexes.  
2\. \`main.py\`: FastAPI server handling the \`/api/vision/process\` endpoint and the \`/ws/session/{session\_id}\` WebSocket handler.  
3\. \`agents.py\`: The multi-agent evaluation logic using LangGraph or raw Python system prompt scaffolding.  
4\. \`+page.svelte\` (or \`page.tsx\`): The responsive, split-screen UI implementing WebRTC camera capture, image rendering, and real-time WebSocket messaging.  
Start by generating the technical file structure and the database schema script.  
