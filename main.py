# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

import os
from agent import BrowserAgent
from computers import BrowserbaseComputer, PlaywrightComputer
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------- FastAPI ----------------
app = FastAPI(title="Gemini Browser Agent")

# ✅ Add CORS middleware immediately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (simple dev solution)
    allow_credentials=True,
    allow_methods=["*"],  # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# ---------------- Gemini Setup ----------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")
genai.configure(api_key=api_key)

PLAYWRIGHT_SCREEN_SIZE = (1440, 900)

# ---------------- Request Model ----------------
class ChatRequest(BaseModel):
    query: str
    env: str = "playwright"
    initial_url: str = "https://www.google.com"
    highlight_mouse: bool = False
    model: str = 'gemini-2.5-computer-use-preview-10-2025'

# ---------------- Routes ----------------
@app.get("/")
def root():
    return {"message": "Backend running! Send POST requests to /chat with a query."}

@app.post("/chat")
def run_agent(request: ChatRequest):
    # Choose environment
    if request.env == "playwright":
        env_instance = PlaywrightComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=request.initial_url,
            highlight_mouse=request.highlight_mouse,
        )
    elif request.env == "browserbase":
        env_instance = BrowserbaseComputer(
            screen_size=PLAYWRIGHT_SCREEN_SIZE,
            initial_url=request.initial_url
        )
    else:
        return {"error": f"Unknown environment: {request.env}"}

    # Run agent
    with env_instance as browser_computer:
        agent = BrowserAgent(
            browser_computer=browser_computer,
            query=request.query,
            model_name=request.model,
        )
        agent.agent_loop()

    return {"result": "Task completed by the agent."}

# ---------------- Run server ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render provides PORT env variable
    uvicorn.run(app, host="0.0.0.0", port=port)
