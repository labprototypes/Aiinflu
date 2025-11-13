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
        Uses REAL timestamps from audio alignment for accurate sync.
        
        Args:
            voiceover_text: Full voiceover text
            audio_alignment: Character-level timestamps from ElevenLabs
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
        
        # Extract character timestamps from alignment for reference
        alignment_data = audio_alignment.get('alignment', {})
        char_start_times = alignment_data.get('char_start_times_seconds', [])
        char_end_times = alignment_data.get('char_end_times_seconds', [])
        characters = alignment_data.get('characters', [])
        
        # Build a text with approximate timestamps for GPT reference
        timestamped_text = voiceover_text
        if char_start_times and characters:
            # Sample every ~50th character to show timing pattern
            sample_points = []
            for i in range(0, len(characters), max(1, len(characters) // 10)):
                if i < len(char_start_times):
                    sample_points.append(f"[{char_start_times[i]:.1f}s]{''.join(characters[max(0, i-20):i+30])}")
            timestamped_text = "\n".join(sample_points)
        
        # Format materials list for prompt
        materials_text = "\n".join([
            f"- ID: {mat['id']}\n  Описание: {mat['description']}"
            for mat in materials_summary
        ])
        
        prompt = f"""Создай тайминги для видео на основе озвучки и доступных материалов.

Полный текст озвучки: "{voiceover_text}"

Примерные временные метки по тексту (для справки):
{timestamped_text}

Общая длительность аудио: {audio_duration:.1f} секунд

Доступные материалы (постеры фильмов):
{materials_text}

ВАЖНЫЕ ПРАВИЛА:
1. Используй ТОЛЬКО точные ID материалов из списка выше!
2. Таймкоды должны ТОЧНО соответствовать длительности аудио ({audio_duration:.1f}s)
3. Раздели видео на 5-8 сегментов примерно по {audio_duration/6:.1f}-{audio_duration/5:.1f} секунд каждый
4. НЕ спеши! Таймкоды должны быть реалистичными для произнесения текста
5. Последний сегмент должен заканчиваться ТОЧНО на {audio_duration:.1f} секунд

Для каждого сегмента укажи:
- start_time: начало в секундах (float)
- end_time: конец в секундах (float)  
- text_snippet: фрагмент озвучки для этого времени
- material_id: ТОЧНЫЙ ID материала из списка или "MISSING"
- rationale: почему этот материал подходит

Верни JSON:
{{
  "timeline": [
    {{
      "start_time": 0.0,
      "end_time": 5.5,
      "text_snippet": "первые слова текста...",
      "material_id": "{materials_summary[0]['id'] if materials_summary else 'MISSING'}",
      "rationale": "объяснение"
    }}
  ]
}}

ВАЖНО: Проверь, что последний end_time = {audio_duration:.1f}"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт видеомонтажа. Создаёшь ТОЧНЫЕ тайминги, используя реальную длительность аудио. НЕ спеши с таймкодами!"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent timing
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            import json
            timeline_data = json.loads(result)
            timeline = timeline_data.get('timeline', [])
            
            # Post-process: ensure last segment ends exactly at audio_duration
            if timeline and len(timeline) > 0:
                last_segment = timeline[-1]
                if abs(last_segment['end_time'] - audio_duration) > 0.5:  # If off by more than 0.5s
                    current_app.logger.warning(f"Adjusting last segment from {last_segment['end_time']} to {audio_duration}")
                    last_segment['end_time'] = audio_duration
            
            return timeline
        except Exception as e:
            current_app.logger.error(f"Timeline generation failed: {str(e)}")
            return []
        except Exception as e:
            current_app.logger.error(f"Timeline generation failed: {str(e)}")
            return []


# Global instance
gpt_helper = GPTHelper()
