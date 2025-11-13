import subprocess
import os
import tempfile
from flask import current_app
from typing import List, Dict, Optional
import json


class FFmpegHelper:
    """Helper for video composition using FFmpeg"""
    
    @staticmethod
    def create_video_composition(
        avatar_video_url: str,
        audio_url: str,
        timeline: List[Dict],
        materials: List[Dict],
        output_filename: str
    ) -> str:
        """
        Create final video composition with avatar, audio, and B-roll materials
        
        Args:
            avatar_video_url: URL to talking avatar video
            audio_url: URL to audio file
            timeline: Timeline segments with material assignments
            materials: Available materials with URLs
            output_filename: Output video filename
            
        Returns:
            Path to composed video file
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Download avatar video
            avatar_path = FFmpegHelper._download_file(avatar_video_url, temp_dir, 'avatar.mp4')
            
            # Download audio
            audio_path = FFmpegHelper._download_file(audio_url, temp_dir, 'audio.mp3')
            
            # Download materials
            material_paths = {}
            for mat in materials:
                mat_id = mat.get('id')
                mat_url = mat.get('url')
                if mat_id and mat_url:
                    # Extract extension from URL (before query parameters)
                    url_path = mat_url.split('?')[0]
                    ext = os.path.splitext(url_path)[1] or '.jpg'
                    mat_path = FFmpegHelper._download_file(mat_url, temp_dir, f'mat_{mat_id}{ext}')
                    material_paths[mat_id] = mat_path
            
            # Create FFmpeg filter complex for overlays
            output_path = os.path.join(temp_dir, output_filename)
            
            # Simple composition: avatar video + audio
            # Future: Add B-roll overlays based on timeline
            cmd = [
                'ffmpeg',
                '-i', avatar_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',
                output_path
            ]
            
            current_app.logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
            
            current_app.logger.info(f"Video composition complete: {output_path}")
            return output_path
            
        except Exception as e:
            current_app.logger.error(f"Video composition error: {str(e)}")
            raise
    
    @staticmethod
    def create_advanced_composition(
        avatar_video_url: str,
        audio_url: str,
        timeline: List[Dict],
        materials: List[Dict],
        output_filename: str
    ) -> str:
        """
        Create advanced video composition with B-roll overlays and transitions
        
        Args:
            avatar_video_url: URL to talking avatar video
            audio_url: URL to audio file
            timeline: Timeline segments with material assignments
            materials: Available materials with URLs
            output_filename: Output video filename
            
        Returns:
            Path to composed video file
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Download all assets
            avatar_path = FFmpegHelper._download_file(avatar_video_url, temp_dir, 'avatar.mp4')
            audio_path = FFmpegHelper._download_file(audio_url, temp_dir, 'audio.mp3')
            
            material_paths = {}
            for mat in materials:
                mat_id = mat.get('id')
                mat_url = mat.get('url')
                if mat_id and mat_url:
                    # Extract extension from URL (before query parameters)
                    url_path = mat_url.split('?')[0]
                    ext = os.path.splitext(url_path)[1] or '.jpg'
                    mat_path = FFmpegHelper._download_file(mat_url, temp_dir, f'mat_{mat_id}{ext}')
                    material_paths[mat_id] = mat_path
            
            # Build filter_complex for timeline overlays
            filters = []
            inputs = ['-i', avatar_path, '-i', audio_path]
            
            # Map material_id to input index (to avoid duplicates)
            mat_id_to_input = {}
            input_index = 2
            
            # Add unique materials as inputs
            for segment in timeline:
                mat_id = segment.get('material_id')
                if mat_id and mat_id != 'MISSING' and mat_id in material_paths:
                    if mat_id not in mat_id_to_input:
                        mat_path = material_paths[mat_id]
                        inputs.extend(['-i', mat_path])
                        mat_id_to_input[mat_id] = input_index
                        input_index += 1
            
            # Build filter chain
            # First, collect all segments with materials
            segments_with_materials = []
            for segment in timeline:
                mat_id = segment.get('material_id')
                if mat_id and mat_id != 'MISSING' and mat_id in mat_id_to_input:
                    segments_with_materials.append(segment)
            
            overlay_count = 0
            prev_video = '[0:v]'
            
            for i, segment in enumerate(segments_with_materials):
                mat_id = segment.get('material_id')
                mat_input = mat_id_to_input[mat_id]
                
                start_time = segment.get('start_time', 0)
                
                # End time: show until next segment starts, or until segment's original end_time
                if i < len(segments_with_materials) - 1:
                    # Show until next poster appears
                    end_time = segments_with_materials[i + 1].get('start_time', start_time + 5)
                else:
                    # Last poster: show until its original end time
                    end_time = segment.get('end_time', start_time + 5)
                
                # Scale material to fit in lower 1.2/3 of video (with side margins)
                # Video is 832x1088, lower 1.2/3 height = ~435px (40% of height), width with margins = ~665px (80%)
                # force_original_aspect_ratio=decrease ensures image fits within bounds
                filters.append(
                    f"[{mat_input}:v]scale=665:435:force_original_aspect_ratio=decrease[mat{overlay_count}];"
                )
                
                # Overlay in lower 1.2/3, centered horizontally
                # Y position: H*0.6 positions it at 60% from top (lower 40% = 1.2/3 of video)
                # X position: (W-w)/2 centers it horizontally
                next_video = f"[v{overlay_count}]"
                filters.append(
                    f"{prev_video}[mat{overlay_count}]overlay=(W-w)/2:H*0.6:enable='between(t,{start_time},{end_time})'{next_video};"
                )
                
                prev_video = next_video
                overlay_count += 1
            
            output_path = os.path.join(temp_dir, output_filename)
            
            if filters:
                # Apply overlays
                filter_complex = ''.join(filters).rstrip(';')
                
                cmd = ['ffmpeg'] + inputs + [
                    '-filter_complex', filter_complex,
                    '-map', prev_video,
                    '-map', '1:a:0',
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-shortest',
                    '-y',
                    output_path
                ]
                
                current_app.logger.info(f"FFmpeg command: {' '.join(cmd[:10])}...")
                current_app.logger.info(f"Filter complex: {filter_complex}")
            else:
                # Fallback: simple composition
                cmd = [
                    'ffmpeg',
                    '-i', avatar_path,
                    '-i', audio_path,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    '-y',
                    output_path
                ]
                current_app.logger.info("Using simple composition (no overlays)")
            
            current_app.logger.info(f"Running FFmpeg with {len(timeline)} timeline segments, {overlay_count} overlays")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                current_app.logger.error(f"FFmpeg stderr: {result.stderr[-2000:]}")  # Last 2000 chars
                raise RuntimeError(f"FFmpeg error: {result.stderr[-1000:]}")  # Last 1000 chars in exception
            
            current_app.logger.info(f"FFmpeg composition completed successfully")
            return output_path
            
        except Exception as e:
            current_app.logger.error(f"Advanced composition error: {str(e)}")
            raise
    
    @staticmethod
    def add_subtitles(
        video_path: str,
        voiceover_text: str,
        audio_alignment: Dict,
        output_filename: str
    ) -> str:
        """
        Add subtitles to video using audio alignment timestamps
        
        Args:
            video_path: Path to video file
            voiceover_text: Full voiceover text (may contain audio tags)
            audio_alignment: Character-level timestamps from ElevenLabs
            output_filename: Output filename
            
        Returns:
            Path to video with subtitles
        """
        temp_dir = os.path.dirname(video_path)
        
        try:
            # Remove audio tags from voiceover text for subtitles
            import re
            clean_text = re.sub(r'\[[\w\s]+\]', '', voiceover_text).strip()
            
            # Generate SRT subtitle file
            srt_path = os.path.join(temp_dir, 'subtitles.srt')
            FFmpegHelper._generate_srt(clean_text, audio_alignment, srt_path)
            
            output_path = os.path.join(temp_dir, output_filename)
            
            # Subtitle style:
            # - FontSize=12 (2x smaller than before)
            # - PrimaryColour=&H00C2CC (BGR format for #CCC200 - yellow/gold)
            # - Outline=0 (no outline)
            # - BackColour and Shadow for readability
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='FontSize=12,PrimaryColour=&H00C2CC,Outline=0,Shadow=1,BackColour=&H80000000'",
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg subtitle error: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            current_app.logger.error(f"Subtitle addition error: {str(e)}")
            raise
    
    @staticmethod
    def _download_file(url: str, dest_dir: str, filename: str) -> str:
        """Download file from URL to local path"""
        import requests
        
        dest_path = os.path.join(dest_dir, filename)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return dest_path
    
    @staticmethod
    def _generate_srt(text: str, alignment: Dict, output_path: str):
        """
        Generate SRT subtitle file from text and alignment with smart line breaks.
        Avoids orphaned prepositions, conjunctions, and other hanging words.
        """
        import re
        
        # Get character-level timestamps from alignment
        alignment_data = alignment.get('alignment', {})
        characters = alignment_data.get('characters', [])
        char_start_times = alignment_data.get('character_start_times_seconds', [])
        char_end_times = alignment_data.get('character_end_times_seconds', [])
        audio_duration = alignment.get('audio_duration', 30)
        
        # If we have alignment data, use it
        if characters and char_start_times and len(characters) == len(char_start_times):
            aligned_text = ''.join(characters)
            current_app.logger.info(f"Generating subtitles with alignment data: {len(characters)} chars")
            
            # Split text into sentences
            sentences = re.split(r'([.!?]+\s*)', text)
            sentences = [''.join(sentences[i:i+2]) for i in range(0, len(sentences)-1, 2)]
            if len(sentences) * 2 < len(text.split()):
                sentences.append(sentences[-1] if sentences else text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    
                    # Find sentence position in aligned text
                    clean_sentence = sentence.strip()
                    # Remove extra spaces for matching
                    search_pattern = re.sub(r'\s+', ' ', clean_sentence)[:50]
                    
                    sentence_pos = aligned_text.find(search_pattern[:30])
                    if sentence_pos == -1:
                        current_app.logger.warning(f"Could not find sentence in alignment: {search_pattern[:30]}")
                        continue
                    
                    # Get timing for this sentence
                    start_time = char_start_times[sentence_pos] if sentence_pos < len(char_start_times) else 0
                    
                    # Find end position
                    sentence_end_pos = min(sentence_pos + len(clean_sentence), len(char_end_times) - 1)
                    end_time = char_end_times[sentence_end_pos] if sentence_end_pos < len(char_end_times) else audio_duration
                    
                    # Smart text splitting: break into 2 lines if needed
                    subtitle_lines = FFmpegHelper._smart_split_subtitle(clean_sentence)
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{FFmpegHelper._format_srt_time(start_time)} --> {FFmpegHelper._format_srt_time(end_time)}\n")
                    f.write(f"{subtitle_lines}\n\n")
                    
                    subtitle_index += 1
        else:
            # Fallback: simple word-based subtitle generation
            current_app.logger.warning("No alignment data, using fallback subtitle generation")
            words = text.split()
            words_per_subtitle = 8
            
            with open(output_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                for i in range(0, len(words), words_per_subtitle):
                    chunk_words = words[i:i+words_per_subtitle]
                    chunk = ' '.join(chunk_words)
                    
                    # Calculate timing
                    start_time = (i / len(words)) * audio_duration
                    end_time = min(((i + words_per_subtitle) / len(words)) * audio_duration, audio_duration)
                    
                    # Smart split
                    subtitle_lines = FFmpegHelper._smart_split_subtitle(chunk)
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{FFmpegHelper._format_srt_time(start_time)} --> {FFmpegHelper._format_srt_time(end_time)}\n")
                    f.write(f"{subtitle_lines}\n\n")
                    
                    subtitle_index += 1
    
    @staticmethod
    def _smart_split_subtitle(text: str, max_chars_per_line: int = 42) -> str:
        """
        Smart text splitting for subtitles with typographic rules.
        Avoids orphaned prepositions, conjunctions, and short words at line ends.
        
        Rules:
        - Prepositions (в, на, с, к, у, о, по, за, из, до, для, без, от, при, про, под) stay with next word
        - Conjunctions (и, а, но, или, да, что, как, если, чтобы, когда) stay with next word
        - Particles (не, ни, ли, же, бы, ведь, уж, вот, даже) stay with next word
        - Numbers stay with following word
        - Max line length ~42 characters
        """
        if len(text) <= max_chars_per_line:
            return text
        
        # List of words that should not end a line (Russian prepositions, conjunctions, particles)
        non_breaking_words = {
            'в', 'на', 'с', 'к', 'у', 'о', 'об', 'по', 'за', 'из', 'до', 'для', 'без', 'от', 'при', 'про', 'под',
            'и', 'а', 'но', 'или', 'да', 'что', 'как', 'если', 'чтобы', 'когда', 'хотя', 'пока', 'чтоб',
            'не', 'ни', 'ли', 'же', 'бы', 'ведь', 'уж', 'вот', 'даже', 'лишь', 'только', 'ещё', 'еще',
            'это', 'тот', 'та', 'то', 'те', 'эта', 'этот', 'эти'
        }
        
        words = text.split()
        
        # Find best split point
        best_split = len(words) // 2
        line1_len = len(' '.join(words[:best_split]))
        
        # Try to find a better split point near the middle
        for i in range(len(words) // 2 - 2, len(words) // 2 + 3):
            if i <= 0 or i >= len(words):
                continue
            
            line1 = ' '.join(words[:i])
            line2 = ' '.join(words[i:])
            
            # Check if line lengths are acceptable
            if len(line1) > max_chars_per_line or len(line2) > max_chars_per_line:
                continue
            
            # Check if last word of first line is non-breaking
            last_word = words[i-1].lower().strip('.,!?;:')
            first_word_line2 = words[i].lower().strip('.,!?;:')
            
            # Avoid breaking before non-breaking words
            if first_word_line2 in non_breaking_words:
                continue
            
            # Avoid ending line with non-breaking word
            if last_word in non_breaking_words:
                continue
            
            # This is a good split point
            best_split = i
            break
        
        # If no good split found, use middle
        if best_split == 0:
            best_split = len(words) // 2
        
        line1 = ' '.join(words[:best_split])
        line2 = ' '.join(words[best_split:])
        
        return f"{line1}\n{line2}"
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


ffmpeg_helper = FFmpegHelper()
