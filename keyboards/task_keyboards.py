from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_supervisor_keyboard(tasks, page):
    keyboard = []
    start = page * 5
    end = start + 5
    for task in tasks[start:end]:
        task_number = task[1]
        keyboard.append([InlineKeyboardButton(text=f"Заявка №{task_number}", callback_data=f"view_task:{task_number}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_page"))
    if end < len(tasks):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data="next_page"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="Главное меню", callback_data="Main_Menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_worker_keyboard(current_index, total_tasks):
    keyboard = []

    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Предыдущая", callback_data="prev_task"))
    if current_index < total_tasks - 1:
        nav_buttons.append(InlineKeyboardButton(text="Следующая ➡️", callback_data="next_task"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="Главное меню", callback_data="Main_Menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_accepted_period_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="За день", callback_data="Accepted_Tasks_Today")],
        [InlineKeyboardButton(text="За неделю", callback_data="Accepted_Tasks_Week")],
        [InlineKeyboardButton(text="За всё время", callback_data="All_Accepted_Tasks")],
        [InlineKeyboardButton(text="Главное меню", callback_data="Main_Menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_new_period_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="За день", callback_data="New_Tasks_Today")],
        [InlineKeyboardButton(text="За неделю", callback_data="New_Tasks_Week")],
        [InlineKeyboardButton(text="За всё время", callback_data="All_New_Tasks")],
        [InlineKeyboardButton(text="Главное меню", callback_data="Main_Menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page-1}"))
    if end < len(tasks):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page:{page+1}"))
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

def get_tasks_keyboard(tasks, page=0):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    start = page * 5
    end = start + 5
    page_tasks = tasks[start:end]

    buttons = [
        [InlineKeyboardButton(text=f"{t['title']}", callback_data=f"view_task:{t['id']}")]
        for t in page_tasks
    ]
    keyboard.inline_keyboard.extend(buttons)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"nav:{page - 1}"))
    if end < len(tasks):
        nav_buttons.append(InlineKeyboardButton(text="➡ Далее", callback_data=f"nav:{page + 1}"))
    keyboard.inline_keyboard.append(nav_buttons)

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")])
    return keyboard

def confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Да", callback_data="confirm_cancel")],
        [InlineKeyboardButton(text="Нет", callback_data="back_to_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

