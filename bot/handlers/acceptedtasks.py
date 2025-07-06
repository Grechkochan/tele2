from aiogram.types import CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from db import db
from keyboards.task_keyboards import create_supervisor_keyboard, create_worker_keyboard, create_accepted_period_keyboard
from keyboards.menu import main_menu
from datetime import datetime, timedelta
import pytz
from aiogram.types import InlineKeyboardButton
menu_router = Router()

@menu_router.callback_query(F.data == "Accepted_Tasks")
async def period_accepted_tasks(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Выберите период для отображения задач:",
        reply_markup=create_accepted_period_keyboard()
    )
    await callback_query.answer()

@menu_router.callback_query(F.data == "Accepted_Tasks_Today")
async def accepted_tasks_today(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)
    today = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d")
    if position == "Supervisor":
        tasks = db.get_accepted_tasks_day(today)
        role = "Supervisor"
    else:
        tasks = db.get_accepted_tasks_day_worker(today,user_id)
        role = "Worker"

    if not tasks:
        await callback_query.message.edit_text("Нет задач за сегодня.", reply_markup=main_menu())
        await callback_query.answer()
        return

    await state.update_data(tasks=tasks, current_page=0, role=role)

    if role == "Supervisor":
        keyboard = create_supervisor_keyboard(tasks, page=0)
        await callback_query.message.edit_text("Задачи за сегодня:", reply_markup=keyboard)
    else:
        task = tasks[0]
        _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
        fio = db.get_fio_worker(assigned_to)

        message_text = (
            f"<b>Номер задачи:</b> {task_number}\n"
            f"<b>Базовая станция:</b> {base_station}\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Исполнитель:</b> {fio}\n"
            f"<b>Выдана:</b> {issue_time}\n"
            f"<b>Время прибытия:</b> {timereq}\n"
            f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
            f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
            f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
            f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
            f"<b>Описание:</b> {description if description else '—'}\n"
            f"<b>Комментарии:</b> {comments if comments else '—'}\n"
            f"<b>Адрес:</b> {address if address else '—'}\n"
            f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
        )

        keyboard = create_worker_keyboard(0, len(tasks), task_number)
        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()

@menu_router.callback_query(F.data == "Accepted_Tasks_Week")
async def accepted_tasks_today(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)
    tz = pytz.timezone("Europe/Moscow")
    end_date_dt = datetime.now(tz).date()
    start_date_dt = end_date_dt - timedelta(days=6)

    end_date = end_date_dt.strftime("%Y-%m-%d")
    start_date = start_date_dt.strftime("%Y-%m-%d")
    if position == "Supervisor":
        tasks = db.get_accepted_tasks_week(start_date,end_date)
        role = "Supervisor"
    else:
        tasks = db.get_accepted_tasks_week_worker(start_date,end_date,user_id)
        role = "Worker"

    if not tasks:
        await callback_query.message.edit_text("Нет задач за неделю.", reply_markup=main_menu())
        await callback_query.answer()
        return

    await state.update_data(tasks=tasks, current_page=0, role=role)

    if role == "Supervisor":
        keyboard = create_supervisor_keyboard(tasks, page=0)
        await callback_query.message.edit_text("Задачи за неделю:", reply_markup=keyboard)
    else:
        task = tasks[0]
        _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
        fio = db.get_fio_worker(assigned_to)

        message_text = (
            f"<b>Номер задачи:</b> {task_number}\n"
            f"<b>Базовая станция:</b> {base_station}\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Исполнитель:</b> {fio}\n"
            f"<b>Выдана:</b> {issue_time}\n"
            f"<b>Время прибытия:</b> {timereq}\n"
            f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
            f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
            f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
            f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
            f"<b>Описание:</b> {description if description else '—'}\n"
            f"<b>Комментарии:</b> {comments if comments else '—'}\n"
            f"<b>Адрес:</b> {address if address else '—'}\n"
            f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
        )

        keyboard = create_worker_keyboard(0, len(tasks), task_number)
        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()


