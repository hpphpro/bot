from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


KEYWORDS = ('Instagram', 'NCS Library', 'Youtube Music',)

# ---> main menu <---
retry_btns = ('To main menu', 'No, thanks',)
retry_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*retry_btns)
main_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*KEYWORDS)


# ---> NCS menu <---
ncs_buttons = ('Search by author', 'Search by title', 'Search by author and title',) # 'Download full library',)
ncs_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*ncs_buttons)

# ---> Youtube menu <---
youtube_buttons = ('Download music', 'Download video',) #'Download music playlist', 'Download video playlist',)
youtube_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*youtube_buttons)