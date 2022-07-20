#!/usr/bin/env python3
from aiogram import Bot, Dispatcher, executor, types 
from aiogram.dispatcher.filters import Text 

import shutil, os, sys

from config.config import TOKEN
from markups.markups import main_menu, KEYWORDS, ncs_menu, youtube_menu, retry_menu, ncs_buttons, youtube_buttons
from parser.instagram import Instagram
from parser.ncs_library import NcsLibrary
from parser.youtube import Converter
from switch_handlers.switches import Handler
from config.logguru_log import error
    

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message): 
    await message.answer('Select button below ↓', reply_markup=main_menu)

@dp.message_handler(Text(equals=KEYWORDS))
async def menu(message: types.Message):    
    if message.text == 'Instagram':
        await message.answer('Enter a username or link')
        Handler.instagram = True
    elif message.text == 'NCS Library':
        await message.answer('Select button below ↓', reply_markup=ncs_menu)
        Handler.ncs = True
    elif message.text == 'Youtube Music':
        await message.answer('Select button below ↓', reply_markup=youtube_menu)
        Handler.youtube = True
   
@dp.message_handler(Text(equals=ncs_buttons))
async def menu_ncs(message: types.Message):
    if message.text == 'Search by author':
        await message.answer('Enter an author of track:\nExample: Modern Revolt\nWords case has no matter')
        Handler.search_by_author = True
    elif message.text == 'Search by author and title':
        await message.answer('Enter an author and title of track\nExample: Modern Revolt - VOLT\nWord case has no matter')
        Handler.search_title_author = True
    elif message.text == 'Search by title':
        await message.answer('Enter an author of track:\nExample: VOLT\nWords case has no matter')
        Handler.search_by_title = True
    # else:
    #     Handler.download_all = True
        
@dp.message_handler(Text(equals=youtube_buttons))
async def menu_youtube(message: types.Message):
    if message.text == 'Download music':
        await message.answer('Enter a url of music')
        Handler.single = True
    elif message.text == 'Download video':
        await message.answer('Enter a url of video')
        Handler.video = True
    # elif message.text == 'Download music playlist':
    #     await message.answer('Enter a url of playlist with music')
    #     Handler.playlist = True
    # elif message.text == 'Download video playlist':
    #     await message.answer('Enter a url of video playlist')
    #     Handler.video_playlist = True
        

@dp.message_handler(Text(equals='No, thanks'))
async def stop(message: types.Message):
    await message.answer('Ok, goodbye!')
    
@dp.message_handler(Text(equals='To main menu'))
async def continues(message: types.Message):
    await message.answer('Select button below ↓', reply_markup=main_menu)

@dp.message_handler()
async def all_messages(message: types.Message):
    if Handler.instagram:
        try:
            await message.answer('Wait a second...')
            if '/' in message.text:
                message.text = message.text.split('/')[-1].strip()
                if '?' in message.text:
                    message.text = message.text.split('?')[0].strip()
            file = await Instagram(message.text)._image_download()
        except Exception:
            await message.answer('Something goes wrong. Try to write username again')
        else:
            Handler.set_all()
            await bot.send_document(message.chat.id, document=open(file, 'rb'))
            shutil.rmtree(message.text)
            os.remove(file)
            await message.answer('Do you want something else?', reply_markup=retry_menu)
    elif Handler.ncs:
        try:
            if Handler.search_by_author:
                await message.answer('Wait a second...')
                await NcsLibrary().search_and_download(author=message.text, first=True, set_description=False)
            elif Handler.search_by_title:
                await message.answer('Wait a second...')
                print(message.text)
                await NcsLibrary().search_and_download(title=message.text, first=True, set_description=False)
            elif Handler.search_title_author:
                await message.answer('Wait a second...')
                full_name = message.text.split('-')
                await NcsLibrary().search_and_download(title=full_name[1].strip(), author=full_name[0].strip(), first=True, set_description=False)
            # elif Handler.download_all:
            #     await message.answer('Wait a second...')
            #     await NcsLibrary().download_all(set_description=False)
        except Exception:
            error(Exception.__class__.__name__)
            await message.answer('Something goes wrong. Try to write username again')
        else:
            Handler.set_all()
            path = f'{os.getcwd()}\\NCS' if sys.platform == 'win32' else f'{os.getcwd()}/NCS'
            if os.path.exists(path):
                shutil.make_archive('NCS', 'zip', 'NCS')
                file = 'NCS.zip'
                try:
                    await bot.send_document(message.chat.id, document=open(file, 'rb'))
                except Exception:
                    error(Exception.__class__.__name__)
                    await message.answer('Guess file is too large, cant upload')
                    
            await message.answer('Do you want something else?', reply_markup=retry_menu)
        finally:
            shutil.rmtree('NCS')
            os.remove(file)
    elif Handler.youtube:
        try:
            if Handler.single:
                await message.answer('Wait a second...')
                file = Converter(single_url=message.text).convert_single(audio=True)
            # elif Handler.playlist:
            #     await message.answer('Wait a second...')
            #     file = Converter(playlist_url=message.text).convert_playlist(audio=True)
            elif Handler.video:
                await message.answer('Wait a second...')
                file = Converter(single_url=message.text).convert_single(video=True)
            # elif Handler.video_playlist:
            #     await message.answer('Wait a second...')
            #     file = Converter(playlist_url=message.text).convert_playlist(video=True)
        except Exception:
            await message.answer('Something goes wrong. Try to write username again')
        else:
            Handler.set_all()
            if file.endswith('.mp4'):
                await bot.send_video(message.chat.id, video=open(file, 'rb'))
            elif file.endswith('.mp3'):
                await bot.send_audio(message.chat.id, audio=open(file, 'rb'))
            else:
                await bot.send_document(message.chat.id, document=open(file, 'rb'))
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
            await message.answer('Do you want something else?', reply_markup=retry_menu)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)