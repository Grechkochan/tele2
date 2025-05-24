from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_phone():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb

def reply_main_menu():
    keyboard = [
        [KeyboardButton(text="Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def main_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
                [InlineKeyboardButton(text="Принятые заявки", callback_data = "Accepted_Tasks")],
                [InlineKeyboardButton(text="Новые заявки", callback_data = "New_Tasks")],
                [InlineKeyboardButton(text="Поиск по заявке", callback_data = "Find_Task")],
                [InlineKeyboardButton(text="Статистика", callback_data = "Statistics")]

        ]
    )
    return kb

def accept_task(task_number):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принять заявку", callback_data = f"Accept_Task:{task_number}")]
        ]
    )
    return kb

def generate_tasks_keyboard(tasks, page=0, per_page=5):
    start = page * per_page
    end = start + per_page
    current_tasks = tasks[start:end]

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for task in current_tasks:
        task_number = task[1]
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Заявка №{task_number}",
                callback_data=f"task:{task_number}"
            )
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"page:{page-1}"))
    if end < len(tasks):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡", callback_data=f"page:{page+1}"))

    if nav_buttons:
        kb.inline_keyboard.append(nav_buttons)
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Главное меню", callback_data="Main_Menu")
    ])

    return kb

def create_tasks_keyboard(tasks, current_page):
    kb = []
    task_number = tasks[current_page][1]
    kb.append([InlineKeyboardButton(text=f"Посмотреть заявку №{task_number}", callback_data=f"view_task:{task_number}")])
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_task"))
    if current_page < len(tasks) - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data="next_task"))
    if nav_buttons:
        kb.append(nav_buttons)
    button = InlineKeyboardButton(text="Главное меню", callback_data = "Main_Menu")
    kb.append(button)
    return InlineKeyboardMarkup(inline_keyboard=kb)


def send_to_topic_button(task_number):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправить в топик", callback_data = f"send_to_topic:{task_number}")],
            [InlineKeyboardButton(text="Принять заявку", callback_data = f"Accept_Task:{task_number}")]
        ]
    )
    return kb

