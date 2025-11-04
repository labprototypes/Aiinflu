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
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not configured. Please set it in Render Dashboard.")
            self.client = OpenAI(api_key=api_key)
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
                    model="gpt-4o",  # Updated to latest vision model
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Если это постер фильма/сериала - верни ТОЛЬКО русское название как оно вышло в российском прокате.

ВАЖНО:
- Только название на русском (как фильм называется в России)
- Никаких дополнительных слов, описаний или пояснений
- Если это НЕ постер - верни "не постер фильма"

Примеры:
- The Dark Knight → "Тёмный рыцарь"
- Inception → "Начало"  
- Breaking Bad → "Во все тяжкие"

Верни ТОЛЬКО название:"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": url}
                                }
                            ]
                        }
                    ],
                    max_tokens=100
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
    
    def generate_timeline(self, voiceover_text: str, audio_alignment: dict, materials: list) -> list:
        """
        Generate video timeline matching voiceover with materials.
        
        Args:
            voiceover_text: Full voiceover text
            audio_alignment: Character-level timestamps
            materials: List of analyzed materials
            
        Returns:
            Timeline segments with matched materials
        """
        client = self._get_client()
        
        # Prepare materials summary
        materials_summary = []
        for mat in materials:
            materials_summary.append({
                'id': mat.get('id'),
                'description': mat.get('analysis', ''),
                'url': mat.get('url')
            })
        
        audio_duration = audio_alignment.get('audio_duration', 30)
        
        # Format materials list for prompt
        materials_text = "\n".join([
            f"- ID: {mat['id']}\n  Название: {mat['description']}"
            for mat in materials_summary
        ])
        
        prompt = f"""Создай тайминги для видео на основе озвучки и доступных материалов.

Текст озвучки: "{voiceover_text}"

Длительность аудио: {audio_duration} секунд

Доступные материалы (постеры фильмов):
{materials_text}

ВАЖНО: Используй ТОЧНЫЕ ID материалов из списка выше! Не придумывай новые ID.

Раздели видео на 5-10 сегментов по 3-8 секунд каждый. Для каждого сегмента:
1. start_time, end_time (в секундах)
2. text_snippet - фрагмент текста озвучки для этого момента
3. material_id - ТОЧНЫЙ ID материала из списка выше (например "{materials_summary[0]['id'] if materials_summary else 'abc123'}") или "MISSING" если нет подходящего
4. rationale - почему этот материал подходит к данному фрагменту текста

Верни JSON:
{{
  "timeline": [
    {{
      "start_time": 0.0,
      "end_time": 5.2,
      "text_snippet": "...",
      "material_id": "{materials_summary[0]['id'] if materials_summary else 'MISSING'}",
      "rationale": "..."
    }}
  ]
}}"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт видеомонтажа. Создаёшь тайминги."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            import json
            timeline_data = json.loads(result)
            return timeline_data.get('timeline', [])
        except Exception as e:
            current_app.logger.error(f"Timeline generation failed: {str(e)}")
            return []


# Global instance
gpt_helper = GPTHelper()
