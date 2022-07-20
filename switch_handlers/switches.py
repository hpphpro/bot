from dataclasses import dataclass

@dataclass
class Handler:
    # main menu set
    instagram: bool = False
    ncs: bool = False
    youtube: bool = False 
    # ncs set
    search_by_author: bool = False
    search_by_title: bool = False
    download_all: bool = False
    search_title_author: bool = False
    # youtube set
    single: bool = False
    playlist: bool = False
    video: bool = False
    video_playlist: bool = False
    
    @classmethod
    def set_all(cls):
        cls.instagram = False
        cls.ncs = False
        cls.youtube = False 
        cls.search_by_author = False
        cls.search_by_title = False
        cls.download_all = False
        cls.search_title_author = False
        cls.single = False
        cls.playlist = False
        cls.video = False
        cls.video_playlist = False