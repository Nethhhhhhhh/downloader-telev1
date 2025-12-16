import os
import shutil
import logging
import yt_dlp
import uuid
import asyncio
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

class MediaType(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'

class DownloaderService:
    def __init__(self, download_path="downloads"):
        # Ensure absolute path to avoid issues
        self.download_path = os.path.abspath(download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
    def _get_ffmpeg_path(self):
        # Check if in PATH
        if shutil.which("ffmpeg"):
            return None # yt-dlp finds it automatically
        
        # Check well-known WinGet path (User-specific)
        # Adapt this based on the specific version found earlier or search generic pattern
        base_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        if os.path.exists(base_path):
            for root, dirs, files in os.walk(base_path):
                if "ffmpeg.exe" in files:
                    return os.path.join(root, "ffmpeg.exe")
        
        return None

    def _get_opts(self, filename_id, is_audio=False):
        ffmpeg_location = self._get_ffmpeg_path()
        if ffmpeg_location:
            logging.info(f"Using FFmpeg at: {ffmpeg_location}")
        else:
            logging.warning("FFmpeg NOT found by auto-detection.")

        opts = {
            'outtmpl': f'{self.download_path}/{filename_id}_%(autonumber)s.%(ext)s', # Handling multiple files
            'noplaylist': True, # We usually want single posts, but might be a carousel
            'quiet': False, # Enable stdout for debug
            'verbose': True, # Enable verbose for debug
            'no_warnings': False,
            'writethumbnail': True, # Ensure we get thumbnails
            'nocache_dir': True, # Disable cache
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        }
        
        if ffmpeg_location:
            opts['ffmpeg_location'] = os.path.dirname(ffmpeg_location) # yt-dlp expects the directory, not the exe

        if is_audio:
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            opts.update({
                # Ensure we select video or audio or separate components
                # For TikTok images it might download m4a audio and jpg images separately if not careful
                'format': 'bestvideo+bestaudio/best', 
                'merge_output_format': 'mp4', # Force MP4 container only for video
            })
        return opts

    async def download_media(self, url: str, force_audio: bool = False):
        """
        Downloads media (Video, Audio, Images) from the given URL.
        Returns a LIST of dictionaries with 'type', 'path', 'title', etc.
        """
        filename_id = str(uuid.uuid4())
        
        # Check for Music Platforms
        is_music_search = False
        search_query = None
        
        if "spotify.com" in url:
            search_query = self._get_spotify_metadata(url)
            is_music_search = True
        elif "music.apple.com" in url:
            search_query = self._get_apple_music_metadata(url)
            is_music_search = True
            
        if is_music_search:
            if not search_query:
                logging.error("Could not extract metadata for music link.")
                return []
            target_url = f"ytsearch1:{search_query}"
            opts = self._get_opts(filename_id, is_audio=True)
            # Override outtmpl for single file search
            opts['outtmpl'] = f'{self.download_path}/{filename_id}.%(ext)s'
        else:
            target_url = url
            is_soundcloud = "soundcloud.com" in url
            # If force_audio is True, treat as audio
            opts = self._get_opts(filename_id, is_audio=is_soundcloud or force_audio)
        
        loop = asyncio.get_event_loop()
        
        try:
            with ThreadPoolExecutor() as pool:
                info_dict = await loop.run_in_executor(
                    pool, 
                    lambda: self._download_sync(target_url, opts)
                )
            
            if not info_dict:
                return []
            
            # If search, unwrap entries
            if is_music_search and 'entries' in info_dict:
                info_dict = info_dict['entries'][0]

            # Find all downloaded files matching this ID
            downloaded_files = {}
            for file in os.listdir(self.download_path):
                if file.startswith(filename_id):
                    full_path = os.path.join(self.download_path, file)
                    # skip part files or temp files
                    if file.endswith('.part') or file.endswith('.ytdl'):
                        continue
                    
                    # Group by base name (without extension) to pair video+thumb
                    # yt-dlp naming: ID_autonumber.ext
                    base_name = os.path.splitext(file)[0]
                    if base_name not in downloaded_files:
                        downloaded_files[base_name] = {'files': []}
                    downloaded_files[base_name]['files'].append(full_path)

            if not downloaded_files:
                return []

            media_list = []
            
            # Map entries if available for better metadata
            entries_map = {}
            if 'entries' in info_dict:
                # Try to map by index if possible, though autonumber is 1-based usually
                for i, entry in enumerate(info_dict['entries']):
                    entries_map[i] = entry
            else:
                entries_map[0] = info_dict

            # Sort by autonumber index to match entries if possible
            # Filenames: uuid_00001.mp4
            sorted_base_names = sorted(downloaded_files.keys())

            for idx, base_name in enumerate(sorted_base_names):
                group = downloaded_files[base_name]
                files = group['files']
                
                video_file = None
                audio_file = None
                image_file = None
                thumb_file = None
                
                # Metadata source
                meta = entries_map.get(idx, info_dict) 

                for f in files:
                    ext = f.split('.')[-1].lower()
                    if ext in ['mp4', 'mkv', 'mov', 'webm']:
                        video_file = f
                    elif ext in ['mp3', 'm4a', 'wav', 'flac', 'ogg']:
                        audio_file = f
                    elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                        # Could be image or thumbnail
                        # If we have a video in this group, treat as thumbnail
                        image_file = f

                if video_file:
                    media_list.append({
                        'type': MediaType.VIDEO,
                        'path': video_file,
                        'title': meta.get('title', 'Video'),
                        'duration': meta.get('duration'),
                        'thumb': image_file, # Local path to thumbnail
                        'width': meta.get('width'),
                        'height': meta.get('height'),
                        'group_id': filename_id
                    })
                elif audio_file:
                    media_list.append({
                        'type': MediaType.AUDIO,
                        'path': audio_file,
                        'title': meta.get('title', 'Audio'),
                        'duration': meta.get('duration'),
                        'thumb': image_file, # Album art?
                        'artist': meta.get('artist'),
                        'group_id': filename_id
                    })
                elif image_file:
                     media_list.append({
                        'type': MediaType.IMAGE,
                        'path': image_file,
                        'title': meta.get('title', 'Image'),
                        'group_id': filename_id
                    })

            return media_list
            
        except Exception as e:
            logging.error(f"Download failed: {e}")
            raise e

    async def convert_video_to_mp3(self, video_path):
        """
        Converts a video file to MP3 using FFmpeg.
        Returns the path to the new MP3 file.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError("Video file not found.")

        base_name = os.path.splitext(video_path)[0]
        mp3_path = f"{base_name}.mp3"
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn", # Disable video recording
            "-acodec", "libmp3lame",
            "-q:a", "2", # High quality
             "-y", # Overwrite output files
            mp3_path
        ]

        # Use full path if found
        ffmpeg_path = self._get_ffmpeg_path()
        if ffmpeg_path:
             ffmpeg_cmd[0] = ffmpeg_path

        logging.info(f"Converting {video_path} to MP3...")
        logging.info(f"FFmpeg Command: {ffmpeg_cmd}")
        
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg Error: {stderr.decode()}")
            raise Exception("Conversion failed.")
            
        if not os.path.exists(mp3_path):
             raise Exception("Output MP3 not created.")
             
        return mp3_path

    def _download_sync(self, url, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    def _get_spotify_metadata(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text
            if " - Song by " in title:
                return title.split(" | ")[0].replace(" - Song by ", " ")
            return title.replace(" | Spotify", "")
        except Exception as e:
            logging.error(f"Spotify scraping error: {e}")
            return None

    def _get_apple_music_metadata(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text
            return title.replace(" on Apple Music", "")
        except Exception as e:
            logging.error(f"Apple Music scraping error: {e}")
            return None

    def cleanup(self, filepath):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                # Also try to cleanup associated thumbnail if it exists
                # This is a bit tricky since we passed the path separately.
                # But typically the handler calls cleanup on the main media path.
                # If we want to be clean, we should delete the thumb file too if it was distinct.
                base = os.path.splitext(filepath)[0]
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    thumb = base + ext
                    if os.path.exists(thumb) and thumb != filepath:
                        os.remove(thumb)
            except Exception as e:
                logging.error(f"Error cleaning up file {filepath}: {e}")

downloader = DownloaderService()
