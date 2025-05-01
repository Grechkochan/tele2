from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def statistics_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика за день", callback_data="stats_day")],
        [InlineKeyboardButton(text="Статистика за неделю", callback_data="stats_week")],
        [InlineKeyboardButton(text="Выбор по дате", callback_data="stats_custom_date")],
        [InlineKeyboardButton(text="Назад", callback_data="Main_Menu")]
    ])
    return keyboard
