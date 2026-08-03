"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

type Step = { line: number; latex: string; hiddenOnCanvas?: boolean };
type FeedMessage = { sender: "student" | "coach" | "system"; text: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SESSION_ID = "00000000-0000-0000-0000-000000000001";

export default function Home() {
  const [steps, setSteps] = useState<Step[]>([]);
  const [feed, setFeed] = useState<FeedMessage[]>([{ sender: "system", text: "Upload or capture a page of algebra to begin." }]);
  const [highlightLine, setHighlightLine] = useState<number | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => () => stopCamera(), []);

  function connectSocket() {
    if (socketRef.current?.readyState === WebSocket.OPEN) return socketRef.current;
    const ws = new WebSocket(`${API_URL.replace(/^http/, "ws")}/ws/session/${SESSION_ID}`);
    ws.onmessage = ({ data }) => {
      const event = JSON.parse(data) as { type: string; payload: Record<string, unknown> };
      if (event.type === "coach_message") {
        setFeed((items) => [...items, { sender: "coach", text: String(event.payload.message) }]);
      }
      if (event.type === "highlight") setHighlightLine(Number(event.payload.line));
      if (event.type === "error") setFeed((items) => [...items, { sender: "system", text: String(event.payload.message) }]);
    };
    ws.onclose = (event) => {
      if (event.code === 1013) {
        setFeed((items) => [...items, { sender: "system", text: "Too many connections — please wait a bit before trying again." }]);
      }
    };
    socketRef.current = ws;
    return ws;
  }

  function evaluate(transcribedSteps: Step[]) {
    const ws = connectSocket();
    const send = () => ws.send(JSON.stringify({ type: "evaluate", steps: transcribedSteps }));
    ws.readyState === WebSocket.OPEN ? send() : ws.addEventListener("open", send, { once: true });
  }

  function sendStudentResponse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message) return;
    const isEquation = message.includes("=") && /^[0-9a-zA-Z\s*+\-/^().−=\\]+$/.test(message);
    const updatedSteps = isEquation
      ? [...steps, { line: Math.max(0, ...steps.map((step) => step.line)) + 1, latex: message, hiddenOnCanvas: true }]
      : steps;
    if (isEquation) setSteps(updatedSteps);
    setFeed((items) => [...items, { sender: "student", text: message }]);
    setDraft("");
    const ws = connectSocket();
    const history = [...feed, { sender: "student", text: message }];
    const send = () => ws.send(JSON.stringify({ type: "student_response", message, steps: updatedSteps, history }));
    ws.readyState === WebSocket.OPEN ? send() : ws.addEventListener("open", send, { once: true });
  }

  async function processFile(file: File) {
    setBusy(true); setHighlightLine(null);
    setPreview(URL.createObjectURL(file));
    try {
      const body = new FormData(); body.append("image", file);
      const response = await fetch(`${API_URL}/api/vision/process`, { method: "POST", body });
      if (!response.ok) throw new Error((await response.json()).detail ?? "Could not process this image.");
      const result = (await response.json()) as { steps: Step[] };

      // Append new steps to existing ones (for multi-step uploads)
      const newSteps = [...steps];
      for (const newStep of result.steps) {
        const maxLine = Math.max(0, ...newSteps.map(s => s.line));
        newSteps.push({ ...newStep, line: maxLine + newStep.line });
      }

      setSteps(newSteps); evaluate(newSteps);
      setFeed((items) => [...items, { sender: "student", text: steps.length === 0 ? "Here are my handwritten algebra steps." : "I've added the next step(s)." }]);
    } catch (error) {
      setFeed((items) => [...items, { sender: "system", text: error instanceof Error ? error.message : "Image processing failed." }]);
    } finally { setBusy(false); }
  }

  function onUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (file) void processFile(file);
    event.target.value = "";
  }

  async function openCamera() {
    try {
      // Try with facingMode for mobile first, fallback to default for Mac
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      } catch {
        // Fallback: just request any video without facingMode (works on Mac)
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(e => console.error("Play error:", e));
      }
      setCameraOpen(true);
    } catch (e) {
      setFeed((items) => [...items, { sender: "system", text: "Camera access was not available. Make sure to allow camera permission in your browser settings." }]);
    }
  }

  function stopCamera() {
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((track) => track.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOpen(false);
  }

  function captureCamera() {
    const video = videoRef.current; if (!video) return;
    const canvas = document.createElement("canvas"); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => { if (blob) void processFile(new File([blob], "homework.jpg", { type: "image/jpeg" })); }, "image/jpeg", .9);
    stopCamera();
  }

  return <main className="app">
    <header className="header"><h1>AI Algebra Coach</h1><span>Learn by thinking, one line at a time.</span></header>
    <section className="split">
      <article className="panel"><div className="panel-title">Your algebra canvas</div>
        <div className="capture">
          <label className="button">Upload image<input aria-label="Upload homework image" type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={onUpload} /></label>
          {busy && <span className="status">Reading your work…</span>}
        </div>
        {preview && <img className="preview" src={preview} alt="Uploaded homework preview" />}
        <div className="steps">{steps.some((step) => !step.hiddenOnCanvas) ? steps.filter((step) => !step.hiddenOnCanvas).map((step) => <div className={`step ${highlightLine === step.line ? "highlight" : ""}`} key={step.line}><small>Line {step.line}</small><div dangerouslySetInnerHTML={{ __html: katex.renderToString(step.latex, { throwOnError: false, displayMode: true }) }} /></div>) : <p className="status">Your transcribed mathematical steps will appear here.</p>}</div>
      </article>
      <aside className="panel"><div className="panel-title">Socratic coach</div><div className="feed">{feed.map((message, index) => <div className={`message ${message.sender === "student" ? "student" : ""}`} key={index}>{message.text}</div>)}</div><form className="reply" onSubmit={sendStudentResponse}><label className="sr-only" htmlFor="coach-reply">Your response</label><input id="coach-reply" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Explain your thinking…" maxLength={1000} /><button className="button" type="submit">Send</button></form></aside>
    </section>
  </main>;
}
