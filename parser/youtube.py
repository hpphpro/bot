from pytube import YouTube, Playlist
import os, sys, shutil
from config.logguru_log import info

class Converter:
    
    def __init__(self, single_url: str=None, playlist_url: str=None) -> None:
        self.single_url = single_url
        self.playlist_url = playlist_url
        if all([self.single_url, self.playlist_url]):
            raise TypeError('Only one parameter expected, got 2')
        elif not all([self.single_url, self.playlist_url]):
            raise TypeError('At least one parameter expected, got 0')
        if self.single_url: self.__youtube = YouTube(self.single_url) 
        if self.playlist_url: self.__youtube = Playlist(self.playlist_url)
        
    @property  
    def title(self):
        return self.__youtube.title
    
    @property
    def description(self):
        if self.playlist_url:
            raise TypeError('A Playlist has no description')
        return self.__youtube.description
    
    def convert_single(self, audio: bool=False, video: bool=False) -> str:
        if self.playlist_url:
            raise TypeError('Expected url with single video, got playlist. Try to use convert_playlist() instead')
        if all([not audio, not video]):
            raise TypeError('Expected at least one parameter, got 0')
        if audio:
            info(f'Downloading audio from {self.single_url}')
            content = self.__youtube.streams.filter(only_audio=True)[-1].download(os.getcwd()) # opus max 160kbps
            base, _ = os.path.splitext(content)
            new_file = f'{base}.mp3'
            os.rename(content, new_file)
            return new_file
        if video:
            content = self.__youtube.streams.get_highest_resolution().download(os.getcwd()) # max 720p with sound
            return content
    
    def convert_playlist(self, playlist_audio: bool=False, playlist_video: bool=False):
        folder = f'{self.title}\\' if sys.platform == 'win32' else f'{self.title}/'
        if self.single_url:
            raise TypeError('Expected url with playlist, got single video. Try to use convert_single() instead')
        if all([not playlist_audio, not playlist_video]):
            raise TypeError('Expected at least one parameter, got 0')
        videos = self.__youtube.videos
        if playlist_audio:
            info(f'Downloading playlist audio from {self.playlist_url}')
            for video in videos:
                os.makedirs(folder, exist_ok=True)
                content = video.streams.filter(only_audio=True)[-1].download(folder)
                base, _ = os.path.splitext(content)
                new_file = f'{base}.mp3'
                os.rename(content, new_file)
        if playlist_video:
            for video in videos:
                os.makedirs(folder, exist_ok=True)
                video.streams.get_highest_resolution().download(folder)
                
        shutil.make_archive(f'{self.title}', 'zip', f'{folder}')
        
        return f'{self.title}.zip'


