import time
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_RETRIES

groq_client = Groq(api_key=GROQ_API_KEY)  # key comes from .env via config, never hardcode


def call_groq_with_retry(prompt, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return f"Groq API error: {e}"