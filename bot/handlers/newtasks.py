from aiogram.types import CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from db import db
from keyboards.menu import main_menu
from keyboards.task_keyboards import create_new_period_keyboard, generate_tasks_keyboard
from states.states import TaskPagination
from datetime import datetime, timedelta
import pytz
new_tasks_router = Router()


@new_tasks_router.callback_query(F.data == "New_Tasks")
async def period_new_tasks(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Выберите период для отображения задач:",
        reply_markup=create_new_period_keyboard()
    )
    await callback_query.answer()

@new_tasks_router.callback_query(F.data == "New_Tasks_Today")
async def new_tasks_today(callback_query: CallbackQuery, state: FSMContext):
    today = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d")
    tasks = db.get_new_tasks_today(today)
    if not tasks:
        await callback_query.message.edit_text("Нет задач за сегодня.", reply_markup=main_menu())
        await callback_query.answer()
        return
    await state.update_data(tasks=tasks, current_page=0)
    keyboard = generate_tasks_keyboard(tasks, page=0)
    await callback_query.message.edit_text("Не принятые задачи за сегодня:", reply_markup=keyboard)
    await callback_query.answer()

@new_tasks_router.callback_query(F.data == "New_Tasks_Week")
async def new_tasks_today(callback_query: CallbackQuery, state: FSMContext):
    tz = pytz.timezone("Europe/Moscow")
    end_date_dt = datetime.now(tz).date()
    start_date_dt = end_date_dt - timedelta(days=6)

    end_date = end_date_dt.strftime("%Y-%m-%d")
    start_date = start_date_dt.strftime("%Y-%m-%d")
    tasks = db.get_new_tasks_week(start_date, end_date)
    if not tasks:
        await callback_query.message.edit_text("Нет задач за неделю.", reply_markup=main_menu())
        await callback_query.answer()
        return

    await state.update_data(tasks=tasks, current_page=0)
    keyboard = generate_tasks_keyboard(tasks, page=0)
    await callback_query.message.edit_text("Не принятые задачи за неделю:", reply_markup=keyboard)
    await callback_query.answer()

@new_tasks_router.callback_query(F.data == "All_New_Tasks")
async def all_new_tasks(callback_query: CallbackQuery, state: FSMContext):
    tasks = db.all_in_new()
    await state.update_data(tasks=tasks, page=0)
    keyboard = generate_tasks_keyboard(tasks, page=0)
    await callback_query.message.edit_text("Список заявок:", reply_markup=keyboard)
    await state.set_state(TaskPagination.page)

@new_tasks_router.callback_query(F.data.startswith("page:"))
async def paginate_tasks_callback(callback: CallbackQuery, state: FSMContext):
    new_page = int(callback.data.split(":")[1])
    data = await state.get_data()
    tasks = data.get("tasks", [])

    keyboard = generate_tasks_keyboard(tasks, page=new_page)
    await state.update_data(page=new_page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@new_tasks_router.callback_query(F.data.startswith("task:"))
async def task_detail(callback_query: CallbackQuery, state: FSMContext):
    task_number = callback_query.data.split(":")[1]
    task = db.get_task_by_number(task_number)
    if not task:
        await callback_query.answer("Заявка не найдена.", show_alert=True)
        return
    _, task_number, base_station, status, _, issue_time, timereq, _, _, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task

    message_text = (
        f"<b>Номер задачи:</b> {task_number}\n"
        f"<b>Базовая станция:</b> {base_station}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Выдана:</b> {issue_time}\n"
        f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
        f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
        f"<b>Описание:</b> {description if description else '—'}\n"
        f"<b>Комментарии:</b> {comments if comments else '—'}\n"
        f"<b>Адрес:</b> {address if address else '—'}\n"
        f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
    )
    data = await state.get_data()
    tasks = data.get("tasks", [])
    page = data.get("page", 0)

    keyboard = generate_tasks_keyboard(tasks, page)
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()
