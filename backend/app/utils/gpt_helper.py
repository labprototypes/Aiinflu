"""OpenAI GPT-4 helper for text extraction and analysis."""
from openai import OpenAI
from flask import current_app


class GPTHelper:
    """Helper class for OpenAI GPT-4 operations."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if not self.client:
            self.client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
        return self.client
    
    def extract_voiceover_text(self, scenario: str) -> str:
        """
        Extract voiceover text from scenario.
        
        Args:
            scenario: Raw scenario text with ideas and instructions
            
        Returns:
            str: Clean text ready for TTS
        """
        client = self._get_client()
        
        prompt = f"""Ты профессиональный сценарист для подкастов и видео.

Твоя задача: извлечь из сценария чистый текст для озвучки (текст ГЗК - голос за кадром).

ВАЖНО:
- Убери все режиссерские ремарки и технические указания
- Оставь только то, что будет произнесено вслух
- Сохрани естественную интонацию и паузы
- Текст должен звучать органично для подкаста
- НЕ добавляй ничего от себя

Сценарий:
{scenario}

Верни ТОЛЬКО текст для озвучки, без комментариев:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию сценариев для подкастов."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            extracted_text = response.choices[0].message.content.strip()
            return extracted_text
            
        except Exception as e:
            current_app.logger.error(f"GPT extraction failed: {str(e)}")
            raise
    
    def analyze_materials_with_vision(self, image_urls: list[str]) -> list[dict]:
        """
        Analyze images using GPT-4 Vision.
        
        Args:
            image_urls: List of image URLs to analyze
            
        Returns:
            List of dicts with filename, description, keywords
        """
        client = self._get_client()
        results = []
        
        for url in image_urls:
            try:
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Проанализируй это изображение и верни JSON:

{
  "description": "краткое описание на русском",
  "keywords": ["ключевые слова на русском и английском"],
  "type": "movie_poster | photo | screenshot | other",
  "entities": ["имена людей, названия фильмов, брендов и тд"]
}

ВАЖНО: если это постер фильма - укажи название на русском И английском."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": url}
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                
                analysis = response.choices[0].message.content
                results.append({
                    "url": url,
                    "analysis": analysis
                })
                
            except Exception as e:
                current_app.logger.error(f"Vision analysis failed for {url}: {str(e)}")
                results.append({
                    "url": url,
                    "analysis": None,
                    "error": str(e)
                })
        
        return results


# Global instance
gpt_helper = GPTHelper()
