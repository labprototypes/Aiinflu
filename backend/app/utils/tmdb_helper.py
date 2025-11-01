import requests
from flask import current_app
from typing import Optional, Dict, List


class TMDBHelper:
    """Helper for The Movie Database (TMDB) API integration"""
    
    BASE_URL = "https://api.themoviedb.org/3"
    
    @staticmethod
    def search_movie(query: str, language: str = "en-US") -> Optional[Dict]:
        """
        Search for a movie by title
        
        Args:
            query: Movie title to search
            language: Language code (e.g., 'en-US', 'ru-RU')
            
        Returns:
            Movie data or None if not found
        """
        api_key = current_app.config.get('TMDB_API_KEY')
        if not api_key:
            raise ValueError("TMDB_API_KEY not configured")
        
        url = f"{TMDBHelper.BASE_URL}/search/movie"
        params = {
            'api_key': api_key,
            'query': query,
            'language': language,
            'page': 1
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                return data['results'][0]  # Return first match
            return None
        except Exception as e:
            current_app.logger.error(f"TMDB search error: {str(e)}")
            return None
    
    @staticmethod
    def get_movie_images(movie_id: int) -> List[str]:
        """
        Get movie images (backdrops and posters)
        
        Args:
            movie_id: TMDB movie ID
            
        Returns:
            List of image URLs
        """
        api_key = current_app.config.get('TMDB_API_KEY')
        if not api_key:
            raise ValueError("TMDB_API_KEY not configured")
        
        url = f"{TMDBHelper.BASE_URL}/movie/{movie_id}/images"
        params = {'api_key': api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            image_urls = []
            base_url = "https://image.tmdb.org/t/p/original"
            
            # Add backdrops
            for backdrop in data.get('backdrops', [])[:5]:
                image_urls.append(f"{base_url}{backdrop['file_path']}")
            
            # Add posters
            for poster in data.get('posters', [])[:3]:
                image_urls.append(f"{base_url}{poster['file_path']}")
            
            return image_urls
        except Exception as e:
            current_app.logger.error(f"TMDB images error: {str(e)}")
            return []
    
    @staticmethod
    def match_cross_language(title_primary: str, title_secondary: str) -> Optional[Dict]:
        """
        Match a movie across languages (e.g., "Tenet" in English and "Довод" in Russian)
        
        Args:
            title_primary: Title in primary language
            title_secondary: Title in secondary language
            
        Returns:
            Matched movie data with images from both languages
        """
        # Try primary language search
        movie_en = TMDBHelper.search_movie(title_primary, language="en-US")
        if not movie_en:
            return None
        
        movie_id = movie_en['id']
        
        # Get movie details in secondary language
        api_key = current_app.config.get('TMDB_API_KEY')
        url = f"{TMDBHelper.BASE_URL}/movie/{movie_id}"
        params = {'api_key': api_key, 'language': 'ru-RU'}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            movie_ru = response.json()
            
            # Get images
            images = TMDBHelper.get_movie_images(movie_id)
            
            return {
                'id': movie_id,
                'title_en': movie_en['title'],
                'title_ru': movie_ru.get('title', ''),
                'overview_en': movie_en.get('overview', ''),
                'overview_ru': movie_ru.get('overview', ''),
                'release_date': movie_en.get('release_date', ''),
                'poster_path': movie_en.get('poster_path', ''),
                'backdrop_path': movie_en.get('backdrop_path', ''),
                'images': images,
                'vote_average': movie_en.get('vote_average', 0),
            }
        except Exception as e:
            current_app.logger.error(f"TMDB cross-language match error: {str(e)}")
            return None


tmdb_helper = TMDBHelper()
