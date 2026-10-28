from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field

QuestionType = Literal["choice", "yes_no", "score", "box"]

class QuestionOption(BaseModel):
    label: str
    description: str = ""

class QuestionConfig(BaseModel):
    id: str
    type: QuestionType
    question: str
    key: str = "verdict"
    options: List[QuestionOption] = Field(default_factory=list)
    score_min: float = 1.0
    score_max: float = 5.0

class EvaluationRequest(BaseModel):
    text_to_judge: str
    image_url: Optional[str] = None
    questions: List[QuestionConfig]
    model: str = "jev-1.14"
    compare_with_llm: bool = True
    llm_model: str = "gemini-1.5-flash"
    llm_provider: str = "gemini"
    typesafe_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    llm_api_key: Optional[str] = None # fallback alias
    api_key: Optional[str] = None # backward-compat fallback
    custom_system_prompt: Optional[str] = None
    custom_user_prompt: Optional[str] = None

class JudgmentOutput(BaseModel):
    question_id: str
    question_key: str
    type: QuestionType
    verdict: str
    confidence: float = 0.95
    score_value: Optional[float] = None
    bounding_box: Optional[List[float]] = None
    probabilities: Optional[Dict[str, float]] = None
    explanation: Optional[str] = None

class BenchmarkMetrics(BaseModel):
    latency_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    is_live_api: bool = False

class ComparisonDelta(BaseModel):
    speedup_ratio: float
    token_savings_percent: float
    cost_savings_percent: float

class ModelResult(BaseModel):
    model_name: str
    model_type: str  # "discriminative" or "generative"
    metrics: BenchmarkMetrics
    judgments: List[JudgmentOutput]
    raw_output: Optional[str] = None
    error: Optional[str] = None

class EvaluationResponse(BaseModel):
    jev_result: ModelResult
    llm_result: Optional[ModelResult] = None
    comparison_delta: Optional[ComparisonDelta] = None
