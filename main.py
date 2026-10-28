import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# Load environment variables from .env file if present
load_dotenv()

from models.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    ComparisonDelta,
    QuestionConfig
)
from services.jev_engine import JevDecisionEngine
from services.llm_engine import GeminiBaselineEngine
from services.presets import PRESETS

app = FastAPI(
    title="Jev Decision Model vs Google Gemini Benchmark API",
    description="Backend service demonstrating the Jev discriminative decision model compared against Google Gemini Generative LLM.",
    version="1.14.0"
)

# Enable CORS for Next.js frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "online",
        "service": "Jev Decision Engine vs Google Gemini API",
        "version": "1.14",
        "tagline": "A question in. A judgment out.",
        "real_api_support": {
            "jev_model": bool(os.environ.get("JEVMODEL_API_KEY") or os.environ.get("TYPESAFE_API_KEY")),
            "gemini_llm": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        }
    }

@app.get("/api/keys/status")
def keys_status():
    return {
        "has_jev_key": bool(os.environ.get("JEVMODEL_API_KEY") or os.environ.get("TYPESAFE_API_KEY")),
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    }

@app.get("/api/presets")
def get_presets():
    return {"presets": PRESETS}

@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    if not request.text_to_judge.strip():
        raise HTTPException(status_code=400, detail="Text to judge cannot be empty.")
    if not request.questions:
        raise HTTPException(status_code=400, detail="At least one question is required.")

    # 1. Execute Jev Decision Engine (Real API or local calibrated)
    jev_key = request.typesafe_api_key or request.api_key
    loop = asyncio.get_event_loop()

    jev_result = await loop.run_in_executor(
        None,
        JevDecisionEngine.evaluate,
        request.text_to_judge,
        request.questions,
        request.model,
        jev_key
    )

    llm_result = None
    delta = None

    # 2. Optionally execute Google Gemini Baseline Engine (Real Gemini API or local calibrated)
    if request.compare_with_llm:
        gemini_key = request.gemini_api_key or request.llm_api_key or request.api_key
        llm_result = await loop.run_in_executor(
            None,
            GeminiBaselineEngine.evaluate,
            request.text_to_judge,
            request.questions,
            request.llm_model,
            request.llm_provider,
            gemini_key,
            request.custom_system_prompt,
            request.custom_user_prompt
        )

        speedup = round(llm_result.metrics.latency_ms / max(1, jev_result.metrics.latency_ms), 1)
        token_savings = round(
            ((llm_result.metrics.total_tokens - jev_result.metrics.total_tokens) / max(1, llm_result.metrics.total_tokens)) * 100,
            1
        )
        cost_savings = round(
            ((llm_result.metrics.estimated_cost_usd - jev_result.metrics.estimated_cost_usd) / max(0.000001, llm_result.metrics.estimated_cost_usd)) * 100,
            1
        )

        delta = ComparisonDelta(
            speedup_ratio=max(1.0, speedup),
            token_savings_percent=max(0.0, token_savings),
            cost_savings_percent=max(0.0, cost_savings)
        )

    return EvaluationResponse(
        jev_result=jev_result,
        llm_result=llm_result,
        comparison_delta=delta
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
