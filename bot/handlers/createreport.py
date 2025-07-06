from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.menu import main_menu
from db import db
from datetime import datetime, timedelta
import pytz
import reportopex
from aiogram.filters.state import StateFilter
from aiogram.types import FSInputFile
import os
report_router = Router()

class ReportSG(StatesGroup):
    waiting_for_worker = State()
    waiting_for_period = State()

@report_router.callback_query(F.data == "ReportOpex")
async def start_report(cb: CallbackQuery, state: FSMContext):
    user_id = cb.from_user.id
    role = db.is_supervisor(user_id)
    if role == "Supervisor":
        workers = db.get_workers() 
        kb_buttons = [
            [InlineKeyboardButton(text="По всем работникам", callback_data="report_worker:all")]
        ]
        for w_id, fio in workers:
            kb_buttons.append(
                [InlineKeyboardButton(text=fio, callback_data=f"report_worker:{w_id}")]
            )
        kb_buttons.append([InlineKeyboardButton(text="Отмена", callback_data="Main_Menu")])

        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)

        await state.set_state(ReportSG.waiting_for_worker)
        await cb.message.edit_text(
            "Выберите рабочего для отчёта:",
            reply_markup=kb
        )
    else:
        await state.update_data(worker_id=str(user_id))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text = "За 2 недели", callback_data="report_period:2weeks"),
                InlineKeyboardButton(text = "За месяц",    callback_data="report_period:1month"),
            ],
            [
                InlineKeyboardButton(text = "Отмена", callback_data="Main_Menu")
            ]
        ])
        await state.set_state(ReportSG.waiting_for_period)
        await cb.message.edit_text(
            "Выберите период для вашего отчёта:",
            reply_markup=kb
        )
    await cb.answer()

@report_router.callback_query(
    F.data.startswith("report_worker:"),
    StateFilter(ReportSG.waiting_for_worker)
)
async def choose_worker(cb: CallbackQuery, state: FSMContext):
    _, w_id = cb.data.split(":", 1)
    await state.update_data(worker_id=w_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="За 2 недели", callback_data="report_period:2weeks"),
            InlineKeyboardButton(text="За месяц",    callback_data="report_period:1month")
        ],
        [
            InlineKeyboardButton(text="Отмена",    callback_data="Main_Menu")
        ]
    ])

    await state.set_state(ReportSG.waiting_for_period)
    await cb.message.edit_text("Выберите период для отчёта:", reply_markup=kb)
    await cb.answer()

@report_router.callback_query(
    F.data.startswith("report_period:")
)
async def generate_report(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    w_id = data["worker_id"]
    _, period = cb.data.split(":", 1)

    tz = pytz.timezone("Europe/Moscow")
    today = datetime.now(tz).date()
    if period == "2weeks":
        start_date = today - timedelta(weeks=2)
    else:
        start_date = today - timedelta(days=30)
    end_date = today

    output_path = f"OPEX_{w_id}_{start_date}_{end_date}.xlsx"
    if w_id == "all":
        output_path = f"OPEX_ALL_{start_date}_{end_date}.xlsx"
        ok = reportopex.fill_report_for_all(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            output=output_path
        )
    else:
        output_path = f"OPEX_{w_id}_{start_date}_{end_date}.xlsx"
        ok = reportopex.fill_report_for(
            worker_id=w_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            output=output_path
        )

    if not ok:
        await cb.message.edit_text("Нет данных за этот период.", reply_markup=main_menu())
        await state.clear()
        return await cb.answer()

    await cb.message.answer_document(FSInputFile(output_path))
    await cb.message.answer("Отчёт готов!", reply_markup=main_menu())
    try:
        os.remove(output_path)
    except OSError:
        pass
    await state.clear()
    await cb.answer()

