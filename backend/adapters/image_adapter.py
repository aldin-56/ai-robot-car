import time
import requests
import urllib.parse
from typing import Dict, Any, Optional
from backend.adapters.base import BaseAdapter


class ImageAdapter(BaseAdapter):
    """Image Generation Adapter supporting DALL-E (OpenAI) and Pollinations AI (free fallback)."""

    def __init__(self, provider_id: str = "pollinations", api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)
        self.provider_id = provider_id.lower()

    def authenticate(self) -> bool:
        if self.provider_id == "openai":
            return bool(self.api_key)
        return True  # Pollinations is free and accessible

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        prompt = input_data.get("prompt") or input_data.get("description")
        return bool(prompt and isinstance(prompt, str))

    def estimate_cost(self, input_data: Dict[str, Any]) -> float:
        if self.provider_id == "openai":
            return 0.040  # DALL-E 3 standard pricing
        return 0.0

    def estimate_time(self, input_data: Dict[str, Any]) -> int:
        return 4000  # ~4 seconds for image rendering

    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        return bool(output_data and output_data.get("image_url"))

    def execute(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {
                "success": False,
                "output": None,
                "execution_time_ms": 0,
                "estimated_cost": 0.0,
                "error": "Invalid image generation prompt."
            }

        prompt = input_data.get("prompt") or input_data.get("description")
        start_time = time.time()

        if self.provider_id == "openai" and self.api_key:
            return self._call_dalle(prompt, start_time)
        else:
            return self._call_pollinations(prompt, start_time)

    def _call_dalle(self, prompt: str, start_time: float) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        res = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload, timeout=60)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if res.status_code == 200:
            data = res.json()
            image_url = data["data"][0]["url"]
            return {
                "success": True,
                "output": {
                    "image_url": image_url,
                    "prompt": prompt,
                    "provider": "OpenAI DALL-E 3"
                },
                "execution_time_ms": elapsed_ms,
                "estimated_cost": 0.040,
                "error": None
            }
        else:
            # Fallback to Pollinations AI on failure or no credits
            return self._call_pollinations(prompt, start_time)

    def _call_pollinations(self, prompt: str, start_time: float) -> Dict[str, Any]:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "output": {
                "image_url": image_url,
                "prompt": prompt,
                "provider": "Pollinations AI"
            },
            "execution_time_ms": elapsed_ms,
            "estimated_cost": 0.0,
            "error": None
        }
