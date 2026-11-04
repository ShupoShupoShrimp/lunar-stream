import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"

load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")

client = AsyncGroq(api_key=api_key)


def save_evidence(
    claim_id: str,
    output_path: str | Path,
    prompt: str,
    response_text: str,
    ttft_ms: float,
    total_duration: float,
    token_tokens: int,
    result: bool,
):

    evidence = {
        "claim_id": claim_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "model": "openai/gpt-oss-20b",
        "prompt": prompt,
        "metrics": {
            "ttft_ms": ttft_ms,
            "total_duration": total_duration,
            "token_tokens": token_tokens,
        },
        "response": response_text,
        "result": result,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


async def main():

    start_time = time.perf_counter()

    def get_timestamp() -> str:
        elapsed = time.perf_counter() - start_time
        return f"[{elapsed:06.3f}s]"

    model = "openai/gpt-oss-20b"

    print("=== LLM STREAMING SMOKE TEST ===")
    print("Provider: Groq")
    print(f"Model: {model}")
    print()

    print(f"{get_timestamp()} Request sent")

    prompt = "Say 'I am Yachiyo and today is my first stream! Join me anytime~'"

    chat_completions = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a smoke test assistant. Provide brief, direct, and concise responses without conversational filler or introductions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        stream=True,
    )

    first_token_received = False
    response_chunks = []
    first_token_time = None
    total_tokens = 0

    async for chunk in chat_completions:
        content = chunk.choices[0].delta.content if chunk.choices else None

        if content:
            if not first_token_received:
                first_token_time = time.perf_counter() - start_time
                print(f"{get_timestamp()} First content received")
                first_token_received = True

            safe_content = content.replace("\n", "\\n")
            print(f"{get_timestamp()} Chunk: {safe_content}")

            response_chunks.append(content)

        if chunk.usage:
            total_tokens = chunk.usage.total_tokens

    total_duration = time.perf_counter() - start_time
    full_text = "".join(response_chunks).strip()
    chunk_count = len(response_chunks)

    print()
    print("=== RESULTS ===")
    print(f"Response: {full_text}")
    print(
        f"First content latency: {first_token_time * 1000:.2f} ms"
        if first_token_time is not None
        else "First content latency: N/A"
    )
    print(f"Total duration: {total_duration * 1000:.2f} ms")
    print(f"Content chunks received: {chunk_count}")

    if first_token_received and full_text:
        print("RESULT: PASS")
        result = True
    else:
        print("RESULT: FAIL")
        result = False

    save_evidence(
        claim_id="C23",
        output_path="bench/out/C23.json",
        prompt=prompt,
        response_text=full_text,
        ttft_ms=first_token_time * 1000 if first_token_time is not None else None,
        total_duration=total_duration * 1000,
        token_tokens=total_tokens,
        result=result,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
