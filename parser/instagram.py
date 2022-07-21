# dependecies
# import asyncio
import aiohttp
# build-in imports
from datetime import datetime
import sys, os, json, shutil
# self imports except loguru in
from config.logguru_log import info
from .auth import InstagramAuth
from .ncs_library import NcsLibrary
from config.config import INSTA_HEADERS, USER_AGENT


class Instagram(NcsLibrary, InstagramAuth):
    __slots__ = ('username',)
    '''An instagram images parser.
    >>> Instagram('<username_to_search>').image_download() # example
    It will create a folder with all user images.'''
    def __init__(self, username: str, step: int=10, user_agent: str=USER_AGENT) -> None:
        super().__init__(step, user_agent)
        self._cookies = self._check_cookies()
        INSTA_HEADERS['x-csrftoken'] = self._cookies['csrftoken']
        INSTA_HEADERS['user-agent'] = self.user_agent
        self._headers = INSTA_HEADERS
        if '/' in username:
            username = username.split('/')[-1].strip()
            if '?' in username:
                username = username.split('?')[0].strip()
        self.username = username
        
    def _check_cookies(self) -> dict:
        '''A function that's check if cookies exists and it's not old'''
        path_to_log  = f'{self.path}\\insta_log.txt' if sys.platform == 'win32' else f'{self.path}/insta_log.txt'
        if not os.path.exists(path_to_log):
            self.authorization()
        
        time_now = datetime.now().strftime('%Y.%m.%d::%H.%M')
        with open(path_to_log, 'r', encoding='utf-8') as f:
            time_created = f.read()

        if time_created.split('::')[-2] != time_now.split('::')[-2]: # check on day/month/year
            self.authorization()   
        elif abs(float(time_created.split('::')[-1]) - float(time_now.split('::')[-1])) > 20: # a life time of cookies
            self.authorization()

        return self.get_cookie()
    
    # def image_download(self) -> str:
    #     return asyncio.run(self._image_download())
    
    async def collect_image_urls(self) -> list:
        '''Collecting image urls'''
        images_links = [] 
        
        async with aiohttp.ClientSession(headers=self._headers, cookies=self._cookies) as session:
            params = {
                'username': f'{self.username}',
            }
            count = 1
            async with session.get(url='https://i.instagram.com/api/v1/users/web_profile_info/', params=params) as response:
                if response.status != 200:
                    raise TimeoutError('Check connection, cookies or useragent that\'s you\'re using')
                
                data_dict = await response.json()
                user_id = data_dict['data']['user'].get('id')
                images_count = int(data_dict['data']['user']['edge_owner_to_timeline_media'].get('count'))
                if not images_count:
                    raise ValueError('A user that you looking for has no images')
                
                next_dict = data_dict['data']['user']['edge_owner_to_timeline_media']['page_info'].get('end_cursor', None)
                content = data_dict['data']['user']['edge_owner_to_timeline_media']['edges']
                for image in content:
                    images_links.append(image['node'].get('display_url'))
                    info(f'fetching {count}/{images_count}')
                    count += 1
            while next_dict:
                params = {
                    'query_hash': '69cba40317214236af40e7efa697781d',
                    'variables': json.dumps({'id': user_id, 'first': 50, 'after': next_dict}), # looking for a key to next json data
                }
                async with session.get(url='https://www.instagram.com/graphql/query/', params=params) as response:
                    if response.status != 200:
                        raise TimeoutError('Check connection, cookies or useragent that\'s you\'re using')
                    
                    data_dict = await response.json()
                    next_dict = data_dict['data']['user']['edge_owner_to_timeline_media']['page_info'].get('end_cursor', None)
                    content = data_dict['data']['user']['edge_owner_to_timeline_media']['edges']
                    for image in content:
                        images_links.append(image['node'].get('display_url'))
                        info(f'fetching {count}/{images_count}')
                        count += 1
            info(f'Fetched {len(images_links)} of {images_count}')
            
        return images_links
      
    async def _image_download(self) -> None:
        '''Dowloading by step'''
        path_to_media = f'{os.getcwd()}\\{self.username}\\' if sys.platform == 'win32' else f'{os.getcwd()}/{self.username}/'
        links = await self.collect_image_urls()
        count = 1
        info('Downloading...')
        async for links_response in self._collect_data(links): # collect response by step
            for response in links_response:
                os.makedirs(path_to_media, exist_ok=True)
                with open(f'{path_to_media}image_{count}.jpg', 'wb') as file:
                    file.write(response['_content'])
                count += 1
        info('Done!')
        return self._archive()

    def _archive(self) -> str:
        path_to_media = f'{os.getcwd()}\\{self.username}\\' if sys.platform == 'win32' else f'{os.getcwd()}/{self.username}/'
        if not os.path.exists(path_to_media):
            raise NotADirectoryError('A directory that\'s need to compress doesn\'t exists')
        
        shutil.make_archive(f'{self.username}', 'zip', f'{self.username}')
        return f'{self.username}.zip'
        
    
