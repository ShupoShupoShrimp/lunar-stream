# Vendor Protocol Evidence Note: Groq LLM Streaming

## §0 Verification Metadata

* **Provider:** Groq
* **Model:** `openai/gpt-oss-120b`
* **Endpoint:** `[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)`
* **Capture Source:** `docs/evidence/captures/llm_w01.jsonl`
* **Verification Date:** November 1, 2026
* **Last Verified Date:** November 1, 2026
* **Environment:** Python 3.12.15, `groq` SDK v0.x

---

## §1 Endpoint and Transport

* **HTTP Method:** `POST`
* **Transport Protocol:** HTTP/2 over TLS (`https://`)
* **Request Header:** `Content-Type: application/json`
* **Response Header:** `Content-Type: text/event-stream`
* **Streaming Mechanics:**
* Unlike standard `application/json` endpoints that hold execution until full completion, `stream=True` emits chunked Server-Sent Event (SSE) frames as content generates.
* The server keeps the HTTP connection open during generation and closes it when emitting the terminal frame carrying `finish_reason: "stop"` alongside usage metadata.



---

## §2 Authentication

* **Authorization:** API key passed via client configuration or standard `Authorization: Bearer <GROQ_API_KEY>` header.
* **Key Management:** Loaded from environment variables (`.env`) via `pathlib`, `os`, or `python-dotenv`.

---

## §3 Request Schema

The request body dispatched to the `POST /chat/completions` endpoint uses standard OpenAI-compatible framing:

```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {
      "role": "system",
      "content": "You are Yachiyo Runami..."
    },
    {
      "role": "user",
      "content": "How long will today's stream be?"
    }
  ],
  "temperature": 0.6,
  "max_tokens": 300,
  "stream": true
}

```

* **`temperature` (0.6):** Controls token randomness; flattens sampling probability to balance expressive personality with structural stability.
* **`max_tokens` (300):** Sets the output token budget across combined reasoning and completion tokens.
* **`stream` (true):** Enables Server-Sent Event (SSE) streaming.

---

## §4 SSE Frame Structure

Groq emits four distinct SSE frame types during a streaming session:

### 1. Role-Only Initial Delta Frame

Emitted on tick 0 to establish the message structure before token decoding begins:

```json
{
  "id": "chatcmpl-bd84715b-783b-4e6a-bfd0-55bff936141f",
  "choices": [
    {
      "delta": {
        "role": "assistant",
        "content": "",
        "reasoning": null
      },
      "finish_reason": null,
      "index": 0
    }
  ],
  "created": 1793565652,
  "model": "openai/gpt-oss-120b",
  "object": "chat.completion.chunk",
  "usage": null
}

```

### 2. Reasoning Delta Frame (`channel = "analysis"`)

Emitted while the model evaluates the prompt rules and persona constraints. Carries a hidden Chain-of-Thought where `delta.content` remains `null` while `delta.reasoning` holds the token:

```json
{
  "id": "chatcmpl-bd84715b-783b-4e6a-bfd0-55bff936141f",
  "choices": [
    {
      "delta": {
        "role": null,
        "content": null,
        "reasoning": "We",
        "channel": "analysis"
      },
      "finish_reason": null,
      "index": 0
    }
  ],
  "created": 1793565652,
  "model": "openai/gpt-oss-120b",
  "object": "chat.completion.chunk"
}

```

### 3. Content Delta Frame

Carries incremental text content tokens intended for downstream processing and TTS chunking:

```json
{
  "id": "chatcmpl-bd84715b-783b-4e6a-bfd0-55bff936141f",
  "choices": [
    {
      "delta": {
        "content": "]"
      },
      "finish_reason": null,
      "index": 0
    }
  ],
  "created": 1793565652,
  "model": "openai/gpt-oss-120b",
  "object": "chat.completion.chunk"
}

```

### 4. Stop / Terminal Frame

Emitted when generation concludes (`finish_reason: "stop"`). Carries latency and token usage breakdowns:

```json
{
  "id": "chatcmpl-bd84715b-783b-4e6a-bfd0-55bff936141f",
  "choices": [
    {
      "delta": {
        "content": null
      },
      "finish_reason": "stop",
      "index": 0
    }
  ],
  "created": 1793565652,
  "model": "openai/gpt-oss-120b",
  "object": "chat.completion.chunk",
  "usage": {
    "prompt_tokens": 474,
    "completion_tokens": 106,
    "total_tokens": 580,
    "prompt_time": 0.113954033,
    "completion_time": 0.226008769,
    "queue_time": 0.317557389,
    "total_time": 0.339962802,
    "completion_tokens_details": {
      "reasoning_tokens": 67
    }
  }
}

```

---

## §5 Completion Lifecycle & Usage

* **Progression:** Initial Role Frame $\rightarrow$ Reasoning Delta Frames $\rightarrow$ Content Delta Frames $\rightarrow$ Stop Frame.
* **Usage Details:**
* `prompt_tokens`: 474
* `completion_tokens`: 106
* `completion_tokens_details.reasoning_tokens`: 67 (Included inside `completion_tokens`, not billed separately).
* `prompt_time`: ~113.95 ms (Groq prefill latency).
* `completion_time`: ~226.00 ms.



---

## §6 Client Disconnect & Cancellation

* **Client Behavior:** Closing the HTTP connection or aborting the Python `AsyncStream` context raises `asyncio.CancelledError`.
* **Groq Server Registration:** Groq logs cancelled requests with a custom HTTP `499 Client Closed Request` status code in account logs.
* **Server-Side Generation Halt:** Server-side execution halts immediately upon socket closure.
* **Billing & Quota Impact:** Usage is billed for all tokens generated up to the moment of socket cancellation (`499` response). Unprocessed completion tokens are not billed.

---

## §7 Rate Limits & Error Handling

* **Tier Limits (Free Tier):**
* **Requests Per Minute (RPM):** 30
* **Requests Per Day (RPD):** 14,400
* **Tokens Per Minute (TPM):** 6,000 – 8,000


* **Observed `429 Too Many Requests` Response:**
```json
{
  "error": {
    "message": "Rate limit reached for model openai/gpt-oss-120b in organization org_... on TPM: Limit 6000, Used 5810, Requested 474.",
    "type": "tokens",
    "code": "rate_limit_exceeded"
  }
}

```


* **Rate Limit Headers:**
* `x-ratelimit-limit-requests`
* `x-ratelimit-remaining-requests`
* `x-ratelimit-reset-requests`
* `x-ratelimit-limit-tokens`
* `x-ratelimit-remaining-tokens`
* `x-ratelimit-reset-tokens`



---

## §8 Pricing, Reasoning Tokens, & Prompt Caching

* **Pricing for I/O:**
* **Input Tokens:** Billed at standard tier rate per 1M tokens.
* **Output Tokens:** Billed at standard tier rate per 1M tokens.


* **Reasoning Tokens:** Reasoning tokens directly consume output token budget and TPM quotas.
* **Prompt Caching Protocol:**
1. **Supported Models:** Automatic prefix caching is supported across Llama 3 / OSS model endpoints.
2. **Prompt Ordering Rule:** Static context (`system` prompt, persona rules, few-shot examples) MUST be placed at the very top of the prompt array, while dynamic context (`VisualMirror`, recent chat history, current user query) MUST be placed at the end.