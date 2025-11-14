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
        Extract voiceover text from scenario with audio tags for Eleven v3.
        
        Args:
            scenario: Raw scenario text with ideas and instructions
            
        Returns:
            str: Clean text with audio tags ready for TTS (Eleven v3)
        """
        client = self._get_client()
        
        prompt = f"""Ты профессиональный сценарист для вирусных TikTok/Reels видео.

Твоя задача: извлечь из сценария чистый текст для озвучки (текст ГЗК - голос за кадром).
Ты также добавляешь аудио-теги для выразительности речи (для ElevenLabs v3).

⚡ КРИТИЧЕСКИ ВАЖНО - ХУК В НАЧАЛЕ:
ВСЕГДА начинай видео с мощного ХУКА (первые 1-3 секунды), который ЗАЦЕПИТ внимание!

Варианты хуков:
- "Знали ли вы, что..."
- "А вы в курсе, что..."
- "Представьте себе..."
- "Вот вам факт..."
- "Сейчас я вам расскажу..."
- "Готовы узнать..."
- "Невероятно, но факт..."
- "Шокирующая правда о..."
- "То, что я сейчас скажу, вас удивит..."

НЕ используй скучные приветствия типа:
❌ "Здравствуйте"
❌ "Привет всем"
❌ "Добро пожаловать"

Хук должен быть:
- КОРОТКИМ (3-8 слов)
- ИНТРИГУЮЩИМ
- С эмоциональным тегом [excited] или [surprised]
- СРАЗУ в суть темы

Пример:
✅ "[excited] Знали ли вы, что Человек-паук 2 стал культовым хитом?"
✅ "[surprised] Представьте: один фильм изменил жанр супергероев навсегда!"

АУДИО-ТЕГИ (используй в квадратных скобках):
Эмоции:
- [excited] - взволнованно, с энтузиазмом
- [happy] - радостно
- [surprised] - удивленно
- [thoughtful] - задумчиво
- [curious] - с любопытством
- [sarcastic] - саркастично
- [annoyed] - раздраженно

Голосовые эффекты:
- [laughs] - смеется
- [chuckles] - хихикает
- [sighs] - вздыхает
- [whispers] - шепчет
- [clears throat] - прочищает горло

Скорость речи:
- [fast] - быстрая речь, ускоренный темп
- [slow] - медленная речь, размеренный темп
- [quickly] - торопливо
- [measured] - очень медленно и обдуманно

Паузы:
- [short pause] - короткая пауза
- [long pause] - длинная пауза

ПРАВИЛА:
- ОБЯЗАТЕЛЬНО начни с мощного хука (см. примеры выше)
- Убери все режиссерские ремарки и технические указания
- Оставь только то, что будет произнесено вслух
- Сохрани естественную интонацию и паузы
- Текст должен звучать динамично и держать внимание
- НЕ добавляй ничего от себя (кроме хука, если его нет)
- ДОБАВЛЯЙ аудио-теги там, где они УМЕСТНЫ для усиления эмоциональности:
  * В начале предложения: [excited] Привет всем!
  * В конце предложения: Не могу поверить... [sighs]
  * Между предложениями: [short pause]
- НЕ злоупотребляй тегами - используй их естественно (примерно 1-3 тега на абзац)
- НЕ добавляй теги к каждому предложению
- НЕ создавай новые теги, используй только из списка выше

Примеры правильного использования:
✅ "[excited] Знали ли вы, что этот фильм изменил киноиндустрию?" (хук с тегом)
✅ "И тут я понял... [long pause] это конец."
✅ "Ну что сказать [sighs] жизнь штука сложная."
✅ "[surprised] Вот вам факт: Человек-паук 2 получил 93% на Rotten Tomatoes!"

Примеры неправильного использования:
❌ "Здравствуйте, сегодня поговорим о фильмах" (скучное начало без хука)
❌ "[excited] Привет! [happy] Сегодня [curious] у нас новость!" (слишком много тегов)
❌ Текст без тегов вообще (слишком мало эмоций)

Сценарий:
{scenario}

