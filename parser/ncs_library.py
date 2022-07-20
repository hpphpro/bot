# dependencies
import asyncio, aiohttp
from bs4 import BeautifulSoup as BS
from alive_progress import alive_bar
# built-in modules
import re 
from datetime import datetime
from functools import reduce
import unicodedata, os, sys
from typing import Any, AsyncGenerator

# self modules except loguru
from .auth import NCSAuth
from config.logguru_log import info, error
from config.config import NCS_HEADERS, USER_AGENT


class NcsLibrary(NCSAuth):
    '''Music downloader from popular NCS channel
    Download all music from https://ncs.io/  if it exists
    or
    download by search
    Example:
            >>> NcsLibrary(step=20).download_all(set_description=False) # or True, if you need.
            or
            >>> NcsLibrary().search_and_download(title='loca', first=True, set_description=True) # search by title.
            >>> NcsLibrary().search_and_download(author='Modern Revolt', all_matches=True, set_description=False) # search by author.
            You can search by author and by title at the same time if you know both names.
            Word case is doesnt matter'''
    __instance = None
    __slots__ = ('user_agent', '_cookies', '_headers', '_replace_things', 'step',)
    
    def __new__(cls, step: int=None, user_agent: str=None, *args, **kwargs):
        '''Singleton class'''
        if not cls.__instance:
            cls.__instance = super(NcsLibrary, cls).__new__(cls, *args, **kwargs)
            
        return cls.__instance
    
    
    def __init__(self, step: int=10, user_agent: str=USER_AGENT) -> None:
        '''taking a step to download:
        If you have 100mb/s internet or above try to increase step value'''
        super().__init__()
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.user_agent = user_agent
        NCS_HEADERS['user-agent'] = self.user_agent
        self._headers = NCS_HEADERS
        self._cookies = self._check_cookies()
        self._replace_things = (('?', ''), ('/', ' '), ('|', ''), ('\\', ' '), ('>', ''), ('<', ''), ('\'', ''), ('*', ''), ('`', '')) # things that shouldn't be in folder name
        self.step = step
        
    @property
    def cookies(self):
        return self._cookies
    
    @property
    def headers(self):
        return self._headers
    
    @cookies.setter
    def cookies(self, value: dict) -> dict:
        if not isinstance(value, dict): 
            raise TypeError('A headers value must be a dictionary')
        self._cookies = value
   
    @headers.setter
    def headers(self, value: dict) -> dict:
        if not isinstance(value, dict): 
            raise TypeError('A headers value must be a dictionary')
        self._headers = value
        
    # def download_all(self, set_description=True) -> None:
    #     return asyncio.run(self._download_all(set_description=set_description))
    
    # def search_and_download(self, title=None, author=None, first=False, all_matches=True, set_description=True):
        
    #     return asyncio.run(self._search_and_download(title=title, 
    #                                                 author=author, 
    #                                                 first=first, 
    #                                                 all_matches=all_matches, 
    #                                                 set_description=set_description))
    
    
    def _check_cookies(self):
        path_to_log  = f'{self.path}\\ncs_log.txt' if sys.platform == 'win32' else f'{self.path}/ncs_log.txt'
        if not os.path.exists(path_to_log):
            self.authorization()
        
        time_now = datetime.now().strftime('%Y.%m.%d::%H.%M')
        with open(path_to_log, 'r', encoding='utf-8') as f:
            time_created = f.read()

        if time_created.split('::')[-2] != time_now.split('::')[-2]:
            self.authorization()   
        elif abs(float(time_created.split('::')[-1]) - float(time_now.split('::')[-1])) > 2:
            self.authorization()

        return self.get_cookie()
    
    
    async def _get_pagination(self) -> tuple[list, dict]:
        '''Fetching site pagination'''
        async for url in self._collect_data(['https://ncs.io/music?page=1']):
            for response in url:
                soup = BS(response['_content'], 'lxml')
                pagination = int(soup.select('a.page-link')[-2].text)
                # return a list with all pages on site
                return [f'https://ncs.io/music?page={str(p)}' for p in range(1, pagination + 1)]
            

    async def __get_page_source(self, url: str, session: aiohttp.ClientSession) -> dict | None:
        '''request every url, checking it status response and retrying if timeouted or else'''
        retrying = 0
        while retrying < 10:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return {
                            'url': url,
                            '_content': await response.read(),
                            'headers': response.headers,
                        }
                    break
            except Exception as ex:
                error(f'{ex.__class__.__name__} error occurred, sleeping')
                retrying += 1
                await asyncio.sleep(5)
                
        if retrying == 10:
            raise Exception('Check your connection, cookies or try to change useragent')


    async def __collect_tasks(self, urls: list, session: aiohttp.ClientSession) -> AsyncGenerator[list[dict], Any]:
        '''Collecting tasks and put on every banch of urls to request function
        It's needs because we should be nice to the server. Helps to not overload the server'''
        if not isinstance(self.step, int) and self.step <= 0:
            raise ValueError('Step to download must be a positiv integer number')
        tasks = set()
        step = self.step if len(urls) >= self.step else 1
        for index in range(0, len(urls), step):
            for url in urls[index:index+step]:
                tasks.add(asyncio.create_task(self.__get_page_source(url, session))) # adding every task to the task_creator function
          
            yield await asyncio.gather(*tasks) # returning sequence list depends on step.
            tasks.clear()
       
        
    async def _collect_data(self, urls: list) -> AsyncGenerator[dict, Any]:
        '''Creating session and delegate response'''
        async with aiohttp.ClientSession(headers=self._headers, cookies=self._cookies) as session:
            async for urls in  self.__collect_tasks(urls, session):
                yield urls # delegate response list to other function


    async def _get_track_id(self) -> list[str] | dict:
        '''Looking for the key of music to fetch information after'''
        pages = await self._get_pagination()
        keys = set()

        with alive_bar(title='Collecting tracks id: ', bar='smooth') as bar:
            async for urls_response in self._collect_data(pages):
                for response in urls_response:
                    soup = BS(response['_content'], 'lxml') # because 'response' variable is a dict we need to get only response in
                    items = soup.select("div.row > div.col-lg-2.item")
                    for item in items:
                        key = item.select_one('a.btn.black.player-play')
                        if key:
                            keys.add(key.get('data-tid'))
                        bar()

        return [f'https://ncs.io/track/info/{track_id}' for track_id in keys]


    async def _get_track_info(self, track_id: list=None) -> tuple[list]:
        '''Fetching track name/description and link to download after.'''
        tracks_id = await self._get_track_id() if not track_id else track_id
        data = {}
        with alive_bar(title='Download: ', bar='smooth') as bar:
            async for urls_response in self._collect_data(tracks_id):
                for response in urls_response:
                    soup = BS(response['_content'], 'lxml')
                    description = unicodedata.normalize('NFKD', soup.select_one('p[id=panel-copy]').text.strip())
                    download_link = 'https://ncs.io' + soup.select_one('a[onclick="ncs.downloadTrack(this, 1);return false;"]').get('data-href')
                    ''' An option, if you dont want to get full track name from site and want to take it from description instead
                    but you still need to put author and name in else condition, otherwise you may get NoneType.
                    
                    # check_name = re.search(r'(\b(?!(song|track|music)(:|)\b))[\w\W]+?\n', description, flags=re.ASCII|re.IGNORECASE)
                    # if check_name:
                    #     name = reduce(lambda name, repl: name.replace(*repl), self._replace_things, check_name[0].split('[')[0].split(':')[-1].strip())
                    #     name = f'{name} [NCS Release]'
                    # else: 
                    '''
                    author = soup.select_one('div.inner > h5 > span').text.strip()
                    name = f"{author} - {soup.select_one('div.inner > h5').text[:-len(author)].strip()} [NCS Release]"
                        
                    data[download_link] = {
                        'name': name,
                        'description': description,
                        }
                   
                yield data
                data.clear() # after downloading, clear the dict and fill it again
                bar()
   
    @staticmethod
    def __check_platform(folder_name: str, music_name: str) -> tuple[str, str]:
        '''Checking the using platform to correct download path'''
        if sys.platform == 'win32':
            folder = f'{os.getcwd()}\\NCS\\{folder_name}\\'
            os.makedirs(folder, exist_ok=True)
            music_folder = f'{folder}{music_name}'
            description_folder = f'{folder}{folder_name}.txt'
        else: 
            folder = f'{os.getcwd()}/NCS/{folder_name}/'
            os.makedirs(folder, exist_ok=True)
            music_folder = f'{folder}{music_name}'
            description_folder = f'{folder}{folder_name}.txt'
            
        return music_folder, description_folder

    async def download_all(self, match: list=None, set_description=True) -> None:
        '''Downloading track by step'''
        matches = self._get_track_info() if not match else match
        async for data in matches:
            async for urls_response in self._collect_data(tuple(data.keys())): # unpacking only urls for requests
                for response in urls_response:
                    try:
                        if response: # because we can get NoneType here we should check it
                            name = response['headers'].get('Content-Disposition').split('"')[-2] # unpacking extension and name
                            name = unicodedata.normalize('NFKD', reduce(lambda name, repl: name.replace(*repl), self._replace_things, name))
                            
                            folder_name = reduce(lambda name, repl: name.replace(*repl), self._replace_things, data[response['url']]['name'])
                            description = data[response['url']]['description'] # check if url has same response and description
                            music_name = f'{folder_name}{name[-4:]}' if name.endswith(('.mp3', '.wav')) else f'{folder_name}.mp3'
                            music_folder, description_folder = self.__check_platform(folder_name, music_name)
                            if set_description:
                                with (
                                    open(music_folder, 'wb') as music_file,
                                    open(description_folder, 'w', encoding='utf-8') as description_file,
                                ):   
                                    music_file.write(response['_content']) # unpacking bytes to write
                                    description_file.write(description)
                                info(f'{music_name} - Done!')
                            else:
                                with open(music_folder, 'wb') as music_file:
                                    music_file.write(response['_content'])
                                info(f'{music_name} - Done!')
                    except Exception as ex:
                        error(f'Unexpected issue {ex}')
                 

    async def search_and_download(self, 
                                   title: str=None, 
                                   author: str=None, 
                                   first: bool=False, 
                                   all_matches: bool=True, 
                                   set_description: bool=True, 
                                   _retry: bool=False) -> None:
        '''Searching by name or by title. Or by title and name at the same time
        NOTE:   title and author shouldnt content punctuation, only a spaces'''
        if first: all_matches = False 
        if all_matches: first = False
        if all([author, title]):
            # if author and title are not empty
            search_author = author.replace(' ', '+') if ' ' in author else author
            search_title = title.replace(' ', '+') if ' ' in title else title
            url = f'https://ncs.io/music-search?q={search_author}'
            if _retry: # if searching by author has no result -> trying to search by title. Otherwise need to check inputs or track doesnt exists in library.
                url = f'https://ncs.io/music-search?q={search_title}'
        else:
            if author:
                search_author = author.replace(' ', '+') if ' ' in author else author
                url = f'https://ncs.io/music-search?q={search_author}'
            if title:
                search_title = title.replace(' ', '+') if ' ' in title else title
                url = f'https://ncs.io/music-search?q={search_title}'
           
        tracks_id = set()
        async for url_response in self._collect_data([url]):
            soup = BS(url_response[0]['_content'], 'lxml')
            items = soup.select('table a')
         
            for item in items:
                track_id = item.get('data-tid')
                # first of all checking both author and title
                if all([title, author]):
                    track_title = item.get('data-track')
                    track_author = item.get('data-artist')
                    if all([track_author, track_id, track_title]):
                        if re.search(author.lower().strip(), track_author.lower().strip(), flags=re.ASCII) and track_title.lower().strip() == title.lower().strip():
                            if first:
                                matches = self._get_track_info(track_id=[f'https://ncs.io/track/info/{track_id}'])
                                return await self.download_all(match=matches, set_description=set_description)
                            if all_matches:
                                tracks_id.add(track_id)
                # if was chosen only author or only title          
                else:
                    if title: 
                        track = item.get('data-track')
                        input_name = title
                    if author:
                        input_name = author
                        track = item.get('data-artist')
                    if all([track, track_id]):
                        if input_name.lower().strip() == track.lower().strip() or re.search(input_name.lower().strip(), track.lower().strip(), re.ASCII):
                            if first:
                                matches = self._get_track_info(track_id=[f'https://ncs.io/track/info/{track_id}'])
                                return await self.download_all(match=matches, set_description=set_description)
                            if all_matches:
                                tracks_id.add(track_id)
        if _retry and not tracks_id:
            raise ValueError('Did you miss up title or author search? If not, try to change a word you looking for.')
                                  
        if tracks_id:       
            matches = self._get_track_info(track_id=[f'https://ncs.io/track/info/{track_id}' for track_id in tracks_id])
            return await self.download_all(match=matches, set_description=set_description)
        if not tracks_id:
            return await self.search_and_download(title=title,
                                                   author=author,
                                                   first=first,
                                                   all_matches=all_matches,
                                                   set_description=set_description,
                                                   _retry=True)

                      
