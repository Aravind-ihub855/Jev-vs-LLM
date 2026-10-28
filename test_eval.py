import asyncio
from main import evaluate
from models.schemas import EvaluationRequest, QuestionConfig, QuestionOption
from services.presets import PRESETS

async def test():
    preset = PRESETS[0]
    questions = [QuestionConfig(**q) for q in preset["questions"]]
    req = EvaluationRequest(
        text_to_judge=preset["text_to_judge"],
        questions=questions,
        model="Jev 1.14",
        compare_with_llm=True,
        llm_model="gpt-4o-mini"
    )
    res = await evaluate(req)
    print("=== Jev Results ===")
    print(f"Latency: {res.jev_result.metrics.latency_ms} ms")
    print(f"Tokens: In={res.jev_result.metrics.input_tokens}, Out={res.jev_result.metrics.output_tokens}, Total={res.jev_result.metrics.total_tokens}")
    for j in res.jev_result.judgments:
        print(f" - [{j.type}] {j.question_key}: {j.verdict} (conf: {j.confidence})")

    print("\n=== LLM Results ===")
    print(f"Latency: {res.llm_result.metrics.latency_ms} ms")
    print(f"Tokens: In={res.llm_result.metrics.input_tokens}, Out={res.llm_result.metrics.output_tokens}, Total={res.llm_result.metrics.total_tokens}")
    for j in res.llm_result.judgments:
        print(f" - [{j.type}] {j.question_key}: {j.verdict}")

    print("\n=== Benchmark Delta ===")
    print(f"Speedup: {res.comparison_delta.speedup_ratio}x faster")
    print(f"Token savings: {res.comparison_delta.token_savings_percent}%")
    print(f"Cost savings: {res.comparison_delta.cost_savings_percent}%")

if __name__ == "__main__":
    asyncio.run(test())