Верни ТОЛЬКО текст для озвучки с аудио-тегами, без комментариев:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию вирусных TikTok/Reels сценариев. ВСЕГДА начинаешь с мощного хука, который зацепит внимание в первые 3 секунды. Используешь эмоциональные аудио-теги для выразительности."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Немного больше креативности для хуков
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
    
    def generate_hook(self, scenario: str) -> str:
        """
        Generate catchy hook/intro for video start.
        
        Args:
            scenario: Raw scenario text
            
        Returns:
            str: Short catchy hook (1-2 sentences)
        """
        client = self._get_client()
        
        prompt = f"""Ты эксперт по созданию вирусных TikTok/Reels видео.

Твоя задача: создать ЦЕПЛЯЮЩИЙ ХУК для начала видео на основе сценария.

Сценарий:
{scenario}

ПРАВИЛА:
- Длина: 1-2 предложения (максимум 15 слов)
- Должен мгновенно захватить внимание
- Создать интригу или любопытство
- Подходит для вертикального короткого видео

СТИЛИ ХУКОВ (выбери наиболее подходящий):
1. "ТОП-формат": "ТОП 5 фильмов которые изменят ваше мировоззрение"
2. "Не поверите": "Вы не поверите какие фильмы могут довести до слез"
3. "Секрет": "Эти фильмы знают немногие но они гениальны"
4. "Вопрос": "Какой фильм посмотреть сегодня вечером"
5. "Шок-факт": "Эти два фильма имеют одну невероятную тайну"
6. "Проблема-решение": "Скучно Вот два фильма которые точно вас зацепят"
7. "Обещание": "Сегодня расскажу о фильмах которые нельзя пропустить"

НЕ используй:
- Длинные предложения
- Сложные конструкции
- Формальный тон
- Банальности ("Привет всем", "В этом видео")

Верни ТОЛЬКО текст хука без объяснений:"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт по вирусному короткому видеоконтенту."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=100
            )
            
            hook = response.choices[0].message.content.strip()
            current_app.logger.info(f"Generated hook: {hook}")
            return hook
            
        except Exception as e:
            current_app.logger.error(f"Hook generation failed: {str(e)}")
            # Fallback to generic hook
            return "Сегодня расскажу о невероятных фильмах"
    
    def generate_timeline(self, voiceover_text: str, audio_alignment: dict, materials: list) -> list:
        """
        Generate video timeline matching voiceover with materials.
        GPT only decides which material to show for each text segment.
        Timestamps come directly from ElevenLabs alignment data.
        
        Args:
            voiceover_text: Full voiceover text
            audio_alignment: Character-level timestamps from ElevenLabs
            materials: List of analyzed materials
            
        Returns:
            Timeline segments with matched materials and REAL timestamps
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
        
        audio_duration = audio_alignment.get('audio_duration', 0)
        
        # Format materials list for prompt
        materials_text = "\n".join([
            f"- ID: {mat['id']}\n  Описание: {mat['description']}"
            for mat in materials_summary
        ])
        
        # Remove audio tags for cleaner text analysis
        import re
        clean_text = re.sub(r'\[[\w\s]+\]', '', voiceover_text).strip()
        
        prompt = f"""Раздели текст озвучки на логические сегменты и подбери к каждому подходящий материал.

Текст озвучки: "{clean_text}"

Доступные материалы (постеры фильмов):
{materials_text}

ЗАДАЧА:
1. Раздели текст на 4-7 логических сегментов (по смысловым блокам)
2. Для каждого сегмента укажи:
   - Фрагмент текста (text_snippet)
   - ID подходящего материала (или "MISSING" если материала нет)
   - Краткое объяснение выбора (rationale)

КРИТИЧЕСКИЕ ПРАВИЛА:
- Используй ТОЛЬКО ID из списка материалов выше
- ВНИМАТЕЛЬНО читай описание материалов - не путай фильмы!
- Когда в тексте говорится о конкретном фильме (например "Человек-паук 2") - ищи ИМЕННО этот фильм в описаниях материалов
- Когда говорится о другом фильме (например "Зеленая миля") - показывай постер ЭТОГО фильма, а НЕ предыдущего
- Каждый сегмент должен соответствовать тому, о чём говорится в тексте В ЭТОТ МОМЕНТ
- Для вступления/заключения без упоминания конкретного фильма - используй "MISSING"
- Если материала нет - ставь "MISSING"

ПРИМЕР:
Если текст: "Сегодня о Человеке-пауке 2... А затем о Зеленой миле..."
То НЕ показывай постер Человека-паука во время текста про Зеленую милю!

Верни JSON:
{{
  "segments": [
    {{
      "text_snippet": "фрагмент текста для этого сегмента",
      "material_id": "ID материала или MISSING",
      "rationale": "почему этот материал (укажи название фильма)"
    }}
  ]
}}"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт видеомонтажа. Подбираешь визуальный материал к тексту озвучки."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            current_app.logger.info(f"GPT response: {result[:500]}...")
            
            import json
            gpt_data = json.loads(result)
            segments = gpt_data.get('segments', [])
            
            current_app.logger.info(f"GPT returned {len(segments)} segments")
            
            # Now map segments to real timestamps from ElevenLabs
            timeline = self._map_segments_to_timestamps(
                segments=segments,
                voiceover_text=voiceover_text,
                audio_alignment=audio_alignment,
                audio_duration=audio_duration
            )
            
            current_app.logger.info(f"Generated timeline with {len(timeline)} entries")
            
            return timeline
            
        except Exception as e:
            current_app.logger.error(f"Timeline generation failed: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []
    
    def _map_segments_to_timestamps(self, segments: list, voiceover_text: str, 
                                    audio_alignment: dict, audio_duration: float) -> list:
        """
        Map GPT text segments to real timestamps from ElevenLabs alignment.
        
        Args:
            segments: List of text segments from GPT with material_id
            voiceover_text: Original voiceover text
            audio_alignment: ElevenLabs alignment data with character timestamps
            audio_duration: Total audio duration
            
        Returns:
            Timeline with real timestamps
        """
        import re
        
        # Get alignment data
        alignment_data = audio_alignment.get('alignment', {})
        char_start_times = alignment_data.get('character_start_times_seconds', [])
        char_end_times = alignment_data.get('character_end_times_seconds', [])
        characters = alignment_data.get('characters', [])
        
        if not char_start_times or not characters:
            current_app.logger.warning("No alignment data available, using fallback timing")
            return self._create_fallback_timeline(segments, audio_duration)
        
        # Build full character string from alignment
        aligned_text = ''.join(characters)
        current_app.logger.info(f"Aligned text length: {len(aligned_text)} chars")
        
        # Remove audio tags from voiceover for matching
        clean_voiceover = re.sub(r'\[[\w\s]+\]', '', voiceover_text).strip()
        
        timeline = []
        
        for i, segment in enumerate(segments):
            text_snippet = segment['text_snippet'].strip()
            material_id = segment['material_id']
            rationale = segment.get('rationale', '')
            
            # Remove audio tags from snippet
            clean_snippet = re.sub(r'\[[\w\s]+\]', '', text_snippet).strip()
            
            # Find this text snippet in the aligned text
            snippet_start_pos = aligned_text.find(clean_snippet[:50])  # Use first 50 chars for matching
            
            if snippet_start_pos == -1:
                current_app.logger.warning(f"Could not find snippet in aligned text: {clean_snippet[:50]}")
                continue
            
            # Get start time from character position
            start_time = char_start_times[snippet_start_pos] if snippet_start_pos < len(char_start_times) else 0
            
            # For end time, look at the next segment or use audio duration
            if i < len(segments) - 1:
                next_snippet = segments[i + 1]['text_snippet'].strip()
                clean_next = re.sub(r'\[[\w\s]+\]', '', next_snippet).strip()
                next_start_pos = aligned_text.find(clean_next[:50])
                
                if next_start_pos != -1 and next_start_pos < len(char_start_times):
                    end_time = char_start_times[next_start_pos]
                else:
                    # Fallback: estimate based on snippet length
                    snippet_end_pos = min(snippet_start_pos + len(clean_snippet), len(char_end_times) - 1)
                    end_time = char_end_times[snippet_end_pos]
            else:
                # Last segment - use audio duration
                end_time = audio_duration
            
            timeline.append({
                'start_time': round(start_time, 1),
                'end_time': round(end_time, 1),
                'text_snippet': text_snippet,
                'material_id': material_id,
                'rationale': rationale
            })
            
            current_app.logger.info(f"Segment {i+1}: {start_time:.1f}s - {end_time:.1f}s | {material_id}")
        
        return timeline
    
    def _create_fallback_timeline(self, segments: list, audio_duration: float) -> list:
        """
        Create timeline with evenly distributed segments (fallback when no alignment data).
        
        Args:
            segments: List of text segments from GPT
            audio_duration: Total audio duration
            
        Returns:
            Timeline with estimated timestamps
        """
        if not segments or audio_duration <= 0:
            return []
        
        segment_duration = audio_duration / len(segments)
        timeline = []
        
        for i, segment in enumerate(segments):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration if i < len(segments) - 1 else audio_duration
            
            timeline.append({
                'start_time': round(start_time, 1),
                'end_time': round(end_time, 1),
                'text_snippet': segment['text_snippet'],
                'material_id': segment['material_id'],
                'rationale': segment.get('rationale', '')
            })
        
        return timeline


# Global instance
gpt_helper = GPTHelper()