@menu_router.callback_query(F.data == "All_Accepted_Tasks")
async def accepted_tasks(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)

    if position == "Supervisor":
        tasks = db.all_in_acc()
        role = "Supervisor"
    else:
        tasks = db.tasks_by_worker(user_id)
        role = "Worker"

    if not tasks:
        await callback_query.message.edit_text("Нет задач в работе.", reply_markup=main_menu())
        await callback_query.answer()
        return

    await state.update_data(tasks=tasks, current_page=0, role=role)

    if role == "Supervisor":
        keyboard = create_supervisor_keyboard(tasks, page=0)
        await callback_query.message.edit_text("Выберите заявку для просмотра:", reply_markup=keyboard)
    else:
        task = tasks[0]
        _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
        fio = db.get_fio_worker(assigned_to)

        message_text = (
            f"<b>Номер задачи:</b> {task_number}\n"
            f"<b>Базовая станция:</b> {base_station}\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Исполнитель:</b> {fio}\n"
            f"<b>Выдана:</b> {issue_time}\n"
            f"<b>Время прибытия:</b> {timereq}\n"
            f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
            f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
            f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
            f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
            f"<b>Описание:</b> {description if description else '—'}\n"
            f"<b>Комментарии:</b> {comments if comments else '—'}\n"
            f"<b>Адрес:</b> {address if address else '—'}\n"
            f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
        )

        keyboard = create_worker_keyboard(0, len(tasks), task_number)
        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()

@menu_router.callback_query(F.data.in_(["next_page", "prev_page"]))
async def switch_page(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get("tasks", [])
    page = data.get("current_page", 0)

    tasks_per_page = 5
    max_page = (len(tasks) - 1) // tasks_per_page

    if callback_query.data == "next_page":
        page += 1
    elif callback_query.data == "prev_page":
        page -= 1

    page = max(0, min(page, max_page))
    await state.update_data(current_page=page)

    keyboard = create_supervisor_keyboard(tasks, page)
    await callback_query.message.edit_text("Выберите заявку для просмотра:", reply_markup=keyboard)
    await callback_query.answer()


@menu_router.callback_query(F.data.in_(["next_task", "prev_task"]))
async def switch_worker_task(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tasks = data.get("tasks", [])
    index = data.get("current_page", 0)

    if callback_query.data == "next_task" and index < len(tasks) - 1:
        index += 1
    elif callback_query.data == "prev_task" and index > 0:
        index -= 1

    await state.update_data(current_page=index)

    task = tasks[index]
    _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
    fio = db.get_fio_worker(assigned_to)

    message_text = (
        f"<b>Номер задачи:</b> {task_number}\n"
        f"<b>Базовая станция:</b> {base_station}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Исполнитель:</b> {fio}\n"
        f"<b>Выдана:</b> {issue_time}\n"
        f"<b>Время прибытия:</b> {timereq}\n"
        f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
        f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
        f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
        f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
        f"<b>Описание:</b> {description if description else '—'}\n"
        f"<b>Комментарии:</b> {comments if comments else '—'}\n"
        f"<b>Адрес:</b> {address if address else '—'}\n"
        f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
    )

    keyboard = create_worker_keyboard(index, len(tasks), task_number)
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


@menu_router.callback_query(F.data.startswith("view_task:"))
async def view_task(callback_query: CallbackQuery, state: FSMContext):
    task_number = callback_query.data.split(":")[1]
    task = db.get_task_by_number(task_number)

    if not task:
        await callback_query.answer("Заявка не найдена.", show_alert=True)
        return

    _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
    fio = db.get_fio_worker(assigned_to)

    message_text = (
        f"<b>Номер задачи:</b> {task_number}\n"
        f"<b>Базовая станция:</b> {base_station}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Исполнитель:</b> {fio}\n"
        f"<b>Выдана:</b> {issue_time}\n"
        f"<b>Время прибытия:</b> {timereq}\n"
        f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
        f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
        f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
        f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
        f"<b>Описание:</b> {description if description else '—'}\n"
        f"<b>Комментарии:</b> {comments if comments else '—'}\n"
        f"<b>Адрес:</b> {address if address else '—'}\n"
        f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
    )

    data = await state.get_data()
    tasks = data.get("tasks", [])
    current_page = data.get("current_page", 0)

    keyboard = create_supervisor_keyboard(tasks, page=current_page)
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="Закрыть заявку",
            callback_data=f"close_task:{task_number}"
        )
    ])
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()

