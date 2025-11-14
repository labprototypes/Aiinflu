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
        Generate TikTok-style dynamic subtitles with short phrases.
        Shows 3-6 words at a time, synced to character-level timestamps.
        """
        import re
        
        # Get character-level timestamps from alignment
        alignment_data = alignment.get('alignment', {})
        characters = alignment_data.get('characters', [])
        char_start_times = alignment_data.get('character_start_times_seconds', [])
        char_end_times = alignment_data.get('character_end_times_seconds', [])
        audio_duration = alignment.get('audio_duration', 30)
        
        # If we have alignment data, use it for precise timing
        if characters and char_start_times and len(characters) == len(char_start_times):
            aligned_text = ''.join(characters)
            current_app.logger.info(f"Generating TikTok-style subtitles with alignment data: {len(characters)} chars")
            
            # Split text into words
            words = text.split()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                i = 0
                
                while i < len(words):
                    # Take 3-6 words for this subtitle chunk
                    chunk_size = FFmpegHelper._calculate_optimal_chunk_size(words[i:])
                    chunk_words = words[i:i+chunk_size]
                    chunk_text = ' '.join(chunk_words)
                    
                    # Find this chunk in aligned text to get precise timing
                    # Search for first few words to find position
                    search_text = ' '.join(chunk_words[:2]) if len(chunk_words) >= 2 else chunk_words[0]
                    
                    # Find position in aligned text
                    chunk_start_pos = aligned_text.find(search_text[:20])
                    
                    if chunk_start_pos != -1 and chunk_start_pos < len(char_start_times):
                        start_time = char_start_times[chunk_start_pos]
                        
                        # Find end position (end of last word in chunk)
                        chunk_end_pos = min(chunk_start_pos + len(chunk_text), len(char_end_times) - 1)
                        end_time = char_end_times[chunk_end_pos] if chunk_end_pos < len(char_end_times) else audio_duration
                        
                        # Ensure minimum subtitle duration (0.8 seconds for readability)
                        if end_time - start_time < 0.8:
                            end_time = min(start_time + 0.8, audio_duration)
                    else:
                        # Fallback timing if not found
                        current_app.logger.warning(f"Could not find chunk in alignment: {search_text[:20]}")
                        word_ratio = i / len(words)
                        start_time = word_ratio * audio_duration
                        end_time = min(((i + chunk_size) / len(words)) * audio_duration, audio_duration)
                    
                    # Smart line breaking (max 2 lines, ~25 chars per line)
                    subtitle_lines = FFmpegHelper._smart_split_short_subtitle(chunk_text)
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{FFmpegHelper._format_srt_time(start_time)} --> {FFmpegHelper._format_srt_time(end_time)}\n")
                    f.write(f"{subtitle_lines}\n\n")
                    
                    subtitle_index += 1
                    i += chunk_size
                    
                    # Move aligned_text forward to avoid finding same position again
                    if chunk_start_pos != -1:
                        aligned_text = aligned_text[chunk_start_pos + len(chunk_text):]
                        # Update character arrays
                        if chunk_start_pos + len(chunk_text) < len(characters):
                            char_start_times = char_start_times[chunk_start_pos + len(chunk_text):]
                            char_end_times = char_end_times[chunk_start_pos + len(chunk_text):]
                            characters = characters[chunk_start_pos + len(chunk_text):]
                            aligned_text = ''.join(characters)
                        
        else:
            # Fallback: simple word-based subtitle generation
            current_app.logger.warning("No alignment data, using fallback subtitle generation")
            words = text.split()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                i = 0
                
                while i < len(words):
                    chunk_size = FFmpegHelper._calculate_optimal_chunk_size(words[i:])
                    chunk_words = words[i:i+chunk_size]
                    chunk = ' '.join(chunk_words)
                    
                    # Calculate timing
                    start_time = (i / len(words)) * audio_duration
                    end_time = min(((i + chunk_size) / len(words)) * audio_duration, audio_duration)
                    
                    # Ensure minimum duration
                    if end_time - start_time < 0.8:
                        end_time = min(start_time + 0.8, audio_duration)
                    
                    # Smart split
                    subtitle_lines = FFmpegHelper._smart_split_short_subtitle(chunk)
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{FFmpegHelper._format_srt_time(start_time)} --> {FFmpegHelper._format_srt_time(end_time)}\n")
                    f.write(f"{subtitle_lines}\n\n")
                    
                    subtitle_index += 1
                    i += chunk_size
    
    @staticmethod
    def _calculate_optimal_chunk_size(words: list) -> int:
        """
        Calculate optimal number of words for a subtitle chunk.
        Aims for 3-6 words, with smart rules:
        - New sentence = new subtitle screen
        - Don't break movie titles in quotes
        - No hanging prepositions or conjunctions
        """
        if len(words) == 0:
            return 0
        
        # Non-breaking words that should not end a chunk
        non_breaking = {'в', 'на', 'с', 'к', 'у', 'о', 'об', 'по', 'за', 'из', 'до', 'для', 'без', 'от', 'при', 'про', 'под',
                       'и', 'а', 'но', 'или', 'да', 'что', 'как', 'если', 'чтобы', 'когда', 'хотя',
                       'не', 'ни', 'ли', 'же', 'бы', 'это', 'эта', 'этот', 'эти', 'тот', 'та', 'то', 'те',
                       '—', '-'}
        
        # Start with default chunk size
        if len(words) <= 3:
            # Check if there's a sentence end
            for i, word in enumerate(words):
                if word.endswith(('.', '!', '?')) and i < len(words) - 1:
                    return i + 1  # Break at sentence end
            return len(words)
        
        # Check for quoted text (movie titles) - don't break them
        text = ' '.join(words[:min(10, len(words))])
        if '"' in text or '«' in text or '"' in text:
            # Find matching closing quote
            for i, word in enumerate(words[:min(10, len(words))]):
                if '"' in word or '»' in word or '"' in word:
                    # Include everything up to and including the closing quote
                    if i < len(words) - 1:
                        return min(i + 2, len(words))  # Quote + next word
        
        # Priority 1: Break at sentence boundaries (. ! ?)
        for i in range(3, min(7, len(words))):
            if words[i-1].endswith(('.', '!', '?')):
                return i
        
        # Priority 2: Try 4-6 words without breaking rules
        for size in [5, 4, 6, 3]:
            if size > len(words):
                continue
            
            # Check if last word of chunk is non-breaking
            last_word = words[size - 1].lower().strip('.,!?;:"«»""')
            next_word = words[size].lower().strip('.,!?;:"«»""') if size < len(words) else ''
            
            # Avoid ending with non-breaking word
            if last_word in non_breaking:
                continue
            
            # Avoid breaking before non-breaking word
            if next_word in non_breaking:
                continue
            
            # Don't break if we're in the middle of quoted text
            chunk_text = ' '.join(words[:size])
            remaining_text = ' '.join(words[size:]) if size < len(words) else ''
            open_quotes = chunk_text.count('"') + chunk_text.count('«') + chunk_text.count('"')
            close_quotes = chunk_text.count('"') + chunk_text.count('»') + chunk_text.count('"')
            if open_quotes > close_quotes:
                continue  # Don't break in middle of quoted text
            
            return size
        
        # Fallback
        return min(4, len(words))
    
    @staticmethod
    def _smart_split_short_subtitle(text: str, max_chars_per_line: int = 28) -> str:
        """
        Smart text splitting for TikTok-style subtitles.
        Maximum 2 lines, ~28 characters per line.
        
        Rules:
        - Don't break movie titles in quotes
        - No hanging prepositions/conjunctions/dashes
        - Break at natural pause points
        - Keep sentence endings intact
        """
        # If text fits in one line, return as is
        if len(text) <= max_chars_per_line:
            return text
        
        # List of words that should not end a line
        non_breaking_words = {
            'в', 'на', 'с', 'к', 'у', 'о', 'об', 'по', 'за', 'из', 'до', 'для', 'без', 'от', 'при', 'про', 'под',
            'и', 'а', 'но', 'или', 'да', 'что', 'как', 'если', 'чтобы', 'когда', 'хотя', 'ведь',
            'не', 'ни', 'ли', 'же', 'бы', 'уж', 'вот', 'даже',
            'это', 'тот', 'та', 'то', 'те', 'эта', 'этот', 'эти', 'тут', 'там', 'здесь',
            '—', '-', '–'
        }
        
        words = text.split()
        
        # Check for quoted text (movie title) - keep it on one line if possible
        if ('"' in text or '«' in text or '"' in text) and len(text) <= max_chars_per_line * 1.5:
            # Try to keep quote on one line
            for i in range(1, len(words)):
                line1 = ' '.join(words[:i])
                line2 = ' '.join(words[i:])
                
                # Check if quote is complete in line1
                open_quotes_l1 = line1.count('"') + line1.count('«') + line1.count('"')
                close_quotes_l1 = line1.count('"') + line1.count('»') + line1.count('"')
                
                # If line1 has complete quote (balanced), split there
                if open_quotes_l1 > 0 and open_quotes_l1 == close_quotes_l1:
                    if len(line1) <= max_chars_per_line * 1.2 and len(line2) <= max_chars_per_line * 1.2:
                        return f"{line1}\n{line2}"
        
        # Priority: Split at sentence boundaries if exists
        for i in range(1, len(words)):
            if words[i-1].endswith(('.', '!', '?')):
                line1 = ' '.join(words[:i])
                line2 = ' '.join(words[i:])
                if len(line1) <= max_chars_per_line * 1.3 and len(line2) <= max_chars_per_line * 1.3:
                    return f"{line1}\n{line2}"
        
        # Try to split near the middle, respecting rules
        mid = len(words) // 2
        
        # Look for best split point around middle (±2 words)
        for i in range(max(1, mid - 2), min(len(words), mid + 3)):
            line1 = ' '.join(words[:i])
            line2 = ' '.join(words[i:])
            
            # Check line lengths (allow slight overflow)
            if len(line1) > max_chars_per_line * 1.3 or len(line2) > max_chars_per_line * 1.3:
                continue
            
            # Check for non-breaking words
            last_word = words[i-1].lower().strip('.,!?;:"«»""')
            first_word_line2 = words[i].lower().strip('.,!?;:"«»""') if i < len(words) else ''
            
            if last_word in non_breaking_words or first_word_line2 in non_breaking_words:
                continue
            
            # Don't split in middle of quoted text
            open_quotes = line1.count('"') + line1.count('«') + line1.count('"')
            close_quotes = line1.count('"') + line1.count('»') + line1.count('"')
            if open_quotes > close_quotes:
                continue
            
            # Good split point found
            return f"{line1}\n{line2}"
        
        # Fallback: split at middle regardless of rules
        mid = max(1, len(words) // 2)
        line1 = ' '.join(words[:mid])
        line2 = ' '.join(words[mid:])
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
