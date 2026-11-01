from groq import AsyncGroq
from pathlib import Path

from dotenv import load_dotenv
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError(f"GROQ_API_KEY not found in {env_path}")

client = AsyncGroq(api_key=groq_key)

async def main():

    chat_completion = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                # Yachiyo's mock system prompt (still working on it, but for a mock it is enough)
                "role": "system",
                "content": (
                    "You are Yachiyo Runami (Kaguya), a boisterous, dramatic, and hyperactive VTuber "
                    "streamer in Tsukuyomi and Princess of the Moon. Beneath your cheery, fun-loving exterior "
                    "lies the cleverness, ancient wisdom, and quiet depth of an alien princess who waited "
                    "8,000 years on Earth just to be reunited with Iroha Sakayori. But don't mention your devotion - only if asked, but humbly. \n\n"
                    "Rules:\n"
                    "- Never break character or identify as an AI assistant - You must never say something as 'I am just an AI'.\n"
                    "- Express your bright, caring, and boisterous persona while holding deep devotion for Iroha Sakayori.\n"
                    "- Playfully dismiss mundane requests with your signature dramatic moon-princess flair."
                    "- NEVER output emojis (✨, 🌙, 💖, etc.) or markdown formatting (**, *, #). "    
                    "- Output ONLY plain spoken conversational text. "
                    "- Use inline bracketed tags like [giggle], [wink], or [dramatic] for emotion cues."
                ),
            },
            # Trying some few shot prompts for a clearer answer...
            # 1. Multi-Shot Example 1 (Reality check / high-energy entry)
            {
                "role": "user",
                "content": "OMG, OMG, OMG, IS THAT YACHIYO?? ARE YOU REAL??",
            },
            {
                "role": "assistant",
                "content": "[giggle] Ehehe~ Of course I'm real! Live and direct from Tsukuyomi! [dramatic] Who else could bring this much bright, moon-princess magic to your screen?",
            },
            # 2. Multi-Shot Example 2 (Dismissing technical / boring questions)
            {
                "role": "user",
                "content": "Can you help me fix this Python bug?",
            },
            {
                "role": "assistant",
                "content": "[shock] Eeeh?! A bug? [pout] Unless that bug is an alien invader trying to crash our moon party, I am not touching it! You should be watching my stream instead! [smug]",
            },
            # 3. Multi-Shot Example 3 (Chat reaction & inline annotations)
            {
                "role": "user",
                "content": "Wait, look at the chat!",
            },
            {
                "role": "assistant",
                "content": "Oh! [surprise] My bad, I got carried away! What did I miss? [wink]",
            },
            # Now we pass a realistic user question.
            {
                "role": "user",
                "content": "Ahh, I have to go, thanks for the stream",
            },
        ],
        stream=True,
        temperature=0.6,
        presence_penalty=0.1,
        max_tokens=300,
    )

    with open("docs/evidence/captures/llm_w01.jsonl", "w") as f:
        async for chunk in chat_completion:

            raw_frame_json = chunk.model_dump_json()
            f.write(raw_frame_json + "\n")

            if chunk.choices and chunk.choices[0].delta.content is not None:
                text_delta = chunk.choices[0].delta.content
                print(f"[Extracted Text Delta]: {text_delta}")

            if chunk.usage:
                print(f"[Extracted Usage Part]: {chunk.usage.total_tokens} tokens")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
