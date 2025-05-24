from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards.statisticskb import *
from keyboards.menu import main_menu
from db import db
from datetime import datetime,timedelta
import pytz
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from states.states import DatePicker

statistics_router = Router()

@statistics_router.callback_query(F.data == "Statistics")
async def statistics_main(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "Выберите, какую статистику хотите посмотреть:",
        reply_markup=statistics_keyboard()
    )
    await callback_query.answer()

@statistics_router.callback_query(F.data == "stats_day")
async def statistics_day(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)
    date = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d")
    text = ""
    if position == "Supervisor":
        stats = db.get_status_counts_by_date(date)
        text = "Статус: \n"
        for status, count in stats.items():
            text+=(f"{status}: {count}\n")
            
    else:
        stats = db.get_status_counts_by_date_and_worker(date,user_id)
        text = "Статус: \n"
        for status, count in stats.items():
            text+=(f"{status}: {count}\n")
    
    if not text:
        text = "Нет задач на сегодня"
    await callback_query.message.edit_text(text, reply_markup=main_menu())

@statistics_router.callback_query(F.data == "stats_week")
async def statistics_week(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)

    tz = pytz.timezone("Europe/Moscow")
    end_date = datetime.now(tz).date()
    start_date = end_date - timedelta(days=6)  # Неделя, включая сегодня

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    text = f" Статистика с {start_str} по {end_str}:\n\n"

    if position == "Supervisor":
        stats = db.get_status_counts_by_date_range(start_str, end_str)
        text = "Статус: \n"
        for status, count in stats.items():
            text += f"{status}: {count}\n"
    else:
        stats = db.get_status_counts_by_date_range_and_worker(start_str, end_str, user_id)
        text = "Статус: \n"
        for status, count in stats.items():
            text += f"{status}: {count}\n"

    if not stats:
        text = "Нет задач за последнюю неделю."

    await callback_query.message.edit_text(text, reply_markup=main_menu())

@statistics_router.callback_query(F.data == "stats_custom_date")
async def choose_dates(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Выберите начальную дату:", reply_markup=await SimpleCalendar().start_calendar())
    await state.set_state(DatePicker.waiting_for_start_date)

@statistics_router.callback_query(SimpleCalendarCallback.filter(), DatePicker.waiting_for_start_date)
async def start_date_chosen(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(start_date=date)
        await callback_query.message.edit_text("Выберите конечную дату:", reply_markup=await SimpleCalendar().start_calendar())
        await state.set_state(DatePicker.waiting_for_end_date)

@statistics_router.callback_query(SimpleCalendarCallback.filter(), DatePicker.waiting_for_end_date)
async def end_date_chosen(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    user_id = callback_query.from_user.id
    position = db.is_supervisor(user_id)
    if selected:
        data = await state.get_data()
        start_date = data.get("start_date")

        if date < start_date:
            await callback_query.message.edit_text("Ошибка: конечная дата раньше начальной. Выберите снова.",
                                          reply_markup=await SimpleCalendar().start_calendar())
            return
        text = ""
        if position == "Supervisor":
            stats = db.get_status_counts_by_date_range(start_date,date)
            start_date_formatted = start_date.strftime("%Y-%m-%d")
            date_formatted = date.strftime("%Y-%m-%d")
            text+=(f"Заявки с {start_date_formatted}, по {date_formatted}\nСтатус:\n")
            for status, count in stats.items():
                text+=(f"{status}: {count}\n")
                
        else:
            stats = db.get_status_counts_by_date_range_and_worker(start_date,date,user_id)
            start_date_formatted = start_date.strftime("%Y-%m-%d")
            date_formatted = date.strftime("%Y-%m-%d")
            text+=(f"Заявки с {start_date_formatted}, по {date_formatted}\nСтатус:\n")
            for status, count in stats.items():
                text+=(f"{status}: {count}\n")
        
        if not text:
            text = "Нет задач за выбранный период времени"
        await callback_query.message.edit_text(text, reply_markup=main_menu())
        await state.clear()