import yt_dlp
import asyncio
from typing import Optional, Dict, List, Any
from loguru import logger
from app.config import settings
import random
import aiohttp
import os


class YouTubeExtractor:
    def __init__(self):
        self.proxy_list = settings.fallback_servers_list if settings.fallback_servers_list else []
        self.current_proxy_index = 0
        self.invidious_instances = [
            'https://invidious.fdn.fr',
            'https://inv.riverside.rocks',
            'https://invidious.osi.kr',
            'https://invidious.namazso.eu'
        ]
        self.current_invidious_index = 0
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        logger.info(f"YouTube API Key loaded: {bool(self.youtube_api_key)}")

    def _get_ydl_options(self, proxy: Optional[str] = None) -> Dict[str, Any]:
        opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'default_search': 'ytsearch',
            'socket_timeout': 30,
        }

        if proxy:
            opts['proxy'] = proxy
        elif settings.HTTP_PROXY:
            opts['proxy'] = settings.HTTP_PROXY

        return opts

    def _rotate_proxy(self) -> Optional[str]:
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def _rotate_invidious(self) -> str:
        instance = self.invidious_instances[self.current_invidious_index]
        self.current_invidious_index = (self.current_invidious_index + 1) % len(self.invidious_instances)
        return instance

    async def search_youtube_api(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search using YouTube Data API as fallback"""
        if not self.youtube_api_key:
            logger.warning("YouTube API key not configured")
            return []
        
        try:
            url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'key': self.youtube_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        entries = []
                        for item in data.get('items', []):
                            entries.append({
                                'video_id': item.get('id', {}).get('videoId', ''),
                                'title': item.get('snippet', {}).get('title', ''),
                                'duration': 0,  # YouTube API doesn't return duration in search
                                'thumbnail': item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', ''),
                                'uploader': item.get('snippet', {}).get('channelTitle', ''),
                                'uploader_id': item.get('snippet', {}).get('channelId', ''),
                                'view_count': 0,  # YouTube API doesn't return view count in search
                                'upload_date': item.get('snippet', {}).get('publishedAt', ''),
                                'url': f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId', '')}"
                            })
                        logger.info(f"YouTube API search successful: {len(entries)} results")
                        return entries
                    else:
                        logger.warning(f"YouTube API search failed with status: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"YouTube API search error: {str(e)}")
            return []

    async def search_invidious(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Invidious API as fallback"""
        try:
            instance = self._rotate_invidious()
            url = f"{instance}/api/v1/search?q={query}&type=video"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        entries = []
                        for item in data[:max_results]:
                            entries.append({
                                'video_id': item.get('videoId', ''),
                                'title': item.get('title', ''),
                                'duration': item.get('lengthSeconds', 0),
                                'thumbnail': item.get('videoThumbnails', [{}])[0].get('url', '') if item.get('videoThumbnails') else '',
                                'uploader': item.get('author', ''),
                                'uploader_id': item.get('authorId', ''),
                                'view_count': item.get('viewCount', 0),
                                'upload_date': item.get('published', ''),
                                'url': f"https://www.youtube.com/watch?v={item.get('videoId', '')}"
                            })
                        logger.info(f"Invidious search successful: {len(entries)} results")
                        return entries
                    else:
                        logger.warning(f"Invidious search failed with status: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Invidious search error: {str(e)}")
            return []

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for videos"""
        try:
            opts = self._get_ydl_options()
            opts['extract_flat'] = True
            opts['playlistend'] = max_results

            logger.info(f"Searching for: {query}")
            logger.info(f"yt-dlp options: {opts}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                    logger.info(f"Search result type: {type(result)}")
                    logger.info(f"Search result keys: {result.keys() if result else 'None'}")
                except Exception as ydl_error:
                    logger.error(f"yt-dlp extraction error: {str(ydl_error)}")
                    logger.error(f"yt-dlp error type: {type(ydl_error)}")
                    # Fallback to YouTube API first, then Invidious
                    logger.info("Falling back to YouTube API")
                    yt_api_results = await self.search_youtube_api(query, max_results)
                    if yt_api_results:
                        return yt_api_results
                    logger.info("Falling back to Invidious API")
                    return await self.search_invidious(query, max_results)
                
                if not result or 'entries' not in result:
                    logger.warning(f"No results found for query: {query}")
                    logger.warning(f"Result: {result}")
                    # Fallback to YouTube API first, then Invidious
                    logger.info("Falling back to YouTube API")
                    yt_api_results = await self.search_youtube_api(query, max_results)
                    if yt_api_results:
                        return yt_api_results
                    logger.info("Falling back to Invidious API")
                    return await self.search_invidious(query, max_results)

                entries = []
                for entry in result['entries']:
                    if entry:
                        entries.append({
                            'video_id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'uploader': entry.get('uploader', ''),
                            'uploader_id': entry.get('uploader_id', ''),
                            'view_count': entry.get('view_count', 0),
                            'upload_date': entry.get('upload_date', ''),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                        })

                logger.info(f"Successfully extracted {len(entries)} entries")
                return entries

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            # Fallback to YouTube API first, then Invidious
            logger.info("Falling back to YouTube API due to error")
            yt_api_results = await self.search_youtube_api(query, max_results)
            if yt_api_results:
                return yt_api_results
            logger.info("Falling back to Invidious API")
            return await self.search_invidious(query, max_results)

    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed video information"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        for attempt in range(3):
            try:
                proxy = self._rotate_proxy() if attempt > 0 else None
                opts = self._get_ydl_options(proxy)

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        continue

                    return {
                        'video_id': info.get('id', video_id),
                        'title': info.get('title', ''),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', ''),
                        'uploader_id': info.get('uploader_id', ''),
                        'view_count': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'description': info.get('description', ''),
                        'tags': info.get('tags', []),
                        'categories': info.get('categories', [])
                    }

            except Exception as e:
                logger.error(f"Video info error (attempt {attempt + 1}): {str(e)}")
                if attempt == 2:
                    raise

        return None

    async def get_audio_stream(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get audio stream URL"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        for attempt in range(3):
            try:
                proxy = self._rotate_proxy() if attempt > 0 else None
                opts = self._get_ydl_options(proxy)
                opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        continue

                    # Find best audio format
                    formats = info.get('formats', [])
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                    
                    if not audio_formats:
                        audio_formats = formats

                    best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0) if audio_formats else None

                    if not best_audio:
                        # Fallback to URL
                        return {
                            'url': info.get('url', ''),
                            'format': 'unknown',
                            'quality': 'unknown',
                            'filesize': info.get('filesize'),
                            'ext': info.get('ext', 'mp3'),
                            'acodec': info.get('acodec', 'unknown'),
                            'abr': info.get('abr', 0)
                        }

                    return {
                        'url': best_audio.get('url', ''),
                        'format': best_audio.get('format', ''),
                        'quality': best_audio.get('format_note', 'unknown'),
                        'filesize': best_audio.get('filesize'),
                        'ext': best_audio.get('ext', 'mp3'),
                        'acodec': best_audio.get('acodec', 'unknown'),
                        'abr': best_audio.get('abr', 0)
                    }

            except Exception as e:
                logger.error(f"Audio stream error (attempt {attempt + 1}): {str(e)}")
                if attempt == 2:
                    raise

        return None

    async def get_lyrics(self, query: str) -> Optional[str]:
        """Get lyrics for a song"""
        try:
            opts = self._get_ydl_options()
            opts['writesubtitles'] = True
            opts['subtitleslangs'] = ['en']
            opts['skip_download'] = True

            # First search for the video
            search_results = await self.search(query, max_results=1)
            if not search_results:
                return None

            video_id = search_results[0]['video_id']
            url = f"https://www.youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None

                # Check for subtitles/captions
                subtitles = info.get('subtitles', {})
                if 'en' in subtitles:
                    return "Lyrics available in video captions"
                
                automatic_captions = info.get('automatic_captions', {})
                if 'en' in automatic_captions:
                    return "Auto-generated lyrics available in video captions"

                return None

        except Exception as e:
            logger.error(f"Lyrics error: {str(e)}")
            return None

    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist information"""
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        try:
            opts = self._get_ydl_options()

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None

                entries = []
                for entry in info.get('entries', []):
                    if entry:
                        entries.append({
                            'video_id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'uploader': entry.get('uploader', ''),
                            'view_count': entry.get('view_count', 0),
                            'upload_date': entry.get('upload_date', ''),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                        })

                return {
                    'playlist_id': info.get('id', playlist_id),
                    'title': info.get('title', ''),
                    'uploader': info.get('uploader', ''),
                    'uploader_id': info.get('uploader_id', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'view_count': info.get('view_count', 0),
                    'video_count': len(entries),
                    'entries': entries
                }

        except Exception as e:
            logger.error(f"Playlist error: {str(e)}")
            return None

    async def get_trending(self, category: str = "music") -> List[Dict[str, Any]]:
        """Get trending videos"""
        try:
            opts = self._get_ydl_options()
            # Use a simpler trending URL that's more likely to work
            url = f"https://www.youtube.com/feed/trending?bp=6gQJRkFleBIoX"

            logger.info(f"Fetching trending videos for category: {category}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                logger.info(f"Trending result: {info}")
                
                if not info or 'entries' not in info:
                    logger.warning(f"No trending videos found")
                    # Fallback to Invidious
                    logger.info("Falling back to Invidious API for trending")
                    return await self.search_invidious("trending music", 20)

                entries = []
                for entry in info['entries'][:20]:  # Limit to 20 results
                    if entry:
                        entries.append({
                            'video_id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'uploader': entry.get('uploader', ''),
                            'view_count': entry.get('view_count', 0),
                            'upload_date': entry.get('upload_date', ''),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                        })

                return entries

        except Exception as e:
            logger.error(f"Trending error: {str(e)}")
            # Fallback to Invidious
            logger.info("Falling back to Invidious API for trending due to error")
            return await self.search_invidious("trending music", 20)

    async def get_related(self, video_id: str) -> List[Dict[str, Any]]:
        """Get related videos"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            opts = self._get_ydl_options()

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return []

                related = info.get('related_videos', [])
                entries = []
                for entry in related[:15]:
                    if entry:
                        entries.append({
                            'video_id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'uploader': entry.get('uploader', ''),
                            'view_count': entry.get('view_count', 0),
                            'upload_date': entry.get('upload_date', ''),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                        })

                return entries

        except Exception as e:
            logger.error(f"Related videos error: {str(e)}")
            return []

    async def get_extractor_version(self) -> str:
        """Get yt-dlp version"""
        return yt_dlp.version.__version__


# Global extractor instance
extractor = YouTubeExtractor()
