import os
from groq import Groq
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GroqLLMClient:
    def __init__(self):
        # Default initialization; relies on GROQ_API_KEY being set in env or settings
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY is not set. LLM calls will fail.")
        
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = settings.GROQ_MODEL

    def get_completion(self, system_prompt: str, user_prompt: str, response_format=None) -> str | None:
        if not self.client:
            logger.error("Cannot call Groq: client not initialized (missing API key).")
            return None
            
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 2048
            }
            if response_format:
                # To enforce JSON output on some models, pass {"type": "json_object"}
                kwargs["response_format"] = response_format

            chat_completion = self.client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return None

groq_client = GroqLLMClient()
